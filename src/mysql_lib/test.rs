#[cfg(test)]
mod tests {
    use poise::serenity_prelude::{ChannelId, GuildId, RoleId};
    use sqlx::{MySql, Pool};
    use sqlx::types::time::Time;

    use crate::mysql_lib::{DatabaseGuild, delete_guild, get_connection, get_guild, insert_guild, is_guild_in_database, migrate_database};

    async fn get_connection_pool() -> Pool<MySql>{
        tracing_subscriber::fmt::init();
        let pool = get_connection(1)
            .await
            .expect("Database could not be connected to");
        migrate_database(&pool).await.expect("Database migration could not be done");
        return pool;
    }

    #[tokio::test]
    async fn test_insert_and_delete_guild() {
        let pool = get_connection_pool().await;
        let guild = DatabaseGuild{
            guild_id: GuildId(1),
            ghost_warning_deadline: 2,
            ghost_kick_deadline: 3,
            ghost_time_to_check: Time::from_hms(8, 0, 0).unwrap(),
            ghost_enabled: true,
            debug_channel: ChannelId(4),
            bot_channel: ChannelId(5),
            help_channel: ChannelId(6),
            study_group_category: ChannelId(7),
            subject_group_category: ChannelId(8),
            studenty_role: RoleId(9),
            moderator_role: RoleId(10),
            newsletter_role: RoleId(11),
            nsfw_role: RoleId(12),
            study_role_separator_role: RoleId(13),
            subject_role_separator_role: RoleId(14),
            friend_role: RoleId(15),
            tmpc_keep_time: Time::from_hms(12, 0, 0).unwrap(),
            alumni_role: RoleId(16),
            alumni_role_separator_role: RoleId(17),
            logger_pipe_channel: None,
            tmp_studenty_role: None
        };
        let result = insert_guild(&pool, guild)
            .await
            .expect("Query was not successful");
        assert!(result, "Could not insert into Database");
        let result = is_guild_in_database(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert!(result, "Guild was not found in Database");
        let result = get_guild(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert_eq!(guild, result, "Guild had not the information expected");
        let result = delete_guild(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert!(result, "Guild could not be deleted");
    }
}

