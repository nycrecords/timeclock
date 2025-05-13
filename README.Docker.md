# Docker Setup for TimeClock

This directory contains Docker configuration for running the TimeClock application with PostgreSQL.

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Getting Started

1. Build and start the containers:

```bash
docker-compose up -d
```

2. The application will be available at http://localhost:5001 (you can change the port in `docker-compose.yml`).

3. Stop the containers:

```bash
docker-compose down
```

## Database Management

The database is automatically initialized when the containers start. This includes the creation of an admin user (`admin@records.nyc.gov`) with the password `password`.

To reset the database:

```bash
docker-compose exec web flask reset_db
```

To create development users:

```bash
docker-compose exec web flask create_dev_users
docker-compose exec web flask create_health_screen_users
```
Note that this step runs automatically when starting the app through `docker-compose`.

## Development

Code changes in the local directory will be reflected in the running application due to the volume mount. However, for some changes (like installing new dependencies), you may need to rebuild:

```bash
docker-compose up -d --build
```

## Database Connection

The PostgreSQL database is accessible from the host machine at:
- Host: localhost
- Port: 5432
- User: developer
- Password: developer_password
- Database: timeclock_dev

You can connect to the database running in Docker:
- Through Docker directly: `docker-compose exec db psql -U developer -d timeclock_dev`
- Through `psql` from your host machine: `psql -h localhost -p 5432 -U developer -d timeclock_dev`
- Through database UI tools using the credentials provided above
