//! TODO: Permissions

use futures::future::join_all;
use poise::serenity_prelude::{GuildId, RoleId};
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

#[poise::command(prefix_command)]
pub async fn create(_ctx: Context<'_>) -> Result<(), Error> {
    todo!()
}

#[poise::command(prefix_command)]
pub async fn delete(_ctx: Context<'_>) -> Result<(), Error> {
    todo!()
}
