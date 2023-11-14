FROM lukemathwalker/cargo-chef:latest-rust-1.73 AS chef
WORKDIR /app

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
COPY --from=planner /app/recipe.json recipe.json
# Build dependencies - this is the caching Docker layer!
RUN cargo chef cook --release --recipe-path recipe.json
# Build application
COPY . .
RUN SQLX_OFFLINE=true cargo build --release

FROM debian:bookworm-slim AS runtime
RUN apt update && apt install ca-certificates openssl -y && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/hm-discord-bot /usr/local/bin/hm-discord-bot

# initialize user as needed
RUN useradd -u 1001 -s /bin/sh abc

# copy entrypoint
COPY ./entrypoint.sh .

# Fix permissions
RUN chmod +x entrypoint.sh

WORKDIR /hm-discord-bot

ENTRYPOINT ["./entrypoint.sh"]
