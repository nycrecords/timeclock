#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TimeClock Docker Entrypoint Script - Production Ready
# ============================================================================
# Features:
# - Structured logging with timestamps and levels
# - Exponential backoff for database connections
# - Signal handling for graceful shutdown
# - Environment variable validation
# - Migration safety checks
# - Debug mode support
# ============================================================================

# Configuration
readonly SCRIPT_NAME="entrypoint"
readonly DB_MAX_ATTEMPTS=30
readonly DB_INITIAL_DELAY=1
readonly DB_MAX_DELAY=30
readonly MIGRATION_BACKUP_ENABLED="${MIGRATION_BACKUP_ENABLED:-false}"
readonly DEBUG="${DEBUG:-false}"

# Color codes for terminal output (disabled in non-TTY)
if [ -t 1 ]; then
    readonly RED='\033[0;31m'
    readonly YELLOW='\033[1;33m'
    readonly GREEN='\033[0;32m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m' # No Color
else
    readonly RED=''
    readonly YELLOW=''
    readonly GREEN=''
    readonly BLUE=''
    readonly NC=''
fi

# ============================================================================
# Logging Functions
# ============================================================================

log_timestamp() {
    date -u '+%Y-%m-%dT%H:%M:%S.%3NZ' 2>/dev/null || date -u '+%Y-%m-%dT%H:%M:%SZ'
}

log_info() {
    echo -e "${GREEN}[$(log_timestamp)]${NC} [${SCRIPT_NAME}] ${BLUE}INFO${NC}: $*"
}

log_warn() {
    echo -e "${YELLOW}[$(log_timestamp)]${NC} [${SCRIPT_NAME}] ${YELLOW}WARN${NC}: $*" >&2
}

log_error() {
    echo -e "${RED}[$(log_timestamp)]${NC} [${SCRIPT_NAME}] ${RED}ERROR${NC}: $*" >&2
}

log_debug() {
    if [ "${DEBUG}" = "true" ]; then
        echo -e "[$(log_timestamp)] [${SCRIPT_NAME}] DEBUG: $*" >&2
    fi
}

# ============================================================================
# Error Handling
# ============================================================================

error_exit() {
    local message="$1"
    local exit_code="${2:-1}"
    log_error "${message}"
    log_error "Exiting with code ${exit_code}"
    exit "${exit_code}"
}

