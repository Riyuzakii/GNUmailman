# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0003_thread_starting_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='archived_date',
            field=models.DateTimeField(default=django.utils.timezone.now, db_index=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='subject',
            field=models.CharField(max_length=512, db_index=True),
        ),
    ]
