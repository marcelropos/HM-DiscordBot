FROM rust:1.71.1 as builder

# create a new empty shell project
RUN USER=root cargo new --bin hm-discord-bot
WORKDIR /hm-discord-bot

# Copy manifests
COPY ./Cargo.lock ./Cargo.lock
COPY ./Cargo.toml ./Cargo.toml

# Build only the dependencies to cache them
RUN cargo build --release
RUN rm src/*.rs

# Now that the dependency is built, copy your source code
COPY ./migrations ./migrations
COPY ./src ./src

# Build for release.
RUN rm ./target/release/deps/hm_discord_bot*
RUN cargo install --path .

FROM debian:bullseye-slim

WORKDIR /hm-discord-bot

#RUN apt-get update && apt-get install -y extra-runtime-dependencies && rm -rf /var/lib/apt/lists/*

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

# initialize user as needed
RUN useradd -u 1001 -s /bin/sh abc

# copy entrypoint
COPY ./entrypoint.sh .

# Fix permissions
RUN chmod +x entrypoint.sh

# copy the build artifact from the build stage
COPY --from=builder /usr/local/cargo/bin/hm-discord-bot /usr/local/bin/hm-discord-bot

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_DIR=/etc/ssl/certs

ENTRYPOINT ./entrypoint.sh