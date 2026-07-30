from .policies import can


def tenant_access(request):
    tenant = getattr(request, "tenant", None)
    if tenant is None or not request.user.is_authenticated:
        return {"can_administer_tenant": False}
    return {
        "can_administer_tenant": (
            can(request.user, tenant, "configuration.manage")
            or can(request.user, tenant, "users.manage")
        )
    }
