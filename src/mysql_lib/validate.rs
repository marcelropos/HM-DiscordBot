use crate::bot::Context;
use crate::mysql_lib::{
    delete_alumni_role, delete_semester_study_group, delete_study_subject_link, delete_subject,
    delete_tmpc, delete_tmpc_join_channel, delete_token_message, update_tmp_studenty_role,
    DatabaseAlumniRole, DatabaseGuild, DatabaseSemesterStudyGroup, DatabaseStudyGroup,
    DatabaseStudySubjectLink, DatabaseSubject, DatabaseTmpc, DatabaseTmpcJoinChannel,
    DatabaseTokenMessage,
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
                database_guild.guild_id.get()
            ));
        }
        Ok(roles) => {
            if !roles.contains_key(&database_guild.studenty_role) {
                return Err(format!(
                    "Bot doesn't know studenty role: {}",
                    database_guild.studenty_role.get()
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
                    database_guild.moderator_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.newsletter_role) {
                return Err(format!(
                    "Bot doesn't know newsletter role: {}",
                    database_guild.newsletter_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.nsfw_role) {
                return Err(format!(
                    "Bot doesn't know nsfw role: {}",
                    database_guild.nsfw_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.study_role_separator_role) {
                return Err(format!(
                    "Bot doesn't know study role separator role: {}",
                    database_guild.study_role_separator_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.subject_role_separator_role) {
                return Err(format!(
                    "Bot doesn't know subject role separator role: {}",
                    database_guild.subject_role_separator_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.friend_role) {
                return Err(format!(
                    "Bot doesn't know friend role: {}",
                    database_guild.friend_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.alumni_role) {
                return Err(format!(
                    "Bot doesn't know alumni role: {}",
                    database_guild.alumni_role.get()
                ));
            }
            if !roles.contains_key(&database_guild.alumni_role_separator_role) {
                return Err(format!(
                    "Bot doesn't know alumni role separator role: {}",
                    database_guild.alumni_role_separator_role.get()
                ));
            }
        }
    }
    if ctx
        .http()
        .get_channel(database_guild.debug_channel)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know debug channel: {}",
            database_guild.debug_channel.get()
        ));
    }
    if ctx
        .http()
        .get_channel(database_guild.bot_channel)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know bot channel: {}",
            database_guild.bot_channel.get()
        ));
    }
    if ctx
        .http()
        .get_channel(database_guild.help_channel)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know help channel: {}",
            database_guild.help_channel.get()
        ));
    }
    if let Some(logger_pipe_channel) = database_guild.logger_pipe_channel {
        if ctx.http().get_channel(logger_pipe_channel).await.is_err() {
            return Err(format!(
                "Bot doesn't know logger pipe channel: {}",
                database_guild.help_channel.get()
            ));
        }
    }
    if ctx
        .http()
        .get_channel(database_guild.study_group_category)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know study group category: {}",
            database_guild.study_group_category.get()
        ));
    }
    if ctx
        .http()
        .get_channel(database_guild.subject_group_category)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know subject group category: {}",
            database_guild.subject_group_category.get()
        ));
    }

    Ok(database_guild)
}

/// If the alumni role is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_alumni<'a>(
    http: Http,
    pool: &Pool<MySql>,
    database_alumni_role: &'a DatabaseAlumniRole,
) -> Result<&'a DatabaseAlumniRole, String> {
    match database_alumni_role.guild_id.roles(http).await {
        Err(_) => {
            return Err(format!(
                "Bot doesn't know guild: {}",
                database_alumni_role.guild_id.get()
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
                    database_alumni_role.role.get()
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
    database_study_group: &DatabaseStudyGroup,
) -> Result<&DatabaseStudyGroup, String> {
    if http
        .get_guild(database_study_group.guild_id)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know guild: {}",
            database_study_group.guild_id.get()
        ));
    }

    Ok(database_study_group)
}

/// If the semester study group is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_semester_study_group<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_semester_study_group: &'a DatabaseSemesterStudyGroup,
    guild_id: GuildId,
) -> Result<&'a DatabaseSemesterStudyGroup, String> {
    match guild_id.roles(ctx.http()).await {
        Err(_) => {
            return Err(format!("Bot doesn't know guild: {}", guild_id.get()));
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
                    database_semester_study_group.role.get()
                ));
            }
        }
    };

    if ctx
        .http()
        .get_channel(database_semester_study_group.text_channel)
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
            database_semester_study_group.text_channel.get()
        ));
    }

    Ok(database_semester_study_group)
}

/// If the guild saved is not found, nothing will be deleted but an error will be returned.
///
/// If anything else is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_subject<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_subject: &'a DatabaseSubject,
) -> Result<&'a DatabaseSubject, String> {
    match database_subject.guild_id.roles(ctx.http()).await {
        Err(_) => {
            return Err(format!(
                "Bot doesn't know guild: {}",
                database_subject.guild_id.get()
            ));
        }
        Ok(roles) => {
            if !roles.contains_key(&database_subject.role) {
                match delete_subject(pool, database_subject.clone()).await {
                    None => {
                        return Err("Couldn't remove subject, query problem.".to_string());
                    }
                    Some(changed) => {
                        if !changed {
                            error!("Subject was not removed.")
                        }
                    }
                }
                return Err(format!(
                    "Bot doesn't know role of subject: {}",
                    database_subject.role.get()
                ));
            }
        }
    };

    if ctx
        .http()
        .get_channel(database_subject.text_channel)
        .await
        .is_err()
    {
        match delete_subject(pool, database_subject.clone()).await {
            None => {
                return Err("Couldn't remove subject, query problem.".to_string());
            }
            Some(changed) => {
                if !changed {
                    error!("Subject was not removed.")
                }
            }
        }
        return Err(format!(
            "Bot doesn't know text channel of subject: {}",
            database_subject.text_channel.get()
        ));
    }

    Ok(database_subject)
}

