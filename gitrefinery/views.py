# git-refinery-web - view definitions
#
# Copyright (C) 2014-2018 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

import os
import shutil
from collections import namedtuple
from datetime import datetime
import re
import git

from django.contrib.messages.views import SuccessMessageMixin
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponseBadRequest
from django.urls import reverse, reverse_lazy, resolve
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from gitrefinery.models import Repository, Release, Commit, Category, CommitCategory, CategorisationRule, Author, AuthorGroup, AuthorGroupMatchRule, AuthorGroupMembership, StatsChart, UserProfile, SecurityQuestion, SecurityQuestionAnswer
from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.base import RedirectView
from django.db import transaction
from django.db.models import Q, Count
from django.template.loader import get_template
from django.template import Context
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from gitrefinery.forms import EditRepositoryForm, EditReleaseForm, EditProfileForm
import settings
from . import utils



class RepoListView(ListView):
    model = Repository
    context_object_name = 'repos'


class RepoDetailView(DetailView):
    model = Repository
    context_object_name = 'repo'
    slug_field = 'name'



class ReleaseDetailView(DetailView):
    model = Release
    context_object_name = 'release'
    slug_field = 'name'
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super(ReleaseDetailView, self).get_context_data(**kwargs)
        release = context['release']

        query_string = self.request.GET.get('q', '')
        try:
            query_category = int(self.request.GET.get('category', -1))
        except ValueError:
            query_category = -1
        commits = release.commit_set.all().order_by('-id')

        try:
            query_authorgroup = int(self.request.GET.get('authorgroup', -1))
        except ValueError:
            query_authorgroup = -1

        query_excludecategories_str = self.request.GET.get('excludecategories', '')
        if query_excludecategories_str:
            query_excludecategories = [int(i) for i in query_excludecategories_str.split(',')]
        else:
            query_excludecategories = []

        if query_authorgroup == -2:
            commits = commits.filter(author_obj__authorgroupmembership__isnull=True)
        elif query_authorgroup > -1:
            commits = commits.filter(author_obj__authorgroupmembership__group__id=query_authorgroup)

        if query_string:
            commits = commits.filter(Q(commit_message__contains=query_string) | Q(author__contains=query_string))

        if query_category == -2:
            commits = commits.filter(commitcategory__isnull=True)
        elif query_category > -1:
            commits = commits.filter(commitcategory__category_id=query_category).distinct()

        if query_excludecategories:
            commits = commits.exclude(commitcategory__category_id__in=query_excludecategories)

        try:
            all_tags = utils.git_get_tags(release.repository.path)
        except:
            all_tags = {}
        # Reorg tags by commit
        reverse_tags = {}
        for tag, commit in all_tags.items():
            reverse_tags[commit] = reverse_tags.get(commit, []) + [tag]

        if self.paginate_by > 0:
            paginator = Paginator(commits, self.paginate_by)
            page = paginator.page(int(self.request.GET.get('page', '1')))
            context['page_obj'] = page
            context['commits'] = page.object_list
            context['is_paginated'] = True
        else:
            context['commits'] = commits
            context['is_paginated'] = False
        context['authorgroups'] = AuthorGroup.objects.all()
        context['search_keyword'] = query_string
        context['search_category'] = query_category
        context['search_authorgroup'] = query_authorgroup
        context['excludecategories'] = query_excludecategories
        if query_excludecategories:
            all_category_names = dict(Category.objects.filter(repository=release.repository).values_list('id', 'name'))
            category_names = [all_category_names[i] for i in query_excludecategories]
            context['excludecategories_display'] = ','.join(category_names)
        else:
            context['excludecategories_display'] = ' (none)'
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied

        release = self.get_object()

        def apply_commits():
            for commit_hash in request.POST.getlist('selecteditems', ''):
                if len(commit_hash) == 40:
                    obj = Commit.objects.get(release=release, revision=commit_hash)
                    yield obj

        action = request.POST.get('action', '')
        if action == 'categorise':
            try:
                category_id = int(request.POST.get('catvalue', -1))
            except ValueError:
                category_id = -1
            if category_id > -1:
                for obj in apply_commits():
                    obj.save()
                    category = get_object_or_404(Category, id=category_id, repository=release.repository)
                    commitcat, _ = CommitCategory.objects.get_or_create(commit=obj, category=category)
                    commitcat.save()
        elif action == 'uncategorise':
            try:
                category_id = int(request.POST.get('catvalue', -1))
            except ValueError:
                category_id = -1
            if category_id > -1:
                for obj in apply_commits():
                    category = get_object_or_404(Category, id=category_id, repository=release.repository)
                    obj.commitcategory_set.filter(category=category).delete()

        return self.get(request, *args, **kwargs)


