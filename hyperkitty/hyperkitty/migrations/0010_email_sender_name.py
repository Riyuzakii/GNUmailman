# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals

from django.db import migrations, models, connection


def populate_sender_name(apps, schema_editor):
    #Email = apps.get_model("hyperkitty", "Email")
    #for email in Email.objects.only("sender").select_related("sender"):
    #    email.sender_name = email.sender.name
    #    email.save()
    # Don't use the model, use a single UPDATE query, it's much faster.
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE hyperkitty_email SET sender_name = (
            SELECT name FROM hyperkitty_sender
            WHERE address = hyperkitty_email.sender_id LIMIT 1
        )
        """)

def populate_sender_name_reverse(apps, schema_editor):
    Sender = apps.get_model("hyperkitty", "Sender")
    for sender in Sender.objects.all():
        for email_sender_name in sender.emails.order_by(
                "-date").values_list("sender_name", flat=True):
            if email_sender_name:
                sender.name = email_sender_name
                sender.save()
                break


class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0009_duplicate_persona_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='sender_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(
            populate_sender_name, populate_sender_name_reverse),
        migrations.RemoveField(
            model_name='sender',
            name='name',
        ),
    ]
