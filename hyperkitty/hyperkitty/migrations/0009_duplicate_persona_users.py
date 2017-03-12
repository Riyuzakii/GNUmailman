# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals

from django.db import migrations, models


def remove_duplicate_persona_accounts(apps, schema_editor):
    # Some people logged in using both Persona and the other login options,
    # resulting in duplicate User accounts (with the same email address). In
    # that case, remove the Persona user and move its data over to the other
    # user instance.
    User = apps.get_model("auth", "User")
    SocialAccount = apps.get_model("socialaccount", "SocialAccount")
    Tagging = apps.get_model("hyperkitty", "Tagging")
    Favorite = apps.get_model("hyperkitty", "Favorite")
    LastView = apps.get_model("hyperkitty", "LastView")
    Vote = apps.get_model("hyperkitty", "Vote")
    query = User.objects.exclude(
            id__in=SocialAccount.objects.all().values("user_id"))
    for user in query:
        other_account = User.objects.filter(
                email=user.email
            ).exclude(
                id=user.id
            ).order_by("-last_login").first()
        if other_account is None:
            continue  # Only keep duplicate accounts.
        for tag in Tagging.objects.filter(user=user):
            tag.user = other_account
            tag.save()
        for fav in Favorite.objects.filter(user=user):
            if Favorite.objects.filter(
                    user=other_account, thread=fav.thread).exists():
                fav.delete()  # the other account has priority
            else:
                fav.user = other_account
                fav.save()
        for lv in LastView.objects.filter(user=user):
            if LastView.objects.filter(
                    user=other_account, thread=lv.thread).exists():
                lv.delete()  # the other account has priority
            else:
                lv.user = other_account
                lv.save()
        for vote in Vote.objects.filter(user=user):
            if Vote.objects.filter(
                    user=other_account, email=vote.email).exists():
                vote.delete()  # the other account has priority
            else:
                vote.user = other_account
                vote.save()
        user.delete()




class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0008_django_mailman3_profile'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_persona_accounts),
    ]
