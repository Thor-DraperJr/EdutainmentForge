# EdutainmentForge Makefile
# Common development and deployment tasks

.PHONY: help install install-dev test test-unit test-integration lint format clean build

# Default target
help:
	@echo "EdutainmentForge Development Commands"
	@echo "=====================================+"
	@echo ""
	@echo "Setup:"
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test          Run all tests"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  lint          Run code linting"
	@echo "  format        Format code with black and isort"
	@echo "  pre-commit    Run pre-commit hooks"
	@echo ""
	@echo "Build & Maintenance:"
	@echo "  build         Build Docker container (local only; CI handles prod)"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "Local Development:"
	@echo "  run           Run Flask app locally"
	@echo "  run-cli       Run CLI example"
	@echo "  smoke         Run lightweight smoke tests (requires server running)"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Testing targets
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v -m "not slow"

test-azure:
	pytest tests/integration/ -v -m azure

# Code quality targets
lint:
	flake8 src/ tests/ *.py
	mypy src/

format:
	black src/ tests/ *.py
	isort src/ tests/ *.py

pre-commit:
	pre-commit run --all-files

# Build and deployment targets
build:
	COMMIT_SHA=$$(git rev-parse --short HEAD || echo unknown); \
	BUILD_VERSION=$$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD); \
	echo "Building image with commit $$COMMIT_SHA version $$BUILD_VERSION"; \
	docker build --build-arg COMMIT_SHA=$$COMMIT_SHA --build-arg BUILD_VERSION=$$BUILD_VERSION -t edutainmentforge:latest .

# (deploy target removed — GitHub Actions workflow handles production deployment)

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

# Local development targets
run:
	python app.py

run-cli:
	python podcast_cli.py --help

smoke:
	DISABLE_AUTH_FOR_TESTING=true bash scripts/smoke_test.sh

# Premium service setup
setup-premium:
	./setup_premium_services.sh

enable-gpt4:
	./setup_premium_services.sh <<< "1"

enable-neural-voices:
	./setup_premium_services.sh <<< "2"

setup-custom-voices:
	./setup_premium_services.sh <<< "3"

enable-all-premium:
	./setup_premium_services.sh <<< "4"

setup-cost-monitoring:
	./setup_premium_services.sh <<< "5"

# Package building
dist: clean
	python -m build

upload-test:
	python -m twine upload --repository testpypi dist/*

upload:
	python -m twine upload dist/*

# Premium features setup
enable-premium-ai:
	@echo "Setting up premium AI features..."
	@echo "1. Deploy GPT-4 model in Azure OpenAI Studio"
	@echo "2. Update Key Vault with premium-ai-enabled=true"
	@echo "3. Configure smart model selection"

enable-neural-voices:
	@echo "Setting up premium neural voices..."
	@echo "1. Enable neural voice features in Speech Service"
	@echo "2. Update Key Vault with neural-voices-enabled=true"
	@echo "3. Configure voice styles and emotions"

setup-custom-voices:
	@echo "Setting up custom voice training..."
	@echo "1. Visit Speech Studio: https://speech.microsoft.com/"
	@echo "2. Create custom voice project"
	@echo "3. Upload voice training data"
	@echo "4. Train and deploy custom models"

# (premium deploy configuration removed; manage via CI + Key Vault updates)
