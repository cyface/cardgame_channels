"""Django URL Configuration
"""
from django.conf.urls import url
from django.contrib import admin

from cardgame_channels_app.views import HomePage

urlpatterns = [
    url(r'^$', HomePage.as_view(), name="home"),
    url(r'^admin/', admin.site.urls),
]
