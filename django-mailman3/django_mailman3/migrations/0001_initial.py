# -*- coding: utf-8 -*-

# flake8: noqa

from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import pytz
TIMEZONES = sorted([(tz, tz) for tz in pytz.common_timezones])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timezone', models.CharField(default='', max_length=100, choices=TIMEZONES)),
                ('user', models.OneToOneField(related_name='mailman_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
