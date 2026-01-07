# Database Migrations with Alembic

This directory contains database schema migrations managed by [Alembic](https://alembic.sqlalchemy.org/).

## Overview

The QualerInternalAPI uses Alembic for version-controlled database schema management. This replaces ad-hoc schema creation scripts and ensures consistent database state across environments.

## Configuration

- **Models**: Located in `persistence/models.py` (SQLAlchemy ORM)
- **Database URL**: Set via `DB_URL` environment variable or defaults to `postgresql://postgres:postgres@localhost:5432/qualer`
- **Alembic Config**: `alembic.ini` at project root
- **Environment Setup**: `alembic/env.py` (loads models and environment variables)

## Common Commands

### Create a new migration after model changes

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review the generated file in alembic/versions/
# Edit if needed, then apply:
alembic upgrade head
```

### Apply migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Downgrade by one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123
```

### Check migration status

```bash
# Show current database version
alembic current

# Show migration history
alembic history --verbose

# Show pending migrations
alembic history --verbose
```

### Create empty migration (for data migrations)

```bash
alembic revision -m "Add seed data"
```

## Migration Files

Located in `alembic/versions/`, migration files contain:
- `upgrade()` - Apply changes
- `downgrade()` - Revert changes
- Revision ID and dependencies

## Schema Design

### `datadump` Table (ORM Model: `APIResponse`)

The main table for storing raw API responses:

```sql
CREATE TABLE datadump (
    id SERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    service VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    request_header JSONB,      -- Request headers as JSON
    response_body TEXT,         -- Raw response body
    response_header JSONB,      -- Response headers as JSON
    parsed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_api_response UNIQUE (url, service, method)
);
```

**Key Points:**
- Uses JSONB for flexible header storage
- Unique constraint prevents duplicate API calls
- `parsed` flag for incremental processing workflow

## Workflow

1. **Modify Models**: Edit `persistence/models.py`
2. **Generate Migration**: `alembic revision --autogenerate -m "Description"`
3. **Review**: Check generated file in `alembic/versions/`
4. **Test**: Apply to test database
5. **Commit**: Add migration file to git
6. **Deploy**: Run `alembic upgrade head` on target environment

## Testing

Tests automatically create fresh database schema using the test fixture in `tests/conftest.py`. The fixture uses Alembic migrations to ensure test database matches production schema.

## Initial Setup (New Database)

```bash
# 1. Ensure DB_URL is set or update alembic.ini
export DB_URL="postgresql://user:pass@localhost:5432/dbname"

# 2. Run all migrations
alembic upgrade head

# 3. Verify
alembic current
```

## Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
alembic current

# Apply pending migrations
alembic upgrade head
```

### "Can't locate revision"
- Check that all migration files are committed
- Verify alembic_version table in database

### "ERROR: database does not exist"
- Create database first: `createdb dbname`
- Verify DB_URL environment variable

## Historical Context

**Pre-Alembic**: Schema was managed via `persistence/schema.py` with `create_datadump_table()` function. This led to schema drift between environments and made schema evolution difficult.

**Post-Alembic** (Current): All schema changes are version-controlled migrations. The initial migration (`4f539123b6db`) converts hstore columns to JSONB to match ORM models.
