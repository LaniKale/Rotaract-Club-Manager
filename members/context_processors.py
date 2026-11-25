def pending_applications(request):
    """Number of membership applications waiting, shown in the menu for executives who can add members."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated or not user.has_perm('members.add_clubmember'):
        return {}
    from .models import MembershipApplication
    return {'pending_applications':
            MembershipApplication.objects.filter(status=MembershipApplication.STATUS_PENDING).count()}
