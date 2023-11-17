#[cfg(test)]
mod tests {
    use poise::serenity_prelude::{ChannelId, GuildId, RoleId};
    use sqlx::{MySql, Pool};
    use sqlx::types::time::Time;

    use crate::mysql_lib::{delete_guild, get_connection, insert_guild, is_guild_in_database, migrate_database};

    async fn get_connection_pool() -> Pool<MySql>{
        let pool = get_connection(1)
            .await
            .expect("Database could not be connected to");
        migrate_database(&pool).await.expect("Database migration could not be done");
        return pool;
    }

    #[tokio::test]
    async fn test_insert_and_delete_guild() {
        let pool = get_connection_pool().await;
        let result = insert_guild(&pool,
                                  GuildId(1),
                                  1,
                                  1,
                                  Time::from_hms(8, 0, 0).unwrap(),
                                  true,
                                  ChannelId(1),
                                  ChannelId(1),
                                  ChannelId(1),
                                  ChannelId(1),
                                  ChannelId(1),
                                  RoleId(1),
                                  RoleId(1),
                                  RoleId(1),
                                  RoleId(1),
                                  RoleId(1),
                                  RoleId(1),
                                  RoleId(1),
                                  Time::from_hms(12, 0, 0).unwrap(),
                                  RoleId(1),
                                  RoleId(1))
            .await
            .expect("Query was not successful");
        assert!(result, "Could not insert into Database");
        let result = is_guild_in_database(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert!(result, "Guild was not found in Database");
        let result = delete_guild(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert!(result, "Guild could not be deleted");
    }
}

