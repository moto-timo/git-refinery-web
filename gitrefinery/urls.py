# git-refinery-web - URL definitions
#
# Copyright (C) 2014 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

from django.conf.urls import *
from django.views.generic import TemplateView, DetailView, ListView, RedirectView
from django.views.defaults import page_not_found
from django.urls import reverse_lazy
from gitrefinery.views import RepoListView, RepoDetailView, ReleaseDetailView, ReleaseNotesView, StatsView, set_commit_note, remove_commit_category, import_commits, edit_repository_view, edit_release_view, fetch_repository_view, RepositoryDeleteView, ReleaseDeleteView, CategoryCheckListView, group_authors, EditProfileFormView

urlpatterns = [
    url(r'^$',
        RedirectView.as_view(url=reverse_lazy('repositories',)),
        name='frontpage'),

    url(r'^repositories/$',
        RepoListView.as_view(
            template_name='gitrefinery/repos.html'),
            name='repositories'),

    url(r'^repo/(?P<slug>[-\w]+)/$',
        RepoDetailView.as_view(
            template_name='gitrefinery/repo.html'),
            name='repository'),

    url(r'^release/(?P<pk>[-\w]+)/$',
        ReleaseDetailView.as_view(
            template_name='gitrefinery/release.html'),
            name='release'),

    url(r'^release/(?P<pk>[-\w]+)/oneline/$',
        ReleaseDetailView.as_view(
            template_name='gitrefinery/release_oneline.html',
            paginate_by=0),
            name='release_oneline',),

    url(r'^release/(?P<pk>[-\w]+)/notes/$',
        ReleaseNotesView.as_view(
            template_name='gitrefinery/releasenotes.html'),
            name='release_notes'),

    url(r'^stats/$',
        StatsView.as_view(
            template_name='gitrefinery/stats.html'),
            name='stats'),

    url(r'^stats/csv/$',
        StatsView.as_view(
            template_name='gitrefinery/stats_csv.txt',
            content_type='text/csv'),
            name='stats_csv'),

    url(r'^group_authors/$',
            group_authors,
            name="group_authors"),

    url(r'^set_commit_note/$',
            set_commit_note,
            name='set_commit_note'),

    url(r'^remove_commit_category/$',
            remove_commit_category,
            name='remove_commit_category'),

    url(r'^release/(?P<pk>[-\w]+)/import/$',
        import_commits, {'template_name': 'gitrefinery/release.html'}, name="import_commits"),

    url(r'^repo/(?P<reponame>[-\w]+)/addrelease/$',
        edit_release_view, {'template_name': 'gitrefinery/editrelease.html'}, name="add_release"),
    url(r'^release/(?P<pk>[-\w]+)/edit/$',
        edit_release_view, {'template_name': 'gitrefinery/editrelease.html'}, name="edit_release"),
    url(r'^release/(?P<pk>[-\w]+)/delete/$',
        ReleaseDeleteView.as_view(
            template_name='gitrefinery/deleteconfirm.html'),
            name="delete_release"),

    url(r'^addrepo/$',
        edit_repository_view, {'template_name': 'gitrefinery/editrepo.html'}, name="add_repository"),
    url(r'^repo/(?P<reponame>[-\w]+)/edit/$',
        edit_repository_view, {'template_name': 'gitrefinery/editrepo.html'}, name="edit_repository"),
    url(r'^repo/(?P<reponame>[-\w]+)/fetch/$',
        fetch_repository_view, name="fetch_repository"),
    url(r'^repo/(?P<slug>[-\w]+)/delete/$',
        RepositoryDeleteView.as_view(
            template_name='gitrefinery/deleteconfirm.html'),
            name="delete_repository"),

    url(r'^ajax/categorychecklist/(?P<repository>[-\w]+)/$',
        CategoryCheckListView.as_view(
            template_name='gitrefinery/categorychecklist.html'),
            name='category_checklist'),

    url(r'^profile/$',
        EditProfileFormView.as_view(
            template_name='gitrefinery/profile.html'),
        name="profile"),

    url(r'.*', page_not_found, kwargs={'exception': Exception("Page not Found")})
]
