# CivicFlow Implementation Plan

**Based on:** CivicFlow PRD v1.1

**Architecture:** Django + Django REST Framework full stack

**Planning horizon:** MVP pilot in approximately 24 weeks

**Status:** Proposed

---

## 1. Recommended Delivery Strategy

Build CivicFlow as a modular Django monolith. Use server-rendered Django templates for the primary web experience and Django REST Framework (DRF) for versioned APIs, integration boundaries, and future mobile clients.

This is the best starting shape for CivicFlow because it:

- keeps authorization, workflow rules, templates, and APIs in one deployable system;
- avoids duplicating business logic between a separate frontend and backend;
- supports rapid delivery with Django forms, templates, and admin;
- preserves a clean API for future native apps and external integrations;
- can be separated into services later only where scale or ownership proves the need.

### 1.1 Frontend approach

- Django templates for pages and layouts
- HTMX for partial updates, filters, modals, inline actions, and workflow transitions
- Alpine.js only for small client-side interactions
- Tailwind CSS or Bootstrap 5 for the design system; select one during project setup
- Accessible progressive enhancement: critical workflows must work without complex JavaScript
- Django forms for validation, using the same domain services as DRF endpoints

Do not make the server-rendered UI call the DRF API over HTTP. Both template views and API views should call the same Python application-service layer.

## 2. Target Architecture

```text
Browser / API client
        |
Reverse proxy / load balancer
        |
Django ASGI application
  ├── Template views + forms + HTMX
  ├── DRF /api/v1 endpoints
  ├── Application services and workflow policies
  ├── Django ORM and domain models
  └── Transactional outbox / background-job dispatch
        |
  ┌─────┼──────────────┬───────────────┐
  |     |              |               |
PostgreSQL/PostGIS   Redis         Object storage
  |                    |               |
Primary records     Celery jobs     Evidence files
                       |
                 Email / integrations
```

### 2.1 Core technology choices

| Concern | Recommended choice |
| --- | --- |
| Runtime | Python 3.12 or a currently supported stable Python release |
| Web framework | Django 5.2 LTS |
| API | Django REST Framework |
| Database | PostgreSQL + PostGIS |
| UI | Django templates + HTMX + Alpine.js |
| Styling | Tailwind CSS or Bootstrap 5 |
| Background work | Celery + Redis |
| File storage | S3-compatible object storage |
| API schema | drf-spectacular / OpenAPI |
| Filtering | django-filter |
| Authentication | Django sessions for web; OIDC-capable identity provider for staff; scoped token authentication for integrations |
| MFA | Identity-provider MFA or django-allauth-compatible flow |
| Observability | Structured logging + OpenTelemetry + Sentry-compatible error monitoring |
| Tests | pytest, pytest-django, factory_boy, Playwright |
| Packaging | `pyproject.toml` with locked dependencies |
| Deployment | Docker images deployed through CI/CD |

The exact third-party packages should be pinned only after compatibility and maintenance review.

## 3. Architectural Principles

1. **Modular monolith first.** Each business capability has a clear Django app boundary.
2. **Thin views and serializers.** Business workflows live in application services, not templates, model `save()` methods, signals, or serializers.
3. **One rule implementation.** Template views, admin actions, jobs, and DRF endpoints call the same policies and services.
4. **Explicit state machines.** State changes occur through named commands such as `approve_issue()` and `submit_completion()`, never arbitrary status edits.
5. **Tenant scope by default.** Every tenant-owned query is scoped before authorization checks.
6. **Database constraints enforce invariants.** Use unique, check, exclusion, and foreign-key constraints where possible.
7. **Audit events are part of the transaction.** A material change and its audit record commit together.
8. **Side effects occur after commit.** Email and integration jobs use `transaction.on_commit()` or a transactional outbox.
9. **Private files by default.** Evidence is served through short-lived authorized URLs, not public object URLs.
10. **Public models are projections.** Public pages expose an explicit allowlist rather than serializing internal records.

