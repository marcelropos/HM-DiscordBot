use std::env;

use poise::serenity_prelude::{ChannelId, GuildId, RoleId};
use sqlx::migrate::MigrateError;
use sqlx::mysql::{MySqlConnectOptions, MySqlPoolOptions, MySqlRow};
use sqlx::types::time::Time;
use sqlx::{migrate, FromRow, MySql, Pool, Row};
use tracing::error;

mod test;

/// Tries to establish a Connection with the given env variables and return the MySQL connection
/// Pool if successful.
///
/// # Env Variables
///
/// * MYSQL_PORT: the port of the mysql database, defaults to 3306
/// * MYSQL_HOST: the host of the mysql database, ip or hostname or domain, defaults to 127.0.0.1
/// * MYSQL_DATABASE: the name of the database to use, needs to be present
/// * MYSQL_USER: the username of the user that has access to the database, needs to be present
/// * MYSQL_PASSWORD: the password of the user specified, needs to be present
pub async fn get_connection(max_concurrent_connections: u32) -> Option<Pool<MySql>> {
    let sql_port = env::var("MYSQL_PORT").unwrap_or("3306".to_owned());
    let sql_port = match sql_port.parse() {
        Ok(val) => val,
        Err(_) => {
            error!("Could not parse MYSQL_PORT");
            return None;
        }
    };

    let sql_hostname = env::var("MYSQL_HOST").unwrap_or("127.0.0.1".to_owned());

    let sql_database = match env::var("MYSQL_DATABASE") {
        Ok(val) => val,
        Err(_) => {
            error!("No database given");
            return None;
        }
    };

    let sql_username = match env::var("MYSQL_USER") {
        Ok(val) => val,
        Err(_) => {
            error!("No database username given");
            return None;
        }
    };

    let sql_password = match env::var("MYSQL_PASSWORD") {
        Ok(val) => val,
        Err(_) => {
            error!("No password for user given");
            return None;
        }
    };

    match MySqlPoolOptions::new()
        .max_connections(max_concurrent_connections)
        .connect_with(
            MySqlConnectOptions::new()
                .host(sql_hostname.as_str())
                .port(sql_port)
                .database(sql_database.as_str())
                .username(sql_username.as_str())
                .password(sql_password.as_str()),
        )
        .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(
                error = err.to_string(),
                "Problem connecting to the Database"
            );
            None
        }
    }
}

pub async fn migrate_database(pool: &Pool<MySql>) -> Result<(), MigrateError> {
    migrate!("./migrations").run(pool).await
}

/// Query if a Guild is saved in the database
#[allow(dead_code)]
pub async fn is_guild_in_database(pool: &Pool<MySql>, guild_id: GuildId) -> Option<bool> {
    match sqlx::query("SELECT * FROM Guild WHERE guild_id=?")
        .bind(guild_id.0)
        .fetch_optional(pool)
        .await
    {
        Ok(val) => Some(val.is_some()),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseGuild {
    guild_id: GuildId,
    ghost_warning_deadline: u32,
    ghost_kick_deadline: u32,
    ghost_time_to_check: Time,
    ghost_enabled: bool,
    debug_channel: ChannelId,
    bot_channel: ChannelId,
    help_channel: ChannelId,
    logger_pipe_channel: Option<ChannelId>,
    study_group_category: ChannelId,
    subject_group_category: ChannelId,
    studenty_role: RoleId,
    tmp_studenty_role: Option<RoleId>,
    moderator_role: RoleId,
    newsletter_role: RoleId,
    nsfw_role: RoleId,
    study_role_separator_role: RoleId,
    subject_role_separator_role: RoleId,
    friend_role: RoleId,
    tmpc_keep_time: Time,
    alumni_role: RoleId,
    alumni_role_separator_role: RoleId,
}

impl FromRow<'_, MySqlRow> for DatabaseGuild {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            guild_id: GuildId(row.try_get("guild_id")?),
            ghost_warning_deadline: row.try_get("ghost_warn_deadline")?,
            ghost_kick_deadline: row.try_get("ghost_kick_deadline")?,
            ghost_time_to_check: row.try_get("ghost_time_to_check")?,
            ghost_enabled: row.try_get("ghost_enabled")?,
            debug_channel: ChannelId(row.try_get("debug_channel")?),
            bot_channel: ChannelId(row.try_get("bot_channel")?),
            help_channel: ChannelId(row.try_get("help_channel")?),
            logger_pipe_channel: row
                .try_get("logger_pipe_channel")
                .map(|val: Option<u64>| val.map(|val| ChannelId(val)))?,
            study_group_category: ChannelId(row.try_get("study_group_category")?),
            subject_group_category: ChannelId(row.try_get("subject_group_category")?),
            studenty_role: RoleId(row.try_get("studenty_role")?),
            tmp_studenty_role: row
                .try_get("logger_pipe_channel")
                .map(|val: Option<u64>| val.map(|val| RoleId(val)))?,
            moderator_role: RoleId(row.try_get("moderator_role")?),
            newsletter_role: RoleId(row.try_get("newsletter_role")?),
            nsfw_role: RoleId(row.try_get("nsfw_role")?),
            study_role_separator_role: RoleId(row.try_get("study_role_separator_role")?),
            subject_role_separator_role: RoleId(row.try_get("subject_role_separator_role")?),
            friend_role: RoleId(row.try_get("friend_role")?),
            tmpc_keep_time: row.try_get("tmpc_keep_time")?,
            alumni_role: RoleId(row.try_get("alumni_role")?),
            alumni_role_separator_role: RoleId(row.try_get("alumni_role_separator_role")?),
        })
    }
}

