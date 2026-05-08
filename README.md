# nats-trading-tests-example

Minimal end-to-end and contract testing example for an event-driven trading system built with microservices, NATS, and PostgreSQL.

This repository was created for a take-home assignment focused on automated testing of a black-box trading system. The tests verify the full order flow, side effects in PostgreSQL, and message contracts between the Order Service and the Trade Service.

## Project overview

The system has two services that communicate through NATS:

- **Order Service** consumes `orders.create`, validates incoming orders, stores them in PostgreSQL, and publishes either `orders.confirmed` or `orders.rejected`.
- **Trade Service** consumes `orders.confirmed`, updates positions in PostgreSQL, and publishes `trades.executed`.

The test suite covers:

- E2E order flow checks for happy paths and negative scenarios.
- Contract validation for messages exchanged between the two services.
- Database side effects for orders and positions.

## Project structure

- `src/pg/` — PostgreSQL models and client helpers.
- `src/nts/` — NATS client, collector, message schemas, and subject names.
- `helpers/` — reusable test helpers for payloads, retries, waits, and side-effect checks.   # TODO: расписать подробнее некоторые папки
- `tests/` — E2E tests and contract tests for the trading flow.
- `logger/` — structlog logging configuration.
- `docker-compose.yml` — local environment with NATS, PostgreSQL, Order Service, and Trade Service.
- `init.sql` — database bootstrap script used by PostgreSQL.
- `pyproject.toml` / `uv.lock` — Python project metadata and locked dependencies.

## Environment setup

### 1. Install `uv`

If `uv` is not already installed, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your shell if needed so the `uv` command is available.

### 2. Create and activate a virtual environment

From the repository root:

```bash
uv venv
source .venv/bin/activate
```

### 3. Install dependencies with `uv`

```bash
uv sync
```

You can also run commands without activating the venv by using `uv run ...`.

## Run tests

### 1. Start the local services

```bash
docker compose up -d
```

If your Docker setup uses the legacy CLI, `docker-compose up -d` works as well.

### 2. Run the full test suite

```bash
uv run pytest
```

### 3. Run a specific test file

```bash
uv run pytest tests/test_order_flow.py
uv run pytest tests/test_order_contracts.py
```

### 4. Stop the environment

```bash
docker compose down -v
```

## Actual tests status
1. `test_order_flow_accepts_high_precision_price` - проверка на максимальное точность. В задании не указано какую точность должно иметь поле Price. В init.sql и согласно логу который отдает сервис я вижу что это NUMERIC(12,4). Но так как согласно заданию для меня сервисы - black box, то я оставил тест падающим потому что он требует получения уточнений у владельца сервисов.
2. `test_order_rejected_when_symbol_value_invalid` - отсутствует валидация на пустую строку или строку из пробелов у поля symbol



## Approach


## Decisions


