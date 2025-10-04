#!/bin/bash
# Initialize Alembic if not already done

set -e

if [ ! -f "alembic/versions/001_initial_migration.py" ]; then
    echo "Creating initial Alembic migration..."
    alembic revision --autogenerate -m "Initial migration"
    echo "Initial migration created!"
else
    echo "Alembic already initialized"
fi
