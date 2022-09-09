# git-refinery-web - model definitions
#
# Copyright (C) 2014 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import os.path
import re
import posixpath


def ValidateName(name):
    if not re.match('^[a-zA-Z0-9-+_.]+$', name):
        raise ValidationError("Name contain invalid characters.")
    return name

def ValidateCommitRev(rev):
    if not re.match('^[a-zA-Z0-9]+$', rev):
        raise ValidationError("Commit contain invalid characters.")
    return rev


class Repository(models.Model):
    name = models.CharField(max_length=50, validators=[ValidateName])
    path = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    commit_url = models.CharField(max_length=255, blank=True, help_text='Web URL template for commits. {rev} will be substituted with the revision (hash) and {branch} will be substituted with the branch from the release.')

    class Meta:
        verbose_name_plural = "Repositories"

    def __str__(self):
        return self.name


class Release(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, validators=[ValidateName])
    description = models.TextField(blank=True)
    branch = models.CharField(max_length=50, help_text='Branch name, without remote/ prefix')
    begin_rev = models.CharField(max_length=80, help_text='Beginning revision, e.g. origin/previous_branchname',
            validators=[ValidateCommitRev])
    end_rev = models.CharField(max_length=80, help_text='Ending revision, e.g. origin/branchname',
            validators=[ValidateCommitRev])

    def __str__(self):
        return "%s: %s" % (self.repository.name, self.name)


class Category(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, validators=[ValidateName])
    title = models.CharField(max_length=100, blank=True, help_text='Title to show for the section in the release notes, blank to exclude from the notes')
    description = models.TextField(blank=True)
    hidden = models.BooleanField(default=False, help_text='Hide from individual commit selection')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return "%s: %s" % (self.repository.name, self.name)


class CategorisationRule(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    shortlog_regex = models.CharField(max_length=250, blank=True, help_text='Regex to match against the commit shortlog')
    body_regex = models.CharField(max_length=250, blank=True, help_text='Regex to match against the commit message body')
    path_regex = models.CharField(max_length=250, blank=True, help_text='Regex to match against a path modified by the commit')
    author_regex = models.CharField(max_length=250, blank=True, help_text='Regex to match against the commit author')
    category = models.ForeignKey(Category, blank=True, null=True, help_text='Category to put the commit into if the rule matches', on_delete=models.CASCADE)
    value = models.CharField(max_length=250, blank=True, help_text='Value to set for the category if the rule matches')
    stop_on_match = models.BooleanField(default=False, help_text='If selected, and this rule matches for a commit, stop checking other rules for that commit')
    order = models.IntegerField(default=0, help_text='Ordering index for this rule (rules will be applied in ascending order)')

    def __str__(self):
        strval = "%s:" % self.repository.name
        if self.shortlog_regex:
            strval += " shortlog contains %s" % self.shortlog_regex
        if self.body_regex:
            strval += " body contains %s" % self.body_regex
        if self.path_regex:
            strval += " path contains %s" % self.path_regex
        if self.author_regex:
            strval += " author contains %s" % self.author_regex
        return strval


class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)

    def __str__(self):
        groups = self.authorgroupmembership_set
        if groups.exists():
            groupstr = ', '.join(groups.values_list('group__name', flat=True))
            return "%s (%s)" % (self.name, groupstr)
        else:
            return "%s <%s>" % (self.name, self.email)


class AuthorGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AuthorGroupMatchRule(models.Model):
    group = models.ForeignKey(AuthorGroup, on_delete=models.CASCADE)
    email_regex = models.CharField(max_length=100, blank=True, help_text='Regular expression to use to match an author\'s email address to this group')
    order = models.IntegerField(default=0, help_text='Ordering index for this rule (rules will be applied in ascending order)')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return '%s - %s' % (self.group, self.email_regex)


class AuthorGroupMembership(models.Model):
    group = models.ForeignKey(AuthorGroup, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.group.name, self.author.name)


class Commit(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    revision = models.CharField(max_length=80, validators=[ValidateCommitRev])
    author = models.CharField(max_length=250)
    author_obj = models.ForeignKey(Author, blank=True, null=True, on_delete=models.CASCADE)
    authored_date = models.DateTimeField()
    committed_date = models.DateTimeField()
    shortlog = models.TextField(blank=True)
    commit_message = models.TextField(blank=True)
    files = models.TextField(blank=True)

    def __str__(self):
        return self.revision

    def url(self):
        commit_url_template = self.release.repository.commit_url
        if commit_url_template:
            return commit_url_template.format(rev=self.revision, branch=self.release.branch)
        else:
            return None


class CommitCategory(models.Model):
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Commit categories"

    def has_unique_note(self):
        if self.note:
            if self.note.rstrip() != self.commit.shortlog.rstrip():
                return True
        return False

    def __str__(self):
        return "%s: %s (%s)" % (self.commit, self.category, self.note)


class StatsChart(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    categories = models.CharField(max_length=250, help_text='Comma-separated list of category names to include')
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

class StatsChartRelease(models.Model):
    chart = models.ForeignKey(StatsChart, on_delete=models.CASCADE)
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    label = models.CharField(max_length=150, blank=True, help_text='Label for this release in the chart (blank to use "repo: release")' )
    order = models.IntegerField(default=0, help_text='Ordering index for this rule within the chart')

    def __str__(self):
        return '%s - %s: %s' % (self.chart.name, self.release.repository.name, self.release.name)

class SecurityQuestion(models.Model):
    question = models.CharField(max_length = 250, null=False)

    def __str__(self):
        return '%s' % (self.question)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    answer_attempts = models.IntegerField(default=0)

    def __str__(self):
        return '%s' % (self.user)


class SecurityQuestionAnswer(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    security_question = models.ForeignKey(SecurityQuestion, on_delete=models.CASCADE)
    answer = models.CharField(max_length = 250, null=False)

    def __str__(self):
        return '%s - %s' % (self.user, self.security_question)

