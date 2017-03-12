# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postorius', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addressconfirmationprofile',
            name='activation_key',
            field=models.CharField(unique=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='addressconfirmationprofile',
            name='created',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='addressconfirmationprofile',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
    ]
