# Clearline assessment notes

**App name:** Clearline. It is a small capital call reconciliation workspace for Northwind Ventures and Bluebird Capital.

## Run locally with Docker

Install Docker Desktop (or another Docker engine with Compose). From the repository root, run:

```sh
docker compose up --build
```

Compose starts PostgreSQL, Django, and Vite. The backend automatically runs `python manage.py migrate` and `python manage.py seed_demo` on startup. To run the idempotent seed command again while the services are running, use a second terminal:

```sh
docker compose exec backend python manage.py seed_demo
```

Open <http://localhost:5173>; the backend is at <http://localhost:8000>. Stop the services with `Ctrl+C`, or run `docker compose down` from another terminal. The PostgreSQL data stays in a Docker volume.

Docker Compose uses local development defaults. To change them, copy `.env.example` to `.env` in the repository root and edit the values before starting Compose. No real credentials are checked in.

Run the full backend test suite with:

```sh
docker compose run --rm backend python manage.py test
```

The test command creates a separate PostgreSQL test database.

## Run locally without Docker

Install Python 3.13, Node.js 22 with npm, and PostgreSQL 17. Start PostgreSQL and create the development role and database. From a terminal with `psql` on the path, run the following as a PostgreSQL administrator (enter its password when prompted):

```sh
psql -h localhost -U postgres -c "CREATE ROLE clearline WITH LOGIN PASSWORD 'clearline_local_only';"
psql -h localhost -U postgres -c "CREATE DATABASE clearline OWNER clearline;"
```

These names and the password match the defaults in `backend/config/settings.py`. If you use different values, set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` in the terminal where you start Django. Django does not read the root `.env` file automatically outside Compose.

From the repository root, create a Python environment and install the backend dependencies:

```sh
cd backend
python -m venv .venv
```

Activate it with `.\.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` in bash, then run:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

`seed_demo` creates the assessment organizations and capital calls through a Django management command. You can rerun it without creating duplicate demo records. Keep Django running and, in a second terminal from the repository root, start the frontend:

```sh
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite forwards `/api` requests to the Django server at `127.0.0.1:8000` by default.

With either setup, import a bank statement through the page, including the supplied `sample_bank_statement (2).csv` if desired. The UI accepts other CSV files with the specified columns.

## Data model

- `Organization` is the tenant. `InvestorEntity`, `CapitalCall`, `LineItem`, `BankTransaction`, and `Match` each carry an organization foreign key.
- `LineItem` holds the called and funded `Decimal` amounts. Its remaining amount is calculated, and database constraints keep funding within the called amount.
- `BankTransaction` stores the original bank row, status, and any reason for review. Its bank reference is unique within an organization.
- `Match` links a transaction and line item, with a status and a human readable reason. A pair can be proposed once.

All API reads and actions are scoped by `X-Organization`. A missing header gives `400`; an unknown organization or another organization's record gives `404`.

## API

Every endpoint below requires `X-Organization: northwind` or `X-Organization: bluebird`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/transactions/` | Newest first transactions with candidates, statuses and reasons |
| `GET` | `/api/line-items/` | Capital call line items with called, funded and remaining amounts |
| `POST` | `/api/imports/` | Multipart upload in field `file`; returns `imported`, `duplicates`, and `errors` (`line`, `message`) |
| `POST` | `/api/matches/<id>/approve/` | Atomically approve a proposed match; `409` if already final or amount exceeds remaining |
| `POST` | `/api/matches/<id>/reject/` | Reject one proposed match |
| `POST` | `/api/transactions/<id>/ignore/` | Ignore an open credit and reject its candidates |

The API uses JSON for responses. Approval locks the transaction and line item in one PostgreSQL transaction, then checks the current remaining balance. Repeated approval requests return `409` without funding twice.

## Assumptions and trade-offs

- Bank references are compared exactly for duplicate detection after trimming surrounding whitespace. Their normalization is used only for matching expected wire references.
- Suggestions are a snapshot at import time. Approval rechecks the current amount. A stale suggestion can therefore return `409` and remain available for manual review.
- A malformed row is reported and skipped. A file missing required columns is rejected before any rows are saved.
- The two workspace options are fixed in the UI because the assessment defines two organizations and no organization listing endpoint.
- The optional Airtable integration and deployment are omitted. There is no manual matching action beyond choosing an existing proposed candidate, as the specified API only requires approve, reject and ignore.
- The local `TEST_SQLITE=1` setting exists only for basic development checks when PostgreSQL is unavailable. Normal runtime and the documented test command use PostgreSQL.
