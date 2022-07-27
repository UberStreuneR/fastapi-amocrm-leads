#!/bin/sh

[ -z $DB_HOST ] && DB_HOST="contact_level_db"
[ -z $DB_PORT ] && DB_PORT="5432"

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
done
echo "PostgreSQL started"

exec "$@"
