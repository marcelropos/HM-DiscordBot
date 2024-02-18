use poise::serenity_prelude::{GuildChannel, GuildId, Mentionable, Role};
use time::Time;

use crate::bot::{checks, Context, Error};
use crate::mysql_lib;
use crate::mysql_lib::{DatabaseGuild, NewGuild};

const OUTSIDE_RANGE: &str = "**Value of number was outside of valid numbers!**";
const NO_NUMBER: &str = "**Did not get a number!**";
const NO_BOOL: &str = "**Did not get a bool value!**";
const NO_CHANNEL_MENTION: &str = "**Did not get a Channel Mention**";
const NO_ROLE_MENTION: &str = "**Did not get a Role Mention**";

const WANING_COMMAND: &str = "setup <days_before_warning>";
const WARNING_BASE_STRING: &str = "Edit the command to include the Days a User can be on the \
                                   server unverified before he is warned about his impending kick.";
const WARNING_RECOMMENDATION: &str = "7 days is recommended. The value must be between 2 and 14";

const KICK_COMMAND: &str = "setup <days_before_kick>";
const KICK_BASE_STRING: &str = "Edit the command to include the Days a User can be on the server \
                                unverified before he is kicked.";

const GHOST_TIME_COMMAND: &str = "setup <hour_of_day_to_check>";
const GHOST_TIME_BASE_STRING: &str =
    "Edit the command to include the Hour of the day where the ghosts are checked.";
const GHOST_TIME_RECOMMENDATION: &str =
    "8 o'clock is recommended. The value must be between 0 and 23";

const GHOST_ENABLED_COMMAND: &str = "setup <check_ghosts>";
const GHOST_ENABLED_BASE_STRING: &str =
    "Edit the command to include if the ghosts check should be turned on. `true|false`";

const DEBUG_CHANNEL_COMMAND: &str = "setup #<debug-channel>";
const DEBUG_CHANNEL_BASE_STRING: &str =
    "Edit the command to include a mention to the debug channel";

const BOT_CHANNEL_COMMAND: &str = "setup #<bot-channel>";
const BOT_CHANNEL_BASE_STRING: &str = "Edit the command to include a mention to the bot channel";

const HELP_CHANNEL_COMMAND: &str = "setup #<help-channel>";
const HELP_CHANNEL_BASE_STRING: &str = "Edit the command to include a mention to the help channel";

const STUDY_GROUP_CATEGORY_COMMAND: &str = "setup #<study-group-category>";
const STUDY_GROUP_CATEGORY_BASE_STRING: &str =
    "Edit the command to include a mention to the study group category";

const SUBJECT_GROUP_CATEGORY_COMMAND: &str = "setup #<subject-group-category>";
const SUBJECT_GROUP_CATEGORY_BASE_STRING: &str =
    "Edit the command to include a mention to the subject group category";

const STUDENTY_ROLE_COMMAND: &str = "setup @<studenty_role>";
const STUDENTY_ROLE_BASE_STRING: &str =
    "Edit the command to include a mention to the studenty role";

const TMP_STUDENTY_ROLE_COMMAND: &str = "setup @<tmp-studenty_role>";
const TMP_STUDENTY_ROLE_COMMAND_2: &str = "setup None";
const TMP_STUDENTY_ROLE_BASE_STRING: &str =
    "Edit the command to include a mention to the temporary studenty role or None to leave empty";

const MODERATOR_ROLE_COMMAND: &str = "setup @<moderator_role>";
const MODERATOR_ROLE_BASE_STRING: &str =
    "Edit the command to include a mention to the moderator role";

const NEWSLETTER_ROLE_COMMAND: &str = "setup @<newsletter_role>";
const NEWSLETTER_ROLE_BASE_STRING: &str =
    "Edit the command to include a mention to the newsletter role";

const NSFW_ROLE_COMMAND: &str = "setup @<nsfw_role>";
const NSFW_ROLE_BASE_STRING: &str = "Edit the command to include a mention to the nsfw role";

const STUDY_ROLE_SEPARATOR_ROLE_COMMAND: &str = "setup @<study_role_separator_role>";
const STUDY_ROLE_SEPARATOR_ROLE_BASE_STRING: &str = "Edit the command to include a mention to the \
                                                     Separator role, below which the study roles \
                                                     should be created";

const SUBJECT_ROLE_SEPARATOR_ROLE_COMMAND: &str = "setup @<subject_role_separator_role>";
const SUBJECT_ROLE_SEPARATOR_ROLE_BASE_STRING: &str = "Edit the command to include a mention to \
                                                       the Separator role, below which the subject \
                                                       roles should be created";

const FRIEND_ROLE_COMMAND: &str = "setup @<friend_role>";
const FRIEND_ROLE_BASE_STRING: &str = "Edit the command to include a mention to the friend role";

