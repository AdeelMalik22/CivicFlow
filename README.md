# CivicFlow

CivicFlow is a public infrastructure transparency platform built with Django
and Django REST Framework.

## Product documentation

- [Product requirements](CivicFlow_PRD_v1.1.md)
- [Implementation plan](CivicFlow_IMPLEMENTATION_PLAN.md)

## Local development

Prerequisites:

- Python 3.11 or newer
- PostgreSQL with PostGIS for integration and production-like development
- GDAL and GEOS for geographic boundary support
- Redis for asynchronous jobs

Create the environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

On Ubuntu, install the geospatial system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y gdal-bin libgdal-dev libgeos-dev postgis postgresql-14-postgis-3
sudo -u postgres psql -d civic_flow -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

GeoDjango is included with Django, so no separate Python GIS package is
required. The PostgreSQL connection is automatically upgraded to Django's
PostGIS backend.

Export the settings module and database URL, then run Django:

```bash
export DJANGO_SETTINGS_MODULE=civicflow.settings.local
export DATABASE_URL=postgresql://civicflow:civicflow@localhost:5432/civicflow
python manage.py migrate
python manage.py runserver
```

SQLite is used when `DATABASE_URL` is omitted, which is convenient for the
earliest UI work. PostgreSQL/PostGIS remains the required integration and
production database.

Run the local quality suite:

```bash
make check
make test
```

Alternatively, start the web application, PostgreSQL/PostGIS, Redis, and a
Celery worker together:

```bash
docker compose up --build
```

The application is available at <http://localhost:8000/>.

DemoPass123!