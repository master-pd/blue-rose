# Blue Rose Bot - Makefile
# Common tasks and commands

.PHONY: help install test run clean deploy docker

# Default target
help:
	@echo "Blue Rose Bot - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Check code quality"
	@echo "  format       Format code"
	@echo "  run          Run bot in development mode"
	@echo ""
	@echo "Production:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker"
	@echo "  deploy       Deploy to production"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Clean temporary files"
	@echo "  backup       Create backup"
	@echo "  update       Update dependencies"

# Development
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	python run_tests.py

lint:
	flake8 .
	mypy .
	black --check .

format:
	black .
	isort .

run:
	python main.py

# Production
docker-build:
	docker build -t blue-rose-bot .

docker-run:
	docker-compose up -d

deploy:
	./deploy.sh

# Maintenance
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

backup:
	python -c "from storage.backup import BackupManager; import asyncio; asyncio.run(BackupManager().create_backup('manual', 'Makefile backup'))"

update:
	pip install --upgrade -r requirements.txt

# Database
db-migrate:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

# Monitoring
logs:
	docker-compose logs -f blue-rose-bot

status:
	docker-compose ps

# SSL certificates (for development)
ssl-dev:
	mkdir -p ssl
	openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/CN=localhost"