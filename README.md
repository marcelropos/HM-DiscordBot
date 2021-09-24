# HM Ersti FK07 Discord Bot

Das ist der Code für den **Sebastian** Bot auf dem "**FK07 Studenty Discord Server**"

## Sprache

Der Bot benutzt Python 3.9

## Setup

Nachdem der Docker das erste Mal gestartet wurde, muss ein entry-point Script in `appdata/mongo/mongo-entrypoint/`
hinzugefügt werden zu:
```
#!/usr/bin/env bash
echo "Creating mongo users..."
mongo admin --host localhost -u ROOT_USERNAME -p ROOT_PASSWORD --eval \
    "use BOT_DATABASE; db.createUser({user: 'BOT_USERNAME', pwd: 'BOT_PASSWORD', roles: [{role: 'readWrite', db: 'BOT_DATABASE'}]});"
echo "Mongo users created."
```
