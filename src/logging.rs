use std::collections::HashMap;
use std::fs;
use std::num::NonZeroU64;
use std::sync::{Arc, OnceLock};

use poise::serenity_prelude::{ChannelId, GuildId, Http};
use poise::serenity_prelude::futures::executor::block_on;
use rolling_file::RollingConditionBasic;
use sqlx::{MySql, Pool};
use tokio::task::spawn_blocking;
use tracing::{error, info, Level, Subscriber};
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{filter, fmt, Registry, reload};
use tracing_subscriber::prelude::*;
use tracing_subscriber::reload::Handle;

use crate::{env, mysql_lib};

const LOG_FILE_MAX_SIZE_MB: u64 = 10;
const MAX_AMOUNT_LOG_FILES: usize = 10;

static DISCORD_LAYER_CHANGE_HANDLE: OnceLock<Handle<DiscordTracingLayer, Registry>> =
    OnceLock::new();

/// Returns a WorkerGuard which needs to be dropped at the end of the main function,
/// to ensure the log files get closed.
pub async fn setup_logging() -> WorkerGuard {
    // create log dir
    fs::create_dir_all("./appdata/logs").expect("Could not create log directory");

    let (rolling_file_writer, worker_guard) = tracing_appender::non_blocking(
        rolling_file::BasicRollingFileAppender::new(
            "./appdata/logs/hm-discord-bot.log",
            RollingConditionBasic::new().max_size(LOG_FILE_MAX_SIZE_MB * 1024 * 1024),
            MAX_AMOUNT_LOG_FILES,
        )
        .expect("Could not create rolling file appender"),
    );

    let discord_layer = DiscordTracingLayer::new();

    let (discord_layer_reloadable, log_reload_handle) = reload::Layer::new(discord_layer);

    let discord_layer_filtered = discord_layer_reloadable
        .with_filter(filter::Targets::new().with_target("hm_discord_bot", Level::INFO));

    tracing_subscriber::registry()
        .with(discord_layer_filtered)
        .with(
            fmt::layer()
                .with_writer(std::io::stdout.with_max_level(*env::LOG_LEVEL.get().unwrap()))
                .compact(),
        )
        .with(
            fmt::layer()
                .compact()
                .with_writer(rolling_file_writer.with_max_level(*env::LOG_LEVEL.get().unwrap()))
                .with_ansi(false),
        )
        .init();

    info!("Setup logging");

    let _ = DISCORD_LAYER_CHANGE_HANDLE.set(log_reload_handle);

    worker_guard
}

/// Panics if called twice
pub async fn setup_discord_logging(discord_http: Arc<Http>, db: Pool<MySql>) {
    modify_discord_layer(|discord_layer| {
        discord_layer.discord_http = Some(discord_http.clone());
    });

    // Setup main logging guild/channel
    let main_guild_channels = discord_http
        .get_channels(*env::MAIN_GUILD_ID.get().unwrap())
        .await
        .expect("Could not get main guild");

    let main_logging_channel = main_guild_channels[0].id;

    modify_discord_layer(|discord_layer| {
        discord_layer.main_log_channel = NonZeroU64::new(main_logging_channel.0);
    });

    // Setup logging channels per server
    let guild_to_log_channel = mysql_lib::get_all_guilds(&db)
        .await
        .unwrap()
        .into_iter()
        .filter_map(|guild| {
            guild
                .logger_pipe_channel
                .map(|logger_pipe_channel| (guild.guild_id, logger_pipe_channel))
        })
        .collect();

    modify_discord_layer(|discord_layer| {
        discord_layer.guild_to_log_channel = guild_to_log_channel;
    });
}

/// Panics if called before [`setup_discord_logging`]
pub fn add_per_server_logging(guild_id: GuildId, log_channel_id: ChannelId) {
    modify_discord_layer(|layer| {
        layer.guild_to_log_channel.insert(guild_id, log_channel_id);
    });
}

/// Panics if called before [`setup_discord_logging`]
pub fn remove_per_server_logging(guild_id: GuildId) {
    modify_discord_layer(|layer| {
        layer.guild_to_log_channel.remove(&guild_id);
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

struct DiscordTracingLayer {
    main_log_channel: Option<NonZeroU64>,
    discord_http: Option<Arc<Http>>,
    /// HashMap of GuilId's -> ChannelId's
    guild_to_log_channel: HashMap<GuildId, ChannelId>,
}

impl DiscordTracingLayer {
    pub fn new() -> DiscordTracingLayer {
        DiscordTracingLayer {
            main_log_channel: None,
            discord_http: None,
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
        let discord_http = if let Some(discord_http) = &self.discord_http {
            discord_http
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

        if let Some(channel_id) = self.main_log_channel {
            let local_discord_http = discord_http.clone();
            let message_copy = message.clone();
            spawn_blocking(move || {
                let _ = block_on(
                    ChannelId(channel_id.get()).send_message(local_discord_http, |m| {
                        m.content(format!("{event_level} {}", message_copy))
                    }),
                );
            });
        }

        if let Some(guild_id) = guild_id {
            if let Some(channel_id) = self.guild_to_log_channel.get(&guild_id.get().into()) {
                let channel_id = *channel_id;
                let local_discord_http = discord_http.clone();
                spawn_blocking(move || {
                    let _ = block_on(channel_id.send_message(local_discord_http.clone(), |m| {
                        m.content(format!("{event_level} {message}"))
                    }));
                });
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
    fn record_u64(&mut self, field: &tracing::field::Field, value: u64) {
        if field.name() == "guild_id" {
            self.guild_id = NonZeroU64::new(value);
        }
    }

    fn record_debug(&mut self, _field: &tracing::field::Field, _value: &dyn std::fmt::Debug) {}
}
