# Utilities for git-refinery-web
#
# Copyright (C) 2014 Intel Corporation
# Author: Paul Eggleton <paul.eggleton@linux.intel.com>
#
# Licensed under the MIT license, see COPYING.MIT for details

import sys
import os.path
import logging
import git

def setup_django():
    import django
    # Get access to our Django model
    newpath = os.path.abspath(os.path.dirname(__file__) + '/..')
    sys.path.append(newpath)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    django.setup()

def logger_create(name):
    logger = logging.getLogger(name)
    loggerhandler = logging.StreamHandler()
    loggerhandler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(loggerhandler)
    logger.setLevel(logging.INFO)
    return logger

def git_get_tags(repopath):
    repo = git.Repo(repopath)
    assert repo.bare == False

    tags = {}
    for tag in repo.tags:
        tags[tag.name] = tag.commit.hexsha

    return tags
