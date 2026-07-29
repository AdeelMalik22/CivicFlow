# Product Requirements Document: CivicFlow

**Product:** CivicFlow — Public Infrastructure Transparency Platform

**Version:** 1.1

**Status:** Draft for stakeholder review

**Document owner:** Product

**Last updated:** 29 July 2026

---

## 1. Executive Summary

CivicFlow is a multi-tenant platform for managing public infrastructure issues from citizen report through verified completion and payment. It gives citizens a simple reporting and tracking experience while giving government departments, contractors, inspectors, finance teams, and auditors one controlled workflow and a shared audit trail.

The first release focuses on small-to-medium public works that can be reported, tendered, completed, inspected, and paid through a standard workflow. Examples include pothole repairs, damaged streetlights, blocked drains, broken sidewalks, and minor public-building repairs.

## 2. Problem and Opportunity

Public infrastructure work is often coordinated through disconnected phone calls, paper records, spreadsheets, and informal messages. As a result:

- Citizens cannot reliably see whether a reported issue is being addressed.
- Government teams lack a consistent method for prioritization, ownership, and escalation.
- Procurement decisions and project changes are difficult to trace.
- Contractors receive inconsistent instructions and evidence requirements.
- Inspectors and finance teams may not share the same completion records.
- Leaders and auditors cannot easily compare delivery time, cost, and quality.

CivicFlow creates a single system of record with explicit ownership, controlled state transitions, evidence-based approvals, and role-appropriate transparency.

## 3. Product Vision

Every eligible public infrastructure issue should have a visible owner, a traceable decision history, and verifiable evidence from report to resolution.

### 3.1 Goals

| Goal | Desired outcome |
| --- | --- |
| Simple reporting | Citizens can submit a complete issue report in a few minutes |
| Predictable operations | Government staff manage work through standardized stages and service targets |
| Fair procurement | Qualified contractors compete through a consistent, auditable process |
| Verified quality | Completion requires documented evidence and independent inspection |
| Financial control | Payment cannot be approved before required operational checks |
| Public trust | Citizens can see meaningful progress without exposing restricted information |
| Accountability | Material actions and decisions are attributable and tamper-evident |

### 3.2 Non-goals for the MVP

The MVP will not:

- Replace a government accounting, treasury, or bank-payment system.
- Support emergency dispatch or life-safety incident response.
- Automate contractor selection or approve payments without a human decision.
- Manage large capital projects with complex bills of quantities or multi-year schedules.
- Provide native mobile applications, drone inspection, or predictive AI.
- Guarantee that every internal document or procurement detail is publicly visible.

## 4. Users and Needs

| Role | Primary need |
| --- | --- |
| Citizen | Report an issue easily and understand what happens next |
| Government Officer | Validate, classify, prioritize, assign, or reject incoming reports |
| Department Manager | Approve procurement decisions, budgets, and material changes |
| Procurement Officer | Configure tenders, evaluate compliant bids, and record an award recommendation |
| Contractor | Discover eligible work, submit bids, and provide progress and completion evidence |
| Inspector | Evaluate completed work against defined criteria and request rework when necessary |
| Finance Officer | Confirm prerequisites and record payment approval or rejection |
| Auditor | Review records, evidence, decisions, and audit history without changing them |
| System Administrator | Manage tenants, users, roles, configuration, and reference data |

One user may hold multiple roles when permitted by organizational policy. The platform must prevent users from approving their own restricted actions where segregation-of-duties rules apply.

## 5. Assumptions and Constraints

- Each government organization or region is a tenant with logically isolated data.
- Every issue belongs to one responsible department before procurement begins.
- Only verified contractor organizations may bid.
- Tender publication and award policies vary by tenant and must be configurable.
- CivicFlow records payment workflow status and external transaction references; funds move through an external financial system.
- Public users may track an issue without seeing personal information, confidential bids, internal notes, or restricted documents.
- Email is required for the MVP. SMS and push notifications depend on later integrations.

## 6. MVP Scope

### 6.1 Included

1. Authentication, tenant isolation, and role-based access control
2. Citizen issue submission and public tracking
3. Issue triage, duplicate handling, prioritization, assignment, and decision history
4. Tender creation, publication, bid submission, evaluation, and award
5. Contract summary, milestones, and approved change records
6. Contractor progress and completion evidence
7. Inspection, rejection, rework, and reinspection
8. Payment approval status and external payment reference
9. In-app and email notifications
10. Operational dashboards, exports, and audit logs

### 6.2 Deferred

