# Slide Speaker Makefile

.PHONY: help migrate test build clean

help:
	@echo "Available commands:"
	@echo "  migrate     - Migrate existing manifests for playback compatibility"
	@echo "  test        - Run tests"
	@echo "  build       - Build the application"
	@echo "  clean       - Clean build artifacts"

migrate:
	@echo "Migrating manifests..."
	cd backend && python scripts/migrate_manifests.py --data-dir ../.data

migrate-dry-run:
	@echo "Dry run migration..."
	cd backend && python scripts/migrate_manifests.py --data-dir ../.data --dry-run

test:
	@echo "Running tests..."
	npx playwright test

build:
	@echo "Building application..."
	docker compose build

clean:
	@echo "Cleaning build artifacts..."
	docker compose down
	docker system prune -f