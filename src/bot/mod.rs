use std::time::Duration;

use poise::serenity_prelude as serenity;
use redis::Client;
use sqlx::{MySql, Pool};
use tracing::info;

use crate::{env, logging};

mod checks;
mod commands;

/// User data, which is stored and accessible in all command invocations
#[derive(Debug)]
pub struct Data {
    #[allow(unused)]
    database_pool: Pool<MySql>,
    #[allow(unused)]
    redis_client: Client,
}

pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;
pub type Framework = poise::Framework<Data, Error>;

/// Entrypoint to start the Bot
pub async fn entrypoint(database_pool: Pool<MySql>, redis_client: Client) {
    info!("Starting the bot");

    let db_clone = database_pool.clone();
    let framework = Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![
                commands::ping(),
                commands::logger_pipe()
            ],
            allowed_mentions: Some({
                let mut f = serenity::CreateAllowedMentions::default();
                f.empty_parse()
                    .parse(serenity::ParseValue::Users)
                    .replied_user(true);
                f
            }),
            prefix_options: poise::PrefixFrameworkOptions {
                prefix: Some("!".into()),
                edit_tracker: Some(poise::EditTracker::for_timespan(Duration::from_secs(3600))),
                ..Default::default()
            },
            pre_command: |ctx| {
                Box::pin(async move {
                    info!(
                        guild_id = ctx.guild_id().map(|id| id.0).unwrap_or(0),
                        "Received Command from @{}, in guild {}, in channel #{}: `{}`",
                        ctx.author().name,
                        ctx.guild()
                            .map(|guild| guild.name)
                            .unwrap_or("no-guild".to_string()),
                        ctx.channel_id()
                            .name(ctx.cache())
                            .await
                            .unwrap_or("Unknown".to_string()),
                        ctx.invocation_string(),
                    );
                })
            },
            ..Default::default()
        })
        .token(env::BOT_TOKEN.get().unwrap())
        .intents(
            serenity::GatewayIntents::non_privileged() | serenity::GatewayIntents::MESSAGE_CONTENT,
        )
        .setup(|_ctx, ready, _framework| {
            Box::pin(async move {
                info!("Logged in as {}", ready.user.name);
                Ok(Data {
                    database_pool,
                    redis_client,
                })
            })
        });

    let built_framework = framework.build().await.expect("Err building poise client");

    logging::setup_discord_logging(
        built_framework.client().cache_and_http.http.clone(),
        db_clone,
    )
    .await;

    built_framework
        .start()
        .await
        .expect("Err running poise client");
}
