"""Give the new "Reset member passwords" permission to the existing President and
Secretary roles, so they keep the ability after this update. Other roles can be
given it on the Roles screen."""
from django.contrib.auth.management import create_permissions
from django.db import migrations

ROLES = ['President', 'Secretary']


def grant(apps, schema_editor):
    # The permission is normally created after migrations finish; create it now.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    perm = Permission.objects.get(content_type__app_label='members', codename='reset_member_password')
    for group in Group.objects.filter(name__in=ROLES):
        group.permissions.add(perm)


class Migration(migrations.Migration):
    dependencies = [('members', '0004_alter_clubmember_options'), ('auth', '0012_alter_user_first_name_max_length'),
                    ('contenttypes', '0002_remove_content_type_name')]
    operations = [migrations.RunPython(grant, migrations.RunPython.noop)]
