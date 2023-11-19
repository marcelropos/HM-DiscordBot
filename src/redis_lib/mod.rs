use std::env;

use redis::{aio::Connection, AsyncCommands, Client};
use sha1::Digest;
use tracing::error;

/// Tries to establish a connection with the given env variables and return the Redis client if
/// successful.
///
/// # Env Variables
///
/// * REDIS_PORT: the port of redis, defaults to 6379
/// * REDIS_HOST: the host of redis, ip or hostname or domain, defaults to 127.0.0.1
pub async fn get_connection() -> Option<Client> {
    let redis_port: u16 = match env::var("REDIS_PORT").unwrap_or("6379".to_owned()).parse() {
        Ok(val) => val,
        Err(err) => {
            error!(error = err.to_string(), "Failed to parse int");
            return None;
        }
    };

    let redis_hostname = env::var("REDIS_HOST").unwrap_or("127.0.0.1".to_owned());

    let client = Client::open(format!("redis://{redis_hostname}:{redis_port}"))
        .map_err(|e| {
            error!(error = e.to_string(), "Problem creating redis client");
        })
        .ok()?;

    match client.get_async_connection().await {
        Err(err) => {
            error!(error = err.to_string(), "Failed connecting to Redis");
            return None;
        }
        Ok(con) => con,
    };

    Some(client)
}

/// Increments the counter that tracks how often an email was successfully used to verify an account
#[allow(dead_code)]
pub async fn increment_email_used_verification_success(
    con: &mut Connection,
    email: &str,
) -> Result<(), ()> {
    let email_hash = hash_email(email);
    let current = get_email_stats(con, &email_hash).await?;
    set_email_stats(con, &email_hash, current.0 + 1, current.1).await?;
    Ok(())
}

/// Increments the counter that tracks how often an email was given to verify an account
#[allow(dead_code)]
pub async fn increment_email_used_verification(
    con: &mut Connection,
    email: &str,
) -> Result<(), ()> {
    let email_hash = hash_email(email);
    let current = get_email_stats(con, &email_hash).await?;
    set_email_stats(con, &email_hash, current.0, current.1 + 1).await?;
    Ok(())
}

/// gets how often an email was used to verify an account (not necessarily successful)
/// return value of 0 means either that there is no entry in redis for this email,
/// or that the entry is 0
#[allow(dead_code)]
pub async fn get_email_used_verification_success(
    con: &mut Connection,
    email: &str,
) -> Result<u64, ()> {
    let stat = get_email_stats(con, &hash_email(email)).await?.0;
    Ok(stat)
}

/// gets how often an email was used to verify an account (not necessarily successful)
/// return value of 0 means either that there is no entry in redis for this email,
/// or that the entry is 0
#[allow(dead_code)]
pub async fn get_email_used_verification(con: &mut Connection, email: &str) -> Result<u64, ()> {
    let stat = get_email_stats(con, &hash_email(email)).await?.1;
    Ok(stat)
}

async fn set_email_stats(
    con: &mut Connection,
    email_hash: &str,
    successful: u64,
    used: u64,
) -> Result<(), ()> {
    let command: Result<(), _> = con.set(email_hash, format!("{successful},{used}")).await;
    if let Err(err) = command {
        error!(
            error = err.to_string(),
            "Could not set stats for email {email_hash}, ({successful},{used})"
        );
        return Err(());
    }
    Ok(())
}

/// (0,0) can mean either a value of 0,0 in redis or no value in redis at all
async fn get_email_stats(con: &mut Connection, email_hash: &str) -> Result<(u64, u64), ()> {
    let command: Result<Option<String>, _> = con.get(email_hash).await;
    let redis_value = match command {
        Err(err) => {
            error!(error = err.to_string(), "Could not read email stats");
            return Err(());
        }
        Ok(val) => val,
    };

    let redis_value = match redis_value {
        Some(val) => val,
        None => return Ok((0, 0)),
    };

    let values: Vec<&str> = redis_value.split(',').collect();
    if values.len() != 2 {
        error!("Redis returned invalid value for {email_hash}");
        return Err(());
    }

    let used_success = values[0].parse();
    if used_success.is_err() {
        error!("Failed to parse used success value for {email_hash}");
        return Err(());
    }

    let used = values[1].parse();
    if used.is_err() {
        error!("Failed to parse used value for {email_hash}");
        return Err(());
    }

    Ok((used_success.unwrap(), used.unwrap()))
}

fn hash_email(email: &str) -> String {
    let mut hasher = sha1::Sha1::new();
    hasher.update(email);
    hex::encode(hasher.finalize())
}

/// The key under which redis stores the main discord channel to put logs into
const MAIN_DISCORD_LOG_CHANNEL_KEY: &str = "main_discord_log_channel";

#[allow(dead_code)]
pub async fn set_main_discord_log_channel(
    con: &mut Connection,
    channel_id: &str,
) -> Result<(), ()> {
    let command: Result<(), _> = con.set(MAIN_DISCORD_LOG_CHANNEL_KEY, channel_id).await;
    command.map_err(|err| {
        error!(
            error = err.to_string(),
            "Could not set discord main log channel"
        );
    })
}

#[allow(dead_code)]
pub async fn get_main_discord_log_channel(con: &mut Connection) -> Result<Option<String>, ()> {
    let command: Result<Option<String>, _> = con.get(MAIN_DISCORD_LOG_CHANNEL_KEY).await;
    command.map_err(|err| {
        error!(error = err.to_string(), "Could not read email stats");
    })
}

#[allow(dead_code)]
pub async fn delete_main_discord_log_channel(con: &mut Connection) -> Result<(), ()> {
    let command: Result<(), _> = con.del(MAIN_DISCORD_LOG_CHANNEL_KEY).await;
    command.map_err(|err| {
        error!(
            error = err.to_string(),
            "Could not delete main discord log channel"
        );
    })
}
