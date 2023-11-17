#[cfg(test)]
mod tests {
    use poise::serenity_prelude::GuildId;
    use sqlx::{MySql, Pool};

    use crate::mysql_lib::{get_connection, is_guild_in_database, migrate_database};

    async fn get_connection_pool() -> Pool<MySql>{
        let pool = get_connection(1)
            .await
            .expect("Database could not be connected to");
        migrate_database(&pool).await.expect("Database migration could not be done");
        return pool;
    }

    #[tokio::test]
    async fn test_is_guild_in_database() {
        let pool = get_connection_pool().await;
        let result = is_guild_in_database(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert!(!result, "Impossible ID was in Database")
    }
}

