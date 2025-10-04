#!/bin/bash
# Database initialization script

set -e

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is ready!"

# Run database migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

# Create initial users
echo "Creating initial users..."
python create_initial_users.py

echo "Database initialization completed!"
