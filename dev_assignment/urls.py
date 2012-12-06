# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required
from tastypie.api import Api
from accounts.api import AccountLeadResource
from accounts.api import MailingListsResource
from accounts.api import FeedResource
from accounts.views import LoginView
from accounts.views import AccountView

from django.contrib.auth.views import login
from django.contrib.auth.views import logout

v1_api = Api(api_name='v1')
v1_api.register(AccountLeadResource())
v1_api.register(MailingListsResource())
v1_api.register(FeedResource())

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', LoginView.as_view()),
    url(r'^login/$', login, {'template_name': 'login.html'}, name="login"),
    url(r'^logout/$', logout, {'template_name': 'logout.html'}, name="logout"),
    (r'^accounts/$', login_required(AccountView.as_view())),
    (r'^api/', include(v1_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
