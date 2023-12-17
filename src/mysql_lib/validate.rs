use crate::bot::Context;
use crate::mysql_lib::{update_tmp_studenty_role, DatabaseGuild};
use sqlx::{MySql, Pool};
use tracing::error;

/// Values won't be deleted from Database if something is not valid but the object is only returned if everything is valid
///
/// The tmp Studenty and logger pipe channel are deleted
#[allow(dead_code)]
pub async fn validate_guild<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_guild: &'a mut DatabaseGuild,
) -> Result<&'a mut DatabaseGuild, String> {
    match database_guild.guild_id.roles(ctx.http()).await {
        Err(_) => {
            return Err(format!(
                "Bot doesn't know guild: {}",
                database_guild.guild_id.0
            ));
        }
        Ok(roles) => {
            if !roles.contains_key(&database_guild.studenty_role) {
                return Err(format!(
                    "Bot doesn't know studenty role: {}",
                    database_guild.studenty_role.0
                ));
            }
            if let Some(tmp_studenty_role) = database_guild.tmp_studenty_role {
                if !roles.contains_key(&tmp_studenty_role) {
                    match update_tmp_studenty_role(pool, database_guild.guild_id, None).await {
                        None => {
                            return Err(
                                "Couldn't remove tmp studenty role, query problem.".to_string()
                            );
                        }
                        Some(changed) => {
                            if !changed {
                                error!("Tmp studenty role was not removed.")
                            }
                        }
                    }
                    database_guild.tmp_studenty_role = None;
                }
            }
            if !roles.contains_key(&database_guild.moderator_role) {
                return Err(format!(
                    "Bot doesn't know moderator role: {}",
                    database_guild.moderator_role.0
                ));
            }
            if !roles.contains_key(&database_guild.newsletter_role) {
                return Err(format!(
                    "Bot doesn't know newsletter role: {}",
                    database_guild.newsletter_role.0
                ));
            }
            if !roles.contains_key(&database_guild.nsfw_role) {
                return Err(format!(
                    "Bot doesn't know nsfw role: {}",
                    database_guild.nsfw_role.0
                ));
            }
            if !roles.contains_key(&database_guild.study_role_separator_role) {
                return Err(format!(
                    "Bot doesn't know study role separator role: {}",
                    database_guild.study_role_separator_role.0
                ));
            }
            if !roles.contains_key(&database_guild.subject_role_separator_role) {
                return Err(format!(
                    "Bot doesn't know subject role separator role: {}",
                    database_guild.subject_role_separator_role.0
                ));
            }
            if !roles.contains_key(&database_guild.friend_role) {
                return Err(format!(
                    "Bot doesn't know friend role: {}",
                    database_guild.friend_role.0
                ));
            }
            if !roles.contains_key(&database_guild.alumni_role) {
                return Err(format!(
                    "Bot doesn't know alumni role: {}",
                    database_guild.alumni_role.0
                ));
            }
            if !roles.contains_key(&database_guild.alumni_role_separator_role) {
                return Err(format!(
                    "Bot doesn't know alumni role separator role: {}",
                    database_guild.alumni_role_separator_role.0
                ));
            }
        }
    }
    if ctx
        .http()
        .get_channel(database_guild.debug_channel.0)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know debug channel: {}",
            database_guild.debug_channel.0
        ));
    }
    if ctx
        .http()
        .get_channel(database_guild.bot_channel.0)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know bot channel: {}",
            database_guild.bot_channel.0
        ));
    }
    if ctx
        .http()
        .get_channel(database_guild.help_channel.0)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know help channel: {}",
            database_guild.help_channel.0
        ));
    }
    if let Some(logger_pipe_channel) = database_guild.logger_pipe_channel {
        if ctx.http().get_channel(logger_pipe_channel.0).await.is_err() {
            return Err(format!(
                "Bot doesn't know logger pipe channel: {}",
                database_guild.help_channel.0
            ));
        }
    }
    if ctx
        .http()
        .get_channel(database_guild.study_group_category.0)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know study group category: {}",
            database_guild.study_group_category.0
        ));
    }
    if ctx
        .http()
        .get_channel(database_guild.subject_group_category.0)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know subject group category: {}",
            database_guild.subject_group_category.0
        ));
    }

    Ok(database_guild)
}