const ALUMNI_ROLE_COMMAND: &str = "setup @<alumni_role>";
const ALUMNI_ROLE_BASE_STRING: &str = "Edit the command to include a mention to the alumni role";

const ALUMNI_ROLE_SEPARATOR_ROLE_COMMAND: &str = "setup @<alumni_role_separator_role>";
const ALUMNI_ROLE_SEPARATOR_ROLE_BASE_STRING: &str = "Edit the command to include a mention to \
                                                       the Separator role, below which the alumni \
                                                       roles should be created";

const TMPC_TIME_COMMAND: &str = "setup <hours_to_keep>";
const TMPC_TIME_BASE_STRING: &str =
    "Edit the command to include the Hours to keep a TMPC (if turned on) after everyone left.";
const TMPC_TIME_RECOMMENDATION: &str =
    "24 hours is recommended. The value must be between 0 and 168 (7 days)";

async fn warning_setup(
    ctx: Context<'_>,
    number: Option<u32>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
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
                        "Kept Ghost warning Deadline to {} days.\n\
                         {}\n\
                         `{}{}`\n\
                         14 days is recommended. The value must be between {} and 28{}",
                        db_guild.ghost_warning_deadline,
                        KICK_BASE_STRING,
                        ctx.prefix(),
                        KICK_COMMAND,
                        db_guild.ghost_warning_deadline + 1,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match number {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`\n{}{}",
                    NO_NUMBER,
                    WARNING_BASE_STRING,
                    ctx.prefix(),
                    WANING_COMMAND,
                    WARNING_RECOMMENDATION,
                    skip_message
                ))
                .await;
        }
        Some(number) => {
            if !(2..=14).contains(&number) {
                let _ = ctx
                    .say(format!(
                        "{}\n{}\n`{}{}`\n{}{}",
                        OUTSIDE_RANGE,
                        WARNING_BASE_STRING,
                        ctx.prefix(),
                        WANING_COMMAND,
                        WARNING_RECOMMENDATION,
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
                         {}\n\
                         `{}{}`\n\
                         14 days is recommended. The value must be between {} and 28{}",
                        number,
                        KICK_BASE_STRING,
                        ctx.prefix(),
                        KICK_COMMAND,
                        number + 1,
                        skip_message
                    ))
                    .await;
            }
        }
    }
    Ok(())
}

async fn kick_setup(
    ctx: Context<'_>,
    number: Option<u32>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.ghost_kick_deadline = Some(db_guild.ghost_kick_deadline);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Ghost kick Deadline to {} days.\n{}\n`{}{}`\n{}{}",
                        db_guild.ghost_kick_deadline,
                        GHOST_TIME_BASE_STRING,
                        ctx.prefix(),
                        GHOST_TIME_COMMAND,
                        GHOST_TIME_RECOMMENDATION,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    let warning_deadline;
    {
        let hash_map = ctx.data().setup_in_progress.lock().unwrap();
        let new_guild = hash_map.get(&guild_id).unwrap();
        // the value is already set since this is always set before
        warning_deadline = new_guild.ghost_warning_deadline.unwrap();
    }
    match number {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`\n\
                    14 days is recommended. The value must be between {} and 28{}",
                    NO_NUMBER,
                    KICK_BASE_STRING,
                    ctx.prefix(),
                    KICK_COMMAND,
                    warning_deadline,
                    skip_message
                ))
                .await;
        }
        Some(number) => {
            if !(warning_deadline..=28).contains(&number) {
                let _ = ctx
                    .say(format!(
                        "{}\n{}\n`{}{}`\n\
                        14 days is recommended. The value must be between {} and 28{}",
                        OUTSIDE_RANGE,
                        KICK_BASE_STRING,
                        ctx.prefix(),
                        KICK_COMMAND,
                        warning_deadline,
                        skip_message
                    ))
                    .await;
            } else {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.ghost_kick_deadline = Some(number);
                }
                let _ = ctx
                    .say(format!(
                        "Set Ghost kick Deadline to {} days.\n{}\n`{}{}`\n{}{}",
                        number,
                        GHOST_TIME_BASE_STRING,
                        ctx.prefix(),
                        GHOST_TIME_COMMAND,
                        GHOST_TIME_RECOMMENDATION,
                        skip_message
                    ))
                    .await;
            }
        }
    }
    Ok(())
}