class ReleaseNotesView(DetailView):
    model = Release
    context_object_name = 'release'
    slug_field = 'name'

    def get_context_data(self, **kwargs):
        context = super(ReleaseNotesView, self).get_context_data(**kwargs)
        release = self.get_object()
        titles = {}
        notes = {}

        for category in release.repository.category_set.all():
            notes[category.id] = []
        for commit in release.commit_set.all().order_by("id"):
            for commitcat in commit.commitcategory_set.all():
                if commitcat.note:
                    notes[commitcat.category.id].append("* %s" % commitcat.note)
                else:
                    # Note not set, get it from the commit shortlog
                    notes[commitcat.category.id].append("* %s" % commit.shortlog)

        output = []
        for category in release.repository.category_set.all():
            if category.title:
                title = category.title
            else:
                continue
            output.append('\n')
            output.append(title)
            output.append('-' * len(title))
            if notes[category.id]:
                output.extend(notes[category.id])
            else:
                output.append('None')

        context['release_notes'] = '\n'.join(output)
        return context


class StatsView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(StatsView, self).get_context_data(**kwargs)

        groups = AuthorGroup.objects.all()
        context['groups'] = groups

        ChartData = namedtuple('ChartData', ['chart', 'categorynames', 'releases'])
        ChartReleaseData = namedtuple('ChartReleaseData', ['release', 'label', 'data', 'total'])

        chartdatalist = []
        charts = StatsChart.objects.all()
        for chart in charts:
            categorynames = [x.strip() for x in chart.categories.split(',')]

            releasedatalist = []
            for statschartrelease in chart.statschartrelease_set.all().order_by('order'):
                release = statschartrelease.release

                # Categories are per repo, not global
                categories = Category.objects.filter(repository=release.repository).filter(name__in=categorynames)
                data = []
                #total = release.commit_set.filter(commitcategory__category__in=categories).filter(author_obj__authorgroupmembership__group__in=groups).distinct().count()
                total = release.commit_set.count()

                # We have to loop through categorynames here not categories so we get the right order
                for category in categorynames:
                    for group in groups:
                        count = release.commit_set.filter(commitcategory__category__name=category).filter(author_obj__authorgroupmembership__group=group).distinct().count()
                        data.append(count / total * 100.0)
                    # Add "other"
                    count = release.commit_set.filter(commitcategory__category__name=category).filter(author_obj__authorgroupmembership__isnull=True).distinct().count()
                    data.append(count / total * 100.0)

                if statschartrelease.label:
                    label = statschartrelease.label
                else:
                    label = '%s: %s' % (release.repository.name, release.name)
                releasedata = ChartReleaseData(release=release, label=label, data=data, total=total)
                releasedatalist.append(releasedata)
            chartdata = ChartData(chart=chart, categorynames=categorynames, releases=releasedatalist)
            chartdatalist.append(chartdata)
        context['chartdatalist'] = chartdatalist
        return context


def set_commit_note(request):
    if not request.user.is_authenticated:
        raise PermissionDenied

    release_id = request.POST.get('release', '')
    commit_hash = request.POST.get('commit', '')
    category_id = request.POST.get('category', None)
    note = request.POST.get('note', '')

    if len(commit_hash) != 40:
        return HttpResponseBadRequest()

    release = get_object_or_404(Release, id=release_id)
    category = get_object_or_404(Category, id=category_id, repository=release.repository)
    commit = get_object_or_404(Commit, release=release, revision=commit_hash)
    commitcat, _ = CommitCategory.objects.get_or_create(commit=commit, category=category)
    commitcat.note = note
    commitcat.save()

    return HttpResponse('saved')


def remove_commit_category(request):
    if not request.user.is_authenticated:
        raise PermissionDenied

    release_id = request.POST.get('release', '')
    commit_hash = request.POST.get('commit', '')
    category_id = request.POST.get('category', None)

    if len(commit_hash) != 40:
        return HttpResponseBadRequest()

    release = get_object_or_404(Release, id=release_id)
    category = get_object_or_404(Category, id=category_id, repository=release.repository)
    commit = get_object_or_404(Commit, release=release, revision=commit_hash)
    commitcat = get_object_or_404(CommitCategory, commit=commit, category=category)
    commitcat.delete()

    return HttpResponse('success')


