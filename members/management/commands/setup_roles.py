"""
Creates the club's starting roles and their permissions.
Run once after migrating:   python manage.py setup_roles

After that, roles are managed on the Roles screen in the app. Running this
again only fills in roles that are missing; it does not undo changes made on
the Roles screen unless you add --reset.
"""
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from members.roles import DEFAULT_ROLES, set_capabilities


class Command(BaseCommand):
    help = 'Create the starting roles (President, Vice President, Secretary, Treasurer, Member).'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Put the starting roles back to their default permissions.')

    def handle(self, *args, **options):
        for role, capabilities in DEFAULT_ROLES.items():
            group, created = Group.objects.get_or_create(name=role)
            if created or options['reset'] or (capabilities and not group.permissions.exists()):
                set_capabilities(group, capabilities)
                if options['verbosity']:
                    self.stdout.write(f'{role}: {len(capabilities)} capabilities')
        if options['verbosity']:
            self.stdout.write(self.style.SUCCESS('Roles set up.'))
