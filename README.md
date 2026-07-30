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

## Current workspace features

CivicFlow includes a public reporting experience and a staff workspace for managing public infrastructure operations.

### Public experience

- Landing page with the accountability chain from report to verified completion
- Public issue reporting with category, service area, location, description, contact preference, and evidence
- Secure issue tracking using a report reference and verification code
- Citizen account area for viewing submitted reports
- Public “How it works” and accountability pages

### Staff workspace

- Overview dashboard with operational activity and quick actions
- Reports operations screen at `/reports/` with search, category, status, and service-area filters
- Report rows showing reference, category, location/service area, status, age, and an Open action
- Procurement tender creation with category, method, department, service area, budget, deadlines, supplier guidance, contact details, and document uploads
- Contractor bidding, tender awards, and procurement audit history
- Organization, service-area, and membership administration
- Roles and policies backed by database permissions and separation-of-duties policies
- Account settings with profile editing, password management, notification status, and workspace access information
- Workspace account menu with Profile, Settings, and secure Sign out actions

### Important workspace routes

| Area | Route |
| --- | --- |
| Staff overview | `/workspace/` |
| Staff reports | `/reports/` |
| Create issue | `/report/` |
| Procurement | `/procurement/tenders/` |
| Organizations | `/workspace/organizations/` |
| Service areas | `/workspace/organizations/service-areas/` |
| Memberships | `/workspace/organizations/memberships/` |
| Roles and policies | `/workspace/access/roles/` |
| Account settings | `/workspace/profile/settings/` |
| Change password | `/password-change/` |

### Geographic service areas

Service areas are stored as WGS 84 PostGIS multipolygons. They are used to validate reported locations and route issues to the appropriate organization boundary. The service-area form provides a map boundary editor and a local fallback drawing surface when the external OpenLayers library is unavailable.

### Demo account

The demo seed command creates an administrator account:

```text
Email: admin@northbridge.gov
Password: DemoPass123!
```

Seed the demo data with:

```bash
python manage.py seed_demo
```