- Native iOS and Android applications
- Offline-first inspections
- Automated duplicate, cost, fraud, or image analysis
- GIS asset-management-system synchronization
- Drone imagery
- Public open-data and developer APIs
- Multi-currency contracts and advanced tax calculations
- Direct bank or treasury payment initiation

## 7. End-to-End Lifecycle

```text
Submitted
  → Under Review
    → Rejected
    → Duplicate (linked to canonical issue)
    → Approved
      → Tender Draft
        → Tender Open
          → Tender Closed
            → Evaluation
              → No Award / Retender
              → Awarded
                → Work In Progress
                  → Completion Submitted
                    → Rework Required → Work In Progress
                    → Inspection Approved
                      → Payment Pending
                        → Payment Approved
                          → Payment Recorded
                            → Closed
```

A cancelled state may be entered by an authorized user from eligible stages. Cancellation requires a reason and remains visible in the audit history.

### 7.1 State-transition rules

- Only authorized roles may transition a record.
- Every rejection, cancellation, rework request, award, and payment decision requires a reason.
- The system records actor, timestamp, previous state, new state, and supplied reason.
- Closed and cancelled records are read-only except for authorized administrative corrections, which must create a new audit entry.
- Public status labels may be simpler than internal workflow states but must never misrepresent progress.

## 8. Functional Requirements

Priority uses **Must**, **Should**, and **Could** for MVP release planning.

### 8.1 Identity, Access, and Administration

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-IAM-01 | Must | Users can authenticate through a secure account flow; privileged roles require MFA. |
| FR-IAM-02 | Must | Administrators can invite, activate, suspend, and assign tenant-scoped roles to users. |
| FR-IAM-03 | Must | Access is denied by default and granted through explicit permissions. |
| FR-IAM-04 | Must | Tenant data is isolated in application queries, exports, attachments, and administrative actions. |
| FR-IAM-05 | Must | Configurable segregation-of-duties rules prevent prohibited self-approval. |

### 8.2 Citizen Reporting and Tracking

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-ISS-01 | Must | A citizen can submit a category, description, map location, contact preference, and up to 5 image attachments. |
| FR-ISS-02 | Must | The system validates required fields, accepted file types, file size, and that the location falls within a supported service area. |
| FR-ISS-03 | Must | On submission, the system creates a unique reference and sends confirmation. |
| FR-ISS-04 | Must | A citizen can view the public timeline using an authenticated account or a reference-plus-verification flow. |
| FR-ISS-05 | Must | Public views exclude personal information, internal notes, confidential bid data, and restricted attachments. |
| FR-ISS-06 | Should | A citizen can add clarifying information while an issue is under review. |
| FR-ISS-07 | Should | A citizen can provide a satisfaction rating after closure. |

### 8.3 Triage and Issue Management

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-TRI-01 | Must | Officers can filter and assign submitted issues by department, category, location, priority, owner, age, and status. |
| FR-TRI-02 | Must | Officers can approve, reject, request clarification, or mark a report as a duplicate. |
| FR-TRI-03 | Must | A duplicate is linked to one canonical issue; its reporter continues to receive public updates from that issue. |
| FR-TRI-04 | Must | Approval requires category, responsible department, priority, scope summary, and target response date. |
| FR-TRI-05 | Must | Rejection requires selection of a reason and a citizen-safe explanation. |
| FR-TRI-06 | Should | The system warns reviewers about possible duplicates based on category and location; the reviewer makes the final decision. |
| FR-TRI-07 | Should | Overdue records are visibly flagged and included in escalation notifications. |

### 8.4 Tendering and Bidding

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-TEN-01 | Must | Authorized staff can create a tender with scope, eligibility rules, evaluation method, required documents, budget visibility, milestones, and opening/closing times. |
| FR-TEN-02 | Must | Only approved tenders can be published, and material edits after publication create a version and notify participating contractors. |
| FR-TEN-03 | Must | Verified contractors can submit or replace a bid before the deadline. |
| FR-TEN-04 | Must | Submitted bid contents remain unavailable to competing contractors. |
| FR-TEN-05 | Must | Late submissions are blocked using server time; withdrawn and replaced bids remain auditable. |
| FR-TEN-06 | Must | Evaluators can record compliance checks, criterion scores, notes, conflicts of interest, and an award recommendation. |
| FR-TEN-07 | Must | An authorized manager can approve an award or return it with a reason. |
| FR-TEN-08 | Must | The award record stores the selected bid, decision rationale, approvers, and timestamps. |
| FR-TEN-09 | Should | Contractors receive tender publication, amendment, deadline, and outcome notifications. |