def import_commits(request, template_name, pk):
    if not request.user.is_authenticated:
        raise PermissionDenied
    release = get_object_or_404(Release, id=pk)

    repo = git.Repo(release.repository.path)
    assert repo.bare == False

    lastobj = release.commit_set.order_by('-id')
    if lastobj:
        lastrev = lastobj[0].revision
        all_commits = repo.iter_commits("%s..%s" % (lastrev, release.end_rev))
        if not all_commits:
            messages.info(request, 'No new commits to import since %s' % lastrev)
            return HttpResponseRedirect(reverse('release', args=(release.id,)))
    else:
        all_commits = repo.iter_commits("%s..%s" % (release.begin_rev, release.end_rev))
        if not all_commits:
            messages.error(request, 'No commits in range between %s and %s' % (release.begin_rev, release.end_rev))
            return HttpResponseRedirect(reverse('release', args=(release.id,)))

    print('Import: gathering rules')
    # FIXME not happy about using dicts here
    rules = []
    for rule in release.repository.categorisationrule_set.order_by('order'):
        ruledict = {}
        if rule.shortlog_regex:
            ruledict['shortlog'] = re.compile(rule.shortlog_regex, re.IGNORECASE)
        if rule.body_regex:
            ruledict['message'] = re.compile(rule.body_regex, re.IGNORECASE)
        if rule.path_regex:
            ruledict['path'] = re.compile(rule.path_regex, re.IGNORECASE)
        if rule.author_regex:
            ruledict['author'] = re.compile(rule.author_regex, re.IGNORECASE)
        if rule.value:
            ruledict['value'] = rule.value
        ruledict['category'] = rule.category
        ruledict['stop_on_match'] = rule.stop_on_match
        rules.append(ruledict)

    print('Import: checking for reverted commits')

    revert_re = re.compile('This reverts commit ([0-9a-z]+)\.')
    reverts = []
    reverted = []

    category_revert = None
    category_reverted = None
    qry = Category.objects.filter(repository=release.repository, name='revert')
    if qry:
        category_revert = qry[0]
    qry = Category.objects.filter(repository=release.repository, name='reverted')
    if qry:
        category_reverted = qry[0]

    commitlist = []
    for commit in all_commits:
        rx = revert_re.search(commit.message)
        if rx:
            reverted.append(rx.group(1))
            reverts.append(commit.hexsha)
        commitlist.append(commit)

    print('Import: processing commits')

    counter = 0
    maxcount = len(commitlist)
    last_percent = -1
    for commit in reversed(commitlist):
        counter += 1
        percent = int(counter / maxcount * 100)
        if percent > last_percent:
            print('imported %d%%' % percent)
        last_percent = percent
        commithash = commit.hexsha
        commitobj = Commit()
        commitobj.release = release
        commitobj.revision = commithash
        commitobj.author = commit.author.name
        author, _ = Author.objects.get_or_create(name=commit.author.name,
                                                email=commit.author.email)
        commitobj.author_obj = author
        commitobj.authored_date = datetime.fromtimestamp(commit.authored_date)
        commitobj.committed_date = datetime.fromtimestamp(commit.committed_date)
        commitobj.shortlog = commit.message.splitlines()[0]
        commitobj.commit_message = commit.message
        #commitobj.files =
        commitobj.save()

        if commithash in reverted and category_reverted:
            # Reverted commits should just be ignored
            commitcat = CommitCategory(commit=commitobj, category=category_reverted)
            commitcat.save()
            continue
        elif commithash in reverts and category_revert:
            # Reverts should just be ignored
            commitcat = CommitCategory(commit=commitobj, category=category_revert)
            commitcat.save()
            continue

        for ruledict in rules:
            match_rx = None
            rx = ruledict.get('shortlog', None)
            if rx:
                if rx.search(commitobj.shortlog):
                    match_rx = rx
                else:
                    continue
            rx = ruledict.get('message', None)
            if rx:
                if rx.search(commitobj.commit_message):
                    match_rx = rx
                else:
                    continue
            rx = ruledict.get('path', None)
            if rx:
                for pth in commit.stats.files:
                    if rx.search(pth):
                        match_rx = rx
                        break
                else:
                    continue
            rx = ruledict.get('author', None)
            if rx:
                if rx.search(commitobj.author):
                    match_rx = rx
                else:
                    continue

            if match_rx:
                if ruledict['category']:
                    commitcat, _ = CommitCategory.objects.get_or_create(commit=commitobj, category=ruledict['category'])
                    value = ruledict.get('value', None)
                    if value:
                        commitcat.note = match_rx.sub(value, commitobj.commit_message)
                    else:
                        commitcat.note = commitobj.shortlog
                    commitcat.save()
                if ruledict['stop_on_match']:
                    break

    messages.info(request, 'categorisation rules applied')
    return HttpResponseRedirect(reverse('release', args=(release.id,)))


