from datetime import timedelta
from decimal import Decimal
import random

from django.contrib.gis.geos import MultiPolygon, Polygon, Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User, TenantRole, MembershipRole
from apps.contractors.models import ContractorApplication
from apps.issues.models import Issue, IssueStatusEvent
from apps.procurement.models import Tender, Bid, Award, ProcurementAuditEvent
from apps.tenants.models import Tenant, Department, ServiceArea, TenantMembership


class Command(BaseCommand):
    help = "Create realistic CivicFlow demo data."

    def handle(self, *args, **options):
        random.seed(42)
        admin, _ = User.objects.get_or_create(email="admin@northbridge.gov", defaults={"first_name": "Amara", "last_name": "Khan", "is_staff": True, "is_superuser": True})
        admin.is_staff = admin.is_superuser = True
        admin.set_password("DemoPass123!")
        admin.save()
        users = [admin]
        for i in range(1, 10):
            user, _ = User.objects.get_or_create(email=f"user{i}@northbridge.gov", defaults={"first_name": ["Aisha", "Omar", "Maya", "Daniel", "Fatima"][i % 5], "last_name": "Demo", "email_verified": True, "cnic": f"42101-{i:05d}-1"})
            user.set_password("DemoPass123!"); user.save(update_fields=("password",))
            users.append(user)
        tenant, _ = Tenant.objects.get_or_create(slug="northbridge", defaults={"name": "Northbridge Council", "status": Tenant.Status.ACTIVE, "contact_email": "contact@northbridge.gov"})
        departments = [Department.objects.get_or_create(tenant=tenant, code=code, defaults={"name": name})[0] for code, name in (("ROADS", "Roads & Drainage"), ("PARKS", "Parks & Public Space"), ("WORKS", "Public Works"))]
        boundary = MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)), srid=4326)
        area, _ = ServiceArea.objects.get_or_create(tenant=tenant, code="CENTRAL", defaults={"name": "Central District", "boundary": boundary})
        for user in users:
            TenantMembership.objects.get_or_create(tenant=tenant, user=user, defaults={"status": TenantMembership.Status.ACTIVE, "department": departments[user.pk % len(departments)]})
        for i in range(100):
            issue, created = Issue.objects.get_or_create(reference=f"CF-DEMO-{i+1:04d}", defaults={"tenant": tenant, "service_area": area, "reporter": users[(i % 9) + 1], "category": random.choice(Issue.Category.values), "description": f"Demo infrastructure report {i+1}: maintenance required in the service area.", "location": Point(0.1 + random.random() * .8, 0.1 + random.random() * .8, srid=4326), "status": random.choice(Issue.Status.values), "tracking_token_hash": "demo"})
            if created: IssueStatusEvent.objects.create(issue=issue, status=issue.status, public_message="Demo status update")
        for i in range(12):
            tender, _ = Tender.objects.get_or_create(reference=f"TN-DEMO-{i+1:03d}", defaults={"title": f"Northbridge works package {i+1}", "description": "Demo procurement opportunity for public infrastructure delivery.", "published": True, "deadline": timezone.now() + timedelta(days=7 + i), "created_by": admin})
            for user in users[1:6]:
                Bid.objects.get_or_create(tender=tender, contractor=user, defaults={"amount": Decimal(10000 + i * 500), "proposal": "Demo bid proposal", "document": "demo/bid.pdf"})
        self.stdout.write(self.style.SUCCESS("Seeded demo users, tenant data, 100 reports, tenders, and bids. Password: DemoPass123!"))