### 8.5 Contract and Work Progress

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-WRK-01 | Must | An award creates a contract record containing parties, price, dates, scope, milestones, and evidence requirements. |
| FR-WRK-02 | Must | Contractors can submit timestamped progress updates with notes and attachments against a milestone. |
| FR-WRK-03 | Must | Completion submission requires all mandatory evidence and a contractor declaration. |
| FR-WRK-04 | Must | Each uploaded file stores uploader, capture/upload time, checksum, and associated record. |
| FR-WRK-05 | Must | Authorized staff can record approved scope, time, or cost changes without overwriting the original contract. |
| FR-WRK-06 | Should | Images can include capture location and time when device metadata and user permission are available. |

### 8.6 Inspection and Rework

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-INS-01 | Must | An inspector can view the contract scope, milestones, completion evidence, and applicable checklist. |
| FR-INS-02 | Must | The inspector records checklist results, notes, attachments, and an approve or rework decision. |
| FR-INS-03 | Must | A rework decision identifies failed criteria, required corrective action, and a target date. |
| FR-INS-04 | Must | Contractors can resubmit completion after rework, preserving every inspection attempt. |
| FR-INS-05 | Must | Inspection approval is blocked until all mandatory checklist items and evidence are complete. |
| FR-INS-06 | Should | Managers can reassign an inspection with a documented reason. |

### 8.7 Payment Control

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-PAY-01 | Must | Payment approval is unavailable until inspection is approved and required contract documents are present. |
| FR-PAY-02 | Must | Finance can approve, reject, or return a payment request and must record a reason for non-approval. |
| FR-PAY-03 | Must | The system records amount, currency, approval chain, external financial-system reference, and payment-recorded date. |
| FR-PAY-04 | Must | The user who submits a payment request cannot approve it when segregation of duties is enabled. |
| FR-PAY-05 | Should | Partial or milestone payments are supported when enabled by tenant policy. |

### 8.8 Notifications

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-NOT-01 | Must | The system creates in-app and email notifications for assignments, required actions, decisions, tender changes, rework, and payment status changes. |
| FR-NOT-02 | Must | Notifications contain a record reference and safe summary but do not expose restricted data in email. |
| FR-NOT-03 | Should | Users can configure non-mandatory notification preferences. |
| FR-NOT-04 | Should | Failed notification deliveries are retried and visible to administrators. |

### 8.9 Reporting, Transparency, and Audit

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-REP-01 | Must | Authorized users can view operational dashboards filtered by tenant, department, category, location, owner, contractor, status, and date range. |
| FR-REP-02 | Must | Authorized users can export filtered tabular data in CSV format, subject to their permissions. |
| FR-REP-03 | Must | Public users can view counts, status, general location, category, key dates, contractor after award, and approved project value where policy permits. |
| FR-AUD-01 | Must | The audit log records authentication events and material create, update, transition, approval, export, and administrative actions. |
| FR-AUD-02 | Must | Audit records include actor, tenant, action, target, timestamp, and before/after values where applicable. |
| FR-AUD-03 | Must | Application users cannot edit or delete audit records. |
| FR-AUD-04 | Must | Auditors can search and export audit records without changing operational data. |

## 9. Key Acceptance Scenarios

### 9.1 Submit and track an issue

**Given** a citizen selects a supported location and supplies all required fields

**When** the report is submitted

**Then** the system creates exactly one issue, assigns a unique reference, shows confirmation, records an audit event, and sends a notification without exposing personal data publicly.

### 9.2 Handle a duplicate

**Given** an officer identifies a new report as the same real-world issue as an existing report

**When** the officer marks it as duplicate

**Then** the duplicate links to the canonical issue, retains its original report and reporter, displays an explanation, and follows public updates from the canonical issue.

### 9.3 Enforce a tender deadline

**Given** a verified contractor has prepared a valid bid

**When** the contractor submits before the server-side deadline

**Then** the bid is timestamped and accepted; submission at or after the deadline is rejected and audited.

### 9.4 Require rework

**Given** a contractor submits completion evidence

**When** an inspector fails one or more required checklist items

**Then** inspection approval is blocked, a rework record is created with corrective actions, and the contractor is notified.

### 9.5 Prevent premature payment

**Given** a project does not have an approved inspection

**When** any user attempts to approve payment

**Then** the system denies the transition, explains the missing prerequisite, and records the attempt where required by audit policy.

### 9.6 Protect restricted information

**Given** a public or unauthorized user opens a project page or export

**When** the system returns project information

