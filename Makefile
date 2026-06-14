.PHONY: help dev-up dev-down dev-logs dev-shell dev-migrate dev-makemigrations \
        standalone-up standalone-down standalone-logs \
        prod-up prod-down prod-logs prod-migrate build clean coverage

help:
	@echo "Available commands:"
	@echo "  make dev-up           - Start dev (runserver + бундлед Postgres)"
	@echo "  make dev-down         - Stop dev"
	@echo "  make dev-logs         - Tail dev logs"
	@echo "  make dev-shell        - Django shell у dev контејнеру"
	@echo "  make standalone-up    - Start standalone (gunicorn + бундлед Postgres)"
	@echo "  make standalone-down  - Stop standalone"
	@echo "  make prod-up          - Start prod (gunicorn, спољашња база)"
	@echo "  make prod-down        - Stop prod"
	@echo "  make build            - Build app image"
	@echo "  make clean            - Remove containers, volumes, images"
	@echo "  make coverage         - Run tests under coverage (bare-metal venv)"

# Development (профил dev → сервис app-dev)
dev-up:
	docker compose --profile dev up -d
dev-down:
	docker compose --profile dev down
dev-logs:
	docker compose --profile dev logs -f
dev-shell:
	docker compose --profile dev exec app-dev python manage.py shell
dev-migrate:
	docker compose --profile dev exec app-dev python manage.py migrate_schemas --noinput
dev-makemigrations:
	docker compose --profile dev exec app-dev python manage.py makemigrations

# Standalone (профил standalone → сервис app, све-у-једном)
standalone-up:
	docker compose --profile standalone up -d --build
standalone-down:
	docker compose --profile standalone down
standalone-logs:
	docker compose --profile standalone logs -f

# Production (профил prod → сервис app-prod, спољашња база)
prod-up:
	docker compose --profile prod up -d
prod-down:
	docker compose --profile prod down
prod-logs:
	docker compose --profile prod logs -f
prod-migrate:
	docker compose --profile prod exec app-prod python manage.py migrate_schemas --noinput

# Common
build:
	docker compose --profile standalone build
clean:
	docker compose --profile dev --profile standalone --profile prod down -v --rmi all

# Test coverage (bare-metal venv). Set SECRET_KEY + DB_* env vars first.
coverage:
	cd crkva && coverage run --rcfile=../.coveragerc manage.py test --keepdb --parallel 1
	cd crkva && coverage report --rcfile=../.coveragerc
