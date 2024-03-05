# HM FK07 Discord Bot

This is the code for the **Sebastian** Bot used on HM Discord Servers

# Local setup

Start a mariadb and redis instance, for example through the provided docker-compose:

```bash
docker compose up -d redis mariadb
```

Put your discord bot token in a `.env.local` at the root of the repo:

```bash
BOT_TOKEN=...
```

Start the bot:

```bash
cargo run
```

# Redesign documentation

In an effort to improve the Bot, the bot will be rewritten from ground up, switching from Python to Rust.

## Parts to redo

* Bot itself
* Database
* Docker setup
* automatic building in GitHub

## Design files

[Bot](docs/Bot.md)

* [Alumni Support](docs/Alumni.md)

[Database](docs/Database.md)

[Redis](docs/Redis.md)
