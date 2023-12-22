
use std::fs;
use std::sync::Arc;
use std::sync::OnceLock;

use poise::serenity_prelude::ChannelId;
use poise::serenity_prelude::futures::executor::block_on;
use rolling_file::RollingConditionBasic;
use tracing::error;
use tracing::info;
use tracing::Level;
use tracing::Subscriber;
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::Registry;
use tracing_subscriber::filter;
use tracing_subscriber::fmt;
use tracing_subscriber::prelude::*;
use tracing_subscriber::reload;
use tracing_subscriber::reload::Handle;

use crate::bot;

const LOG_FILE_MAX_SIZE_MB: u64 = 10;
const MAX_AMOUNT_LOG_FILES: usize = 10;

static DISCORD_LAYER_CHANGE_HANDLE: OnceLock<Handle<DiscordTracingLayer, Registry>> = OnceLock::new();

/// Returns a WorkerGuard which needs to be dropped at the end of the main function,
/// to ensure the log files get closed.
/// Also returns a Handle to later change the DiscordTracingLayer,
/// for example when the configuration changes or when we create the poise framework.
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

    // TODO: Get the guild and channel id's from a proper source
    let discord_layer = DiscordTracingLayer::new(0, 0);

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

pub fn install_framework(framework: Arc<bot::Framework>) {
    let result = DISCORD_LAYER_CHANGE_HANDLE.get().unwrap().modify(|discord_layer| {
        discord_layer.set_poise_framework(framework);
    });
    if let Err(err) = result {
        error!(error = err.to_string(), "Failed to install poise framework into discord tracing layer");
    }
}

#[allow(dead_code)]
struct DiscordTracingLayer {
    main_log_guild: u64,
    main_log_channel: u64,
    poise_framework: Option<Arc<bot::Framework>>,
}

impl DiscordTracingLayer {
    pub fn new(main_log_guild: u64, main_log_channel: u64) -> DiscordTracingLayer {
        DiscordTracingLayer {
            main_log_guild,
            main_log_channel,
            poise_framework: None,
        }
    }

    #[allow(dead_code)]
    pub fn set_poise_framework(&mut self, poise_framework: Arc<bot::Framework>) {
        self.poise_framework = Some(poise_framework);
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
        let event_message = event.fields().find_map(|field| {
            if field.name() != "message" {
                return None;
            }
            Some(field.to_string())
        }).unwrap_or("No message".to_string());

        let event_guild_id = event.fields().find_map(|field| {
            if field.name() == "guild_id" {
                return Some(field.to_string());
            }
            None
        });


        let http = &poise_framework.client().cache_and_http.http;

        let channel_id = ChannelId(self.main_log_channel);

        let _ = block_on(
            channel_id.send_message(http, |m| {
                m.content(format!("{event_level} {event_message}"))
            })
        );

        if let Some(_guild_id) = event_guild_id {
            // TODO: Send message to a specific guild's log channel
        }
    }

}