**Then** personal details, internal notes, confidential bids, and restricted attachments are omitted.

## 10. Permissions and Separation of Duties

| Capability | Citizen | Officer | Procurement | Manager | Contractor | Inspector | Finance | Auditor | Admin |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Submit issue | ✓ |  |  |  |  |  |  |  |  |
| Triage issue |  | ✓ |  | ✓ |  |  |  | View | Config |
| Create/manage tender |  |  | ✓ | ✓ |  |  |  | View | Config |
| Submit bid |  |  |  |  | ✓ |  |  |  |  |
| Approve award |  |  |  | ✓ |  |  |  | View |  |
| Submit work evidence |  |  |  |  | ✓ |  |  | View |  |
| Approve inspection |  |  |  |  |  | ✓ |  | View |  |
| Approve/record payment |  |  |  |  |  |  | ✓ | View |  |
| View audit trail | Own | Assigned | Assigned | Tenant | Own | Assigned | Assigned | ✓ | ✓ |
| Manage users/configuration |  |  |  |  |  |  |  |  | ✓ |

Exact permissions are tenant-configurable within platform-enforced safety constraints. “Own,” “Assigned,” and “Tenant” indicate data scope, not unrestricted access.

## 11. Data Model

### 11.1 Core entities

- Tenant, Department, Service Area
- User, Role, Permission, User Role
- Issue, Issue Attachment, Location, Duplicate Link, Issue Status Event
- Contractor Organization, Contractor Verification
- Tender, Tender Version, Eligibility Rule, Bid, Bid Document
- Evaluation, Evaluation Criterion, Award Decision
- Contract, Milestone, Contract Change
- Progress Update, Evidence File
- Inspection, Checklist, Checklist Result, Rework Request
- Payment Request, Payment Decision, External Payment Reference
- Notification, Comment, Audit Event

### 11.2 Data rules

- Operational records use stable unique identifiers and tenant ownership.
- Timestamps are stored in UTC and displayed in the tenant or user timezone.
- Monetary values store amount and ISO currency code using fixed-precision decimals.
- Status history and decisions are append-only.
- Attachments are malware-scanned and access-controlled before download.
- Personal data is collected only when required for service delivery and is not included in public records.

## 12. Non-Functional Requirements

| Area | Requirement |
| --- | --- |
| Availability | Production service target of 99.9% monthly uptime, excluding announced maintenance |
| Performance | 95% of standard API reads complete within 500 ms and writes within 1 second under agreed normal load, excluding large uploads and third-party latency |
| Scale baseline | Support at least 100,000 issues per tenant, 5,000 active internal users, and 500 concurrent sessions; validate final targets through capacity planning |
| Security | TLS in transit, encryption at rest, least privilege, MFA for privileged roles, secure secret management, rate limiting, and OWASP-aligned controls |
| Privacy | Configurable retention, consent/notice where required, data-subject handling, export controls, and redaction of public views |
| Auditability | Material actions are attributable, timestamped, searchable, exportable, and protected against application-level modification |
| Accessibility | Citizen and staff web experiences conform to WCAG 2.2 AA for supported journeys |
| Resilience | Automated backups, documented restore procedure, target RPO of 24 hours and RTO of 4 hours for MVP |
| Compatibility | Responsive support for the latest two major versions of Chrome, Edge, Firefox, and Safari |
| Localization | UI architecture supports translated strings, locale-aware dates/numbers, and right-to-left layouts |
| Observability | Centralized logs, metrics, tracing for critical workflows, and alerts for availability, errors, queue backlog, and failed integrations |
| API | Versioned REST API with documented authentication, authorization, validation, pagination, filtering, and error formats |

## 13. Success Metrics

Final targets must be agreed after a baseline measurement or pilot.

| Metric | Definition | Initial target |
| --- | --- | --- |
| Complete-report rate | Reports submitted without staff requesting basic missing information ÷ submitted reports | ≥ 80% |
| Time to first decision | Median time from submission to approval, rejection, clarification, or duplicate decision | ≤ 2 business days |
| On-time triage rate | Issues receiving a first decision within the configured service target | ≥ 90% |
| On-time project completion | Closed projects completed by the approved contract date ÷ closed projects | ≥ 80% |
| First-pass inspection rate | Completion submissions approved on first inspection ÷ inspected submissions | Establish baseline, then improve |
| Payment processing time | Median time from inspection approval to payment approval | ≤ 5 business days |
| Citizen satisfaction | Average post-closure rating on a 5-point scale, with response count shown | ≥ 4.0 |
| Public tracking adoption | Track-page visits or notification subscribers ÷ submitted reports | Establish baseline |
| Audit completeness | Sampled material actions with actor, timestamp, and decision context | 100% |
| Platform reliability | Monthly uptime measured at public and authenticated entry points | ≥ 99.9% |

