from collections.abc import Callable

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, HttpResponse
from django.urls import Resolver404, resolve

from .request import ACTIVE_TENANT_SESSION_KEY, active_memberships_for, clear_active_tenant


class ActiveTenantMiddleware:
    """Resolve the active tenant from a server-verified membership selection."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.tenant = None
        request.tenant_membership = None

        if request.user.is_authenticated:
            memberships = active_memberships_for(request)
            requested_slug = self._tenant_slug(request)
            selected_public_id = request.session.get(ACTIVE_TENANT_SESSION_KEY)
            membership = None
            if requested_slug:
                membership = memberships.filter(tenant__slug=requested_slug).first()
                if membership is None:
                    raise PermissionDenied(
                        "You do not have an active membership in this organization."
                    )
                request.session[ACTIVE_TENANT_SESSION_KEY] = str(
                    membership.tenant.public_id
                )
            elif selected_public_id:
                try:
                    membership = memberships.filter(
                        tenant__public_id=selected_public_id
                    ).first()
                except (ValidationError, ValueError):
                    membership = None
                if membership is None:
                    clear_active_tenant(request)
            else:
                candidates = list(memberships[:2])
                if len(candidates) == 1:
                    membership = candidates[0]
                    request.session[ACTIVE_TENANT_SESSION_KEY] = str(
                        membership.tenant.public_id
                    )

            if membership is not None:
                request.tenant = membership.tenant
                request.tenant_membership = membership

        return self.get_response(request)

    @staticmethod
    def _tenant_slug(request: HttpRequest) -> str | None:
        try:
            return resolve(request.path_info).kwargs.get("tenant_slug")
        except Resolver404:
            return None
