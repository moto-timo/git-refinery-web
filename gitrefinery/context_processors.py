# git-refinery-web - custom context processor
#
# Copyright (C) 2017 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

from django.contrib.sites.models import Site

def gitrefinery_context(request):
    site = Site.objects.get_current()
    if site and site.name and site.name != 'example.com':
        site_name = site.name
    else:
        site_name = 'git-refinery'
    return {
        'site_name': site_name
    }
