# Senior Automation QA Engineer — Take-Home Assignment

## Overview

You are given a simplified trading system consisting of two microservices that communicate via NATS. Your task is to write automated tests that verify the system works correctly end-to-end.

- **Time expectation:** 3–4 hours. We value quality and thoughtfulness over quantity.
- **Language:** Your choice. Use whatever you are most productive with.
- **Services are provided as pre-built Docker images** — treat them as black boxes. You do not have access to their source code, and you do not need it.
- If you haven't worked with NATS before, budget some extra time for ramp-up.

---

## System Description

The system processes trade orders through two services. The entry point is the NATS subject `orders.create` — there is no upstream producer in this bundle, so your tests act as the client publishing orders to it.

### Order Service

- Listens on NATS subject `orders.create`
- Validates the incoming order (required fields: `symbol`, `side`, `quantity`, `price`)
- Saves the order to PostgreSQL (`orders` table) with status `CREATED`
- Publishes an event to NATS subject `orders.confirmed` (or `orders.rejected` if validation fails)

### Trade Service

- Listens on NATS subject `orders.confirmed`
- Updates the position in PostgreSQL (`positions` table) — adjusts quantity for the given symbol
- Publishes an event to NATS subject `trades.executed`

### Message Schemas

**`orders.create`** (request)

```json
{
  "order_id": "string (UUID)",
  "symbol": "string (e.g. AAPL)",
  "side": "BUY | SELL",
  "quantity": "integer (> 0)",
  "price": "number (> 0)"
}
```

**`orders.confirmed`** / **`orders.rejected`**

```json
{
  "order_id": "string (UUID)",
  "status": "CONFIRMED | REJECTED",
  "reason": "string | null"
}
```

**`trades.executed`**

```json
{
  "order_id": "string (UUID)",
  "symbol": "string",
  "side": "BUY | SELL",
  "quantity": "integer",
  "executed_at": "ISO 8601 timestamp"
}
```

---

## Your Task

### 1. E2E Tests

Write end-to-end tests that verify the full order flow — both happy path and negative scenarios. We are interested in which edge cases you identify and why.

### 2. Contract Tests

Implement contract validation between the two services.

### 3. README

Include a README with instructions to run the tests and notes on your approach and decisions.

---

## Deliverables

- A link to your own Git repository (GitHub, GitLab, Bitbucket — your choice) containing:
  - Your test code
  - The files from this bundle (`docker-compose.yml`, `init.sql`) so the reviewer can run your tests against the same setup
  - A working README with instructions to run everything
- Tests should run against the provided docker-compose setup

We will review your commit history, so please commit your work incrementally rather than in a single final commit.

---

## Notes

- You do not need (and do not have access) to modify the services. Treat them as black boxes — discover their behavior through tests.
- If the behavior of the system is ambiguous in a given scenario, document your interpretation in the README rather than guessing what we want.
- If you encounter issues with the provided setup, document them and explain how you worked around them.
