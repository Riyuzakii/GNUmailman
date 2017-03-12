# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals

from django.db import migrations, models


def move_timezone_to_django_mailman3(apps, schema_editor):
    HKProfile = apps.get_model("hyperkitty", "Profile")
    DMProfile = apps.get_model("django_mailman3", "Profile")
    for hk_profile in HKProfile.objects.all():
        dm_profile, _created = DMProfile.objects.get_or_create(
            user=hk_profile.user)
        dm_profile.timezone = hk_profile.timezone
        dm_profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0007_allauth_20160808_1604'),
        ('django_mailman3', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(move_timezone_to_django_mailman3),
        migrations.RemoveField(
            model_name='profile',
            name='timezone',
        ),
    ]