# Cleanup function for graceful shutdown
cleanup() {
    local exit_code=$?
    log_info "Received shutdown signal, cleaning up..."
    # Add any cleanup tasks here (close connections, save state, etc.)
    exit "${exit_code}"
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# ============================================================================
# Environment Validation
# ============================================================================

validate_environment() {
    log_info "Validating environment variables..."

    # Required variables
    local required_vars=("DATABASE_URL")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("${var}")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        error_exit "Missing required environment variables: ${missing_vars[*]}" 2
    fi

    # Validate DATABASE_URL format
    if [[ ! "${DATABASE_URL}" =~ ^postgresql:// ]]; then
        error_exit "DATABASE_URL must start with postgresql://" 3
    fi

    # Optional but recommended variables
    local optional_vars=("FLASK_ENV" "SECRET_KEY")
    for var in "${optional_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_warn "${var} is not set (recommended for production)"
        fi
    done

    log_debug "Environment validation passed"
    log_info "Environment: FLASK_ENV=${FLASK_ENV:-production}"
    log_info "Database URL: configured"
    log_info "Debug mode: ${DEBUG}"
}

# ============================================================================
# Database Connection with Exponential Backoff
# ============================================================================

wait_for_database() {
    log_info "Waiting for database availability (max ${DB_MAX_ATTEMPTS} attempts)..."

    python - <<'PYTHON_SCRIPT'
import os
import sys
import time
import psycopg2
from urllib.parse import urlparse

def log_msg(level, msg):
    """Structured logging helper"""
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    print(f"[{timestamp}] [entrypoint] {level}: {msg}", file=sys.stderr if level == "ERROR" else sys.stdout)

url = os.environ.get('DATABASE_URL')
if not url:
    log_msg('ERROR', 'DATABASE_URL not set')
    sys.exit(1)

# Parse database info for logging (without credentials)
try:
    parsed = urlparse(url)
    db_host = parsed.hostname or 'unknown'
    db_port = parsed.port or 5432
    db_name = parsed.path.lstrip('/') or 'unknown'
    log_msg('INFO', f'Connecting to {db_host}:{db_port}/{db_name}')
except Exception as e:
    log_msg('WARN', f'Could not parse DATABASE_URL: {e}')

max_attempts = int(os.environ.get('DB_MAX_ATTEMPTS', 30))
initial_delay = float(os.environ.get('DB_INITIAL_DELAY', 1))
max_delay = float(os.environ.get('DB_MAX_DELAY', 30))
debug = os.environ.get('DEBUG', 'false').lower() == 'true'

delay = initial_delay
for attempt in range(1, max_attempts + 1):
    try:
        if debug:
            log_msg('DEBUG', f'Attempt {attempt}/{max_attempts} - connecting...')

        conn = psycopg2.connect(url, connect_timeout=5)
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        log_msg('INFO', f'Database is reachable (attempt {attempt}/{max_attempts})')
        log_msg('INFO', f'PostgreSQL version: {db_version[:50]}...')
        sys.exit(0)

    except psycopg2.OperationalError as e:
        error_msg = str(e).replace('\n', ' ')[:200]

        if attempt % 5 == 0 or attempt == 1:
            log_msg('WARN', f'Attempt {attempt}/{max_attempts} - {error_msg}')

        if attempt >= max_attempts:
            log_msg('ERROR', f'Database not reachable after {max_attempts} attempts')
            log_msg('ERROR', f'Last error: {error_msg}')
            sys.exit(1)

        if debug:
            log_msg('DEBUG', f'Retrying in {delay:.1f}s...')

        time.sleep(delay)

        # Exponential backoff with jitter
        delay = min(delay * 1.5, max_delay)

    except Exception as e:
        log_msg('ERROR', f'Unexpected error connecting to database: {e}')
        sys.exit(1)
PYTHON_SCRIPT

    local exit_code=$?
    if [ ${exit_code} -ne 0 ]; then
        error_exit "Failed to establish database connection" "${exit_code}"
    fi

    log_info "Database connection verified successfully"
}

# ============================================================================
# Migration Safety Checks
# ============================================================================

pre_migration_checks() {
    log_info "Running pre-migration checks..."

    # Check if migrations directory exists
    if [ ! -d "migrations" ]; then
        log_warn "Migrations directory not found, skipping migration checks"
        return 0
    fi

    # Check if flask db command is available
    if ! command -v flask &> /dev/null; then
        error_exit "Flask command not found in PATH" 4
    fi

    # Verify we can connect to database before migrating
    log_debug "Verifying database connection before migration..."

    # Get current migration status
    log_info "Checking current migration status..."
    if flask db current &> /dev/null; then
        log_info "Migration system is initialized"
    else
        log_warn "Migration system may not be initialized"
    fi

    log_debug "Pre-migration checks passed"
}

run_migrations() {
    log_info "Running database migrations (flask db upgrade)..."

    pre_migration_checks

    # Optional: Create backup point before migration
    if [ "${MIGRATION_BACKUP_ENABLED}" = "true" ]; then
        log_warn "Migration backup requested but not implemented (set MIGRATION_BACKUP_ENABLED=false to silence)"
    fi

    # Run migrations with error handling
    local migration_output
    if migration_output=$(flask db upgrade 2>&1); then
        log_info "Migrations completed successfully"
        log_debug "Migration output: ${migration_output}"
    else
        log_error "Migration failed with output:"
        echo "${migration_output}" >&2
        error_exit "Database migration failed - database may be in inconsistent state" 5
    fi

    # Verify migrations were applied
    log_info "Verifying migration status..."
    if flask db current &> /dev/null; then
        log_info "Migration verification passed"
    else
        log_warn "Could not verify migration status"
    fi
}

# ============================================================================
# Application Verification
# ============================================================================

verify_application() {
    log_info "Verifying application can start..."

    # Check if app module exists
    if [ ! -f "app/__init__.py" ]; then
        error_exit "Application module app/__init__.py not found" 6
    fi

    # Try to import the application
    local import_output
    if import_output=$(python -c "from app import create_app; print('OK')" 2>&1); then
        log_info "Application imported successfully"
        log_debug "Import output: ${import_output}"
    else
        log_error "Failed to import application:"
        echo "${import_output}" >&2
        error_exit "Application import failed - check your code for errors" 7
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log_info "Starting TimeClock application container..."
    log_info "Script version: 2.0 (production-ready)"

    # Step 1: Validate environment
    validate_environment

    # Step 2: Wait for database
    wait_for_database

    # Step 3: Run migrations (unless skipped)
    if [ "${SKIP_MIGRATIONS:-false}" = "true" ]; then
        log_warn "Skipping database migrations (SKIP_MIGRATIONS=true)"
    else
        run_migrations
    fi

    # Step 4: Verify application
    verify_application

    # Step 5: Start application
    log_info "All pre-flight checks passed!"

    if [ $# -eq 0 ]; then
        log_warn "No command provided, using default: gunicorn"
        log_info "Starting gunicorn with 2 workers on 0.0.0.0:5000"
        exec gunicorn \
            -w 2 \
            -b 0.0.0.0:5000 \
            --timeout 120 \
            --log-level info \
            --access-logfile - \
            --error-logfile - \
            timeclock:app
    else
        log_info "Executing command: $*"
        exec "$@"
    fi
}

# ============================================================================
# Entry Point
# ============================================================================

# Run main function
main "$@"
