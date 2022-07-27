#!/bin/sh

[ -z $DB_HOST ] && DB_HOST="postgres"
[ -z $DB_PORT ] && DB_PORT="5433"

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
done
echo "PostgreSQL started"

exec "$@"