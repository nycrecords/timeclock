#!/bin/bash
set -e

# Wait for database to be ready (with timeout)
echo "Waiting for PostgreSQL..."
max_attempts=5
attempt=0

# Check if we can ping the database
while [ $attempt -lt $max_attempts ]; do
  if pg_isready -h db -U developer -d timeclock_dev > /dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi

  attempt=$((attempt+1))
  if [ $attempt -eq $max_attempts ]; then
    echo "Could not connect to PostgreSQL after $max_attempts attempts. Falling back to localhost."
    # Try connecting to localhost as fallback
    if pg_isready -h localhost -U developer -d timeclock_dev > /dev/null 2>&1; then
      echo "PostgreSQL is ready on localhost!"
      export DATABASE_URL="postgresql://developer:developer_password@localhost:5432/timeclock_dev"
      break
    else
      echo "Could not connect to PostgreSQL on localhost either. Using 172.17.0.1 (Docker host)."
      export DATABASE_URL="postgresql://developer:developer_password@172.17.0.1:5432/timeclock_dev"
    fi
  fi

  >&2 echo "PostgreSQL is unavailable - sleeping (attempt $attempt/$max_attempts)"
  sleep 2
done

# Create the database tables directly without migrations first
echo "Creating database tables..."
python -c "from app import create_app, db; app = create_app('development'); app.app_context().push(); db.create_all()" || echo "Table creation failed, but continuing..."

# Set up initial database
echo "Setting up initial database data..."
python -m flask setup_db || echo "Database setup failed, but continuing..."

# Create dev users if in development mode
if [ "$FLASK_ENV" = "development" ] || [ "$FLASK_CONFIG" = "development" ]; then
  echo "Creating development users..."
  python -m flask create_dev_users || echo "Creating dev users failed, but continuing..."
  python -m flask create_health_screen_users || echo "Creating health screen users failed, but continuing..."
fi

# Start application
echo "Starting application..."
exec "$@"
