//! TODO: Permissions
use std::borrow::BorrowMut;

use poise::serenity_prelude::{GuildId, UserId};
use sqlx::{MySql, Pool};

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
    #[description = "list of subject names or id's from \"subject show\""]
    names_or_ids: Vec<String>,
) -> Result<(), Error> {
    let author_id = ctx.author().id;
    let guild_id = ctx.guild_id().unwrap();

    let requested_subjects =
        parse_subject_names_or_ids(&ctx.data().database_pool, guild_id, author_id, names_or_ids)
            .await;

    let roles: Vec<_> = requested_subjects
        .into_iter()
        .map(|subject| subject.role)
        .collect();

    let mut author_member = ctx.author_member().await.unwrap();
    author_member.to_mut().add_roles(ctx.http(), &roles).await?;

    // TODO: Feedback to user

    Ok(())
}

/// Gets all available subjects for this user from the database, sorted alphabetically by the subject name
/// TODO: Filter out only the ones that the user should be able to access
async fn get_available_subjects(
    db: &Pool<MySql>,
    guild: GuildId,
    user: UserId,
) -> Vec<DatabaseSubject> {
    mysql_lib::get_subjects(db, guild).await.unwrap()
}

/// Removes a subject from the user that sent this command
#[poise::command(slash_command, prefix_command)]
pub async fn remove(
    ctx: Context<'_>,
    #[description = "list of subject names or id's from \"subject show\""]
    names_or_ids: Vec<String>
) -> Result<(), Error> {
    let author_id = ctx.author().id;
    let guild_id = ctx.guild_id().unwrap();

    let requested_subjects =
        parse_subject_names_or_ids(&ctx.data().database_pool, guild_id, author_id, names_or_ids)
            .await;

    let roles: Vec<_> = requested_subjects
        .into_iter()
        .map(|subject| subject.role)
        .collect();

    let mut author_member = ctx.author_member().await.unwrap();
    author_member.to_mut().remove_roles(ctx.http(), &roles).await?;

    // TODO: Feedback to user

    Ok(())
}

/// Show available subjects for a user
#[poise::command(slash_command, prefix_command)]
pub async fn show(ctx: Context<'_>) -> Result<(), Error> {
    let db = &ctx.data().database_pool;
    let guild = ctx.guild_id().unwrap();
    let user = ctx.author().id;

    let available_subjects = get_available_subjects(db, guild, user).await;

    // TODO: Feedback to user

    Ok(())
}



/// TODO: Handle failures correctly
async fn parse_subject_names_or_ids(
    db: &Pool<MySql>,
    guild: GuildId,
    user: UserId,
    names_or_ids: Vec<String>,
) -> Vec<DatabaseSubject> {
    let available_subjects = get_available_subjects(db, guild, user).await;

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