def group_authors(request):
    groupmap = {}
    for rule in AuthorGroupMatchRule.objects.all().order_by('order'):
        if rule.email_regex:
            groupmap[rule.group] = re.compile(rule.email_regex)
    if not groupmap:
        messages.warning(request, 'No AuthorGroupMatchRule records have email_regex set - nothing to do')
        return HttpResponseRedirect(reverse('frontpage'))

    changes = False
    groupmsgs = []
    for author in Author.objects.all():
        for group, email_re in groupmap.items():
            if email_re.match(author.email):
                if author.authorgroupmembership_set.exists():
                    # Author is already in a group, skip
                    break
                groupmsgs.append("Added %s to %s group" % (author, group.name))
                groupm = AuthorGroupMembership()
                groupm.author = author
                groupm.group = group
                groupm.save()
                changes = True
                break

    if changes:
        messages.success(request, 'Author group changes made:\n  -' + ('\n  -'.join(groupmsgs)))
    else:
        messages.info(request, 'No grouping changes needed to be made')

    # Check if any authors are part of more than one group -
    # if they are that's not necessarily a problem, you just need
    # to be aware that they exist when interpreting the stats as the
    # total percentages will then not add up to 100%
    for author in Author.objects.all():
        if author.authorgroupmembership_set.count() > 1:
            messages.warning(request, '%s is a member of more than one group' % author)

    return HttpResponseRedirect(reverse('frontpage'))


def fetch_repository_view(request, reponame=None):
    if not request.user.is_authenticated:
        raise PermissionDenied
    repo = get_object_or_404(Repository, name=reponame)
    if not os.access(repo.path, os.W_OK):
        raise Exception('Repo path %s is not writeable' % repo.path)
    try:
        frepo = git.Repo(repo.path)
        for remote in frepo.remotes:
            remote.fetch(prune=True)
        messages.success(request, 'Fetched successfully')
    except:
        raise Exception("Failed to fetch repo")
    return HttpResponseRedirect(reverse('repository', args=(repo.name,)))


def edit_repository_view(request, template_name, reponame=None):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if reponame:
        # Edit mode
        repo = get_object_or_404(Repository, name=reponame)
    else:
        # Add mode
        repo = Repository()

    if request.method == 'POST':
        form = EditRepositoryForm(request.POST, instance=repo)
        if form.is_valid():
            repobase = settings.REPO_BASE_DIR
            if not repobase:
                raise Exception('REPO_BASE_DIR not set')
            insert = False
            if not repo.pk:
                insert = True
                # FIXME this is ugly doing this synchronously
                if not os.access(repobase, os.W_OK):
                    raise Exception('REPO_BASE_DIR %s is not writeable' % repobase)
                repo.path = os.path.join(repobase, repo.name)
                git.Repo.clone_from(form.cleaned_data['fetch_url'], repo.path)
            form.save()

            if insert:
                copy_source = form.cleaned_data['copy_source']
                if copy_source:
                    for category in copy_source.category_set.all():
                        category.pk = None
                        category.repository = repo
                        category.save()
                    for rule in copy_source.categorisationrule_set.all():
                        rule.pk = None
                        rule.repository = repo
                        rule.category = repo.category_set.filter(name=rule.category.name).first()
                        rule.save()

            messages.success(request, 'Repository %s saved successfully.' % repo.name)
            return HttpResponseRedirect(reverse('repository', args=(repo.name,)))
    else:
        form = EditRepositoryForm(instance=repo)

    return render(request, template_name, {
        'form': form,
    })


