use std::env;

use poise::serenity_prelude::{ChannelId, GuildId, MessageId, RoleId, UserId};
use sqlx::migrate::MigrateError;
use sqlx::mysql::{MySqlConnectOptions, MySqlPoolOptions, MySqlRow};
use sqlx::types::time::{PrimitiveDateTime, Time};
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

#[derive(Copy, Clone)]
enum Column {
    GhostWarningDeadline(u32),
    GhostKickDeadline(u32),
    GhostTimeToCheck(Time),
    GhostEnabled(bool),
    DebugChannel(ChannelId),
    BotChannel(ChannelId),
    HelpChannel(ChannelId),
    LoggerPipeChannel(Option<ChannelId>),
    StudyGroupCategory(ChannelId),
    SubjectGroupCategory(ChannelId),
    StudentyRole(RoleId),
    TmpStudentyRole(Option<RoleId>),
    ModeratorRole(RoleId),
    NewsletterRole(RoleId),
    NsfwRole(RoleId),
    StudyRoleSeparatorRole(RoleId),
    SubjectRoleSeparatorRole(RoleId),
    FriendRole(RoleId),
    TmpcKeepTime(Time),
    AlumniRole(RoleId),
    AlumniRoleSeparatorRole(RoleId),
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

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseAlumniRole {
    role: RoleId,
    guild_id: GuildId,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseStudyGroup {
    id: Option<i32>,
    guild_id: GuildId,
    name: String,
    color: u32,
    active: bool,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseSemesterStudyGroup {
    role: RoleId,
    study_group_id: i32,
    semester: u32,
    text_channel: ChannelId,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseSubject {
    role: RoleId,
    guild_id: GuildId,
    name: String,
    text_channel: ChannelId,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseStudySubjectLink {
    study_group_role: RoleId,
    subject_role: RoleId,
    guild_id: GuildId,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseTmpcJoinChannel {
    voice_channel: ChannelId,
    guild_id: GuildId,
    persist: bool,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseTmpc {
    voice_channel: ChannelId,
    text_channel: ChannelId,
    guild_id: GuildId,
    owner: UserId,
    persist: bool,
    token: u32,
    keep: bool,
    delete_at: Option<PrimitiveDateTime>,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseTokenMessage {
    tmpc_voice_channel: ChannelId,
    message: MessageId,
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
                .map(|val: Option<u64>| val.map(ChannelId))?,
            study_group_category: ChannelId(row.try_get("study_group_category")?),
            subject_group_category: ChannelId(row.try_get("subject_group_category")?),
            studenty_role: RoleId(row.try_get("studenty_role")?),
            tmp_studenty_role: row
                .try_get("tmp_studenty_role")
                .map(|val: Option<u64>| val.map(RoleId))?,
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

impl FromRow<'_, MySqlRow> for DatabaseAlumniRole {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            role: RoleId(row.try_get("role")?),
            guild_id: GuildId(row.try_get("guild_id")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseStudyGroup {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            id: row.try_get("id")?,
            guild_id: GuildId(row.try_get("guild_id")?),
            name: row.try_get("name")?,
            color: row.try_get("color")?,
            active: row.try_get("active")?,
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseSemesterStudyGroup {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            role: RoleId(row.try_get("role")?),
            study_group_id: row.try_get("study_group_id")?,
            semester: row.try_get("semester")?,
            text_channel: ChannelId(row.try_get("text_channel")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseSubject {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            role: RoleId(row.try_get("role")?),
            guild_id: GuildId(row.try_get("guild_id")?),
            name: row.try_get("name")?,
            text_channel: ChannelId(row.try_get("text_channel")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseStudySubjectLink {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            study_group_role: RoleId(row.try_get("study_group_role")?),
            subject_role: RoleId(row.try_get("subject_role")?),
            guild_id: GuildId(row.try_get("guild_id")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseTmpcJoinChannel {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            voice_channel: ChannelId(row.try_get("voice_channel")?),
            guild_id: GuildId(row.try_get("guild_id")?),
            persist: row.try_get("persist")?,
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseTmpc {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            voice_channel: ChannelId(row.try_get("voice_channel")?),
            text_channel: ChannelId(row.try_get("text_channel")?),
            guild_id: GuildId(row.try_get("guild_id")?),
            owner: UserId(row.try_get("owner")?),
            persist: row.try_get("persist")?,
            token: row.try_get("token")?,
            keep: row.try_get("keep")?,
            delete_at: row.try_get("deleteAt")?,
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseTokenMessage {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            tmpc_voice_channel: ChannelId(row.try_get("tmpc_voice_channel")?),
            message: MessageId(row.try_get("message")?),
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
        "INSERT IGNORE INTO Guild (
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
            None
        }
    }
}

/// Update the Ghost warning deadline (in days), returns if the value was changed
#[allow(dead_code)]
pub async fn update_ghost_warning_deadline(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    ghost_warning_deadline: u32,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::GhostWarningDeadline(ghost_warning_deadline),
    )
    .await
}

/// Update the Ghost kick deadline (in days), returns if the value was changed
#[allow(dead_code)]
pub async fn update_ghost_kick_deadline(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    ghost_kick_deadline: u32,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::GhostKickDeadline(ghost_kick_deadline),
    )
    .await
}

/// Update the Ghost Time to check, returns if the value was changed
#[allow(dead_code)]
pub async fn update_ghost_time_to_check(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    ghost_time_to_check: Time,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::GhostTimeToCheck(ghost_time_to_check),
    )
    .await
}

/// Update the ghost enabled flag, returns if the value was changed
#[allow(dead_code)]
pub async fn update_ghost_enabled(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    ghost_enabled: bool,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::GhostEnabled(ghost_enabled)).await
}

/// Update the debug channel, returns if the value was changed
#[allow(dead_code)]
pub async fn update_debug_channel(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    debug_channel: ChannelId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::DebugChannel(debug_channel)).await
}

/// Update the bot channel, returns if the value was changed
#[allow(dead_code)]
pub async fn update_bot_channel(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    bot_channel: ChannelId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::BotChannel(bot_channel)).await
}

/// Update the help channel, returns if the value was changed
#[allow(dead_code)]
pub async fn update_help_channel(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    help_channel: ChannelId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::HelpChannel(help_channel)).await
}

/// Update the logger pipe channel, returns if the value was changed
#[allow(dead_code)]
pub async fn update_logger_pipe_channel(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    logger_pipe_channel: Option<ChannelId>,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::LoggerPipeChannel(logger_pipe_channel),
    )
    .await
}

/// Update the study group category, returns if the value was changed
#[allow(dead_code)]
pub async fn update_study_group_category(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    study_group_category: ChannelId,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::StudyGroupCategory(study_group_category),
    )
    .await
}

/// Update the subject group category, returns if the value was changed
#[allow(dead_code)]
pub async fn update_subject_group_category(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    subject_group_category: ChannelId,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::SubjectGroupCategory(subject_group_category),
    )
    .await
}

/// Update the studenty role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_studenty_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    studenty_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::StudentyRole(studenty_role)).await
}

/// Update the tmp studenty role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_tmp_studenty_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    tmp_studenty_role: Option<RoleId>,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::TmpStudentyRole(tmp_studenty_role)).await
}

/// Update the moderator role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_moderator_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    moderator_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::ModeratorRole(moderator_role)).await
}

/// Update the newsletter role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_newsletter_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    newsletter_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::NewsletterRole(newsletter_role)).await
}

/// Update the nsfw role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_nsfw_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    nsfw_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::NsfwRole(nsfw_role)).await
}

/// Update the study role separator role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_study_role_separator_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    study_role_separator_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::StudyRoleSeparatorRole(study_role_separator_role),
    )
    .await
}

