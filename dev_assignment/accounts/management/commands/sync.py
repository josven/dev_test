# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from dev_assignment.accounts.models import ExternalApi


class Command(BaseCommand):

    def handle(self, *args, **options):
        mailing_list = ExternalApi.objects.get(name="mailing list")
        account_lead = ExternalApi.objects.get(name="account lead")

        mailing_list.import_from_extapi()
        account_lead.import_from_extapi()
        print "Sync complete"
