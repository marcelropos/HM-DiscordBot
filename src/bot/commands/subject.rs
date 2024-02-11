//! TODO: Permissions

use futures::future::join_all;
use poise::serenity_prelude::{CacheHttp, ChannelId, ChannelType, GuildId, RoleId};
use sqlx::{MySql, Pool};
use itertools::Itertools;

use crate::{
    bot::{Context, Error},
    mysql_lib::{self, DatabaseSubject},
};

/// Everything regarding subjects, admin commands are in the "manage" subcommand
#[poise::command(
    slash_command,
    prefix_command,
    guild_only,
    subcommands("add", "remove", "show", "manage"),
    subcommand_required
)]
pub async fn subject(_ctx: Context<'_>) -> Result<(), Error> {
    unimplemented!()
}

/// Adds a subject to the user that sent this command
#[poise::command(slash_command, prefix_command)]
pub async fn add(
    ctx: Context<'_>,
    #[description = "list of subject names or id's from \"subject show\""] names_or_ids: Vec<
        String,
    >,
) -> Result<(), Error> {
    let user_roles = &ctx.author_member().await.unwrap().roles;
    let guild_id = ctx.guild_id().unwrap();

    let requested_subjects =
        get_subjects_from_user_input(&ctx.data().database_pool, guild_id, user_roles, names_or_ids)
            .await;

    let formatted_subjects = format_subjects(&requested_subjects);

    let roles: Vec<_> = requested_subjects
        .into_iter()
        .map(|subject| subject.role)
        .collect();

    let mut author_member = ctx.author_member().await.unwrap();
    author_member.to_mut().add_roles(ctx.http(), &roles).await?;

    ctx.reply(format!("Added following subjects to you:\n{formatted_subjects}")).await?;

    Ok(())
}

/// Removes a subject from the user that sent this command
#[poise::command(slash_command, prefix_command)]
pub async fn remove(
    ctx: Context<'_>,
    #[description = "list of subject names or id's from \"subject show\""] names_or_ids: Vec<
        String,
    >,
) -> Result<(), Error> {
    let user_roles = &ctx.author_member().await.unwrap().roles;
    let guild_id = ctx.guild_id().unwrap();

    let requested_subjects =
        get_subjects_from_user_input(&ctx.data().database_pool, guild_id, user_roles, names_or_ids)
            .await;
    
    let formatted_subjects = format_subjects(&requested_subjects);

    let roles: Vec<_> = requested_subjects
        .into_iter()
        .map(|subject| subject.role)
        .collect();

    let mut author_member = ctx.author_member().await.unwrap();
    author_member
        .to_mut()
        .remove_roles(ctx.http(), &roles)
        .await?;

    ctx.reply(format!("Removed following subjects from you:\n{formatted_subjects}")).await?;

    Ok(())
}