def edit_release_view(request, template_name, reponame=None, pk=None):
    if not request.user.is_authenticated:
        raise PermissionDenied
    if pk:
        # Edit mode
        release = get_object_or_404(Release, pk=pk)
    else:
        # Add mode
        repo = get_object_or_404(Repository, name=reponame)
        release = Release()
        release.repository = repo

    if request.method == 'POST':
        form = EditReleaseForm(request.POST, instance=release)
        if form.is_valid():
            form.save()
            messages.success(request, 'Release %s saved successfully.' % release.name)
            return HttpResponseRedirect(reverse('release', args=(release.id,)))
    else:
        form = EditReleaseForm(instance=release)

    return render(request, template_name, {
        'form': form,
    })


class BaseDeleteView(DeleteView):

    def get_context_data(self, **kwargs):
        context = super(BaseDeleteView, self).get_context_data(**kwargs)
        obj = context.get('object', None)
        if obj:
            context['object_type'] = obj._meta.verbose_name
            cancel = self.request.GET.get('cancel', '')
            if cancel:
                if self.slug_field != 'slug':
                    args = (getattr(obj, self.slug_field),)
                else:
                    args = (obj.pk,)
                context['cancel_url'] = reverse_lazy(cancel, args=args)
        return context


class RepositoryDeleteView(BaseDeleteView):
    model = Repository
    slug_field = 'name'
    success_url = reverse_lazy('repositories')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        repopath = self.object.path
        self.object.delete()
        # Tidy up after ourselves
        basedir = settings.REPO_BASE_DIR
        if basedir:
            if basedir[-1] != '/':
                basedir += '/'
            if repopath.startswith(basedir) and os.path.exists(repopath):
                shutil.rmtree(repopath)
        return HttpResponseRedirect(success_url)

class ReleaseDeleteView(BaseDeleteView):
    model = Release

    def get_success_url(self):
        return reverse_lazy('repository', args=(self.get_object().repository.name,))


class CategoryCheckListView(ListView):
    model = Category
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(repository__id=self.kwargs['repository'])

class EditProfileFormView(SuccessMessageMixin, UpdateView):
    form_class = EditProfileForm

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        return super(EditProfileFormView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditProfileFormView, self).get_context_data(**kwargs)
        form = context['form']
        # Prepare a list of fields with errors
        # We do this so that if there's a problem with the captcha, that's the only error shown
        # (since we have a username field, we want to make user enumeration difficult)
        if 'captcha' in form.errors:
            error_fields = ['captcha']
        else:
            error_fields = form.errors.keys()
        context['error_fields'] = error_fields
        context['return_url'] = self.get_success_url()
        return context

    def get_object(self, queryset=None):
        return self.user

    def form_valid(self, form):
        self.object = form.save()

        if'answer_1' in form.changed_data:
            # If one security answer has changed, they all have. Delete current questions and add new ones.
            # Don't throw an error if we are editing the super user and they don't have security questions yet.
            try:
                self.user.userprofile.securityquestionanswer_set.all().delete()
                user = self.user.userprofile
            except UserProfile.DoesNotExist:
                user = UserProfile.objects.create(user=self.user)

            security_question_1 = SecurityQuestion.objects.get(question=form.cleaned_data.get("security_question_1"))
            security_question_2 = SecurityQuestion.objects.get(question=form.cleaned_data.get("security_question_2"))
            security_question_3 = SecurityQuestion.objects.get(question=form.cleaned_data.get("security_question_3"))
            answer_1 = form.cleaned_data.get("answer_1").replace(" ", "").lower()
            answer_2 = form.cleaned_data.get("answer_2").replace(" ", "").lower()
            answer_3 = form.cleaned_data.get("answer_3").replace(" ", "").lower()

            # Answers are hashed using Django's password hashing function make_password()
            SecurityQuestionAnswer.objects.create(user=user, security_question=security_question_1,
                                                  answer=make_password(answer_1))
            SecurityQuestionAnswer.objects.create(user=user, security_question=security_question_2,
                                                  answer=make_password(answer_2))
            SecurityQuestionAnswer.objects.create(user=user, security_question=security_question_3,
                                                  answer=make_password(answer_3))

        if 'email' in form.changed_data:
            # Take a copy of request.user as it is about to be invalidated by logout()
            user = self.request.user
            logout(self.request)
            # Deactivate user and put through registration again
            user.is_active = False
            user.save()
            view = RegistrationView()
            view.request = self.request
            view.send_activation_email(user)
            return HttpResponseRedirect(reverse('reregister'))

        return super(EditProfileFormView, self).form_valid(form)

    def get_success_message(self, cleaned_data):
        return "Profile saved successfully"

    def get_success_url(self):
        return self.request.GET.get('return_to', reverse('frontpage'))


