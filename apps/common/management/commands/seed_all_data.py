from datetime import timedelta
from decimal import Decimal
import hashlib
import random

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.accounts.models import (AccessPermission, MembershipRole, RolePermission, SeparationOfDutiesPolicy, SignupOTP, StaffInvitation, TenantRole, User)
from apps.common.models import Project
from apps.contractors.models import ContractorApplication
from apps.issues.models import Issue, IssueAttachment, IssueStatusEvent
from apps.procurement.models import Award, Bid, ProcurementAuditEvent, Tender
from apps.tenants.models import Department, ServiceArea, Tenant, TenantMembership


class Command(BaseCommand):
    help = "Create 100 coherent records for every CivicFlow business model."

    def handle(self, *args, **options):
        fake = Faker("en_US"); Faker.seed(20260731); random.seed(20260731); now = timezone.now()
        boundary = MultiPolygon(Polygon.from_bbox((67.0, 24.7, 67.2, 24.95)), srid=4326)
        admin, _ = User.objects.get_or_create(email="admin@northbridge.gov", defaults={"first_name":"Amara", "last_name":"Khan", "is_staff":True, "is_superuser":True})
        admin.is_staff = admin.is_superuser = True; admin.set_password("DemoPass123!"); admin.save()
        users = [admin]
        for i in range(99):
            user, _ = User.objects.get_or_create(email=f"civic.user{i+1}@northbridge.gov", defaults={"first_name":fake.first_name(), "last_name":fake.last_name(), "phone_number":fake.phone_number()[:32], "cnic":f"42101-{i+1:05d}-1", "address":fake.address()[:255], "email_verified":True})
            user.set_password("DemoPass123!"); user.save(update_fields=("password",)); users.append(user)
        tenants = []
        for i in range(100):
            tenants.append(Tenant.objects.get_or_create(slug=f"civic-district-{i+1}", defaults={"name":f"{fake.city()} District Council", "status":Tenant.Status.ACTIVE, "contact_email":f"contact{i+1}@civic.gov"})[0])
        departments = []; areas = []
        for i, tenant in enumerate(tenants):
            d, _ = Department.objects.get_or_create(tenant=tenant, code="WORKS", defaults={"name":"Public Works"}); departments.append(d)
            a, _ = ServiceArea.objects.get_or_create(tenant=tenant, code="CENTRAL", defaults={"name":"Central Service Area", "description":"Primary public-service boundary.", "boundary":boundary}); areas.append(a)
        permissions = []
        for i in range(100):
            permissions.append(AccessPermission.objects.get_or_create(code=f"civic.capability.{i+1:03d}", defaults={"name":f"{fake.word().title()} operations {i+1:03d}", "description":fake.sentence(), "default_scope":AccessPermission.Scope.TENANT, "is_sensitive":i % 5 == 0})[0])
        roles = []
        for i, tenant in enumerate(tenants):
            role, _ = TenantRole.objects.get_or_create(tenant=tenant, code=f"operations-{i+1:03d}", defaults={"name":f"Operations Officer {i+1:03d}", "description":"Coordinates public infrastructure delivery."}); roles.append(role); RolePermission.objects.get_or_create(role=role, permission=permissions[i], defaults={"scope":AccessPermission.Scope.TENANT})
        memberships = []
        for i, user in enumerate(users):
            tenant = tenants[i % 100]; membership, _ = TenantMembership.objects.get_or_create(tenant=tenant, user=user, defaults={"department":departments[i % 100], "status":TenantMembership.Status.ACTIVE, "invited_by":admin, "activated_at":now}); memberships.append(membership); MembershipRole.objects.get_or_create(membership=membership, role=roles[i % 100], defaults={"assigned_by":admin})
        for i in range(100):
            SeparationOfDutiesPolicy.objects.get_or_create(tenant=tenants[i], name=f"Maker checker policy {i+1:03d}", initiator_permission=permissions[i], approver_permission=permissions[(i+1) % 100])
            StaffInvitation.objects.get_or_create(membership=memberships[i], email=users[i].email, defaults={"invited_by":admin})
            SignupOTP.objects.get_or_create(user=users[i], code_hash=hashlib.sha256(f"{i:06d}".encode()).hexdigest(), defaults={"expires_at":now + timedelta(days=1)})
        issues = []
        for i in range(100):
            issue, _ = Issue.objects.get_or_create(reference=f"CF-LIVE-{i+1:04d}", defaults={"tenant":tenants[i], "service_area":areas[i], "reporter":users[i], "category":random.choice(Issue.Category.values), "description":fake.paragraph(nb_sentences=3), "location":Point(67.02 + random.random()*.16, 24.72 + random.random()*.20, srid=4326), "status":random.choice(Issue.Status.values), "tracking_token_hash":hashlib.sha256(f"tracking-{i}".encode()).hexdigest()}); issues.append(issue); IssueStatusEvent.objects.get_or_create(issue=issue, status=issue.status, defaults={"actor":admin, "public_message":"Status reviewed by the responsible public team."}); IssueAttachment.objects.get_or_create(issue=issue, original_name=f"site-evidence-{i+1:04d}.pdf", defaults={"file":f"seed/issue-evidence-{i+1:04d}.pdf", "checksum":hashlib.sha256(f"evidence-{i}".encode()).hexdigest(), "uploaded_by":users[i]})
        projects = []
        for i in range(100):
            projects.append(Project.objects.get_or_create(tenant=tenants[i], reference=f"PRJ-{i+1:04d}", defaults={"name":f"{fake.city()} {random.choice(['road renewal','drainage upgrade','street lighting'])}", "description":fake.paragraph(), "status":random.choice(Project.Status.values), "budget":Decimal(random.randint(2,80)*100000), "target_date":(now + timedelta(days=random.randint(30,700))).date(), "created_by":admin})[0])
        tenders = []
        for i in range(100):
            tender, _ = Tender.objects.get_or_create(reference=f"TN-LIVE-{i+1:04d}", defaults={"title":f"{fake.city()} infrastructure package", "description":fake.paragraph(nb_sentences=4), "category":random.choice(Tender.Category.values), "procurement_method":random.choice(Tender.Method.values), "department":departments[i], "service_area":areas[i], "budget":Decimal(random.randint(5,100)*100000), "published":i % 4 != 0, "deadline":now + timedelta(days=random.randint(10,180)), "created_by":admin}); tenders.append(tender); Bid.objects.get_or_create(tender=tender, contractor=users[(i+1)%100], defaults={"amount":Decimal(random.randint(2,90)*100000), "proposal":fake.paragraph(), "document":f"seed/bids/bid-{i+1:04d}.pdf"}); ProcurementAuditEvent.objects.get_or_create(tender=tender, action="created", defaults={"actor":admin, "note":"Tender record created for test workflow."})
            if not hasattr(tender, "award"):
                bid = tender.bids.first(); Award.objects.create(tender=tender, winning_bid=bid, awarded_by=admin, decision_note="Award decision recorded for workflow testing.")
        for i in range(100):
            ContractorApplication.objects.get_or_create(applicant=users[(i+1)%100], registration_number=f"REG-LIVE-{i+1:04d}", defaults={"company_name":f"{fake.last_name()} Infrastructure Services", "contact_person":fake.name(), "phone":fake.phone_number()[:32], "cnic_ntn":f"NTN-{i+1:08d}", "category":random.choice(["Road works", "Drainage", "Electrical services"]), "years_experience":random.randint(2,25), "registration_document":f"seed/contractors/registration-{i+1:04d}.pdf", "tax_document":f"seed/contractors/tax-{i+1:04d}.pdf", "cnic_document":f"seed/contractors/cnic-{i+1:04d}.pdf", "status":random.choice(ContractorApplication.Status.values)})
        self.stdout.write(self.style.SUCCESS("Seeded 100 coherent records across every CivicFlow business model. Password: DemoPass123!"))