async fn ghost_time_setup(
    ctx: Context<'_>,
    number: Option<u32>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.ghost_time_to_check = Some(db_guild.ghost_time_to_check);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Ghost Time to check to {} o'clock.\n{}\n`{}{}`{}",
                        db_guild.ghost_time_to_check.hour(),
                        GHOST_ENABLED_BASE_STRING,
                        ctx.prefix(),
                        GHOST_ENABLED_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match number {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`\n{}{}",
                    NO_NUMBER,
                    GHOST_TIME_BASE_STRING,
                    ctx.prefix(),
                    GHOST_TIME_COMMAND,
                    GHOST_TIME_RECOMMENDATION,
                    skip_message
                ))
                .await;
        }
        Some(number) => {
            if !(0..=23).contains(&number) {
                let _ = ctx
                    .say(format!(
                        "{}\n{}\n`{}{}`\n{}{}",
                        OUTSIDE_RANGE,
                        GHOST_TIME_BASE_STRING,
                        ctx.prefix(),
                        GHOST_TIME_COMMAND,
                        GHOST_TIME_RECOMMENDATION,
                        skip_message
                    ))
                    .await;
            } else {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.ghost_time_to_check =
                        Some(Time::from_hms(number as u8, 0, 0).unwrap());
                }
                let _ = ctx
                    .say(format!(
                        "Set Ghost Time to check to {} o'clock.\n{}\n`{}{}`{}",
                        number,
                        GHOST_ENABLED_BASE_STRING,
                        ctx.prefix(),
                        GHOST_ENABLED_COMMAND,
                        skip_message
                    ))
                    .await;
            }
        }
    }
    Ok(())
}

async fn ghost_enabled_setup(
    ctx: Context<'_>,
    flag: Option<bool>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.ghost_enabled = Some(db_guild.ghost_enabled);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Ghost check {}.\n{}\n`{}{}`{}",
                        if db_guild.ghost_enabled {
                            "enabled"
                        } else {
                            "disabled"
                        },
                        DEBUG_CHANNEL_BASE_STRING,
                        ctx.prefix(),
                        DEBUG_CHANNEL_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match flag {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_BOOL,
                    GHOST_ENABLED_BASE_STRING,
                    ctx.prefix(),
                    GHOST_ENABLED_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(flag) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.ghost_enabled = Some(flag);
            }
            let _ = ctx
                .say(format!(
                    "Set Ghost check to {}.\n{}\n`{}{}`{}",
                    if flag { "enabled" } else { "disabled" },
                    DEBUG_CHANNEL_BASE_STRING,
                    ctx.prefix(),
                    DEBUG_CHANNEL_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn debug_channel_setup(
    ctx: Context<'_>,
    channel_mention: Option<GuildChannel>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.debug_channel = Some(db_guild.debug_channel);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Debug Channel to {}.\n{}\n`{}{}`{}",
                        db_guild.debug_channel.mention(),
                        BOT_CHANNEL_BASE_STRING,
                        ctx.prefix(),
                        BOT_CHANNEL_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match channel_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_CHANNEL_MENTION,
                    DEBUG_CHANNEL_BASE_STRING,
                    ctx.prefix(),
                    DEBUG_CHANNEL_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(channel_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.debug_channel = Some(channel_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Debug Channel to {}.\n{}\n`{}{}`{}",
                    channel_mention.mention(),
                    BOT_CHANNEL_BASE_STRING,
                    ctx.prefix(),
                    BOT_CHANNEL_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn bot_channel_setup(
    ctx: Context<'_>,
    channel_mention: Option<GuildChannel>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.bot_channel = Some(db_guild.bot_channel);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Bot Channel to {}.\n{}\n`{}{}`{}",
                        db_guild.bot_channel.mention(),
                        HELP_CHANNEL_BASE_STRING,
                        ctx.prefix(),
                        HELP_CHANNEL_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match channel_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_CHANNEL_MENTION,
                    BOT_CHANNEL_BASE_STRING,
                    ctx.prefix(),
                    BOT_CHANNEL_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(channel_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.bot_channel = Some(channel_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Bot Channel to {}.\n{}\n`{}{}`{}",
                    channel_mention.mention(),
                    HELP_CHANNEL_BASE_STRING,
                    ctx.prefix(),
                    HELP_CHANNEL_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn help_channel_setup(
    ctx: Context<'_>,
    channel_mention: Option<GuildChannel>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.help_channel = Some(db_guild.help_channel);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Help Channel to {}.\n{}\n`{}{}`{}",
                        db_guild.bot_channel.mention(),
                        STUDY_GROUP_CATEGORY_BASE_STRING,
                        ctx.prefix(),
                        STUDY_GROUP_CATEGORY_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match channel_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_CHANNEL_MENTION,
                    HELP_CHANNEL_BASE_STRING,
                    ctx.prefix(),
                    HELP_CHANNEL_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(channel_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.help_channel = Some(channel_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Help Channel to {}.\n{}\n`{}{}`{}",
                    channel_mention.mention(),
                    STUDY_GROUP_CATEGORY_BASE_STRING,
                    ctx.prefix(),
                    STUDY_GROUP_CATEGORY_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn study_group_category_setup(
    ctx: Context<'_>,
    channel_mention: Option<GuildChannel>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.study_group_category = Some(db_guild.study_group_category);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Study Group Category to {}.\n{}\n`{}{}`{}",
                        db_guild.study_group_category.mention(),
                        SUBJECT_GROUP_CATEGORY_BASE_STRING,
                        ctx.prefix(),
                        SUBJECT_GROUP_CATEGORY_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match channel_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_CHANNEL_MENTION,
                    STUDY_GROUP_CATEGORY_BASE_STRING,
                    ctx.prefix(),
                    STUDY_GROUP_CATEGORY_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(channel_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.study_group_category = Some(channel_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Study Group Category to {}.\n{}\n`{}{}`{}",
                    channel_mention.mention(),
                    SUBJECT_GROUP_CATEGORY_BASE_STRING,
                    ctx.prefix(),
                    SUBJECT_GROUP_CATEGORY_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn subject_group_category_setup(
    ctx: Context<'_>,
    channel_mention: Option<GuildChannel>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.subject_group_category = Some(db_guild.subject_group_category);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Subject Group Category to {}.\n{}\n`{}{}`{}",
                        db_guild.subject_group_category.mention(),
                        STUDENTY_ROLE_BASE_STRING,
                        ctx.prefix(),
                        STUDENTY_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match channel_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_CHANNEL_MENTION,
                    SUBJECT_GROUP_CATEGORY_BASE_STRING,
                    ctx.prefix(),
                    SUBJECT_GROUP_CATEGORY_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(channel_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.subject_group_category = Some(channel_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Subject Group Category to {}.\n{}\n`{}{}`{}",
                    channel_mention.mention(),
                    STUDENTY_ROLE_BASE_STRING,
                    ctx.prefix(),
                    STUDENTY_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn studenty_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.studenty_role = Some(db_guild.studenty_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Studenty Role to {}.\n{}\n`{prefix}{}` or `{prefix}{}`{}",
                        db_guild.studenty_role.mention(),
                        TMP_STUDENTY_ROLE_BASE_STRING,
                        TMP_STUDENTY_ROLE_COMMAND,
                        TMP_STUDENTY_ROLE_COMMAND_2,
                        skip_message,
                        prefix = ctx.prefix()
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    STUDENTY_ROLE_BASE_STRING,
                    ctx.prefix(),
                    STUDENTY_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.studenty_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Studenty Role to {}.\n{}\n`{prefix}{}` or `{prefix}{}`{}",
                    role_mention.mention(),
                    TMP_STUDENTY_ROLE_BASE_STRING,
                    TMP_STUDENTY_ROLE_COMMAND,
                    TMP_STUDENTY_ROLE_COMMAND_2,
                    skip_message,
                    prefix = ctx.prefix()
                ))
                .await;
        }
    }
    Ok(())
}

async fn tmp_studenty_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.tmp_studenty_role = Some(db_guild.tmp_studenty_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept temporary Studenty Role to {}.\n{}\n`{}{}`{}",
                        if db_guild.tmp_studenty_role.is_some() {
                            db_guild.tmp_studenty_role.unwrap().mention().to_string()
                        } else {
                            "None".to_string()
                        },
                        MODERATOR_ROLE_BASE_STRING,
                        ctx.prefix(),
                        MODERATOR_ROLE_COMMAND,
                        skip_message,
                    ))
                    .await;
                return Ok(());
            }
        } else if text.eq_ignore_ascii_case("none") {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.tmp_studenty_role = Some(None);
            }
            let _ = ctx
                .say(format!(
                    "Set temporary Studenty Role to None.\n{}\n`{}{}`{}",
                    MODERATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    MODERATOR_ROLE_COMMAND,
                    skip_message,
                ))
                .await;
            return Ok(());
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{prefix}{}` or `{prefix}{}`{}",
                    NO_ROLE_MENTION,
                    TMP_STUDENTY_ROLE_BASE_STRING,
                    TMP_STUDENTY_ROLE_COMMAND,
                    TMP_STUDENTY_ROLE_COMMAND_2,
                    skip_message,
                    prefix = ctx.prefix()
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.tmp_studenty_role = Some(Some(role_mention.id));
            }
            let _ = ctx
                .say(format!(
                    "Set temporary Studenty Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    MODERATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    MODERATOR_ROLE_COMMAND,
                    skip_message,
                ))
                .await;
        }
    }
    Ok(())
}