## 4. Proposed Django App Structure

```text
civicflow/
  settings/
    base.py
    local.py
    test.py
    production.py
  urls.py
  asgi.py

apps/
  common/          # base models, IDs, shared validation, utilities
  accounts/        # custom user, invitations, role assignments, MFA metadata
  tenants/         # tenants, departments, service areas, tenant configuration
  issues/          # reports, locations, triage, duplicates, public timeline
  contractors/     # contractor organizations and verification
  procurement/     # tenders, versions, bids, evaluations, awards
  contracts/       # contracts, milestones, changes, progress
  inspections/     # checklists, inspections, rework
  payments/        # payment requests, approvals, external references
  evidence/        # attachment metadata, scans, access, checksums
  notifications/   # in-app/email notification delivery and preferences
  audit/           # append-only audit events and export
  reporting/       # dashboards, read models, CSV exports
  api/             # API router, API-wide concerns, version composition

templates/
static/
tests/
```

Keep models within their owning app. Avoid a generic “workflow” app until multiple domains genuinely share a stable abstraction.

## 5. Data and Domain Design

### 5.1 Identity and tenancy

- Create a custom `User` model before the first migration.
- Use UUID primary keys for externally referenced and sensitive records.
- Model tenant membership separately from the user account.
- Assign roles per tenant, not globally.
- Include `tenant_id` on all tenant-owned aggregate roots.
- Add database indexes beginning with `tenant_id` for common tenant-scoped queries.
- Resolve the active tenant from URL/domain and verified membership; never accept an unrestricted tenant ID from the client.

Start with shared-schema multi-tenancy. It is operationally simpler than schema-per-tenant and sufficient if query scoping and tests are rigorous.

### 5.2 Workflow model

For every workflow aggregate:

- define status with `TextChoices`;
- expose allowed transitions through service functions;
- lock records with `select_for_update()` during approval or award decisions;
- check authorization, current state, and prerequisites inside the transaction;
- create an immutable status-history entry;
- create an audit event;
- enqueue notifications after commit;
- use idempotency keys for API commands that may be retried.

### 5.3 Files and evidence

- Store files in object storage and metadata in PostgreSQL.
- Validate extension, MIME type, size, and image dimensions.
- Upload to quarantine, scan asynchronously, then mark available.
- Store a SHA-256 checksum and immutable storage key.
- Strip unsafe metadata from public derivatives while retaining authorized originals where policy allows.
- Use image thumbnails to avoid loading full-resolution evidence in list views.
- Define retention and legal-hold behavior before production.

### 5.4 Audit design

An audit event should contain:

- UUID, tenant, actor, impersonator if applicable;
- action and target type/identifier;
- request/correlation ID;
- timestamp, source IP, and user agent where appropriate;
- reason and workflow transition;
- redacted before/after values;
- hash linkage or equivalent tamper-evidence mechanism.

Audit tables must not be editable through normal application permissions or Django admin.

## 6. API and Web Conventions

### 6.1 URL design

```text
/                         Public landing page
/report/                   Citizen report flow
/track/<reference>/        Citizen-safe tracking
/app/...                   Authenticated server-rendered application
/api/v1/...                Versioned DRF API
/admin/                    Restricted platform administration
/health/live/              Liveness probe
/health/ready/             Readiness probe
```

### 6.2 DRF standards

- Namespaced `/api/v1/` routes
- OpenAPI schema generated and validated in CI
- Consistent pagination, filtering, ordering, and error envelope
- Separate input serializers from output serializers for complex commands
- Explicit permission classes and tenant-filtered querysets
- Throttling for anonymous reporting and public lookup
- Idempotency support for submissions and financial/integration commands
- Optimistic concurrency or version checks for high-conflict edits
- No public API field appears accidentally through `fields = "__all__"`

### 6.3 Web standards