Metrics must be segmented by department, category, region, and time period where sample sizes permit. Dashboards must display denominator and reporting period to avoid misleading comparisons.

## 14. Dependencies

- Government identity and contractor-verification processes
- Tenant procurement, publication, retention, and public-disclosure policies
- Email delivery provider
- Object storage and malware-scanning service
- Mapping/geocoding and service-area boundary data
- External financial system identifiers or integration method
- Agreed issue categories, inspection checklists, and service targets

## 15. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Public transparency exposes personal or commercially sensitive data | Define public-field policy, classify attachments, redact by default, and test authorization |
| Users move work back to informal channels | Keep required workflows concise, provide notifications and dashboards, and involve operational users in pilot design |
| Poor location or image data reduces report quality | Validate service areas, provide capture guidance, and allow staff clarification |
| Duplicate reports distort workload and citizen experience | Link duplicates to a canonical issue while retaining reporters and subscriptions |
| Tender rules differ across departments | Use configurable templates and approval rules while preserving mandatory audit controls |
| Inspectors or approvers face conflicts of interest | Require declarations, enforce reassignment and separation-of-duties policies |
| Uploaded files contain malware or fabricated metadata | Scan files, preserve checksums, restrict file types, and treat metadata as supporting—not conclusive—evidence |
| Integration failure blocks operations | Use retryable jobs, visible failure states, reconciliation reports, and documented manual fallback |

## 16. Release Plan

### Phase 1 — Foundation and issue management

Identity, tenant configuration, citizen reporting, triage, public tracking, notifications, and audit foundation.

### Phase 2 — Procurement and delivery

Contractor verification, tenders, bidding, evaluation, awards, contracts, milestones, and progress evidence.

### Phase 3 — Inspection, payment control, and reporting

Inspection and rework, payment status, operational dashboards, exports, hardening, and pilot readiness.

### MVP release criteria

- All Must requirements pass acceptance testing.
- No unresolved critical or high-severity security vulnerabilities.
- Authorization and tenant-isolation tests cover all protected endpoints and file access.
- Backup restoration and audit export are successfully exercised.
- Accessibility review covers the citizen-reporting and core staff workflows.
- Monitoring, incident response, support ownership, and rollback procedures are documented.
- Pilot stakeholders approve configured categories, permissions, checklists, notification templates, and public fields.

## 17. Open Decisions

| Decision | Owner | Needed by |
| --- | --- | --- |
| Which jurisdiction and issue categories are included in the pilot? | Sponsor / Product | Before solution design |
| Are anonymous reports allowed, and how are they verified or rate-limited? | Policy / Legal | Before citizen-flow sign-off |
| Which tender data becomes public, and at what stage? | Procurement / Legal | Before tender implementation |
| What monetary thresholds determine approval steps? | Finance / Procurement | Before workflow configuration |
| Are partial payments required in the MVP? | Finance / Product | Before payment implementation |
| What are the retention periods for reports, bids, evidence, and audit records? | Legal / Records | Before production readiness |
| Which map, geocoding, email, identity, and finance integrations are available? | Architecture | Before technical design |
| What are the validated volume, concurrency, RPO, and RTO targets? | Architecture / Operations | Before load and recovery testing |

## Appendix A: Indicative Technology Direction

Technology choices should be confirmed through architecture review and are not product requirements.

| Layer | Candidate technology |
| --- | --- |
| Backend | Django and Django REST Framework |
| Database | PostgreSQL with PostGIS |
| Background jobs / cache | Celery and Redis |
| File storage | S3-compatible object storage |
| Web frontend | React |
| Mapping | OpenStreetMap-compatible provider |
| Authentication | Standards-based identity provider, short-lived tokens, and MFA |
| Monitoring | OpenTelemetry-compatible telemetry, Prometheus, and Grafana |

## Appendix B: Glossary

| Term | Meaning |
| --- | --- |
| Canonical issue | The primary issue record to which duplicate reports are linked |
| Evidence | An attachment or structured record supporting progress, completion, inspection, or payment |
| Material action | A change that affects status, ownership, scope, cost, decision, access, or public visibility |
| Public status | A citizen-safe representation of internal workflow progress |
| Tenant | A government organization or jurisdiction whose users and data are logically isolated |
