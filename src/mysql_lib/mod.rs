use std::env;

use sqlx::{migrate, MySql, Pool};
use sqlx::migrate::MigrateError;
use sqlx::mysql::{MySqlConnectOptions, MySqlPoolOptions};
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
    let sql_port: u16;
    match env::var("MYSQL_PORT") {
        Ok(val) => match val.parse() {
            Ok(value) => sql_port = value,
            Err(err) => {
                error!(error=err.to_string(), "Failed to parse int");
                return None;
            }
        },
        Err(_) => sql_port = 3306
    };
    let sql_hostname = match env::var("MYSQL_HOST") {
        Ok(val) => val,
        Err(_) => "127.0.0.1".to_string()
    };
    let sql_database = match env::var("MYSQL_DATABASE") {
        Ok(val) => val,
        Err(_) => {
            error!("No database name given");
            return None;
        }
    };
    let sql_username = match env::var("MYSQL_USER") {
        Ok(val) => val,
        Err(_) => {
            error!("No database username given");
            return None;
        }
    };
    let sql_password = match env::var("MYSQL_PASSWORD") {
        Ok(val) => val,
        Err(_) => {
            error!("No password for user given");
            return None;
        }
    };
    match MySqlPoolOptions::new()
        .max_connections(max_concurrent_connections)
        .connect_with(MySqlConnectOptions::new()
            .host(sql_hostname.as_str())
            .port(sql_port)
            .database(sql_database.as_str())
            .username(sql_username.as_str())
            .password(sql_password.as_str())).await {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error=err.to_string(), "Problem connecting to the Database");
            None
        }
    }
}

pub async fn migrate_database(pool: &Pool<MySql>) -> Result<(), MigrateError> {
    migrate!("./migrations")
        .run(pool)
        .await
}