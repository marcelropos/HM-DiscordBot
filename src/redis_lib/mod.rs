use std::env;

use redis::{aio::Connection, AsyncCommands, Client};
use tracing::error;

/// Tries to establish a connection with the given env variables and return the Redis client if
/// successful.
///
/// # Env Variables
///
/// * REDIS_PORT: the port of redis, defaults to 6379
/// * REDIS_HOST: the host of redis, ip or hostname or domain, defaults to 127.0.0.1
pub async fn get_connection() -> Option<(Client, Connection)> {
    let redis_port: Result<u16, _> = env::var("REDIS_PORT").unwrap_or("6379".to_owned()).parse();
    if let Err(err) = redis_port {
        error!(error = err.to_string(), "Failed to parse int");
        return None;
    }
    let redis_port = redis_port.unwrap();

    let redis_hostname = env::var("REDIS_HOST").unwrap_or("127.0.0.1".to_owned());

    let client = Client::open(format!("redis://{redis_hostname}:{redis_port}"))
        .map_err(|e| {
            error!(error = e.to_string(), "Problem creating redis client");
        })
        .ok()?;

    let connection = match client.get_async_connection().await {
        Err(err) => {
            error!(error = err.to_string(), "Failed connecting to Redis");
            return None;
        }
        Ok(con) => con,
    };

    Some((client, connection))
}

/// Increments the counter that tracks how often an email was successfully used to verify an account
#[allow(unused)]
pub async fn increment_email_used_verification_success(con: &mut Connection, email: &str) {
    let email_hash = hash_email(email);
    let current = get_email_stats(con, email_hash).await;
    set_email_stats(con, email_hash, current.0 + 1, current.1);
}

/// Increments the counter that tracks how often an email was given to verify an account
#[allow(unused)]
pub async fn increment_email_used_verification(con: &mut Connection, email: &str) {
    let email_hash = hash_email(email);
    let current = get_email_stats(con, email_hash).await;
    set_email_stats(con, email_hash, current.0, current.1 + 1);
}

/// gets how often an email was used to verify an account (not necessarily successful)
#[allow(unused)]
pub async fn get_email_used_verification_success(con: &mut Connection, email: &str) -> u64 {
    get_email_stats(con, hash_email(email)).await.0
}

/// gets how often an email was used to verify an account (not necessarily successful)
#[allow(unused)]
pub async fn get_email_used_verification(con: &mut Connection, email: &str) -> u64 {
    get_email_stats(con, hash_email(email)).await.1
}

async fn set_email_stats(con: &mut Connection, email_hash: &str, successful: u64, used: u64) {
    let command: Result<(), _> = con.set(email_hash, format!("{successful},{used}")).await;
    if let Err(err) = command {
        error!(
            error = err.to_string(),
            "Could not set stats for email {email_hash}, ({successful},{used})"
        );
    }
}

async fn get_email_stats(con: &mut Connection, email_hash: &str) -> (u64, u64) {
    let command: Result<Option<String>, _> = con.get(email_hash).await;
    if let Err(err) = command {
        error!(error = err.to_string(), "Could not read email stats");
        return (0, 0);
    }
    let redis_value = command.unwrap();

    if redis_value.is_none() {
        return (0, 0);
    }
    let redis_value = redis_value.unwrap();

    let values: Vec<&str> = redis_value.split(",").collect();
    if values.len() != 2 {
        error!("Redis returned invalid value for {email_hash}")
    }
    let used_success = values[0].parse();
    if used_success.is_err() {
        error!("Failed to parse used success value for {email_hash}");
        return (0, 0);
    }

    let used = values[1].parse();
    if used.is_err() {
        error!("Failed to parse used value for {email_hash}");
        return (0, 0);
    }
    (used_success.unwrap(), used.unwrap())
}

/// TODO: Which hash function should this use?
fn hash_email(email: &str) -> &str {
    email
}

/// The key under which redis stores the main discord channel to put logs into
/// TODO: put the actual key in here
const MAIN_DISCORD_LOG_CHANNEL_KEY: &str = "main_discord_log_channel";

#[allow(unused)]
pub async fn set_main_discord_log_channel(con: &mut Connection, channel_id: &str) {
    let command: Result<(), _> = con.set(MAIN_DISCORD_LOG_CHANNEL_KEY, channel_id).await;
    if let Err(err) = command {
        error!(
            error = err.to_string(),
            "Could not set discord main log channel"
        );
    }
}

#[allow(unused)]
pub async fn get_main_discord_log_channel(con: &mut Connection) -> Option<String> {
    con.get(MAIN_DISCORD_LOG_CHANNEL_KEY).await.ok()
}

#[allow(unused)]
pub async fn delete_main_discord_log_channel(con: &mut Connection) {
    let command: Result<(), _> = con.del(MAIN_DISCORD_LOG_CHANNEL_KEY).await;
    if let Err(err) = command {
        error!(
            error = err.to_string(),
            "Could not delete main discord log channel"
        );
    }
}