- Session authentication and CSRF protection for browser workflows
- Post/Redirect/Get for non-HTMX form submissions
- HTMX responses return reusable template partials
- Forms show field-level and summary errors
- Status, error, and loading states are screen-reader accessible
- Permission checks occur on the server even when buttons are hidden

## 7. Delivery Phases

The estimate assumes a cross-functional team of approximately:

- 1 product manager or product owner
- 1 designer/researcher, at least part-time
- 1 technical lead
- 2–3 Django engineers
- 1 QA/automation engineer
- DevOps and security support part-time

With fewer engineers, retain the sequence and reduce parallel work rather than weakening foundational controls.

### Phase 0 — Discovery and technical foundation (Weeks 1–3)

**Objectives**

- Confirm pilot jurisdiction, categories, policies, integrations, and public fields.
- Establish the production-grade Django foundation.

**Work**

- Resolve PRD open decisions needed for MVP.
- Map the top six user journeys with pilot stakeholders.
- Define service targets, approval thresholds, retention rules, and segregation-of-duties rules.
- Establish design tokens, accessible page shell, navigation, and form patterns.
- Replace SQLite with PostgreSQL/PostGIS.
- Add custom user model before business migrations.
- Split settings by environment and move secrets to environment configuration.
- Add DRF, schema generation, Celery, Redis, object-storage configuration, and email backend.
- Configure linting, formatting, type checking, tests, pre-commit hooks, Docker, and CI.
- Add health endpoints, structured logs, correlation IDs, and error monitoring.
- Establish deployment environments: local, CI, staging, and production.

**Exit criteria**

- CI builds and tests every change.
- Staging deployment is reproducible.
- Database backup and migration procedure is documented.
- Architecture decision records cover tenancy, authentication, UI, storage, and audit approach.
- Pilot workflow and public-data policy are approved.

### Phase 1 — Tenancy, identity, and authorization (Weeks 4–6)

**Work**

- Tenant, department, service-area, membership, role, and permission models
- Staff invitations, activation, suspension, and password/account flows
- Active-tenant resolution and tenant-scoped managers/querysets
- Permission-policy layer and segregation-of-duties framework
- MFA or external identity-provider integration for privileged users
- Admin configuration screens
- Initial audit-event pipeline

**Exit criteria**

- Cross-tenant isolation tests cover models, views, APIs, exports, and files.
- Each staff role can access only its intended empty-state workspace.
- Privileged accounts enforce MFA in the target environment.

### Phase 2 — Citizen reporting and issue triage (Weeks 7–10)

Deliver the first complete vertical slice:

```text
Citizen submits → officer reviews → citizen tracks decision
```

**Work**

- Issue categories, service areas, report form, map/location capture, and evidence upload
- Reference generation and secure tracking verification
- Staff issue queue with filters, ownership, priority, and age
- Approve, reject, request clarification, and merge-as-duplicate commands
- Canonical issue and follower/update behavior
- Public status projection and timeline
- Email and in-app notification foundation
- SLA flags and basic operational dashboard

**Exit criteria**

- PRD acceptance scenarios 9.1, 9.2, and 9.6 pass end-to-end.
- Anonymous endpoints are rate-limited and abuse-tested.
- Uploaded files pass validation, quarantine, scan, and authorized download.
- Accessibility tests cover report submission and tracking.

### Phase 3 — Contractor and procurement workflow (Weeks 11–15)

**Work**

- Contractor organizations, users, and verification
- Tender drafts, configurable templates, approval, publication, and immutable versions
- Eligibility requirements and tender documents
- Bid draft, validation, submission, replacement, and withdrawal
- Server-side deadline enforcement
- Bid confidentiality and evaluator access
- Compliance checks, evaluation criteria, scoring, conflicts, recommendation, and award approval
- Tender amendment and outcome notifications

**Exit criteria**

- A verified contractor can bid without viewing competitors’ bid data.
- Concurrent submissions and deadline boundaries are tested.
- Published tender changes create versions instead of overwriting history.
- PRD acceptance scenario 9.3 passes end-to-end.
- Award actions enforce manager authorization and segregation rules.