/// Update the subject role separator role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_subject_role_separator_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    subject_role_separator_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::SubjectRoleSeparatorRole(subject_role_separator_role),
    )
    .await
}

/// Update the friend role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_friend_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    friend_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::FriendRole(friend_role)).await
}

/// Update the tmpc keep time, returns if the value was changed
#[allow(dead_code)]
pub async fn update_tmpc_keep_time(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    tmpc_keep_time: Time,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::TmpcKeepTime(tmpc_keep_time)).await
}

/// Update the alumni role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_alumni_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    alumni_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(pool, guild_id, Column::AlumniRole(alumni_role)).await
}

/// Update the alumni role separator role, returns if the value was changed
#[allow(dead_code)]
pub async fn update_alumni_role_separator_role(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    alumni_role_separator_role: RoleId,
) -> Option<bool> {
    update_guild_table_value(
        pool,
        guild_id,
        Column::AlumniRoleSeparatorRole(alumni_role_separator_role),
    )
    .await
}

async fn update_guild_table_value(
    pool: &Pool<MySql>,
    guild_id: GuildId,
    action: Column,
) -> Option<bool> {
    macro_rules! query_format {
        ($($args:tt)*) => {format!("UPDATE Guild SET {}=? WHERE guild_id=?", $($args)*)};
    }
    let query: String;
    match match action {
        Column::GhostWarningDeadline(val) => {
            query = query_format!("ghost_warn_deadline");
            sqlx::query(query.as_str()).bind(val)
        }
        Column::GhostKickDeadline(val) => {
            query = query_format!("ghost_kick_deadline");
            sqlx::query(query.as_str()).bind(val)
        }
        Column::GhostTimeToCheck(val) => {
            query = query_format!("ghost_time_to_check");
            sqlx::query(query.as_str()).bind(val)
        }
        Column::GhostEnabled(val) => {
            query = query_format!("ghost_enabled");
            sqlx::query(query.as_str()).bind(val)
        }
        Column::DebugChannel(val) => {
            query = query_format!("debug_channel");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::BotChannel(val) => {
            query = query_format!("bot_channel");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::HelpChannel(val) => {
            query = query_format!("help_channel");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::LoggerPipeChannel(val) => {
            query = query_format!("logger_pipe_channel");
            sqlx::query(query.as_str()).bind(val.map(|val| val.0))
        }
        Column::StudyGroupCategory(val) => {
            query = query_format!("study_group_category");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::SubjectGroupCategory(val) => {
            query = query_format!("subject_group_category");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::StudentyRole(val) => {
            query = query_format!("studenty_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::TmpStudentyRole(val) => {
            query = query_format!("tmp_studenty_role");
            sqlx::query(query.as_str()).bind(val.map(|val| val.0))
        }
        Column::ModeratorRole(val) => {
            query = query_format!("moderator_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::NewsletterRole(val) => {
            query = query_format!("newsletter_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::NsfwRole(val) => {
            query = query_format!("nsfw_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::StudyRoleSeparatorRole(val) => {
            query = query_format!("study_role_separator_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::SubjectRoleSeparatorRole(val) => {
            query = query_format!("subject_role_separator_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::FriendRole(val) => {
            query = query_format!("friend_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::TmpcKeepTime(val) => {
            query = query_format!("tmpc_keep_time");
            sqlx::query(query.as_str()).bind(val)
        }
        Column::AlumniRole(val) => {
            query = query_format!("alumni_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
        Column::AlumniRoleSeparatorRole(val) => {
            query = query_format!("alumni_role_separator_role");
            sqlx::query(query.as_str()).bind(val.0)
        }
    }
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

/// Inserts a new Alumni Role into the Database. Return if the Alumni Role was inserted into the
/// Database, may be false if the Alumni Role was already in the Database.
#[allow(dead_code)]
pub async fn insert_alumni_role(
    pool: &Pool<MySql>,
    alumni_role: DatabaseAlumniRole,
) -> Option<bool> {
    match sqlx::query("INSERT IGNORE INTO Alumni_roles (role, guild_id) VALUES (?, ?);")
        .bind(alumni_role.role.0)
        .bind(alumni_role.guild_id.0)
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

/// Deletes a Alumni Role saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_alumni_role(
    pool: &Pool<MySql>,
    alumni_role: DatabaseAlumniRole,
) -> Option<bool> {
    match sqlx::query("DELETE FROM Alumni_roles WHERE role=? AND guild_id=?")
        .bind(alumni_role.role.0)
        .bind(alumni_role.guild_id.0)
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

/// Gets the Alumni Roles saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_alumni_roles(
    pool: &Pool<MySql>,
    guild_id: GuildId,
) -> Option<Vec<DatabaseAlumniRole>> {
    match sqlx::query_as::<_, DatabaseAlumniRole>("SELECT * FROM Alumni_roles WHERE guild_id=?")
        .bind(guild_id.0)
        .fetch_all(pool)
        .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Inserts a new Study Group into the Database. Return if the Study Group was inserted into the
/// Database, may be false if the Study Group was already in the Database.
///
/// `DatabaseStudyGroup::id` is ignored
#[allow(dead_code)]
pub async fn insert_study_group(
    pool: &Pool<MySql>,
    study_group: DatabaseStudyGroup,
) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Study_groups (guild_id, name, color, active) VALUES (?, ?, ?, ?);",
    )
    .bind(study_group.guild_id.0)
    .bind(study_group.name)
    .bind(study_group.color)
    .bind(study_group.active)
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

/// Deletes a Study Group saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_study_group(
    pool: &Pool<MySql>,
    study_group: DatabaseStudyGroup,
) -> Option<bool> {
    if study_group.id.is_none() {
        error!("Can't delete Study group without id");
        return None;
    }
    match sqlx::query("DELETE FROM Study_groups WHERE id=? AND guild_id=?")
        .bind(study_group.id)
        .bind(study_group.guild_id.0)
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

/// Gets the Study Groups saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_study_groups(
    pool: &Pool<MySql>,
    guild_id: GuildId,
) -> Option<Vec<DatabaseStudyGroup>> {
    match sqlx::query_as::<_, DatabaseStudyGroup>("SELECT * FROM Study_groups WHERE guild_id=?")
        .bind(guild_id.0)
        .fetch_all(pool)
        .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Inserts a new Semester Study Group into the Database. Return if the Semester Study Group was
/// inserted into the Database, may be false if the Semester Study Group was already in the Database.
#[allow(dead_code)]
pub async fn insert_semester_study_group(
    pool: &Pool<MySql>,
    semester_study_group: DatabaseSemesterStudyGroup,
) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Semester_study_groups (\
role,
study_group_id,
semester,
text_channel)
VALUES (?, ?, ?, ?);",
    )
    .bind(semester_study_group.role.0)
    .bind(semester_study_group.study_group_id)
    .bind(semester_study_group.semester)
    .bind(semester_study_group.text_channel.0)
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

/// Deletes a Semester Study Group saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_semester_study_group(
    pool: &Pool<MySql>,
    semester_study_group: DatabaseSemesterStudyGroup,
) -> Option<bool> {
    match sqlx::query("DELETE FROM Semester_study_groups WHERE role=? AND study_group_id=?")
        .bind(semester_study_group.role.0)
        .bind(semester_study_group.study_group_id)
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

/// Gets the Semester Study Groups saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_semester_study_groups_in_guild(
    pool: &Pool<MySql>,
    guild_id: GuildId,
) -> Option<Vec<DatabaseSemesterStudyGroup>> {
    match sqlx::query_as::<_, DatabaseSemesterStudyGroup>(
        "SELECT Semester_study_groups.*
FROM Semester_study_groups
INNER JOIN Study_groups ON Semester_study_groups.study_group_id = Study_groups.id
WHERE guild_id=?",
    )
    .bind(guild_id.0)
    .fetch_all(pool)
    .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Gets the Semester Study Groups saved for the StudyGroup in the Database
#[allow(dead_code)]
pub async fn get_semester_study_groups_in_study_group(
    pool: &Pool<MySql>,
    study_group_id: i32,
) -> Option<Vec<DatabaseSemesterStudyGroup>> {
    match sqlx::query_as::<_, DatabaseSemesterStudyGroup>(
        "SELECT * FROM Semester_study_groups WHERE study_group_id=?",
    )
    .bind(study_group_id)
    .fetch_all(pool)
    .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Inserts a new Subject into the Database. Return if the Subject was inserted into the
/// Database, may be false if the Subject was already in the Database.
#[allow(dead_code)]
pub async fn insert_subject(pool: &Pool<MySql>, subject: DatabaseSubject) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Subject (role, guild_id, name, text_channel) VALUES (?, ?, ?, ?);",
    )
    .bind(subject.role.0)
    .bind(subject.guild_id.0)
    .bind(subject.name)
    .bind(subject.text_channel.0)
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

/// Deletes a Subject saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_subject(pool: &Pool<MySql>, subject: DatabaseSubject) -> Option<bool> {
    match sqlx::query("DELETE FROM Subject WHERE role=? AND guild_id=?")
        .bind(subject.role.0)
        .bind(subject.guild_id.0)
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

/// Gets theSubject saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_subjects(pool: &Pool<MySql>, guild_id: GuildId) -> Option<Vec<DatabaseSubject>> {
    match sqlx::query_as::<_, DatabaseSubject>("SELECT * FROM Subject WHERE guild_id=?")
        .bind(guild_id.0)
        .fetch_all(pool)
        .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Inserts a new Study-Subject Link into the Database. Return if the Study-Subject Link was
/// inserted into the Database, may be false if the Study-Subject Link was already in the Database.
#[allow(dead_code)]
pub async fn insert_study_subject_link(
    pool: &Pool<MySql>,
    study_subject_link: DatabaseStudySubjectLink,
) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Study_subject_link (\
study_group_role,
subject_role,
guild_id)
VALUES (?, ?, ?);",
    )
    .bind(study_subject_link.study_group_role.0)
    .bind(study_subject_link.subject_role.0)
    .bind(study_subject_link.guild_id.0)
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

/// Deletes a Study-Subject Link saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_study_subject_link(
    pool: &Pool<MySql>,
    study_subject_link: DatabaseStudySubjectLink,
) -> Option<bool> {
    match sqlx::query(
        "DELETE FROM Study_subject_link WHERE study_group_role=? AND subject_role=? AND guild_id=?",
    )
    .bind(study_subject_link.study_group_role.0)
    .bind(study_subject_link.subject_role.0)
    .bind(study_subject_link.guild_id.0)
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

/// Gets the Study-Subject Link saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_study_subject_links_in_guild(
    pool: &Pool<MySql>,
    guild_id: GuildId,
) -> Option<Vec<DatabaseStudySubjectLink>> {
    match sqlx::query_as::<_, DatabaseStudySubjectLink>(
        "SELECT * FROM Study_subject_link WHERE guild_id=?",
    )
    .bind(guild_id.0)
    .fetch_all(pool)
    .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Gets the Study-Subject Link saved for the Subject in the Database
#[allow(dead_code)]
pub async fn get_study_subject_links_for_subject(
    pool: &Pool<MySql>,
    subject_role_id: RoleId,
) -> Option<Vec<DatabaseStudySubjectLink>> {
    match sqlx::query_as::<_, DatabaseStudySubjectLink>(
        "SELECT * FROM Study_subject_link WHERE subject_role=?",
    )
    .bind(subject_role_id.0)
    .fetch_all(pool)
    .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Gets the Study-Subject Link saved for the Semester Study Group in the Database
#[allow(dead_code)]
pub async fn get_study_subject_links_for_study_group(
    pool: &Pool<MySql>,
    study_group_role: RoleId,
) -> Option<Vec<DatabaseStudySubjectLink>> {
    match sqlx::query_as::<_, DatabaseStudySubjectLink>(
        "SELECT * FROM Study_subject_link WHERE study_group_role=?",
    )
    .bind(study_group_role.0)
    .fetch_all(pool)
    .await
    {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Checks id there exists a Study-Subject Link saved for the Semester Study Group and Subject in the Database
#[allow(dead_code)]
pub async fn is_study_subject_link_in_database(
    pool: &Pool<MySql>,
    study_subject_link: DatabaseStudySubjectLink,
) -> Option<bool> {
    match sqlx::query_as::<_, DatabaseStudySubjectLink>(
        "SELECT * FROM Study_subject_link WHERE study_group_role=? AND subject_role=? AND guild_id=?",
    )
    .bind(study_subject_link.study_group_role.0)
    .bind(study_subject_link.subject_role.0)
    .bind(study_subject_link.guild_id.0)
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
