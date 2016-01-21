from django.conf.urls.defaults import include, patterns
'''
Created on 9 apr 2010

@author: laurent.ploix
'''
urlpatterns = patterns('DjangoWebSite.tech.views',
    (r'^api/', include('DjangoWebSite.api.urls')),
    (r'^batch', 'batch'),
    (r'^index', 'index'),
    )