/// If the guild saved is not found, nothing will be deleted but an error will be returned.
///
/// If anything else is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_study_subject_link<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_study_subject_link: &'a DatabaseStudySubjectLink,
) -> Result<&'a DatabaseStudySubjectLink, String> {
    match database_study_subject_link.guild_id.roles(ctx.http()).await {
        Err(_) => {
            return Err(format!(
                "Bot doesn't know guild: {}",
                database_study_subject_link.guild_id.get()
            ));
        }
        Ok(roles) => {
            if !roles.contains_key(&database_study_subject_link.study_group_role)
                || !roles.contains_key(&database_study_subject_link.subject_role)
            {
                match delete_study_subject_link(pool, *database_study_subject_link).await {
                    None => {
                        return Err(
                            "Couldn't remove study-subject link, query problem.".to_string()
                        );
                    }
                    Some(changed) => {
                        if !changed {
                            error!("Study-subject link was not removed.")
                        }
                    }
                }
                return Err(format!(
                    "Bot doesn't know study_group_role or subject role of study-subject link: {}",
                    database_study_subject_link.study_group_role.get()
                ));
            }
        }
    };

    Ok(database_study_subject_link)
}

/// If the guild isn't known, nothing will be deleted from the database
///
/// If the tmpc join channel is not found, it will be deleted from the database
#[allow(dead_code)]
pub async fn validate_tmpc_join_channel<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_tmpc_join_channel: &'a DatabaseTmpcJoinChannel,
) -> Result<&'a DatabaseTmpcJoinChannel, String> {
    if ctx
        .http()
        .get_guild(database_tmpc_join_channel.guild_id)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know guild: {}",
            database_tmpc_join_channel.guild_id.get()
        ));
    }

    if ctx
        .http()
        .get_channel(database_tmpc_join_channel.voice_channel)
        .await
        .is_err()
    {
        match delete_tmpc_join_channel(pool, *database_tmpc_join_channel).await {
            None => {
                return Err("Couldn't remove tmpc join channel, query problem.".to_string());
            }
            Some(changed) => {
                if !changed {
                    error!("Tmpc join channel was not removed.")
                }
            }
        }
        return Err(format!(
            "Bot doesn't know voice channel of tmpc join channel: {}",
            database_tmpc_join_channel.voice_channel.get()
        ));
    }

    Ok(database_tmpc_join_channel)
}

/// If the guild isn't known, nothing will be deleted from the database
///
/// If the tmpc is not found, it will be deleted from the database
///
/// If the owner is not checked
#[allow(dead_code)]
pub async fn validate_tmpc<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_tmpc: &'a DatabaseTmpc,
) -> Result<&'a DatabaseTmpc, String> {
    if ctx
        .http()
        .get_guild(database_tmpc.guild_id)
        .await
        .is_err()
    {
        return Err(format!(
            "Bot doesn't know guild: {}",
            database_tmpc.guild_id.get()
        ));
    }

    if ctx
        .http()
        .get_channel(database_tmpc.voice_channel)
        .await
        .is_err()
        || ctx
            .http()
            .get_channel(database_tmpc.text_channel)
            .await
            .is_err()
    {
        match delete_tmpc(pool, *database_tmpc).await {
            None => {
                return Err("Couldn't remove tmpc, query problem.".to_string());
            }
            Some(changed) => {
                if !changed {
                    error!("Tmpc was not removed.")
                }
            }
        }
        return Err(format!(
            "Bot doesn't know tmpc: {} {}",
            database_tmpc.voice_channel.get(), database_tmpc.text_channel.get()
        ));
    }

    Ok(database_tmpc)
}

/// If the message is not found, it will be deleted from the database
///
/// The tmpc voice channel is not checked
#[allow(dead_code)]
pub async fn validate_token_message<'a>(
    ctx: Context<'_>,
    pool: &Pool<MySql>,
    database_token_message: &'a DatabaseTokenMessage,
) -> Result<&'a DatabaseTokenMessage, String> {
    if ctx
        .http()
        .get_channel(database_token_message.message_channel)
        .await
        .is_err()
        || ctx
            .http()
            .get_message(
                database_token_message.message_channel,
                database_token_message.message,
            )
            .await
            .is_err()
    {
        match delete_token_message(pool, *database_token_message).await {
            None => {
                return Err("Couldn't remove token message, query problem.".to_string());
            }
            Some(changed) => {
                if !changed {
                    error!("Token message was not removed.")
                }
            }
        }
        return Err(format!(
            "Bot doesn't know token message: {} {}",
            database_token_message.message_channel.get(), database_token_message.message.get()
        ));
    }

    Ok(database_token_message)
}
