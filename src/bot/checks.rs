use poise::serenity_prelude::{ChannelId, Permissions, RoleId};
use sqlx::{MySql, Pool};

use crate::bot::Context;
use crate::{env, mysql_lib};

/// Checks if the author has any of the specified roles
///
/// Will return false when:
/// - the message was not sent in a guild
/// - the author doesn't have any of the roles
pub async fn has_one_of_roles(ctx: Context<'_>, roles: Vec<RoleId>) -> bool {
    if let Some(member) = ctx.author_member().await {
        return member.roles.iter().any(|role| roles.contains(role));
    }
    false
}

/// Checks if the author has the specified role
///
/// Will return false when:
/// - the message was not sent in a guild
/// - the author doesn't the role
#[allow(dead_code)]
pub async fn has_role(ctx: Context<'_>, role: RoleId) -> bool {
    has_one_of_roles(ctx, vec![role]).await
}

/// Checks that the author doesn't have any of the specified roles
///
/// Will return true when:
/// - the message was not sent in a guild
/// - the author doesn't have any of the role
#[allow(dead_code)]
pub async fn has_none_of_roles(ctx: Context<'_>, roles: Vec<RoleId>) -> bool {
    !has_one_of_roles(ctx, roles).await
}

/// Checks if the author has a role that gives him admin permissions
///
/// Will return false when:
/// - the message was not sent in a guild
/// - the author doesn't have a role with admin permissions
#[allow(dead_code)]
pub async fn is_admin(ctx: Context<'_>) -> bool {
    if let Some(member) = ctx.author_member().await {
        if let Some(guild) = ctx.guild() {
            return member.roles.iter().any(|role_id| {
                guild.roles.get(role_id).map_or(false, |role| {
                    role.has_permission(Permissions::ADMINISTRATOR)
                })
            });
        }
    }
    false
}

/// Checks if the author is the owner of the guild where the message was sent
///
/// Will return false when:
/// - the message was not sent in a guild
/// - the message was sent by the guild owner
#[allow(dead_code)]
pub async fn is_owner(ctx: Context<'_>) -> bool {
    if let Some(guild) = ctx.guild() {
        return guild.owner_id == ctx.author().id;
    }
    false
}

/// Checks if the message was sent in the main guild
///
/// Will return false when:
/// - guild is not main guild
/// - message was not sent in guild
#[allow(dead_code)]
pub async fn sent_in_main_guild(ctx: Context<'_>) -> bool {
    if let Some(guild) = ctx.guild() {
        return env::MAIN_GUILD_ID
            .get()
            .map_or(false, |&main_guild_id| guild.id.0 == main_guild_id);
    }
    false
}

/// Checks if the message was sent in one of the allowed channels
#[allow(dead_code)]
pub async fn sent_in_channels(ctx: Context<'_>, channels: Vec<ChannelId>) -> bool {
    channels.contains(&ctx.channel_id())
}

/// Checks if the message was sent in the wanted channel
#[allow(dead_code)]
pub async fn sent_in_channel(ctx: Context<'_>, channel: ChannelId) -> bool {
    ctx.channel_id() == channel
}

/// Checks if the message was sent in a guild that is already setup
///
/// Will return false if:
/// - the message was not sent in a guild
/// - the guild is not in the database
/// - the sql query had some kind of problem
#[allow(dead_code)]
pub async fn sent_in_setup_guild(ctx: Context<'_>, pool: &Pool<MySql>) -> bool {
    if let Some(guild_id) = ctx.guild_id() {
        return mysql_lib::is_guild_in_database(pool, guild_id)
            .await
            .unwrap_or(false);
    }
    false
}

/// Checks if the message was sent in a guild
#[allow(dead_code)]
pub async fn sent_in_guild(ctx: Context<'_>) -> bool {
    ctx.guild_id().is_some()
}
