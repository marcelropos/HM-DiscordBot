use std::env;
use std::str::FromStr;
use std::sync::OnceLock;

pub static MAIN_GUILD_ID: OnceLock<u64> = OnceLock::new();
pub static REDIS_PORT: OnceLock<u16> = OnceLock::new();
pub static REDIS_HOST: OnceLock<String> = OnceLock::new();
pub static MYSQL_PORT: OnceLock<u16> = OnceLock::new();
pub static MYSQL_HOST: OnceLock<String> = OnceLock::new();
pub static MYSQL_DATABASE: OnceLock<String> = OnceLock::new();
pub static MYSQL_USER: OnceLock<String> = OnceLock::new();
pub static MYSQL_PASSWORD: OnceLock<String> = OnceLock::new();
pub static BOT_TOKEN: OnceLock<String> = OnceLock::new();
pub static LOG_LEVEL: OnceLock<tracing::Level> = OnceLock::new();

pub fn init() {
    LOG_LEVEL.get_or_init(|| {
        env::var("RUST_LOG")
            .map(|level| {
                tracing::Level::from_str(level.as_str()).expect("Could not parse Logger level")
            })
            .unwrap_or(tracing::Level::INFO)
    });
    MAIN_GUILD_ID.get_or_init(|| {
        env::var("MAIN_GUILD_ID")
            .expect("No Main Guild ID given")
            .parse()
            .expect("Failed to parse Main Guild ID to u64")
    });
    REDIS_PORT.get_or_init(|| {
        env::var("REDIS_PORT")
            .unwrap_or("6379".to_owned())
            .parse()
            .expect("Failed to parse Redis Port to u16")
    });
    REDIS_HOST.get_or_init(|| env::var("REDIS_HOST").unwrap_or("127.0.0.1".to_owned()));
    MYSQL_PORT.get_or_init(|| {
        env::var("MYSQL_PORT")
            .unwrap_or("3306".to_owned())
            .parse()
            .expect("Failed to parse MySQL Port to u16")
    });
    MYSQL_HOST.get_or_init(|| env::var("MYSQL_HOST").unwrap_or("127.0.0.1".to_owned()));
    MYSQL_DATABASE.get_or_init(|| env::var("MYSQL_DATABASE").expect("No database given"));
    MYSQL_USER.get_or_init(|| env::var("MYSQL_USER").expect("No database username given"));
    MYSQL_PASSWORD.get_or_init(|| env::var("MYSQL_PASSWORD").expect("No password for user given"));
    BOT_TOKEN.get_or_init(|| env::var("BOT_TOKEN").expect("No Bot Token given"));
}