### Phase 4 — Contract delivery and evidence (Weeks 16–18)

**Work**

- Contract creation from award
- Milestones, dates, value, evidence requirements, and contractor declaration
- Progress updates and completion submission
- Scope, schedule, and cost change-control records
- Evidence gallery, thumbnails, checksums, capture metadata, and permissions
- Contractor and government work dashboards

**Exit criteria**

- Original award and contract values remain traceable after changes.
- Completion cannot be submitted with missing mandatory evidence.
- File authorization tests cover every user role and public access.

### Phase 5 — Inspection, rework, and payment control (Weeks 19–21)

**Work**

- Checklist templates and contract-specific inspection checklists
- Inspection assignment, execution, attachments, approval, and rework
- Multiple inspection attempts with immutable history
- Payment request, finance review, approval/return/reject, and external reference
- Optional milestone payment support only if confirmed for MVP
- Transaction locking and duplicate-action protection

**Exit criteria**

- PRD acceptance scenarios 9.4 and 9.5 pass end-to-end.
- Payment approval cannot bypass inspection or document prerequisites.
- The configured initiator/approver separation is enforced.
- Repeated requests cannot create duplicate payment decisions.

### Phase 6 — Reporting, hardening, and pilot launch (Weeks 22–24)

**Work**

- Role-specific dashboards and CSV exports
- Defined success-metric calculations
- Audit search and export
- Performance tuning, database indexes, and query-budget tests
- Security assessment, dependency scan, penetration test, and remediation
- Backup restore, disaster-recovery, and integration-failure exercises
- Accessibility audit and remediation
- Data migration/import tools if required for the pilot
- Support runbooks, training, administrator guide, and pilot onboarding

**Exit criteria**

- Every Must requirement has a passing test or recorded acceptance result.
- No open critical or high-severity security issue.
- Load, recovery, privacy, accessibility, monitoring, and rollback checks pass.
- Product, operations, procurement, finance, and security owners approve release.

## 8. Initial Epic Backlog

| Order | Epic | Primary output | Depends on |
| ---: | --- | --- | --- |
| 1 | Engineering foundation | Reproducible local, CI, staging, and production setup | None |
| 2 | Tenant and department administration | Isolated organizations and service areas | 1 |
| 3 | Identity and authorization | Secure staff and contractor access | 2 |
| 4 | Audit and evidence foundations | Traceable actions and protected files | 2, 3 |
| 5 | Citizen reporting | Valid report with location and evidence | 2, 4 |
| 6 | Issue triage | Decisions, assignment, duplicates, SLAs | 5 |
| 7 | Public tracking | Safe public project timeline | 5, 6 |
| 8 | Notifications | Reliable in-app/email updates | 4–7 |
| 9 | Contractor verification | Eligible bidding organizations | 3 |
| 10 | Tender management | Approved, versioned tender publication | 6, 9 |
| 11 | Bid submission | Confidential, deadline-safe bids | 10 |
| 12 | Evaluation and award | Auditable selection decision | 11 |
| 13 | Contracts and milestones | Award converted into controlled delivery | 12 |
| 14 | Progress and completion evidence | Verifiable contractor delivery | 13 |
| 15 | Inspection and rework | Independent acceptance loop | 14 |
| 16 | Payment control | Verified approval and external reference | 15 |
| 17 | Reporting and exports | Operational and oversight views | All domains |
| 18 | Pilot hardening | Secure, accessible, supportable release | All MVP epics |

## 9. Testing Strategy

### 9.1 Test layers

