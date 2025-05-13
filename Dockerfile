FROM python:3.6

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install pipenv and dependencies
RUN pip install pipenv && \
    pipenv install --deploy --system && \
    pip install psycopg2-binary IPython>=5.0.0 flask-shell-ipython

# Copy application code
COPY . .

# Add entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set environment variables
ENV FLASK_APP=timeclock.py
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=development
ENV FLASK_CONFIG=development
ENV FLASK_DEBUG=1
ENV DATABASE_URL=postgresql://developer:developer_password@db:5432/timeclock_dev

# Expose port
EXPOSE 5000

# Run entrypoint and command
ENTRYPOINT ["/docker-entrypoint.sh"]
# Allow hot-reloading with debugger enabled
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001", "--reload"] 
