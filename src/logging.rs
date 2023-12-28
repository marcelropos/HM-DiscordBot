use std::collections::HashMap;
use std::env;
use std::fs;
use std::num::NonZeroU64;
use std::sync::Arc;
use std::sync::OnceLock;

use poise::serenity_prelude::futures::executor::block_on;
use poise::serenity_prelude::ChannelId;
use rolling_file::RollingConditionBasic;
use sqlx::MySql;
use sqlx::Pool;
use tracing::error;
use tracing::info;
use tracing::Level;
use tracing::Subscriber;
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::filter;
use tracing_subscriber::fmt;
use tracing_subscriber::prelude::*;
use tracing_subscriber::reload;
use tracing_subscriber::reload::Handle;
use tracing_subscriber::Registry;

use crate::bot;
use crate::mysql_lib;

const LOG_FILE_MAX_SIZE_MB: u64 = 10;
const MAX_AMOUNT_LOG_FILES: usize = 10;

static DISCORD_LAYER_CHANGE_HANDLE: OnceLock<Handle<DiscordTracingLayer, Registry>> =
    OnceLock::new();

/// Returns a WorkerGuard which needs to be dropped at the end of the main function,
/// to ensure the log files get closed.
pub async fn setup_logging() -> WorkerGuard {
    // create log dir
    fs::create_dir_all("./appdata/logs").expect("Could not create log directory");
    let absolute_path = fs::canonicalize("./appdata/logs").unwrap();
    println!("Absolute path: {absolute_path:?}");

    let (rolling_file_writer, worker_guard) = tracing_appender::non_blocking(
        rolling_file::BasicRollingFileAppender::new(
            "./appdata/logs/hm-discord-bot",
            RollingConditionBasic::new().max_size(LOG_FILE_MAX_SIZE_MB * 1024 * 1024),
            MAX_AMOUNT_LOG_FILES,
        )
        .expect("Could not create rolling file appender"),
    );

    let discord_layer = DiscordTracingLayer::new();

    let (discord_layer_reloadable, log_reload_handle) = reload::Layer::new(discord_layer);

    let discord_layer_filtered = discord_layer_reloadable
        .with_filter(filter::Targets::new().with_target("discord", Level::INFO));

    tracing_subscriber::registry()
        .with(discord_layer_filtered)
        .with(fmt::layer().compact())
        .with(fmt::layer().compact().with_writer(rolling_file_writer))
        .init();

    info!("Setup logging");

    let _ = DISCORD_LAYER_CHANGE_HANDLE.set(log_reload_handle);

    worker_guard
}

/// Panics if called twice
pub async fn setup_discord_logging(framework: Arc<bot::Framework>, db: Pool<MySql>) {
    modify_discord_layer(|discord_layer| {
        discord_layer.poise_framework = Some(framework.clone());
    });

    let http = &framework.client().cache_and_http.http;

    // Setup main logging guild/channel

    let main_guild_id: u64 = env::var("MAIN_GUILD_ID")
        .expect("No main logging guild id configured")
        .parse()
        .expect("Could not parse MAIN_GUILD_ID env variable");

    let main_guild = http
        .get_channels(main_guild_id)
        .await
        .expect("Could not get main guild");

    let main_logging_channel = main_guild[0].id;

    modify_discord_layer(|discord_layer| {
        discord_layer.main_log_channel = NonZeroU64::new(main_logging_channel.0);
    });

    // Setup logging channels per server
    let guild_to_log_channel = mysql_lib::get_all_guilds(&db).await.into_iter()
        .filter_map(|guild| {
            if let Some(logger_pipe_channel) = guild.logger_pipe_channel {
                Some((guild.guild_id.0, logger_pipe_channel.0))
            } else {
                None
            }
        })
        .collect();

    modify_discord_layer(|discord_layer| {
        discord_layer.guild_to_log_channel = guild_to_log_channel;
    });
}

fn modify_discord_layer(f: impl FnOnce(&mut DiscordTracingLayer)) {
    let result = DISCORD_LAYER_CHANGE_HANDLE.get().unwrap().modify(f);

    if let Err(err) = result {
        error!(
            error = err.to_string(),
            "Something went wrong while trying to modify the discord tracing layer"
        );
    }
}

#[allow(dead_code)]
/// Panics if called before [`install_framework`]
pub fn add_per_server_logging(guild_id: u64, log_channel_id: u64) {
    let layer_change_handle = DISCORD_LAYER_CHANGE_HANDLE.get().unwrap();
    let result = layer_change_handle.modify(|layer| {
        layer.guild_to_log_channel.insert(guild_id, log_channel_id);
    });
    if let Err(err) = result {
        error!(
            error = err.to_string(),
            "Failed to install poise framework into discord tracing layer"
        );
    }
}

struct DiscordTracingLayer {
    main_log_channel: Option<NonZeroU64>,
    poise_framework: Option<Arc<bot::Framework>>,
    /// HashMap of GuilId's -> ChannelId's
    guild_to_log_channel: HashMap<u64, u64>,
}

impl DiscordTracingLayer {
    pub fn new() -> DiscordTracingLayer {
        DiscordTracingLayer {
            main_log_channel: None,
            poise_framework: None,
            guild_to_log_channel: HashMap::new(),
        }
    }
}

impl<S> tracing_subscriber::Layer<S> for DiscordTracingLayer
where
    S: Subscriber,
{
    fn on_event(
        &self,
        event: &tracing::Event<'_>,
        _ctx: tracing_subscriber::layer::Context<'_, S>,
    ) {
        let poise_framework = if let Some(poise_framework) = &self.poise_framework {
            poise_framework
        } else {
            return;
        };

        let event_level = event.metadata().level();

        let mut message_visitor = MessageVisitor::new();
        event.record(&mut message_visitor);
        let message = message_visitor.message;

        let mut guild_id_visitor = GuildIdVisitor::new();
        event.record(&mut guild_id_visitor);
        let guild_id = guild_id_visitor.guild_id;

        let http = &poise_framework.client().cache_and_http.http;

        if let Some(channel_id) = self.main_log_channel {
            let _ = block_on(
                ChannelId(channel_id.get())
                    .send_message(http, |m| m.content(format!("{event_level} {message}"))),
            );
        }

        if let Some(guild_id) = guild_id {
            if let Some(channel_id) = self.guild_to_log_channel.get(&guild_id.get()) {
                let channel_id = ChannelId(*channel_id);
                let _ = block_on(
                    channel_id
                        .send_message(http, |m| m.content(format!("{event_level} {message}"))),
                );
            }
        }
    }
}

struct MessageVisitor {
    message: String,
}

impl MessageVisitor {
    pub fn new() -> MessageVisitor {
        MessageVisitor {
            message: String::new(),
        }
    }
}

impl tracing::field::Visit for MessageVisitor {
    fn record_debug(&mut self, field: &tracing::field::Field, value: &dyn std::fmt::Debug) {
        if field.name() == "message" {
            self.message.push_str(&format!("{value:?}"));
        }
    }
}

struct GuildIdVisitor {
    guild_id: Option<NonZeroU64>,
}

impl GuildIdVisitor {
    pub fn new() -> GuildIdVisitor {
        GuildIdVisitor { guild_id: None }
    }
}

impl tracing::field::Visit for GuildIdVisitor {
    fn record_debug(&mut self, _field: &tracing::field::Field, _value: &dyn std::fmt::Debug) {}

    fn record_u64(&mut self, field: &tracing::field::Field, value: u64) {
        if field.name() == "guild_id" {
            self.guild_id = NonZeroU64::new(value);
        }
    }
}