| Layer | Purpose |
| --- | --- |
| Model and constraint tests | Data invariants, uniqueness, tenant ownership |
| Policy tests | Role, record scope, workflow state, and separation of duties |
| Service tests | Transactions, state transitions, audit creation, side-effect scheduling |
| View/form tests | Server-rendered flows, validation, CSRF, HTMX responses |
| API tests | Authentication, permissions, schema, errors, idempotency |
| Integration tests | PostgreSQL/PostGIS, Redis/Celery, storage, email, identity provider |
| End-to-end tests | Critical citizen, officer, contractor, inspector, and finance journeys |
| Security tests | Tenant isolation, object-level access, upload abuse, rate limits |
| Accessibility tests | Automated checks plus manual keyboard and screen-reader review |
| Performance tests | Critical list pages, public tracking, bid deadline, exports |

### 9.2 Mandatory test rules

- Every state-transition service has happy-path, invalid-state, unauthorized, cross-tenant, and retry/concurrency tests.
- Every endpoint has anonymous, wrong-role, wrong-tenant, and correct-role coverage.
- Public serializers and templates receive dedicated privacy regression tests.
- Tests use PostgreSQL, not SQLite, in CI.
- Celery jobs are tested both synchronously and against a real broker in integration CI.
- Critical browser journeys run on every release candidate.

## 10. Security and Privacy Workstream

Security is continuous rather than a final phase.

- Threat-model citizen submissions, tenant boundaries, bids, evidence, inspections, payments, exports, and admin actions.
- Require secure headers, CSRF, CSP, HTTPS, safe cookies, rate limits, and brute-force protection.
- Avoid long-lived JWTs in browser storage; use secure Django sessions for web users.
- Apply object-level authorization before returning records or signed file URLs.
- Sanitize filenames and never trust client MIME types or image metadata.
- Redact secrets, tokens, personal information, and bid details from logs and audit diffs.
- Review dependencies and container images automatically.
- Establish a vulnerability reporting and incident-response process.
- Run privacy-impact and records-retention reviews before pilot data is loaded.

## 11. DevOps and Environments

### 11.1 CI pipeline

For each change:

1. dependency and secret scan;
2. formatting and lint checks;
3. type checks;
4. Django system and migration checks;
5. unit and integration tests with coverage;
6. OpenAPI schema validation;
7. frontend asset build;
8. container build and vulnerability scan.

For release candidates:

1. deploy to staging;
2. run migrations;
3. run smoke and end-to-end tests;
4. run accessibility and targeted performance tests;
5. require approval;
6. deploy with a documented rollback path.

### 11.2 Production topology

- At least two stateless Django web instances
- Separate Celery worker and scheduler processes
- Managed PostgreSQL with automated backups and point-in-time recovery if available
- Managed Redis with appropriate eviction and persistence settings
- Versioned, encrypted object storage with lifecycle policies
- CDN only for public static assets; evidence remains private
- Centralized logs, metrics, traces, alerts, and uptime checks

## 12. Team Working Agreement

- Use short-lived branches and small reviewed changes.
- Require migration review for schema changes.
- Record material architecture choices as ADRs.
- Define “ready” with acceptance criteria, permission rules, and designs.
- Define “done” as code, tests, documentation, telemetry, accessibility, and stakeholder acceptance.
- Demo a working vertical slice every two weeks.
- Keep feature flags for incomplete or high-risk workflows.
- Do not use Django admin as the operational interface for citizens, officers, contractors, inspectors, or finance staff.

## 13. First Two Sprints

### Sprint 1 — Production-grade foundation

- Confirm architecture and write initial ADRs.
- Upgrade the runtime from the current Python 3.11 release candidate to a stable supported Python version.
- Convert dependency management to `pyproject.toml` and lock dependencies.
- Split settings into base, local, test, and production.
- Add PostgreSQL/PostGIS and configure test databases.
- Create the custom user model.
- Add DRF, API schema, health endpoints, structured logging, and correlation IDs.
- Add pytest, factories, linting, formatting, type checking, and CI.
- Establish the base template and accessible design primitives.
- Create Docker-based local and deployment workflows.

### Sprint 2 — Tenant and authorization skeleton