/// Inserts a new Guild into the Database. Return if the guild was inserted into the Database,
/// may be false if the guild was already in the Database.
///
/// `DatabaseGuild::logger_pipe_channel` and `DatabaseGuild::tmp_studenty_role` are ignored.
#[allow(dead_code)]
pub async fn insert_guild(pool: &Pool<MySql>, guild: DatabaseGuild) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO USER_DB_NAME.Guild (
guild_id,
ghost_warn_deadline,
ghost_kick_deadline,
ghost_time_to_check,
ghost_enabled,
debug_channel,
bot_channel,
help_channel,
study_group_category,
subject_group_category,
studenty_role,
moderator_role,
newsletter_role,
nsfw_role,
study_role_separator_role,
subject_role_separator_role,
friend_role,
tmpc_keep_time,
alumni_role,
alumni_role_separator_role)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
    )
    .bind(guild.guild_id.0)
    .bind(guild.ghost_warning_deadline)
    .bind(guild.ghost_kick_deadline)
    .bind(guild.ghost_time_to_check)
    .bind(guild.ghost_enabled)
    .bind(guild.debug_channel.0)
    .bind(guild.bot_channel.0)
    .bind(guild.help_channel.0)
    .bind(guild.study_group_category.0)
    .bind(guild.subject_group_category.0)
    .bind(guild.studenty_role.0)
    .bind(guild.moderator_role.0)
    .bind(guild.newsletter_role.0)
    .bind(guild.nsfw_role.0)
    .bind(guild.study_role_separator_role.0)
    .bind(guild.subject_role_separator_role.0)
    .bind(guild.friend_role.0)
    .bind(guild.tmpc_keep_time)
    .bind(guild.alumni_role.0)
    .bind(guild.alumni_role_separator_role.0)
    .execute(pool)
    .await
    {
        Ok(val) => Some(val.rows_affected() != 0),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Deletes a Guild saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_guild(pool: &Pool<MySql>, guild_id: GuildId) -> Option<bool> {
    match sqlx::query("DELETE FROM Guild WHERE guild_id=?")
        .bind(guild_id.0)
        .execute(pool)
        .await
    {
        Ok(val) => Some(val.rows_affected() != 0),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Gets the guild information from the Database
#[allow(dead_code)]
pub async fn get_guild(pool: &Pool<MySql>, guild_id: GuildId) -> Option<DatabaseGuild> {
    match sqlx::query_as::<_, DatabaseGuild>("SELECT * FROM Guild WHERE guild_id=?")
        .bind(guild_id.0)
        .fetch_one(pool)
        .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            return None;
        }
    }
}

/// Updated the Ghost warning deadline (in days), returns if the value was changed
#[allow(dead_code)]
pub async fn update_ghost_warning_deadline(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    ghost_warning_deadline: u32,
) -> Option<bool> {
    match sqlx::query("UPDATE Guild SET ghost_warn_deadline = ? WHERE guild_id=?")
        .bind(ghost_warning_deadline)
        .bind(guild_id.0)
        .execute(pool)
        .await
    {
        Ok(val) => Some(val.rows_affected() != 0),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}