async fn moderator_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.moderator_role = Some(db_guild.moderator_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Moderator Role to {}.\n{}\n`{}{}`{}",
                        db_guild.moderator_role.mention(),
                        NEWSLETTER_ROLE_BASE_STRING,
                        ctx.prefix(),
                        NEWSLETTER_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    MODERATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    MODERATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.moderator_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Moderator Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    NEWSLETTER_ROLE_BASE_STRING,
                    ctx.prefix(),
                    NEWSLETTER_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn newsletter_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.newsletter_role = Some(db_guild.newsletter_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Newsletter Role to {}.\n{}\n`{}{}`{}",
                        db_guild.newsletter_role.mention(),
                        NSFW_ROLE_BASE_STRING,
                        ctx.prefix(),
                        NSFW_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    NEWSLETTER_ROLE_BASE_STRING,
                    ctx.prefix(),
                    NEWSLETTER_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.newsletter_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Newsletter Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    NSFW_ROLE_BASE_STRING,
                    ctx.prefix(),
                    NSFW_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn nsfw_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.nsfw_role = Some(db_guild.nsfw_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept NSFW Role to {}.\n{}\n`{}{}`{}",
                        db_guild.nsfw_role.mention(),
                        STUDY_ROLE_SEPARATOR_ROLE_BASE_STRING,
                        ctx.prefix(),
                        STUDY_ROLE_SEPARATOR_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    NSFW_ROLE_BASE_STRING,
                    ctx.prefix(),
                    NSFW_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.nsfw_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set NSFW Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    STUDY_ROLE_SEPARATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    STUDY_ROLE_SEPARATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn study_role_separator_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.study_role_separator_role = Some(db_guild.study_role_separator_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Study Role Separator Role to {}.\n{}\n`{}{}`{}",
                        db_guild.study_role_separator_role.mention(),
                        SUBJECT_ROLE_SEPARATOR_ROLE_BASE_STRING,
                        ctx.prefix(),
                        SUBJECT_ROLE_SEPARATOR_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    STUDY_ROLE_SEPARATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    STUDY_ROLE_SEPARATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.study_role_separator_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Study Role Separator Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    SUBJECT_ROLE_SEPARATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    SUBJECT_ROLE_SEPARATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn subject_role_separator_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.subject_role_separator_role =
                        Some(db_guild.subject_role_separator_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Subject Role Separator Role to {}.\n{}\n`{}{}`{}",
                        db_guild.subject_role_separator_role.mention(),
                        FRIEND_ROLE_BASE_STRING,
                        ctx.prefix(),
                        FRIEND_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    SUBJECT_ROLE_SEPARATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    SUBJECT_ROLE_SEPARATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.subject_role_separator_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Subject Role Separator Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    FRIEND_ROLE_BASE_STRING,
                    ctx.prefix(),
                    FRIEND_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn friend_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.friend_role = Some(db_guild.friend_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Friend Role to {}.\n{}\n`{}{}`{}",
                        db_guild.friend_role.mention(),
                        ALUMNI_ROLE_BASE_STRING,
                        ctx.prefix(),
                        ALUMNI_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    FRIEND_ROLE_BASE_STRING,
                    ctx.prefix(),
                    FRIEND_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.friend_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Friend Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    ALUMNI_ROLE_BASE_STRING,
                    ctx.prefix(),
                    ALUMNI_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn alumni_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.alumni_role = Some(db_guild.alumni_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Alumni Role to {}.\n{}\n`{}{}`{}",
                        db_guild.alumni_role.mention(),
                        ALUMNI_ROLE_SEPARATOR_ROLE_BASE_STRING,
                        ctx.prefix(),
                        ALUMNI_ROLE_SEPARATOR_ROLE_COMMAND,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    ALUMNI_ROLE_BASE_STRING,
                    ctx.prefix(),
                    ALUMNI_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.alumni_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Alumni Role to {}.\n{}\n`{}{}`{}",
                    role_mention.mention(),
                    ALUMNI_ROLE_SEPARATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    ALUMNI_ROLE_SEPARATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn alumni_role_separator_role_setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Result<(), Error> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.alumni_role_separator_role =
                        Some(db_guild.alumni_role_separator_role);
                }
                let _ = ctx
                    .say(format!(
                        "Kept Alumni Role Separator Role to {}.\n{}\n`{}{}`\n{}{}",
                        db_guild.alumni_role_separator_role.mention(),
                        TMPC_TIME_BASE_STRING,
                        ctx.prefix(),
                        TMPC_TIME_COMMAND,
                        TMPC_TIME_RECOMMENDATION,
                        skip_message
                    ))
                    .await;
                return Ok(());
            }
        }
    }
    match role_mention {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`{}",
                    NO_ROLE_MENTION,
                    ALUMNI_ROLE_SEPARATOR_ROLE_BASE_STRING,
                    ctx.prefix(),
                    ALUMNI_ROLE_SEPARATOR_ROLE_COMMAND,
                    skip_message
                ))
                .await;
        }
        Some(role_mention) => {
            {
                let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                new_guild.alumni_role_separator_role = Some(role_mention.id);
            }
            let _ = ctx
                .say(format!(
                    "Set Alumni Role Separator Role to {}.\n{}\n`{}{}`\n{}{}",
                    role_mention.mention(),
                    TMPC_TIME_BASE_STRING,
                    ctx.prefix(),
                    TMPC_TIME_COMMAND,
                    TMPC_TIME_RECOMMENDATION,
                    skip_message
                ))
                .await;
        }
    }
    Ok(())
}

async fn tmpc_keep_time_setup(
    ctx: Context<'_>,
    number: Option<u32>,
    rest: Option<String>,
    db_guild: Option<DatabaseGuild>,
    guild_id: GuildId,
    skip_message: String,
) -> Option<u32> {
    if let Some(text) = rest {
        if text == "skip" {
            if let Some(db_guild) = db_guild {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.tmpc_keep_time = Some(db_guild.tmpc_keep_time);
                }
                return Some(db_guild.tmpc_keep_time);
            }
        }
    }
    match number {
        None => {
            let _ = ctx
                .say(format!(
                    "{}\n{}\n`{}{}`\n{}{}",
                    NO_NUMBER,
                    TMPC_TIME_BASE_STRING,
                    ctx.prefix(),
                    TMPC_TIME_COMMAND,
                    TMPC_TIME_RECOMMENDATION,
                    skip_message
                ))
                .await;
        }
        Some(number) => {
            if !(0..=168).contains(&number) {
                let _ = ctx
                    .say(format!(
                        "{}\n{}\n`{}{}`\n{}{}",
                        OUTSIDE_RANGE,
                        TMPC_TIME_BASE_STRING,
                        ctx.prefix(),
                        TMPC_TIME_COMMAND,
                        TMPC_TIME_RECOMMENDATION,
                        skip_message
                    ))
                    .await;
            } else {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    let new_guild: &mut NewGuild = hash_map.get_mut(&guild_id).unwrap();
                    new_guild.tmpc_keep_time = Some(number);
                }
                return Some(number);
            }
        }
    }
    None
}

pub async fn setup(
    ctx: Context<'_>,
    role_mention: Option<Role>,
    channel_mention: Option<GuildChannel>,
    flag: Option<bool>,
    number: Option<u32>,
    rest: Option<String>,
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
    let skip_message = if db_guild.is_some() {
        format!(
            "\n**You can also skip setting this value by writing `{prefix}setup skip` or \
                `{prefix}setup skip.`**",
            prefix = ctx.prefix()
        )
    } else {
        "".to_string()
    };

    let rest = rest.map(|rest| {
        if rest == "skip." {
            "skip".to_string()
        } else {
            rest
        }
    });

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
                "{}\n`{}{}`\n{}{}",
                WARNING_BASE_STRING,
                ctx.prefix(),
                WANING_COMMAND,
                WARNING_RECOMMENDATION,
                skip_message
            ))
            .await;
        return Ok(());
    }

    let new_guild_copy;
    {
        new_guild_copy = *ctx
            .data()
            .setup_in_progress
            .lock()
            .unwrap()
            .get(&guild_id)
            .unwrap()
    }

    if new_guild_copy.ghost_warning_deadline.is_none() {
        return warning_setup(ctx, number, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.ghost_kick_deadline.is_none() {
        return kick_setup(ctx, number, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.ghost_time_to_check.is_none() {
        return ghost_time_setup(ctx, number, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.ghost_enabled.is_none() {
        return ghost_enabled_setup(ctx, flag, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.debug_channel.is_none() {
        return debug_channel_setup(ctx, channel_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.bot_channel.is_none() {
        return bot_channel_setup(ctx, channel_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.help_channel.is_none() {
        return help_channel_setup(ctx, channel_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.study_group_category.is_none() {
        return study_group_category_setup(
            ctx,
            channel_mention,
            rest,
            db_guild,
            guild_id,
            skip_message,
        )
        .await;
    } else if new_guild_copy.subject_group_category.is_none() {
        return subject_group_category_setup(
            ctx,
            channel_mention,
            rest,
            db_guild,
            guild_id,
            skip_message,
        )
        .await;
    } else if new_guild_copy.studenty_role.is_none() {
        return studenty_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.tmp_studenty_role.is_none() {
        return tmp_studenty_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.moderator_role.is_none() {
        return moderator_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.newsletter_role.is_none() {
        return newsletter_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message)
            .await;
    } else if new_guild_copy.nsfw_role.is_none() {
        return nsfw_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.study_role_separator_role.is_none() {
        return study_role_separator_role_setup(
            ctx,
            role_mention,
            rest,
            db_guild,
            guild_id,
            skip_message,
        )
        .await;
    } else if new_guild_copy.subject_role_separator_role.is_none() {
        return subject_role_separator_role_setup(
            ctx,
            role_mention,
            rest,
            db_guild,
            guild_id,
            skip_message,
        )
        .await;
    } else if new_guild_copy.friend_role.is_none() {
        return friend_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.alumni_role.is_none() {
        return alumni_role_setup(ctx, role_mention, rest, db_guild, guild_id, skip_message).await;
    } else if new_guild_copy.alumni_role_separator_role.is_none() {
        return alumni_role_separator_role_setup(
            ctx,
            role_mention,
            rest,
            db_guild,
            guild_id,
            skip_message,
        )
        .await;
    } else if new_guild_copy.tmpc_keep_time.is_none() {
        if let Some(number) =
            tmpc_keep_time_setup(ctx, number, rest, db_guild, guild_id, skip_message).await
        {
            let new_guild;
            {
                let hash_map = ctx.data().setup_in_progress.lock().unwrap();
                new_guild = *hash_map.get(&guild_id).unwrap();
            }
            if let Some(db_guild) = db_guild {
                if new_guild == db_guild {
                    {
                        let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                        hash_map.remove(&guild_id);
                    }
                    let _ = ctx
                        .say("There are no differences to the current config. Done with setup.")
                        .await;
                } else {
                    let mut differences = String::new();
                    if new_guild.ghost_warning_deadline.unwrap() != db_guild.ghost_warning_deadline
                    {
                        differences.push_str(
                            format!(
                                "- ghost_warning_deadline = {}\n+ ghost_warning_deadline = {}\n\n",
                                db_guild.ghost_warning_deadline,
                                new_guild.ghost_warning_deadline.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.ghost_kick_deadline.unwrap() != db_guild.ghost_kick_deadline {
                        differences.push_str(
                            format!(
                                "- ghost_kick_deadline = {}\n+ ghost_kick_deadline = {}\n\n",
                                db_guild.ghost_kick_deadline,
                                new_guild.ghost_kick_deadline.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.ghost_time_to_check.unwrap() != db_guild.ghost_time_to_check {
                        differences.push_str(
                            format!(
                                "- ghost_time_to_check = {}\n+ ghost_time_to_check = {}\n\n",
                                db_guild.ghost_time_to_check,
                                new_guild.ghost_time_to_check.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.ghost_enabled.unwrap() != db_guild.ghost_enabled {
                        differences.push_str(
                            format!(
                                "- ghost_enabled = {}\n+ ghost_enabled = {}\n\n",
                                db_guild.ghost_enabled,
                                new_guild.ghost_enabled.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.debug_channel.unwrap() != db_guild.debug_channel {
                        differences.push_str(
                            format!(
                                "- debug_channel = {}\n+ debug_channel = {}\n\n",
                                db_guild.debug_channel,
                                new_guild.debug_channel.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.bot_channel.unwrap() != db_guild.bot_channel {
                        differences.push_str(
                            format!(
                                "- bot_channel = {}\n+ bot_channel = {}\n\n",
                                db_guild.bot_channel,
                                new_guild.bot_channel.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.help_channel.unwrap() != db_guild.help_channel {
                        differences.push_str(
                            format!(
                                "- help_channel = {}\n+ help_channel = {}\n\n",
                                db_guild.help_channel,
                                new_guild.help_channel.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.study_group_category.unwrap() != db_guild.study_group_category {
                        differences.push_str(
                            format!(
                                "- study_group_category = {}\n+ study_group_category = {}\n\n",
                                db_guild.study_group_category,
                                new_guild.study_group_category.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.subject_group_category.unwrap() != db_guild.subject_group_category
                    {
                        differences.push_str(
                            format!(
                                "- subject_group_category = {}\n+ subject_group_category = {}\n\n",
                                db_guild.subject_group_category,
                                new_guild.subject_group_category.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.studenty_role.unwrap() != db_guild.studenty_role {
                        differences.push_str(
                            format!(
                                "- studenty_role = {}\n+ studenty_role = {}\n\n",
                                db_guild.studenty_role,
                                new_guild.studenty_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.tmp_studenty_role.unwrap() != db_guild.tmp_studenty_role {
                        differences.push_str(
                            format!(
                                "- tmp_studenty_role = {:?}\n+ tmp_studenty_role = {:?}\n\n",
                                db_guild.tmp_studenty_role,
                                new_guild.tmp_studenty_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.moderator_role.unwrap() != db_guild.moderator_role {
                        differences.push_str(
                            format!(
                                "- moderator_role = {}\n+ moderator_role = {}\n\n",
                                db_guild.moderator_role,
                                new_guild.moderator_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.newsletter_role.unwrap() != db_guild.newsletter_role {
                        differences.push_str(
                            format!(
                                "- newsletter_role = {}\n+ newsletter_role = {}\n\n",
                                db_guild.newsletter_role,
                                new_guild.newsletter_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.nsfw_role.unwrap() != db_guild.nsfw_role {
                        differences.push_str(
                            format!(
                                "- nsfw_role = {}\n+ nsfw_role = {}\n\n",
                                db_guild.nsfw_role,
                                new_guild.nsfw_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.study_role_separator_role.unwrap()
                        != db_guild.study_role_separator_role
                    {
                        differences.push_str(format!(
                            "- study_role_separator_role = {}\n+ study_role_separator_role = {}\n\n",
                            db_guild.study_role_separator_role,
                            new_guild.study_role_separator_role.unwrap()
                        ).as_str())
                    }
                    if new_guild.subject_role_separator_role.unwrap()
                        != db_guild.subject_role_separator_role
                    {
                        differences.push_str(format!(
                            "- subject_role_separator_role = {}\n+ subject_role_separator_role = {}\n\n",
                            db_guild.subject_role_separator_role,
                            new_guild.subject_role_separator_role.unwrap()
                        ).as_str())
                    }
                    if new_guild.friend_role.unwrap() != db_guild.friend_role {
                        differences.push_str(
                            format!(
                                "- friend_role = {}\n+ friend_role = {}\n\n",
                                db_guild.friend_role,
                                new_guild.friend_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.tmpc_keep_time.unwrap() != db_guild.tmpc_keep_time {
                        differences.push_str(
                            format!(
                                "- tmpc_keep_time = {}\n+ tmpc_keep_time = {}\n\n",
                                db_guild.tmpc_keep_time,
                                new_guild.tmpc_keep_time.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.alumni_role.unwrap() != db_guild.alumni_role {
                        differences.push_str(
                            format!(
                                "- alumni_role = {}\n+ alumni_role = {}\n\n",
                                db_guild.alumni_role,
                                new_guild.alumni_role.unwrap()
                            )
                            .as_str(),
                        )
                    }
                    if new_guild.alumni_role_separator_role.unwrap()
                        != db_guild.alumni_role_separator_role
                    {
                        differences.push_str(format!(
                            "- alumni_role_separator_role = {}\n+ alumni_role_separator_role = {}\n\n",
                            db_guild.alumni_role_separator_role,
                            new_guild.alumni_role_separator_role.unwrap()
                        ).as_str())
                    }
                    let _ = ctx
                        .say(format!(
                            "Here are the changes made:\n```diff\n{}```\n\
                         Check these and then change to command to\n`{}setup confirm`",
                            differences,
                            ctx.prefix()
                        ))
                        .await;
                }
            } else {
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    hash_map.remove(&guild_id);
                }
                let db_guild: DatabaseGuild = match new_guild.try_into() {
                    Err(()) => {
                        let _ = ctx
                            .say(format!(
                                "Error: Unexpected error converting the New Guild into a DatabaseGuild\n{:?}",
                                new_guild
                            ))
                            .await;
                        return Ok(());
                    }
                    Ok(db_guild) => db_guild,
                };
                match mysql_lib::insert_guild(db, db_guild).await {
                    None => {
                        let _ = ctx
                            .say("Error: Problem inserting Guild info into the Database")
                            .await;
                    }
                    Some(res) => {
                        if res {
                            let _ = ctx
                                .say(format!(
                                    "Set TMPC Keep time to {} hours.\n\
                                     Done with setup, the Guild is now saved in the Database.",
                                    number
                                ))
                                .await;
                        } else {
                            let _ = ctx.say("Error: Guild was already in the Database").await;
                        }
                    }
                };
            }
        }
        return Ok(());
    } else if new_guild_copy.is_setup() {
        if let Some(text) = rest.clone() {
            if text == "confirm" && db_guild.is_some() {
                let new_guild;
                {
                    let mut hash_map = ctx.data().setup_in_progress.lock().unwrap();
                    new_guild = *hash_map.get(&guild_id).unwrap();
                    hash_map.remove(&guild_id);
                }
                let db_guild: DatabaseGuild = match new_guild.try_into() {
                    Err(()) => {
                        let _ = ctx
                            .say(format!(
                                "Error: Unexpected error converting the New Guild into a DatabaseGuild\n{:?}",
                                new_guild
                            ))
                            .await;
                        return Ok(());
                    }
                    Ok(db_guild) => db_guild,
                };
                match mysql_lib::update_guild(db, db_guild).await {
                    None => {
                        let _ = ctx
                            .say("Error: Problem inserting Guild info into the Database")
                            .await;
                    }
                    Some(res) => {
                        if res {
                            let _ = ctx
                                .say("Done with setup, the Guild is now updated in the Database.")
                                .await;
                        } else {
                            let _ =
                                ctx.say("Error: Guild wasn't updated in the Database").await;
                        }
                    }
                }
                return Ok(());
            }
        }
    }

    let _ = ctx
        .say(format!(
            "**Role Mention:** {:?}\n**Channel Mention:** {:?}\n**Number** {:?}\n**Rest:** {:?}",
            role_mention, channel_mention, number, rest
        ))
        .await;

    Ok(())
}
