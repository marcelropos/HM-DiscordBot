use std::time::SystemTime;

use poise::serenity_prelude::{GuildChannel, Role};
use poise::CreateReply;
use tracing::info;

use crate::mysql_lib::NewGuild;
use crate::{
    bot::{Context, Error},
    logging, mysql_lib,
};

use super::checks;

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
    number: Option<u32>,
    #[rest] rest: Option<String>,
) -> Result<(), Error> {
    // Check permissions
    if !checks::is_owner(ctx).await && !checks::is_admin(ctx).await {
        ctx.say("Missing permissions, requires admin permissions")
            .await?;
        return Ok(());
    }

    let guild_id = ctx.guild_id().unwrap();

    let db = &ctx.data().database_pool;
    let db_guild = mysql_lib::get_guild(db, guild_id).await;
    let skip_message = if db_guild.is_none() {
        format!(
            "\n**You can also skip setting this value by writing `{}setup skip`**",
            ctx.prefix()
        )
    } else {
        "".to_string()
    };
    if !ctx
        .data()
        .setup_in_progress
        .lock()
        .unwrap()
        .contains_key(&guild_id)
    {
        let new_guild = NewGuild {
            guild_id,
            ..Default::default()
        };
        {
            let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
            hash_map.insert(guild_id, new_guild);
        }
        let _ = ctx
            .say(format!(
                "Edit the command to include the Days a User can be on the \
                 server unverified before he is warned about his impending kick.\n\
                 `{}setup <days_before_warning>`\n\
                 7 days is recommended. The value must be between 2 and 14{}",
                ctx.prefix(),
                skip_message
            ))
            .await;
        return Ok(());
    }

    if ctx
        .data()
        .setup_in_progress
        .lock()
        .unwrap()
        .get(&guild_id)
        .unwrap()
        .ghost_warning_deadline
        .is_none()
    {
        if let Some(text) = rest {
            if text == "skip" {
                if let Some(db_guild) = db_guild {
                    {
                        let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                        let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                        new_guild.ghost_warning_deadline = Some(db_guild.ghost_warning_deadline);
                    }
                    let _ = ctx
                        .say(format!(
                            "Kept Ghost warning Deadline at {} days.\n\
                             Edit the command to include the Days a User can be on the server \
                             unverified before he is kicked.\n\
                             `{}setup <days_before_kick>`\n\
                             14 days is recommended. The value must be between {} and 28{}",
                            db_guild.ghost_warning_deadline,
                            ctx.prefix(),
                            db_guild.ghost_warning_deadline + 1,
                            skip_message
                        ))
                        .await;
                }
            }
        }
        match number {
            None => {
                let _ = ctx
                    .say(format!(
                        "**Did not get a number!**\n\
                         Edit the command to include the Days a User can be on the server \
                         unverified before he is warned about his impending kick.\n\
                         `{}setup <days_before_warning>`\n\
                         7 days is recommended. The value must be between 2 and 14{}",
                        ctx.prefix(),
                        skip_message
                    ))
                    .await;
            }
            Some(number) => {
                if !(2..=14).contains(&number) {
                    let _ = ctx
                        .say(format!(
                            "**Value of number was outside of valid numbers!**\n\
                             Edit the command to include the Days a User can be on the server \
                             unverified before he is warned about his impending kick.\n\
                             `{}setup <days_before_warning>`\n\
                             7 days is recommended. The value must be between 2 and 14{}",
                            ctx.prefix(),
                            skip_message
                        ))
                        .await;
                } else {
                    {
                        let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                        let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                        new_guild.ghost_warning_deadline = Some(number);
                    }
                    let _ = ctx
                        .say(format!(
                            "Set Ghost warning Deadline to {} days.\n\
                             Edit the command to include the Days a User can be on the server \
                             unverified before he is kicked.\n\
                             `{}setup <days_before_kick>`\n\
                             14 days is recommended. The value must be between {} and 28{}",
                            number,
                            ctx.prefix(),
                            number + 1,
                            skip_message
                        ))
                        .await;
                }
            }
        }
        return Ok(());
    }

    let _ = ctx
        .say(format!(
            "**Role Mention:** {:?}\n**Channel Mention:** {:?}\n**Number** {:?}\n**Rest:** {:?}",
            role_mention, channel_mention, number, rest
        ))
        .await;

    Ok(())
}
