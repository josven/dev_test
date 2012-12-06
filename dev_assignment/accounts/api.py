# -*- coding: utf-8 -*-

from tastypie import fields
from tastypie.resources import ModelResource
from models import AccountLead
from models import MailingLists
from models import Feed


class FeedResource(ModelResource):
    class Meta:
        queryset = Feed.objects.all()
        resource_name = 'tr_referral'
        excludes = ['id']


class MailingListsResource(ModelResource):
    class Meta:
        queryset = MailingLists.objects.all()
        resource_name = 'mailing_lists'


class AccountLeadResource(ModelResource):

    mailing_lists = fields.ToManyField(
        'dev_assignment.accounts.api.MailingListsResource',
        'mailing_lists', full=True)

    tr_referral = fields.ForeignKey(
        'dev_assignment.accounts.api.FeedResource', 'tr_referral', full=True)

    class Meta:
        queryset = AccountLead.objects.all()
        resource_name = 'account_lead'


class AccountLeadExportResource(ModelResource):

    """
    This resource only usage is to export
    resources Account Lead Resources in a
    format provided by an specifications
    """

    def dehydrate(self, bundle):
        bundle.data['ip_address'] = bundle.obj.tr_ip_address
        bundle.data['utm_medium'] = "api"
        bundle.data['mailing_lists'] = bundle.obj.mailing_lists.count()
        bundle.data['tr_referral'] = bundle.obj.tr_referral.name
        del bundle.data['resource_uri']

        return bundle

    class Meta:
        queryset = AccountLead.objects.all()
        resource_name = 'account_lead_export'
        excludes = ['id', 'lead', 'resource_uri', 'tr_language',
                    'utm_campaign', 'utm_source', 'tr_input_method',
                    'tr_ip_address']
