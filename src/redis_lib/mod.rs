use std::env;

use redis::{Client, Connection};
use tracing::error;

/// Tries to establish a connection with the given env variables and return the Redis client if
/// successful.
///
/// # Env Variables
///
/// * REDIS_PORT: the port of redis, defaults to 6379
/// * REDIS_HOST: the host of redis, ip or hostname or domain, defaults to 127.0.0.1
pub fn get_connection() -> Option<Client> {
    let redis_port: u16;
    match env::var("REDIS_PORT") {
        Ok(val) => match val.parse() {
            Ok(value) => redis_port = value,
            Err(err) => {
                error!(error=err.to_string(), "Failed to parse int");
                return None;
            }
        },
        Err(_) => redis_port = 6379
    };
    let redis_hostname = match env::var("REDIS_HOST") {
        Ok(val) => val,
        Err(_) => "127.0.0.1".to_string()
    };
    let client;
    match Client::open(format!("redis://{}:{}", redis_hostname, redis_port)) {
        Ok(val) => client = val,
        Err(err) => {
            error!(error=err.to_string(), "Problem creating redis client");
            return None;
        }
    }
    if let Err(err) = client.get_connection() {
        error!(error=err.to_string(), "Failed connecting to Redis");
        return None;
    }
    return Some(client);
}

/// Opens a connection to the redis database
pub fn connect(client: Client) -> Option<Connection> {
    match client.get_connection() {
        Ok(val) => Some(val),
        Err(err) => {
            error!(error=err.to_string(), "Failed connecting to Redis");
            None
        }
    }
}