# CivicFlow development notes

## Project overview

CivicFlow is a Django/GeoDjango public-infrastructure accountability platform. It supports citizen issue reporting, public tracking, staff operations, procurement, organization administration, service-area routing, memberships, roles, and account settings.

## Development rules

- Preserve tenant isolation and explicit permission checks.
- Do not replace database-backed data with hardcoded demo values in templates.
- Keep public pages extending `templates/base.html` and staff pages extending `templates/workspace/base.html`.
- Use existing CivicFlow design tokens and CSS before adding new styles.
- Verify text and control contrast on both light cards and dark workspace surfaces.
- Use POST plus CSRF protection for state-changing actions.
- Use migrations for model changes.
- Run `.venv/bin/python manage.py check` and `git diff --check` after changes.
- Run relevant tests when the PostgreSQL/PostGIS test database is available.

## Important routes

- `/` — public landing page
- `/report/` — citizen issue form
- `/track/` — public issue lookup
- `/workspace/` — staff overview
- `/reports/` — staff issue operations with filters
- `/procurement/tenders/` — procurement workspace
- `/workspace/organizations/` — organizations
- `/workspace/organizations/service-areas/` — service-area directory
- `/workspace/organizations/memberships/` — membership directory
- `/workspace/access/roles/` — roles and policies
- `/workspace/profile/settings/` — account settings
- `/password-change/` — password change

## UI conventions

Staff workspace pages use a dark navigation shell with readable cards, visible action buttons, responsive filters, and explicit empty states. The workspace header contains search, an Overview-only Invite staff action, and an account avatar dropdown with Profile, Settings, and Sign out.

Reports should use the operations layout from `civicflow_screens/screens/reports.html`: search, category/status/service-area filters, a New report action, and rows showing reference, category, area, status, age, and Open.

Service areas represent PostGIS WGS 84 multipolygon boundaries used to validate and route issue locations. Prefer a map drawing interaction; do not ask administrators to enter raw coordinates when a map editor is available.

Roles and policies are database-backed. Capabilities are assigned through role forms and displayed as Granted or Not granted. Avoid decorative controls that do not submit changes.

## Reference screens

The visual references are in `civicflow_screens/screens/`. When implementing a screen, compare the matching reference with the Django template and preserve the intended information hierarchy while replacing static sample values with context data.

## Demo data

`python manage.py seed_demo` creates the administrator account `admin@northbridge.gov` with password `DemoPass123!` and Northbridge demonstration data. Never use demo credentials in production.