/// Show available subjects for a user
#[poise::command(slash_command, prefix_command)]
pub async fn show(ctx: Context<'_>) -> Result<(), Error> {
    let db = &ctx.data().database_pool;
    let guild = ctx.guild_id().unwrap();
    let user_roles = &ctx.author_member().await.unwrap().roles;

    let available_subjects = get_available_subjects(db, guild, user_roles).await;

    let formatted_subjects = format_subjects(&available_subjects);

    ctx.reply(format!(
        "
    The following subjects are available (add them using \"subject add/remove\":
    {formatted_subjects}
    "
    ))
    .await?;

    Ok(())
}

fn format_subjects(subjects: &[DatabaseSubject]) -> String {
    subjects
        .iter()
        .map(|subject| format!("{}: {}", subject.id.unwrap_or(-1), subject.name))
        .join("\n")
}

/// Gets all available subjects for this user from the database
/// 
/// This could probably be rewritten to use only a single SQL statement,
/// which would be substantially better
/// 
/// TODO: Test this
async fn get_available_subjects(
    db: &Pool<MySql>,
    guild: GuildId,
    user_roles: &[RoleId],
) -> Vec<DatabaseSubject> {


    // objective: Get all semester study groups below or at the user's

    // get all semester study groups for guild (they have an associated discord role)
    let guild_semester_study_groups = mysql_lib::get_semester_study_groups_in_guild(db, guild).await.unwrap();
    
    // find out which semester study group user is in using that role
    let user_semester_study_group = guild_semester_study_groups
        .iter()
        .find(|group| user_roles.contains(&group.role))
        .unwrap();

    // get all related semester study groups
    let related_semester_study_groups = mysql_lib::get_semester_study_groups_in_study_group(db, user_semester_study_group.study_group_id).await.unwrap();

    // filter out to only those whose semester <= user's semester
    let valid_semester_study_groups = related_semester_study_groups.into_iter()
        .filter(|sem_study_group| sem_study_group.semester <= user_semester_study_group.semester);

    // get all subject's for all those semester study groups
    let subjects: Vec<_> = valid_semester_study_groups
        .map(|sem_study_group| {
            mysql_lib::get_subjects_for_semester_study_group(db, sem_study_group.role)
        })
        .collect();

    let subjects = join_all(subjects).await;

    subjects.iter()
        .flatten().flatten().cloned()
        .sorted_by_key(|subject| subject.id)
        .dedup()
        .collect()
}

/// Parses subject names/ids from user input, then
/// gets the appropriate database objects for it.
/// Needs the user's roles because those dictate which
/// subjects are available to them.
/// 
/// TODO: Handle failures correctly
async fn get_subjects_from_user_input(
    db: &Pool<MySql>,
    guild: GuildId,
    user_roles: &[RoleId],
    names_or_ids: Vec<String>,
) -> Vec<DatabaseSubject> {
    let available_subjects = get_available_subjects(db, guild, user_roles).await;

    names_or_ids
        .into_iter()
        .map(|name_or_id| {
            if let Ok(subject_id) = name_or_id.parse::<usize>() {
                // user specified a subject id
                available_subjects.get(subject_id).unwrap().clone()
            } else {
                // user specified a name
                let subject_name = name_or_id;

                let matching_subject = available_subjects
                    .iter()
                    .find(|db_subject| db_subject.name == subject_name);

                if let Some(subject) = matching_subject {
                    subject.clone()
                } else {
                    todo!(
                        "User has specified subject name which does not exist / they can't access"
                    )
                }
            }
        })
        .collect()
}

/// Admin commands for creating/deleting subjects
#[poise::command(prefix_command, subcommands("create", "delete"), subcommand_required)]
pub async fn manage(_ctx: Context<'_>) -> Result<(), Error> {
    unimplemented!()
}

/// Creates a new subject, together with role and text channel
#[poise::command(prefix_command)]
pub async fn create(ctx: Context<'_>, name: String) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let db = &ctx.data().database_pool;
    let discord_http = ctx.http();

    let subjects = mysql_lib::get_subjects(db, guild_id).await.unwrap_or_default();

    let similar_subject = subjects.into_iter()
        .find(|sub| {
            sub.name == name
        });

    if let Some(similar_subject) = similar_subject {
        ctx.reply(format!("Found subject with same name/role/text channel: {}", similar_subject.name)).await?;
        return Ok(());
    }

    let db_guild = mysql_lib::get_guild(db, guild_id).await.unwrap();
    let discord_guild = ctx.guild().unwrap();

    // create role
    let new_role = discord_guild.create_role(discord_http, |r|
        r.name(&name).mentionable(true)).await?;

    let role = new_role.id;

    // create channel
    let base_category = db_guild.subject_group_category;

    let new_channel = discord_guild.create_channel(discord_http, |c|
            c.category(base_category).name(&name).kind(ChannelType::Text)).await?;

    let text_channel = new_channel.id;

    let subject = DatabaseSubject {
        id: None,
        role,
        guild_id,
        name,
        text_channel
    };

    match mysql_lib::insert_subject(db, subject).await {
        Some(true) => {
            ctx.reply("Created subject").await?
        },
        Some(false) => {
            ctx.reply("Didn't create subject, was it already in the database?").await?
        },
        None => {
            ctx.reply("Error while trying to execute query").await?
        }
    };
    
    Ok(())
}

/// Deletes the subject, it's role, and it's text channel
#[poise::command(prefix_command)]
pub async fn delete(ctx: Context<'_>, role: RoleId) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let db = &ctx.data().database_pool;

    let db_subject = match mysql_lib::get_subject_for_role(db, guild_id, role).await {
        Some(subject) => subject,
        None => {
            ctx.reply("Could not find subject for this role, is this a subject?").await?;
            return Ok(());
        }
    };

    let discord_guild = ctx.guild().unwrap();
    let discord_http = ctx.http();

    discord_guild.delete_role(discord_http, role).await?;

    db_subject.text_channel.delete(discord_http).await?;

    // delete_subject only cares about role and guild_id
    let subject = DatabaseSubject {
        id: None,
        role,
        guild_id,
        name: "".to_string(),
        text_channel: ChannelId(0),
    };

    match mysql_lib::delete_subject(db, subject).await {
        Some(true) => {
            ctx.reply("Deleted subject").await?
        },
        Some(false) => {
            ctx.reply("Didn't delete subject, was it already deleted?").await?
        },
        None => {
            ctx.reply("Error while trying to execute query").await?
        }
    };
    
    Ok(())
}
