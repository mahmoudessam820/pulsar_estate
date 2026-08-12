#!/usr/bin/env bash 
set -euo pipefail

echo "🚀 Pulsar Estate Entrypoint Started"

# ======================
# Configuration
# ======================
DB_HOST="${DPP_DATABASE_HOST:-db}"
DB_PORT="${DPP_DATABASE_PORT:-5432}"
DB_USER="${DPP_DATABASE_USER:-pulsar_user}"
MAX_RETRIES=30
RETRY_INTERVAL=2

# ======================
# Wait for PostgreSQL
# ======================
echo "⏳ Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
retry_count=0

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $MAX_RETRIES ]; then
        echo "❌ ERROR: Database is still unavailable after ${MAX_RETRIES} attempts. Exiting."
        exit 1
    fi
    echo "Database unavailable - retrying in ${RETRY_INTERVAL}s... (${retry_count}/${MAX_RETRIES})"
    sleep "$RETRY_INTERVAL"
done

echo "✅ PostgreSQL is ready!"

# ======================
# Run Database Migrations
# ======================
echo "🔄 Running Alembic migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed! Check the logs above."
    exit 1
fi

# ======================
# Start the main application
# ======================
echo "🚀 Starting application: $*"
exec "$@"