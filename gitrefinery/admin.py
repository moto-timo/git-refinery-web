# git-refinery-web - admin interface definitions
#
# Copyright (C) 2017 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

from gitrefinery.models import *
from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

class CommitCategoryAdminForm(forms.ModelForm):
    def clean_category(self):
        cat = self.cleaned_data['category']
        if not cat:
            raise ValidationError('You must select a category')
        commit = self.cleaned_data['commit']
        if cat.repository != commit.release.repository:
            raise ValidationError('Category is from a different repository than the commit')
        return cat

class CommitCategoryAdmin(admin.ModelAdmin):
    search_fields = ['commit__revision']
    list_filter = ['category', 'commit__release']
    form = CommitCategoryAdminForm

class CommitAdmin(admin.ModelAdmin):
    list_filter = ['release']

class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['name', 'email']

class AuthorGroupMembershipAdmin(admin.ModelAdmin):
    search_fields = ['author__name', 'author__email']
    list_filter = ['group']

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name', 'title']
    list_filter = ['repository', 'hidden']
    actions = ['hide', 'show']

    def hide(self, request, queryset):
        rows_updated = queryset.update(hidden=True)
        if rows_updated == 1:
            msg = "1 category was successfully hidden."
        else:
            msg = "%s categories were successfully hidden." % rows_updated
        self.message_user(request, msg)

    def show(self, request, queryset):
        rows_updated = queryset.update(hidden=False)
        if rows_updated == 1:
            msg = "1 category was successfully shown."
        else:
            msg = "%s categories were successfully shown." % rows_updated
        self.message_user(request, msg)

class CategorisationRuleAdminForm(forms.ModelForm):
    def clean_category(self):
        cat = self.cleaned_data['category']
        if cat:
            repo = self.cleaned_data['repository']
            if cat.repository != repo:
                raise ValidationError('Category is from a different repository than this rule')
        return cat

class CategorisationRuleAdmin(admin.ModelAdmin):
    form = CategorisationRuleAdminForm


admin.site.register(Author, AuthorAdmin)
admin.site.register(AuthorGroup)
admin.site.register(AuthorGroupMatchRule)
admin.site.register(AuthorGroupMembership, AuthorGroupMembershipAdmin)
admin.site.register(Repository)
admin.site.register(Release)
admin.site.register(Category, CategoryAdmin)
admin.site.register(CategorisationRule, CategorisationRuleAdmin)
admin.site.register(Commit, CommitAdmin)
admin.site.register(CommitCategory, CommitCategoryAdmin)
admin.site.register(StatsChart)
admin.site.register(StatsChartRelease)
admin.site.register(SecurityQuestion)
admin.site.register(SecurityQuestionAnswer)
admin.site.register(UserProfile)
