from django.db import migrations


def create_boomerang_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Boomerang')


def delete_boomerang_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Boomerang').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0001_site_page_visit'),
    ]

    operations = [
        migrations.RunPython(create_boomerang_group, delete_boomerang_group),
    ]
