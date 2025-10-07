#!/bin/bash
# Database initialization script

set -e

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is ready!"

# Create database and user if they don't exist
echo "Creating database and user..."
PGPASSWORD=postgres psql -h postgres -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'slide_speaker'" | grep -q 1 || \
    PGPASSWORD=postgres psql -h postgres -U postgres -c "CREATE DATABASE slide_speaker"

PGPASSWORD=postgres psql -h postgres -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = 'slide_speaker'" | grep -q 1 || \
    PGPASSWORD=postgres psql -h postgres -U postgres -c "CREATE USER slide_speaker WITH PASSWORD 'slide_speaker_pass'"

PGPASSWORD=postgres psql -h postgres -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE slide_speaker TO slide_speaker"
PGPASSWORD=postgres psql -h postgres -U postgres -d slide_speaker -c "GRANT ALL ON SCHEMA public TO slide_speaker"
PGPASSWORD=postgres psql -h postgres -U postgres -d slide_speaker -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO slide_speaker"
PGPASSWORD=postgres psql -h postgres -U postgres -d slide_speaker -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO slide_speaker"
PGPASSWORD=postgres psql -h postgres -U postgres -d slide_speaker -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO slide_speaker"
PGPASSWORD=postgres psql -h postgres -U postgres -d slide_speaker -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO slide_speaker"

echo "Database and user created!"

# Run database migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

# Create initial users
echo "Creating initial users..."
python create_initial_users.py

echo "Database initialization completed!"
