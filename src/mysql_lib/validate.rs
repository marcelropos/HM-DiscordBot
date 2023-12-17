use crate::bot::Context;
use crate::mysql_lib::{
    delete_alumni_role, delete_semester_study_group, update_tmp_studenty_role, DatabaseAlumniRole,
    DatabaseGuild, DatabaseSemesterStudyGroup, DatabaseStudyGroup,
};
use poise::serenity_prelude::{GuildId, Http};
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

/// If the alumni role is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_alumni<'a>(
    http: Http,
    pool: &Pool<MySql>,
    database_alumni_role: &'a mut DatabaseAlumniRole,
) -> Result<&'a mut DatabaseAlumniRole, String> {
    match database_alumni_role.guild_id.roles(http).await {
        Err(_) => {
            return Err(format!(
                "Bot doesn't know guild: {}",
                database_alumni_role.guild_id.0
            ));
        }
        Ok(roles) => {
            if !roles.contains_key(&database_alumni_role.role) {
                match delete_alumni_role(pool, *database_alumni_role).await {
                    None => {
                        return Err("Couldn't remove alumni role, query problem.".to_string());
                    }
                    Some(changed) => {
                        if !changed {
                            error!("alumni role was not removed.")
                        }
                    }
                }
                return Err(format!(
                    "Bot doesn't know alumni role: {}",
                    database_alumni_role.role.0
                ));
            }
        }
    }

    Ok(database_alumni_role)
}

/// If the guild saved is not found, nothing will be deleted but an error will be returned
#[allow(dead_code)]
pub async fn validate_study_group(
    http: Http,
    database_study_group: &mut DatabaseStudyGroup,
) -> Result<&mut DatabaseStudyGroup, String> {
    if http
        .get_guild(database_study_group.guild_id.0)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know guild: {}",
            database_study_group.guild_id.0
        ));
    }

    Ok(database_study_group)
}

/// If the semester study group is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_semester_study_group_with_roles<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_semester_study_group: &'a mut DatabaseSemesterStudyGroup,
    guild_id: GuildId,
) -> Result<&'a mut DatabaseSemesterStudyGroup, String> {
    match guild_id.roles(ctx.http()).await {
        Err(_) => {
            return Err(format!("Bot doesn't know guild: {}", guild_id.0));
        }
        Ok(roles) => {
            if !roles.contains_key(&database_semester_study_group.role) {
                match delete_semester_study_group(pool, *database_semester_study_group).await {
                    None => {
                        return Err(
                            "Couldn't remove semester study group, query problem.".to_string()
                        );
                    }
                    Some(changed) => {
                        if !changed {
                            error!("Semester study group was not removed.")
                        }
                    }
                }
                return Err(format!(
                    "Bot doesn't know semester study group: {}",
                    database_semester_study_group.role.0
                ));
            }
        }
    };

    if ctx
        .http()
        .get_channel(database_semester_study_group.text_channel.0)
        .await
        .is_err()
    {
        match delete_semester_study_group(pool, *database_semester_study_group).await {
            None => {
                return Err("Couldn't remove semester study group, query problem.".to_string());
            }
            Some(changed) => {
                if !changed {
                    error!("Semester study group was not removed.")
                }
            }
        }
        return Err(format!(
            "Bot doesn't know text channel of semester study group: {}",
            database_semester_study_group.text_channel.0
        ));
    }

    Ok(database_semester_study_group)
}