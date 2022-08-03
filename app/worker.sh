#!/bin/sh

[ -z $RABBIT_HOST ] && RABBIT_HOST="contact_level_rabbitmq"
[ -z $RABBIT_PORT ] && RABBIT_PORT="5672"

echo "Waiting for RabbitMQ..."
while ! nc -z $RABBIT_HOST $RABBIT_PORT; do
    sleep 0.1
done
echo "RabbitMQ started"
celery -A app.worker worker --loglevel=INFO -Q settings
exec "$@"