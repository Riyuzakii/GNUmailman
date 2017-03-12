# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals, print_function

from django.db import migrations, models, IntegrityError, connection, utils


PROVIDERS_MAP = {
    "fedora": "fedora",
    "yahoo": "openid",
}


def populate_emailaddress(apps, schema_editor):
    # All current users have verified their email. Populate the EmailAddress
    # and mark is as such.
    User = apps.get_model("auth", "User")
    EmailAddress = apps.get_model("account", "EmailAddress")
    for user in User.objects.all():
        if not EmailAddress.objects.filter(email=user.email).exists():
            EmailAddress.objects.create(
                email=user.email, user=user,
                verified=True, primary=True,
                )


def migrate_social_users(apps, schema_editor):
    # Migrate the Social Auth association to AllAuth
    SocialAccount = apps.get_model("socialaccount", "SocialAccount")
    # We can't use the UserSocialAuth model because the social_auth app has
    # been removed, and thus the model isn't available.
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT 1 from social_auth_usersocialauth")
    except (utils.OperationalError, utils.ProgrammingError):
        # No social_auth table, stop here.
        return
    for provider_old, provider_new in PROVIDERS_MAP.items():
        cursor.execute("""
            SELECT uid, user_id, last_login, date_joined
            FROM social_auth_usersocialauth usa
            JOIN auth_user ON usa.user_id = auth_user.id
            WHERE provider = %s
            """, (provider_old,))
        for row in cursor:
            uid, user_id, last_login, date_joined = row
            if not SocialAccount.objects.filter(
                    provider=provider_new, uid=uid).exists():
                SocialAccount.objects.create(
                        provider=provider_new,
                        uid=uid,
                        user_id=user_id,
                        last_login=last_login,
                        date_joined=date_joined,
                        extra_data={},
                    )


class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0006_thread_on_delete'),
        ('socialaccount', '0003_extra_data_default_dict'),
        ('account', '0002_email_max_length'),
    ]

    operations = [
        migrations.RunPython(populate_emailaddress),
        migrations.RunPython(migrate_social_users),
    ]
