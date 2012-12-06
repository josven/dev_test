# -*- coding: utf-8 -*-

import requests
import string
import json
import random
from urlparse import urljoin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.db import models
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


class ExternalApi(models.Model):

    name = models.CharField(max_length=1024)
    endpoint = models.URLField(max_length=1024)
    user_name = models.CharField(max_length=1024)
    api_key = models.CharField(max_length=1024)
    internal_model = models.ForeignKey(ContentType)

    FORMAT_CHOICES = (
        ('json', 'json'),
        ('xml', 'xml'),
        ('yaml', 'yaml'),
    )

    format = models.CharField(max_length=1024, choices=FORMAT_CHOICES)

    class Meta:
        verbose_name = "External API"
        verbose_name_plural = "External API's"

    def __unicode__(self):
        return self.name

    def import_from_extapi(self):

        # Get external resourses
        cache_buster = [random.choice(string.ascii_letters +
                        string.digits) for n in xrange(30)]
        cache_buster = "".join(cache_buster)
        params = {'username': self.user_name, 'api_key': self.api_key,
                  'format': self.format, 'cache_buster': cache_buster}
        r = requests.get(self.endpoint, params=params)
        resourses = r.json['objects']

        # Get model
        model = self.internal_model.model_class()

        # Get all relevant fields
        fields = model._meta.get_all_field_names()

        # Find unique fields
        query_fields = []
        for model_field in model._meta.fields:
            if model_field.unique and not model_field.primary_key:
                query_fields += [model_field.name]

        for resourse in resourses:

            # Remove all unwanted fields
            data = resourse.copy()
            for key in resourse:
                if not key in fields:
                    del data[key]

            # Special case!
            # If some key have a dict of array as value
            # is mean its a f-field or a m2m
            f_resources = []
            l_resources = []

            for key in resourse:
                if type(resourse[key]) == dict:
                    f_resources += [{"key_name": key, "data": data.pop(key)}]
                if type(resourse[key]) == list:
                    l_resources += [{"key_name": key, "data": data.pop(key)}]

            for f_resource in f_resources:

                # Field name
                field_name = f_resource['key_name']

                # Model class
                n_resource_model = getattr(model, field_name).field.rel.to

                # Get relevant fields
                n_fields = n_resource_model._meta.get_all_field_names()

                n_data = f_resource['data'].copy()
                for key in f_resource['data']:
                    if not key in n_fields:
                        del n_data[key]

                m_objects = n_resource_model.objects
                n_old_obj, n_obj = m_objects.get_or_create(**n_data)

                if n_old_obj:
                    data[field_name] = n_old_obj

                if n_obj:
                    data[field_name] = n_obj

            m2m_data = []
            for l_resource in l_resources:

                # Field name
                field_name = l_resource['key_name']

                # Model class
                n_resource_model = getattr(model, field_name).field.rel.to

                # Array of data
                data_array = l_resource['data']

                # Find unique fields
                n_query_fields = []
                for model_field in n_resource_model._meta.fields:
                    if model_field.unique and not model_field.primary_key:
                        n_query_fields += [model_field.name]

                # Get relevant fields
                m_fields = n_resource_model._meta.fields
                n_fields = [field.name for field in m_fields]
                for data_obj in data_array:
                    temp = data_obj.copy()
                    for key in data_obj:
                        if not key in n_fields:
                            del temp[key]
                    data_obj = temp.copy()

                    n_query = {}
                    for field in n_query_fields:
                        n_query[field] = data_obj[field]
                    try:
                        obj = n_resource_model.objects.get(**n_query)
                        obj.__dict__.update(**data_obj)
                    except n_resource_model.DoesNotExist:
                        obj = n_resource_model(**data_obj)

                    obj.save()

                    # Save m2m data to apply this later on the main model
                    m2m_data += [{"field": field_name, "data": obj}]

            # create a query on unique fields and
            # try to get the obj. If it not exist,
            # then create it.
            query = {}
            for field in query_fields:
                query[field] = data[field]

            try:
                obj = model.objects.get(**query)
                obj.__dict__.update(**data)
            except model.DoesNotExist:
                obj = model(**data)

            # Avoid syncing to extapi when saving
            # Dissconnect save signal
            post_save.disconnect(account_lead_post_save_handler,
                                 sender=AccountLead)
            obj.save()
            # Reconnect save signal
            post_save.connect(account_lead_post_save_handler,
                              sender=AccountLead)

            # Dissconnect save signal
            m2m_changed.disconnect(account_lead_m2m_changed_handler,
                                   sender=AccountLead.external_api.through)
            obj.external_api.add(self)
            m2m_changed.connect(account_lead_m2m_changed_handler,
                                sender=AccountLead.external_api.through)

            # Apply m2m data
            for d in m2m_data:
                getattr(obj, d['field']).add(d['data'])


