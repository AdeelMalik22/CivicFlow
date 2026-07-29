.PHONY: check format migrate run test up

check:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/python manage.py check
	.venv/bin/python manage.py makemigrations --check --dry-run

format:
	.venv/bin/ruff check --fix .
	.venv/bin/ruff format .

migrate:
	.venv/bin/python manage.py migrate

run:
	.venv/bin/python manage.py runserver

test:
	.venv/bin/pytest

up:
	docker compose up --build
