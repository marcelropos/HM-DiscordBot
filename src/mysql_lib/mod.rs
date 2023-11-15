use std::env;

use sqlx::migrate::MigrateError;
use sqlx::mysql::{MySqlConnectOptions, MySqlPoolOptions};
use sqlx::{migrate, MySql, Pool};
use tracing::error;

/// Tries to establish a Connection with the given env variables and return the MySQL connection
/// Pool if successful.
///
/// # Env Variables
///
/// * MYSQL_PORT: the port of the mysql database, defaults to 3306
/// * MYSQL_HOST: the host of the mysql database, ip or hostname or domain, defaults to 127.0.0.1
/// * MYSQL_DATABASE: the name of the database to use, needs to be present
/// * MYSQL_USER: the username of the user that has access to the database, needs to be present
/// * MYSQL_PASSWORD: the password of the user specified, needs to be present
pub async fn get_connection(max_concurrent_connections: u32) -> Option<Pool<MySql>> {
    let sql_port = env::var("MYSQL_PORT").unwrap_or("3306".to_owned());
    let sql_port: u16 = sql_port.parse().ok()?;

    let sql_hostname = env::var("MYSQL_HOST").unwrap_or("127.0.0.1".to_owned());

    let sql_database = if let Ok(val) = env::var("MYSQL_DATABASE") {
        val
    } else {
        error!("No database given");
        return None;
    };

    let sql_username = if let Ok(val) = env::var("MYSQL_USER") {
        val
    } else {
        error!("No database username given");
        return None;
    };

    let sql_password = if let Ok(val) = env::var("MYSQL_PASSWORD") {
        val
    } else {
        error!("No password for user given");
        return None;
    };

    match MySqlPoolOptions::new()
        .max_connections(max_concurrent_connections)
        .connect_with(
            MySqlConnectOptions::new()
                .host(sql_hostname.as_str())
                .port(sql_port)
                .database(sql_database.as_str())
                .username(sql_username.as_str())
                .password(sql_password.as_str()),
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
