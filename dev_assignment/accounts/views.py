# -*- coding: utf-8 -*-

from django.contrib.auth.forms import AuthenticationForm
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django.views.generic import TemplateView
from django.contrib.auth import login


class LoginView(FormView):
    template_name = "login.html"
    form_class = AuthenticationForm
    success_url = '/accounts/'


class ProtectedView(TemplateView):
    template_name = 'secret.html'


class AccountView(TemplateView):
    template_name = "accounts.html"
