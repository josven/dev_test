# -*- coding: utf-8 -*-

from django.contrib import admin
from models import Feed
from models import MailingLists
from models import AccountLead
from models import ExternalApi


class ExternalApiAdmin(admin.ModelAdmin):
    list_display = ('name', 'endpoint',)


class FeedAdmin(admin.ModelAdmin):
    list_display = ('name',)


class MailingListsAdmin(admin.ModelAdmin):
    list_display = ('name',)


class AccountLeadAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'country', 'lead',
                    'tr_referral',)
    fieldsets = (
        (None, {
            'fields': ('email', 'lead', 'mailing_lists', 'external_api')
        }),
        ('Personal', {
            'fields': ('first_name', 'last_name', 'phone', 'gender',
                       'birth_date', 'city', 'street_number', 'zipcode',
                       'country',)
        }),
        ('More', {
            'fields': ('tr_input_method', 'tr_ip_address', 'tr_language',
                       'tr_referral', 'utm_campaign', 'utm_medium',
                       'utm_source',)
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'tr_ip_address':
            kwargs['initial'] = kwargs['request'].META['REMOTE_ADDR']
        return super(AccountLeadAdmin, self).formfield_for_dbfield(
            db_field, **kwargs)

admin.site.register(ExternalApi, ExternalApiAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(MailingLists, MailingListsAdmin)
admin.site.register(AccountLead, AccountLeadAdmin)
