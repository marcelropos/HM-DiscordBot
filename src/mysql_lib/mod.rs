use poise::serenity_prelude::{ChannelId, GuildId, MessageId, RoleId, UserId};
use sqlx::migrate::MigrateError;
use sqlx::mysql::{MySqlConnectOptions, MySqlPoolOptions, MySqlRow};
use sqlx::types::time::{PrimitiveDateTime, Time};
use sqlx::{migrate, FromRow, MySql, Pool, Row};
use tracing::error;

use crate::env;

mod test;
pub mod validate;

/// Tries to establish a Connection with the given env variables and return the MySQL connection
/// Pool if successful.
pub async fn get_connection(max_concurrent_connections: u32) -> Option<Pool<MySql>> {
    match MySqlPoolOptions::new()
        .max_connections(max_concurrent_connections)
        .connect_with(
            MySqlConnectOptions::new()
                .host(env::MYSQL_HOST.get().unwrap().as_str())
                .port(*env::MYSQL_PORT.get().unwrap())
                .database(env::MYSQL_DATABASE.get().unwrap().as_str())
                .username(env::MYSQL_USER.get().unwrap().as_str())
                .password(env::MYSQL_PASSWORD.get().unwrap().as_str()),
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
        .bind(guild_id.get())
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
    TmpcKeepTime(u32),
    AlumniRole(RoleId),
    AlumniRoleSeparatorRole(RoleId),
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseGuild {
    pub guild_id: GuildId,
    pub ghost_warning_deadline: u32,
    pub ghost_kick_deadline: u32,
    pub ghost_time_to_check: Time,
    pub ghost_enabled: bool,
    pub debug_channel: ChannelId,
    pub bot_channel: ChannelId,
    pub help_channel: ChannelId,
    pub logger_pipe_channel: Option<ChannelId>,
    pub study_group_category: ChannelId,
    pub subject_group_category: ChannelId,
    pub studenty_role: RoleId,
    pub tmp_studenty_role: Option<RoleId>,
    pub moderator_role: RoleId,
    pub newsletter_role: RoleId,
    pub nsfw_role: RoleId,
    pub study_role_separator_role: RoleId,
    pub subject_role_separator_role: RoleId,
    pub friend_role: RoleId,
    pub tmpc_keep_time: u32,
    pub alumni_role: RoleId,
    pub alumni_role_separator_role: RoleId,
}

impl TryFrom<NewGuild> for DatabaseGuild {
    type Error = ();

    fn try_from(new_guild: NewGuild) -> Result<Self, ()> {
        Ok(DatabaseGuild {
            guild_id: new_guild.guild_id,
            ghost_warning_deadline: new_guild.ghost_warning_deadline.ok_or(())?,
            ghost_kick_deadline: new_guild.ghost_kick_deadline.ok_or(())?,
            ghost_time_to_check: new_guild.ghost_time_to_check.ok_or(())?,
            ghost_enabled: new_guild.ghost_enabled.ok_or(())?,
            debug_channel: new_guild.debug_channel.ok_or(())?,
            bot_channel: new_guild.bot_channel.ok_or(())?,
            help_channel: new_guild.help_channel.ok_or(())?,
            logger_pipe_channel: None,
            study_group_category: new_guild.study_group_category.ok_or(())?,
            subject_group_category: new_guild.subject_group_category.ok_or(())?,
            studenty_role: new_guild.studenty_role.ok_or(())?,
            tmp_studenty_role: new_guild.tmp_studenty_role.ok_or(())?,
            moderator_role: new_guild.moderator_role.ok_or(())?,
            newsletter_role: new_guild.newsletter_role.ok_or(())?,
            nsfw_role: new_guild.nsfw_role.ok_or(())?,
            study_role_separator_role: new_guild.study_role_separator_role.ok_or(())?,
            subject_role_separator_role: new_guild.subject_role_separator_role.ok_or(())?,
            friend_role: new_guild.friend_role.ok_or(())?,
            tmpc_keep_time: new_guild.tmpc_keep_time.ok_or(())?,
            alumni_role: new_guild.alumni_role.ok_or(())?,
            alumni_role_separator_role: new_guild.alumni_role_separator_role.ok_or(())?,
        })
    }
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord, Default)]
pub struct NewGuild {
    pub guild_id: GuildId,
    pub ghost_warning_deadline: Option<u32>,
    pub ghost_kick_deadline: Option<u32>,
    pub ghost_time_to_check: Option<Time>,
    pub ghost_enabled: Option<bool>,
    pub debug_channel: Option<ChannelId>,
    pub bot_channel: Option<ChannelId>,
    pub help_channel: Option<ChannelId>,
    pub study_group_category: Option<ChannelId>,
    pub subject_group_category: Option<ChannelId>,
    pub studenty_role: Option<RoleId>,
    pub tmp_studenty_role: Option<Option<RoleId>>,
    pub moderator_role: Option<RoleId>,
    pub newsletter_role: Option<RoleId>,
    pub nsfw_role: Option<RoleId>,
    pub study_role_separator_role: Option<RoleId>,
    pub subject_role_separator_role: Option<RoleId>,
    pub friend_role: Option<RoleId>,
    pub tmpc_keep_time: Option<u32>,
    pub alumni_role: Option<RoleId>,
    pub alumni_role_separator_role: Option<RoleId>,
}

impl NewGuild {
    pub fn is_setup(&self) -> bool {
        self.ghost_warning_deadline.is_some()
            && self.ghost_kick_deadline.is_some()
            && self.ghost_time_to_check.is_some()
            && self.ghost_enabled.is_some()
            && self.debug_channel.is_some()
            && self.bot_channel.is_some()
            && self.help_channel.is_some()
            && self.study_group_category.is_some()
            && self.subject_group_category.is_some()
            && self.studenty_role.is_some()
            && self.tmp_studenty_role.is_some()
            && self.moderator_role.is_some()
            && self.newsletter_role.is_some()
            && self.nsfw_role.is_some()
            && self.study_role_separator_role.is_some()
            && self.subject_role_separator_role.is_some()
            && self.friend_role.is_some()
            && self.tmpc_keep_time.is_some()
            && self.alumni_role.is_some()
            && self.alumni_role_separator_role.is_some()
    }
}

impl PartialEq<DatabaseGuild> for NewGuild {
    fn eq(&self, db_guild: &DatabaseGuild) -> bool {
        self.guild_id == db_guild.guild_id
            && self.is_setup()
            && self.ghost_warning_deadline.unwrap() == db_guild.ghost_warning_deadline
            && self.ghost_kick_deadline.unwrap() == db_guild.ghost_kick_deadline
            && self.ghost_time_to_check.unwrap() == db_guild.ghost_time_to_check
            && self.ghost_enabled.unwrap() == db_guild.ghost_enabled
            && self.debug_channel.unwrap() == db_guild.debug_channel
            && self.bot_channel.unwrap() == db_guild.bot_channel
            && self.help_channel.unwrap() == db_guild.help_channel
            && self.study_group_category.unwrap() == db_guild.study_group_category
            && self.subject_group_category.unwrap() == db_guild.subject_group_category
            && self.studenty_role.unwrap() == db_guild.studenty_role
            && self.tmp_studenty_role.unwrap() == db_guild.tmp_studenty_role
            && self.moderator_role.unwrap() == db_guild.moderator_role
            && self.newsletter_role.unwrap() == db_guild.newsletter_role
            && self.nsfw_role.unwrap() == db_guild.nsfw_role
            && self.study_role_separator_role.unwrap() == db_guild.study_role_separator_role
            && self.subject_role_separator_role.unwrap() == db_guild.subject_role_separator_role
            && self.friend_role.unwrap() == db_guild.friend_role
            && self.tmpc_keep_time.unwrap() == db_guild.tmpc_keep_time
            && self.alumni_role.unwrap() == db_guild.alumni_role
            && self.alumni_role_separator_role.unwrap() == db_guild.alumni_role_separator_role
    }
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseAlumniRole {
    pub role: RoleId,
    pub guild_id: GuildId,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseStudyGroup {
    pub id: Option<i32>,
    pub guild_id: GuildId,
    pub name: String,
    pub color: u32,
    pub active: bool,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseSemesterStudyGroup {
    pub role: RoleId,
    pub study_group_id: i32,
    pub semester: u32,
    pub text_channel: ChannelId,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseSubject {
    pub role: RoleId,
    pub guild_id: GuildId,
    pub name: String,
    pub text_channel: ChannelId,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseStudySubjectLink {
    pub study_group_role: RoleId,
    pub subject_role: RoleId,
    pub guild_id: GuildId,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseTmpcJoinChannel {
    pub voice_channel: ChannelId,
    pub guild_id: GuildId,
    pub persist: bool,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseTmpc {
    pub voice_channel: ChannelId,
    pub text_channel: ChannelId,
    pub guild_id: GuildId,
    pub owner: UserId,
    pub persist: bool,
    pub token: u32,
    pub keep: bool,
    pub delete_at: Option<PrimitiveDateTime>,
}

#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq, PartialOrd, Ord)]
pub struct DatabaseTokenMessage {
    pub tmpc_voice_channel: ChannelId,
    pub message_channel: ChannelId,
    pub message: MessageId,
}

impl FromRow<'_, MySqlRow> for DatabaseGuild {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            guild_id: GuildId::new(row.try_get("guild_id")?),
            ghost_warning_deadline: row.try_get("ghost_warn_deadline")?,
            ghost_kick_deadline: row.try_get("ghost_kick_deadline")?,
            ghost_time_to_check: row.try_get("ghost_time_to_check")?,
            ghost_enabled: row.try_get("ghost_enabled")?,
            debug_channel: ChannelId::new(row.try_get("debug_channel")?),
            bot_channel: ChannelId::new(row.try_get("bot_channel")?),
            help_channel: ChannelId::new(row.try_get("help_channel")?),
            logger_pipe_channel: row
                .try_get("logger_pipe_channel")
                .map(|val: Option<u64>| val.map(ChannelId::new))?,
            study_group_category: ChannelId::new(row.try_get("study_group_category")?),
            subject_group_category: ChannelId::new(row.try_get("subject_group_category")?),
            studenty_role: RoleId::new(row.try_get("studenty_role")?),
            tmp_studenty_role: row
                .try_get("tmp_studenty_role")
                .map(|val: Option<u64>| val.map(RoleId::new))?,
            moderator_role: RoleId::new(row.try_get("moderator_role")?),
            newsletter_role: RoleId::new(row.try_get("newsletter_role")?),
            nsfw_role: RoleId::new(row.try_get("nsfw_role")?),
            study_role_separator_role: RoleId::new(row.try_get("study_role_separator_role")?),
            subject_role_separator_role: RoleId::new(row.try_get("subject_role_separator_role")?),
            friend_role: RoleId::new(row.try_get("friend_role")?),
            tmpc_keep_time: row.try_get("tmpc_keep_time")?,
            alumni_role: RoleId::new(row.try_get("alumni_role")?),
            alumni_role_separator_role: RoleId::new(row.try_get("alumni_role_separator_role")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseAlumniRole {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            role: RoleId::new(row.try_get("role")?),
            guild_id: GuildId::new(row.try_get("guild_id")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseStudyGroup {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            id: row.try_get("id")?,
            guild_id: GuildId::new(row.try_get("guild_id")?),
            name: row.try_get("name")?,
            color: row.try_get("color")?,
            active: row.try_get("active")?,
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseSemesterStudyGroup {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            role: RoleId::new(row.try_get("role")?),
            study_group_id: row.try_get("study_group_id")?,
            semester: row.try_get("semester")?,
            text_channel: ChannelId::new(row.try_get("text_channel")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseSubject {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            role: RoleId::new(row.try_get("role")?),
            guild_id: GuildId::new(row.try_get("guild_id")?),
            name: row.try_get("name")?,
            text_channel: ChannelId::new(row.try_get("text_channel")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseStudySubjectLink {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            study_group_role: RoleId::new(row.try_get("study_group_role")?),
            subject_role: RoleId::new(row.try_get("subject_role")?),
            guild_id: GuildId::new(row.try_get("guild_id")?),
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseTmpcJoinChannel {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            voice_channel: ChannelId::new(row.try_get("voice_channel")?),
            guild_id: GuildId::new(row.try_get("guild_id")?),
            persist: row.try_get("persist")?,
        })
    }
}

impl FromRow<'_, MySqlRow> for DatabaseTmpc {
    fn from_row(row: &'_ MySqlRow) -> sqlx::Result<Self> {
        Ok(Self {
            voice_channel: ChannelId::new(row.try_get("voice_channel")?),
            text_channel: ChannelId::new(row.try_get("text_channel")?),
            guild_id: GuildId::new(row.try_get("guild_id")?),
            owner: UserId::new(row.try_get("owner")?),
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
            tmpc_voice_channel: ChannelId::new(row.try_get("tmpc_voice_channel")?),
            message: MessageId::new(row.try_get("message")?),
            message_channel: ChannelId::new(row.try_get("message_channel")?),
        })
    }
}

/// Inserts a new Guild into the Database. Return if the guild was inserted into the Database,
/// may be false if the guild was already in the Database.
///
/// `DatabaseGuild::logger_pipe_channel` is ignored.
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
tmp_studenty_role,
moderator_role,
newsletter_role,
nsfw_role,
study_role_separator_role,
subject_role_separator_role,
friend_role,
tmpc_keep_time,
alumni_role,
alumni_role_separator_role)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
    )
    .bind(guild.guild_id.get())
    .bind(guild.ghost_warning_deadline)
    .bind(guild.ghost_kick_deadline)
    .bind(guild.ghost_time_to_check)
    .bind(guild.ghost_enabled)
    .bind(guild.debug_channel.get())
    .bind(guild.bot_channel.get())
    .bind(guild.help_channel.get())
    .bind(guild.study_group_category.get())
    .bind(guild.subject_group_category.get())
    .bind(guild.studenty_role.get())
    .bind(guild.tmp_studenty_role.map(|role| role.get()))
    .bind(guild.moderator_role.get())
    .bind(guild.newsletter_role.get())
    .bind(guild.nsfw_role.get())
    .bind(guild.study_role_separator_role.get())
    .bind(guild.subject_role_separator_role.get())
    .bind(guild.friend_role.get())
    .bind(guild.tmpc_keep_time)
    .bind(guild.alumni_role.get())
    .bind(guild.alumni_role_separator_role.get())
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
        .bind(guild_id.get())
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
        .bind(guild_id.get())
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

/// Gets the guild information from the Database
#[allow(dead_code)]
pub async fn get_all_guilds(pool: &Pool<MySql>) -> Option<Vec<DatabaseGuild>> {
    match sqlx::query_as::<_, DatabaseGuild>("SELECT * FROM Guild")
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
    tmpc_keep_time: u32,
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
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::BotChannel(val) => {
            query = query_format!("bot_channel");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::HelpChannel(val) => {
            query = query_format!("help_channel");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::LoggerPipeChannel(val) => {
            query = query_format!("logger_pipe_channel");
            sqlx::query(query.as_str()).bind(val.map(|val| val.get()))
        }
        Column::StudyGroupCategory(val) => {
            query = query_format!("study_group_category");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::SubjectGroupCategory(val) => {
            query = query_format!("subject_group_category");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::StudentyRole(val) => {
            query = query_format!("studenty_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::TmpStudentyRole(val) => {
            query = query_format!("tmp_studenty_role");
            sqlx::query(query.as_str()).bind(val.map(|val| val.get()))
        }
        Column::ModeratorRole(val) => {
            query = query_format!("moderator_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::NewsletterRole(val) => {
            query = query_format!("newsletter_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::NsfwRole(val) => {
            query = query_format!("nsfw_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::StudyRoleSeparatorRole(val) => {
            query = query_format!("study_role_separator_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::SubjectRoleSeparatorRole(val) => {
            query = query_format!("subject_role_separator_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::FriendRole(val) => {
            query = query_format!("friend_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::TmpcKeepTime(val) => {
            query = query_format!("tmpc_keep_time");
            sqlx::query(query.as_str()).bind(val)
        }
        Column::AlumniRole(val) => {
            query = query_format!("alumni_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
        Column::AlumniRoleSeparatorRole(val) => {
            query = query_format!("alumni_role_separator_role");
            sqlx::query(query.as_str()).bind(val.get())
        }
    }
    .bind(guild_id.get())
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

/// Update everything in a Guild in the Database. Return if the guild was changed
///
/// `DatabaseGuild::logger_pipe_channel` is ignored.
#[allow(dead_code)]
pub async fn update_guild(pool: &Pool<MySql>, guild: DatabaseGuild) -> Option<bool> {
    match sqlx::query(
        "UPDATE Guild SET
ghost_warn_deadline=?,
ghost_kick_deadline=?,
ghost_time_to_check=?,
ghost_enabled=?,
debug_channel=?,
bot_channel=?,
help_channel=?,
study_group_category=?,
subject_group_category=?,
studenty_role=?,
tmp_studenty_role=?,
moderator_role=?,
newsletter_role=?,
nsfw_role=?,
study_role_separator_role=?,
subject_role_separator_role=?,
friend_role=?,
tmpc_keep_time=?,
alumni_role=?,
alumni_role_separator_role=?
WHERE guild_id=?;",
    )
    .bind(guild.ghost_warning_deadline)
    .bind(guild.ghost_kick_deadline)
    .bind(guild.ghost_time_to_check)
    .bind(guild.ghost_enabled)
    .bind(guild.debug_channel.get())
    .bind(guild.bot_channel.get())
    .bind(guild.help_channel.get())
    .bind(guild.study_group_category.get())
    .bind(guild.subject_group_category.get())
    .bind(guild.studenty_role.get())
    .bind(guild.tmp_studenty_role.map(|role| role.get()))
    .bind(guild.moderator_role.get())
    .bind(guild.newsletter_role.get())
    .bind(guild.nsfw_role.get())
    .bind(guild.study_role_separator_role.get())
    .bind(guild.subject_role_separator_role.get())
    .bind(guild.friend_role.get())
    .bind(guild.tmpc_keep_time)
    .bind(guild.alumni_role.get())
    .bind(guild.alumni_role_separator_role.get())
    .bind(guild.guild_id.get())
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
        .bind(alumni_role.role.get())
        .bind(alumni_role.guild_id.get())
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
        .bind(alumni_role.role.get())
        .bind(alumni_role.guild_id.get())
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
        .bind(guild_id.get())
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
    .bind(study_group.guild_id.get())
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
        .bind(study_group.guild_id.get())
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
        .bind(guild_id.get())
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

/// Updates the name, color and active values of the study group, returns if the value was changed
///
/// IMPORTANT: The changed values only change in the database, existing roles and chats need to be updated outside this
/// function if wanted
#[allow(dead_code)]
pub async fn update_study_group(
    pool: &Pool<MySql>,
    study_group: DatabaseStudyGroup,
) -> Option<bool> {
    if study_group.id.is_none() {
        error!("Can't update Study group without id");
        return None;
    }
    match sqlx::query("UPDATE Study_groups SET name=?, color=?, active=? WHERE id=? AND guild_id=?")
        .bind(study_group.name)
        .bind(study_group.color)
        .bind(study_group.active)
        .bind(study_group.id)
        .bind(study_group.guild_id.get())
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
    .bind(semester_study_group.role.get())
    .bind(semester_study_group.study_group_id)
    .bind(semester_study_group.semester)
    .bind(semester_study_group.text_channel.get())
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
        .bind(semester_study_group.role.get())
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
    .bind(guild_id.get())
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
    .bind(subject.role.get())
    .bind(subject.guild_id.get())
    .bind(subject.name)
    .bind(subject.text_channel.get())
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
        .bind(subject.role.get())
        .bind(subject.guild_id.get())
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

/// Gets the Subject saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_subjects(pool: &Pool<MySql>, guild_id: GuildId) -> Option<Vec<DatabaseSubject>> {
    match sqlx::query_as::<_, DatabaseSubject>("SELECT * FROM Subject WHERE guild_id=?")
        .bind(guild_id.get())
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
    .bind(study_subject_link.study_group_role.get())
    .bind(study_subject_link.subject_role.get())
    .bind(study_subject_link.guild_id.get())
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
    .bind(study_subject_link.study_group_role.get())
    .bind(study_subject_link.subject_role.get())
    .bind(study_subject_link.guild_id.get())
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
    .bind(guild_id.get())
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
    .bind(subject_role_id.get())
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
    .bind(study_group_role.get())
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
    .bind(study_subject_link.study_group_role.get())
    .bind(study_subject_link.subject_role.get())
    .bind(study_subject_link.guild_id.get())
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

/// Inserts a new Tmpc Join Channel into the Database. Return if the Tmpc Join Channel was inserted
/// into the Database, may be false if the Tmpc Join Channel was already in the Database.
#[allow(dead_code)]
pub async fn insert_tmpc_join_channel(
    pool: &Pool<MySql>,
    tmpc_join_channel: DatabaseTmpcJoinChannel,
) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Tmpc_join_channel (voice_channel, guild_id, persist) VALUES (?, ?, ?);",
    )
    .bind(tmpc_join_channel.voice_channel.get())
    .bind(tmpc_join_channel.guild_id.get())
    .bind(tmpc_join_channel.persist)
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

/// Deletes a Tmpc Join Channel saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_tmpc_join_channel(
    pool: &Pool<MySql>,
    tmpc_join_channel: DatabaseTmpcJoinChannel,
) -> Option<bool> {
    match sqlx::query("DELETE FROM Tmpc_join_channel WHERE voice_channel=? AND guild_id=?")
        .bind(tmpc_join_channel.voice_channel.get())
        .bind(tmpc_join_channel.guild_id.get())
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

/// Gets the Tmpc Join Channel saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_tmpc_join_channel(
    pool: &Pool<MySql>,
    guild_id: GuildId,
) -> Option<Vec<DatabaseTmpcJoinChannel>> {
    match sqlx::query_as::<_, DatabaseTmpcJoinChannel>(
        "SELECT * FROM Tmpc_join_channel WHERE guild_id=?",
    )
    .bind(guild_id.get())
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

/// Updates the persist value of the tmpc join channel, returns if the value was changed
///
/// IMPORTANT: The changed values don't change existing tmpc
#[allow(dead_code)]
pub async fn update_tmpc_join_channel_persist(
    pool: &Pool<MySql>,
    tmpc_join_channel: DatabaseTmpcJoinChannel,
) -> Option<bool> {
    match sqlx::query("UPDATE Tmpc_join_channel SET persist=? WHERE voice_channel=? AND guild_id=?")
        .bind(tmpc_join_channel.persist)
        .bind(tmpc_join_channel.voice_channel.get())
        .bind(tmpc_join_channel.guild_id.get())
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

/// Inserts a new Tmpc into the Database. Return if the Tmpc was inserted into the Database, may be
/// false if the Tmpc was already in the Database.
///
/// `DatabaseTmpc::delete_at` is ignored
#[allow(dead_code)]
pub async fn insert_tmpc(pool: &Pool<MySql>, tmpc: DatabaseTmpc) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Tmpc (
voice_channel,
text_channel,
guild_id,
owner,
persist,
token,
keep)
VALUES (?, ?, ?, ?, ?, ?, ?);",
    )
    .bind(tmpc.voice_channel.get())
    .bind(tmpc.text_channel.get())
    .bind(tmpc.guild_id.get())
    .bind(tmpc.owner.get())
    .bind(tmpc.persist)
    .bind(tmpc.token)
    .bind(tmpc.keep)
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

/// Modifies the deleteAt time of a Tmpc, returns if the value was changed
#[allow(dead_code)]
pub async fn update_tmpc_delete_at(pool: &Pool<MySql>, tmpc: DatabaseTmpc) -> Option<bool> {
    match sqlx::query("UPDATE Tmpc SET deleteAt=? WHERE voice_channel=? AND guild_id=?")
        .bind(tmpc.delete_at)
        .bind(tmpc.voice_channel.get())
        .bind(tmpc.guild_id.get())
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

/// Updates the token value of a tmpc, returns if the value was changed
#[allow(dead_code)]
pub async fn update_tmpc_token(pool: &Pool<MySql>, tmpc: DatabaseTmpc) -> Option<bool> {
    match sqlx::query("UPDATE Tmpc SET token=? WHERE voice_channel=? AND guild_id=?")
        .bind(tmpc.token)
        .bind(tmpc.voice_channel.get())
        .bind(tmpc.guild_id.get())
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

/// Updates the keep value of a tmpc, returns if the value was changed
#[allow(dead_code)]
pub async fn update_tmpc_keep(pool: &Pool<MySql>, tmpc: DatabaseTmpc) -> Option<bool> {
    match sqlx::query("UPDATE Tmpc SET keep=? WHERE voice_channel=? AND guild_id=?")
        .bind(tmpc.keep)
        .bind(tmpc.voice_channel.get())
        .bind(tmpc.guild_id.get())
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

/// Deletes a Tmpc  saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_tmpc(pool: &Pool<MySql>, tmpc: DatabaseTmpc) -> Option<bool> {
    match sqlx::query("DELETE FROM Tmpc WHERE voice_channel=? AND guild_id=?")
        .bind(tmpc.voice_channel.get())
        .bind(tmpc.guild_id.get())
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

/// Gets the Tmpc saved for the Guild in the Database
#[allow(dead_code)]
pub async fn get_tmpc(pool: &Pool<MySql>, guild_id: GuildId) -> Option<Vec<DatabaseTmpc>> {
    match sqlx::query_as::<_, DatabaseTmpc>("SELECT * FROM Tmpc WHERE guild_id=?")
        .bind(guild_id.get())
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

/// Inserts a new Token Message into the Database. Return if the Token Message was inserted into the
/// Database, may be false if the Token Message was already in the Database.
#[allow(dead_code)]
pub async fn insert_token_message(
    pool: &Pool<MySql>,
    token_message: DatabaseTokenMessage,
) -> Option<bool> {
    match sqlx::query(
        "INSERT IGNORE INTO Token_message (tmpc_voice_channel, message, message_channel) VALUES (?, ?, ?);",
    )
    .bind(token_message.tmpc_voice_channel.get())
    .bind(token_message.message.get())
    .bind(token_message.message_channel.get())
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

/// Deletes a Token Message saved in the Database, returns if the query deleted something
#[allow(dead_code)]
pub async fn delete_token_message(
    pool: &Pool<MySql>,
    token_message: DatabaseTokenMessage,
) -> Option<bool> {
    match sqlx::query(
        "DELETE FROM Token_message WHERE tmpc_voice_channel=? AND message=? AND message_channel=?",
    )
    .bind(token_message.tmpc_voice_channel.get())
    .bind(token_message.message.get())
    .bind(token_message.message_channel.get())
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

/// Deletes all Token Message saved in the Database for the tmpc channel, returns if the query
/// deleted something
#[allow(dead_code)]
pub async fn delete_all_token_messages(
    pool: &Pool<MySql>,
    tmpc_voice_channel: ChannelId,
) -> Option<bool> {
    match sqlx::query("DELETE FROM Token_message WHERE tmpc_voice_channel=?")
        .bind(tmpc_voice_channel.get())
        .execute(pool)
        .await
    {
        Ok(val) => Some(val.rows_affected() > 0),
        Err(err) => {
            error!(error = err.to_string(), "Problem executing query");
            None
        }
    }
}

/// Gets the Token Message saved for tmpc voice channel in the Database
#[allow(dead_code)]
pub async fn get_token_messages(
    pool: &Pool<MySql>,
    tmpc_voice_channel: ChannelId,
) -> Option<Vec<DatabaseTokenMessage>> {
    match sqlx::query_as::<_, DatabaseTokenMessage>(
        "SELECT * FROM Token_message WHERE tmpc_voice_channel=?",
    )
    .bind(tmpc_voice_channel.get())
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
