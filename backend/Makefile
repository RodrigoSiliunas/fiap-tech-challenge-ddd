.PHONY: test cov up down

test:
	pytest --cov=oficina --cov-report=term-missing --cov-fail-under=80

cov:
	pytest --cov=oficina --cov-report=term-missing --cov-report=xml --cov-fail-under=80

up:
	docker compose up --build

down:
	docker compose down
