.PHONY: help dev-up dev-down dev-logs prod-up prod-down prod-logs build clean coverage

help:
	@echo "Available commands:"
	@echo "  make dev-up       - Start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo "  make dev-logs     - View development logs"
	@echo "  make dev-shell    - Access Django shell in dev container"
	@echo "  make prod-up      - Start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo "  make prod-logs    - View production logs"
	@echo "  make build        - Build Docker images"
	@echo "  make clean        - Remove all containers, volumes, and images"
	@echo "  make coverage     - Run test suite under coverage and print report"

# Development commands
dev-up:
	docker-compose up -d

dev-down:
	docker-compose down

dev-logs:
	docker-compose logs -f

dev-shell:
	docker-compose exec app python manage.py shell

dev-migrate:
	docker-compose exec app python manage.py migrate_schemas --noinput

dev-makemigrations:
	docker-compose exec app python manage.py makemigrations

# Production commands
prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-migrate:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec app python manage.py migrate_schemas --noinput

# Common commands
build:
	docker-compose build

clean:
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v --rmi all

# Test coverage (bare-metal venv). Set SECRET_KEY + DB_* env vars first.
# Runs from crkva/ so manage.py test discovers the app test packages.
coverage:
	cd crkva && coverage run --rcfile=../.coveragerc manage.py test --keepdb --parallel 1
	cd crkva && coverage report --rcfile=../.coveragerc