- Implement tenant, department, service-area, membership, and role models.
- Add active-tenant resolution and tenant-aware query utilities.
- Implement invitation and staff account lifecycle.
- Build permission-policy interfaces.
- Add audit-event creation and request context.
- Add tenant administration screens.
- Add isolation and permission test matrices.
- Deploy the completed slice to staging and perform the first security review.

## 14. Decisions Required Before Development Accelerates

1. Pilot jurisdiction, departments, and issue categories
2. Anonymous versus authenticated citizen reporting
3. Staff authentication provider and MFA ownership
4. Public disclosure rules for location, contractor, price, tender, and evidence
5. Contractor verification process
6. Tender evaluation method and award approval thresholds
7. Partial-payment requirement
8. Retention periods and legal-hold requirements
9. Mapping/geocoding, email, object-storage, malware-scanning, and financial-system providers
10. Expected pilot volumes, concurrent users, and file-storage growth
11. Supported languages and right-to-left requirements
12. Design-system choice: Tailwind CSS or Bootstrap 5

## 15. Recommended Immediate Next Actions

1. Approve or revise the architecture and 24-week delivery sequence.
2. Resolve the decisions in Section 14 with named owners and deadlines.
3. Convert Phase 0 and Phase 1 into two-week sprint tickets.
4. Stabilize the Python/runtime and Django project foundation.
5. Build the tenant-isolation and authorization test harness before business modules.
6. Implement citizen reporting as the first end-to-end product slice.

This sequence deliberately makes tenant isolation, authorization, audit, and secure evidence handling foundational capabilities. Retrofitting them after tender or payment workflows would be significantly riskier.

## 16. Remaining Product Work

The following backlog captures the remaining work identified during implementation and visual review of the reference screens.

### Priority 1 — Complete core workflows

1. **Service-area map editor**
   - Make the OpenLayers map load reliably without depending on an unavailable CDN.
   - Keep the local drawing fallback usable when map assets cannot load.
   - Support drawing, editing, closing, clearing, and validating WGS 84 multipolygon boundaries.
   - Add browser-level tests for submitting and editing boundaries.

2. **Reports operations**
   - Make each Open action resolve directly to the selected report.
   - Add assignment and reassignment workflows.
   - Add pagination, bulk actions, and CSV export where authorized.
   - Preserve search, category, status, and service-area filters in pagination and actions.

3. **Procurement lifecycle**
   - Add tender detail and edit screens.
   - Implement draft, publish, unpublish, close, cancel, and award states.
   - Display budget, location, category, dates, attachments, and evaluation criteria.
   - Validate file type and size and provide attachment download/preview behavior.

### Priority 2 — Administration completeness

4. **Roles and policies**
   - Add clear role-level edit controls.
   - Add safe activate/deactivate or archive behavior.
   - Prevent deactivation of roles required by active memberships without an explicit migration path.
   - Keep capabilities database-backed and editable through the role form rather than decorative matrix controls.

5. **Membership administration**
   - Add visible role assignments in the directory and edit workflow.
   - Add activate, suspend, resend invitation, and confirmation flows.
   - Ensure all membership actions remain tenant-scoped and audited.

6. **Account settings**
   - Replace informational notification and organization-preference cards with persisted settings where those features are approved.
   - Add success/error feedback after profile and password changes.
   - Add session/security visibility and MFA controls when the authentication provider is selected.

### Priority 3 — Quality and release readiness

7. **UI consistency pass**
   - Verify headers, profile dropdowns, buttons, inputs, selects, maps, empty states, and error states across every workspace page.
   - Test desktop, tablet, and mobile layouts.
   - Remove placeholder copy and any static sample data from production templates.
   - Confirm every visible action has a working route and appropriate permission check.

8. **Testing and deployment**
   - Restore PostgreSQL/PostGIS availability and run the full test suite.
   - Add browser tests for critical flows: report, track, tender, membership, role, settings, and service-area boundary creation.
   - Run migrations against a clean database and verify static/media serving.
   - Perform a tenant-isolation, authorization, upload-security, and audit-log review before staging deployment.
