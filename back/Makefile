run-local:
	python -m app

run-db:
	docker compose -f ../docker-compose.yaml up db redis --build -d
# Make database migration
.PHONY: migration
migration:
	alembic revision \
	  --autogenerate \
	  --rev-id $(shell python alembic/_get_next_revision_id.py) \
	  --message $(message)

.PHONY: migrate
migrate:
	alembic upgrade heads

.PHONY: app-build
app-build:
	docker compose -f ../docker-compose.yaml build

.PHONY: app-run
app-run:
	docker compose -f ../docker-compose.yaml stop
	docker compose -f ../docker-compose.yaml up -d --remove-orphans

.PHONY: app-stop
app-stop:
	docker compose -f ../docker-compose.yaml stop

.PHONY: app-down
app-down:
	docker compose -f ../docker-compose.yaml down

.PHONY: app-destroy
app-destroy:
	docker compose -f ../docker-compose.yaml down -v --remove-orphans

.PHONY: app-logs
app-logs:
	docker compose -f ../docker-compose.yaml logs -f api