class Feed(models.Model):

    name = models.CharField(max_length=1024, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Feed"
        verbose_name_plural = "Feeds"


class MailingLists(models.Model):

    name = models.CharField(max_length=1024, unique=True)
    external_api = models.ManyToManyField(ExternalApi, blank=True,
                                          related_name='mailing_lists')

    class Meta:
        verbose_name = "Mailing list"
        verbose_name_plural = "Mailing lists"

    def __unicode__(self):
        return self.name


class AccountLead(models.Model):

    birth_date = models.DateTimeField(null=True)
    city = models.CharField(max_length=1024, blank=True)
    country = models.CharField(max_length=1024, default="nl")
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=1024, blank=True)

    GENDER_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    last_name = models.CharField(max_length=1024, blank=True)
    lead = models.BooleanField()
    mailing_lists = models.ManyToManyField(MailingLists)
    phone = models.CharField(max_length=1024, blank=True)
    street_number = models.CharField(max_length=1024, blank=True)
    tr_input_method = models.CharField(max_length=1024, blank=True)
    tr_ip_address = models.GenericIPAddressField()
    tr_language = models.CharField(max_length=1024, blank=True)
    tr_referral = models.ForeignKey(Feed)
    utm_campaign = models.CharField(max_length=1024, blank=True)
    utm_medium = models.CharField(max_length=1024, blank=True)
    utm_source = models.CharField(max_length=1024, blank=True)
    zipcode = models.CharField(max_length=1024, blank=True)
    external_api = models.ManyToManyField(ExternalApi, blank=True,
                                          related_name='accounts')

    class Meta:
        verbose_name = "Account lead"
        verbose_name_plural = "Account leads"

    def prepare_resource_for_export(self):
        """ Return a dict

        Take advatage of tasty pie serializer
        to get data in right format for export.

        """

        from api import AccountLeadExportResource
        resource = AccountLeadExportResource()
        dummy_request = HttpRequest()
        resource_bundle = resource.build_bundle(obj=self,
                                                request=dummy_request)
        resource_dehydrated = resource.full_dehydrate(resource_bundle)
        json_data = resource.serialize(None, resource_dehydrated,
                                       'application/json')
        dict_data = json.loads(json_data)

        return dict_data

    def get_external(self):
        """ Returns an array of objects

            Get the corresponding resources
            from the external apis """

        objects = []

        for api in self.external_api.all():

            # Experinced problem with cache control
            # on the external APIs. The resource_uri
            # field sometimes pointed to a resource
            # that did not existed.
            cache_buster = [random.choice(string.ascii_letters +
                            string.digits) for n in xrange(30)]
            cache_buster = "".join(cache_buster)
            params = {'username': api.user_name, 'api_key': api.api_key,
                      'format': 'json', 'email': self.email,
                      'cache_buster': cache_buster}
            r = requests.get(api.endpoint, params=params)

            if r.status_code == 200:
                objects += [{'objects': r.json['objects'], 'api': api}]

        return objects

    def post_external(self):
        """ Returns array of objects

            Post new resources to
            the corresponding resources
            on the external apis """

        headers = {'content-type': 'application/json'}
        post_data = json.dumps(self.prepare_resource_for_export())
        status = []

        for api in self.external_api.all():
            params = {'username': api.user_name, 'api_key': api.api_key,
                      'format': 'json'}

            r_post = requests.post(api.endpoint, post_data, params=params,
                                   headers=headers)

            status += [{'status': r_post.status_code, 'api': api}]

        return status

    def put_external(self):
        """ Returns array of status codes

            updates corresponding resources
            on the external apis """

        status = []
        objects = self.get_external()

        for ext_resource in objects:
            base_uri = ext_resource['api'].endpoint
            post_data = json.dumps(self.prepare_resource_for_export())
            params = {'username': ext_resource['api'].user_name,
                      'api_key': ext_resource['api'].api_key, 'format': 'json'}
            headers = {'content-type': 'application/json'}

            if not ext_resource['objects']:
                # No external objects exists
                # Do a POST instead of PUT
                # and create a new resource
                requests.post(
                    base_uri, post_data, params=params,
                    headers=headers)

            else:
                uri = ext_resource['objects'][0]['resource_uri']
                endpoint = urljoin(base_uri, uri)
                r_put = requests.put(endpoint, post_data, params=params,
                                     headers=headers)
                status += [{'status': r_put.status_code,
                            'api': ext_resource['api']}]

                # Fallback, if PUT method is not allowed
                # use DELETE and then POST to simulate PUT
                # This is nessary if the databases going to be in sync
                # and allow account editing in the django admin
                # (as instructed)

                if r_put.status_code == 405:
                    requests.delete(endpoint, params=params,
                                    headers=headers)

                    requests.post(base_uri, post_data, params=params,
                                  headers=headers)

        return status

    def delete_external(self, ext_resource=None):
        """ Returns array of status codes

            Deletes the external resource """

        status = []
        objects = self.get_external()

        for ext_resource in objects:

            base_uri = ext_resource['api'].endpoint
            if ext_resource['objects']:
                uri = ext_resource['objects'][0]['resource_uri']
                endpoint = urljoin(base_uri, uri)
                headers = {'content-type': 'application/json'}

                params = {'username': ext_resource['api'].user_name,
                          'api_key': ext_resource['api'].api_key,
                          'format': 'json'}

                r_delete = requests.delete(endpoint, params=params,
                                           headers=headers)

                status += [{'status': r_delete.status_code,
                            'api': ext_resource['api']}]

        return status


@receiver(post_save, sender=AccountLead)
def account_lead_post_save_handler(sender, **kwargs):
    """ Signal for sync external resourses
        when they are created and updated """

    obj = kwargs['instance']
    new_obj = kwargs['created']

    if new_obj is False:
        """ Can't pick up signals on new resourses
            becaouse of the m2m fields. Othervise the
            external_apis field appears empty in the
            post_external() method """
        obj.put_external()


@receiver(pre_delete, sender=AccountLead)
def account_lead_pre_delete_handler(sender, **kwargs):
    """ Signal for sync external resourses
        when they are deleted """

    obj = kwargs['instance']
    obj.delete_external()


@receiver(m2m_changed, sender=AccountLead.external_api.through)
def account_lead_m2m_changed_handler(sender, **kwargs):
    """ This signal take executes when a new resource are created
        due to the instance are saved multiple times, and the m2m
        fields are saved after the post_save signal, I have to
        pick up newly created resourses here. """

    action = kwargs['action']
    obj = kwargs['instance']

    if action == "post_add":
        obj.post_external()
