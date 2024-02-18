use std::time::SystemTime;

use poise::serenity_prelude::{GuildChannel, Role};
use poise::CreateReply;
use tracing::info;

use crate::{
    bot::{Context, Error},
    logging, mysql_lib,
};

use super::{checks, setup_command};

/// ping command
#[poise::command(slash_command, prefix_command)]
pub async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    let response = "Pong!";
    let now = SystemTime::now();
    let reply_message = ctx.say(response).await?;
    reply_message
        .edit(
            ctx,
            CreateReply::default().content(match now.elapsed() {
                Ok(elapsed) => {
                    format!("Pong: {} ms", elapsed.as_millis())
                }
                Err(_) => "Pong: could not calculate time difference".to_owned(),
            }),
        )
        .await?;
    Ok(())
}

/// admin-only. Sets the configured logger pipe channel to the current channel.
/// If the current channel is the current logger pipe channel, it will be deactivated.
#[poise::command(prefix_command, guild_only)]
pub async fn logger_pipe(ctx: Context<'_>) -> Result<(), Error> {
    // Check permissions
    if !checks::is_owner(ctx).await
        && !checks::is_admin(ctx).await
        && !checks::is_bot_admin(ctx).await
    {
        ctx.say("Missing permissions, requires admin permissions")
            .await?;
        return Ok(());
    }

    let guild_id = ctx.guild_id().unwrap();

    let db = &ctx.data().database_pool;
    let db_guild = if let Some(db_guild) = mysql_lib::get_guild(db, guild_id).await {
        db_guild
    } else {
        ctx.say("Needs to be executed in an already setup guild")
            .await?;
        return Ok(());
    };

    let current_logger_pipe = db_guild.logger_pipe_channel;

    if current_logger_pipe.is_some_and(|logger_pipe| logger_pipe == ctx.channel_id()) {
        // Current channel is logger pipe
        // => deactivate logger pipe
        info!(?guild_id, "Deactivating logger pipe");

        ctx.say("Deactivating logger pipe in current channel")
            .await?;

        mysql_lib::update_logger_pipe_channel(db, guild_id, None).await;

        logging::remove_per_server_logging(guild_id);
    } else {
        // Logger pipe either not setup, or not the current channel
        // => set current channel as logger pipe
        info!(?guild_id, "Setting logger pipe");

        ctx.say("Setting logger pipe to the current channel")
            .await?;

        mysql_lib::update_logger_pipe_channel(db, guild_id, Some(ctx.channel_id())).await;

        logging::add_per_server_logging(guild_id, ctx.channel_id());
    }

    Ok(())
}

/// admin-only. Enter setup mode, either new server setup or edit setup information
#[poise::command(prefix_command, invoke_on_edit, reuse_response, guild_only)]
pub async fn setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    channel_mention: Option<GuildChannel>,
    flag: Option<bool>,
    number: Option<u32>,
    #[rest] rest: Option<String>,
) -> Result<(), Error> {
    setup_command::setup(ctx, role_mention, channel_mention, flag, number, rest).await
}
