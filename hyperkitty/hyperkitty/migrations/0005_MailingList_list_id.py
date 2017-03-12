# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals

from django.db import models, migrations


def populate_list_id(apps, schema_editor):
    MailingList = apps.get_model("hyperkitty", "MailingList")
    for ml in MailingList.objects.filter(list_id=None):
        ml.list_id = ml.name.replace("@", ".")
        ml.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0004_archived_date_and_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailinglist',
            name='list_id',
            field=models.CharField(max_length=254, null=True, unique=True),
        ),
        migrations.RunPython(populate_list_id),
    ]
