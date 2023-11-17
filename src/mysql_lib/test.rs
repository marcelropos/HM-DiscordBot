#[cfg(test)]
mod tests {
    use poise::serenity_prelude::GuildId;

    use crate::mysql_lib::{get_connection, is_guild_in_database};

    #[tokio::test]
    async fn test_is_guild_in_database() {
        let pool = get_connection(1)
            .await
            .expect("Database could not be connected to");
        let result = is_guild_in_database(&pool, GuildId(1))
            .await
            .expect("Query was not successful");
        assert!(!result, "Impossible ID was in Database")
    }
}

