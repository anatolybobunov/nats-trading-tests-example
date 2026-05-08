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

- `src/pg/` — PostgreSQL models and client helpers
- `src/nts/` — NATS client, collector, message schemas, and subject names
- `helpers/` — reusable test helpers for payloads, retries, waits, and side-effect checks
- `tests/` — E2E tests and contract tests for the trading flow
- `logger/` — structlog logging configuration
- `utils/` — auxiliary functions not related to business logic
- `docker-compose.yml` — local environment with NATS, PostgreSQL, Order Service, and Trade Service.
- `init.sql` — database bootstrap script used by PostgreSQL
- `pyproject.toml` / `uv.lock` — Python project metadata and locked dependencies

## Environment setup

### Requirements

You must have Docker installed locally.

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
uv run pytest tests/e2e/test_order_flow.py 
```

### 4. Stop the environment

```bash
docker compose down -v
```

## Actual tests status
1. `test_order_flow_accepts_high_precision_price` - The task does not specify what precision the Price field should have. In init.sql and in the service logs, I can see that it uses NUMERIC(12,4). This test needs clarification from the service owners. 
2. `test_order_rejected_when_symbol_value_invalid` - Bug: there is no validation for the symbol field. 
3. `test_order_rejected_when_order_id_is_invalid_uuid ` - Bug: we should get an order rejection, but the service lets an invalid order_id pass through, and we reach a database error. 


## Approach

- Tech stack: pytest, pytest-asyncio, nats-py, pydantic, asyncpg — these are popular and widely used tools.  
- The layered architecture was chosen from the beginning because it separates different logic into layers, makes the project easier to change, and helps with future extension.  
- Environment setup and linters: uv, ruff, ty, and pre-commit — a popular and common combination.

## Decisions
There were no specific requirements for the libraries in the task, so I chose the most commonly used ones. This should make it easier for another tester to start working with the repository and code.

I set up linters at the very beginning, before writing the code, so the code would follow one consistent style from the start.

I chose layered architecture because I have used this approach for the last few years, and it fits this task well. The only downside may be a little over-engineering at the beginning.


