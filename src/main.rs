use tracing::{error, info};

mod redis_lib;
mod mysql_lib;
mod bot;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let redis_client;
    match redis_lib::get_connection() {
        None => return,
        Some(val) => redis_client = val
    }
    info!("Successfully connected to redis");

    let sql_pool;
    match mysql_lib::get_connection(5).await {
        None => return,
        Some(val) => sql_pool = val
    }
    info!("Successfully connected to MySQL Database");
    match mysql_lib::migrate_database(&sql_pool).await {
        Ok(_) => {}
        Err(err) => {
            error!(error=err.to_string(), "SQL Migration failed");
            return;
        }
    }
    info!("Successfully made the SQL migration if any");

    bot::entrypoint(sql_pool, redis_client).await;
}
