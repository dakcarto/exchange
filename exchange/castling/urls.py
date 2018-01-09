
from django.conf.urls import patterns, url, include
from django.conf.urls.static import static

from . import views


urlpatterns = [
    # TODO: make these one regex.
    url(r'^castling/$', views.index, name='index'),
    url(r'^castling/index.html$', views.index, name='index'),
    url(r'^castling/config.js$', views.config, name='config'),
] + static('castling', document_root='/code/vendor/castling/build')
