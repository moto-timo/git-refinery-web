# git-refinery-web - form definitions
#
# Copyright (C) 2017 Intel Corporation
#
# Licensed under the MIT license, see COPYING.MIT for details

from captcha.fields import CaptchaField
from django.contrib.auth.models import User
from gitrefinery.models import Repository, Release, SecurityQuestion, UserProfile
from django import forms
from django.core.validators import URLValidator, RegexValidator, EmailValidator
from django.forms.models import inlineformset_factory, modelformset_factory
from django_registration.forms import RegistrationForm
from django_registration.validators import (DEFAULT_RESERVED_NAMES,
                                            ReservedNameValidator,
                                            validate_confusables)
import re
import settings


class EditRepositoryForm(forms.ModelForm):
    # Additional fields
    fetch_url = forms.CharField(label='Repository URL', max_length=250, required=True, help_text='URL to fetch the repository from')
    copy_source = forms.ModelChoiceField(label='Copy categories from', queryset=Repository.objects.all(), required=False)

    class Meta:
        model = Repository
        fields = ('name', 'description', 'commit_url')

    def __init__(self, *args, **kwargs):
        super(EditRepositoryForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['fetch_url']
            del self.fields['copy_source']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if name:
            if not re.match('^[a-zA-Z0-9-+_.]+$', name):
                raise forms.ValidationError('Name can only contain alphanumeric characters, -, +, _, and .')
        return name

    def clean_fetch_url(self):
        url = self.cleaned_data['fetch_url'].strip()
        if url:
            val = URLValidator(schemes=['git', 'ssh', 'http', 'https'])
            val(url)
        return url

    def clean_commit_url(self):
        url = self.cleaned_data['commit_url'].strip()
        if url:
            val = URLValidator(schemes=['http', 'https'])
            val(url)
        return url


class EditReleaseForm(forms.ModelForm):
    class Meta:
        model = Release
        fields = ('name', 'description', 'branch', 'begin_rev', 'end_rev')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if name:
            if not re.match('^[a-zA-Z0-9-+_.]+$', name):
                raise forms.ValidationError('Name can only contain alphanumeric characters, -, +, _, and .')
        return name

class EditProfileForm(forms.ModelForm):
    captcha = CaptchaField(label='Verification', help_text='Please enter the letters displayed for verification purposes', error_messages={'invalid':'Incorrect entry, please try again'})
    security_question_1 = forms.ModelChoiceField(queryset=SecurityQuestion.objects.all())
    answer_1 = forms.CharField(widget=forms.TextInput(), label='Answer', initial="*****")
    security_question_2 = forms.ModelChoiceField(queryset=SecurityQuestion.objects.all())
    answer_2 = forms.CharField(widget=forms.TextInput(), label='Answer', initial="*****")
    security_question_3 = forms.ModelChoiceField(queryset=SecurityQuestion.objects.all())
    answer_3 = forms.CharField(widget=forms.TextInput(), label='Answer', initial="*****")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'captcha')

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self ).__init__(*args, **kwargs)
        for field in ['captcha', 'security_question_1', 'security_question_2', 'security_question_3', 'answer_1', 'answer_2', 'answer_3']:
            self.fields[field].widget.attrs.update({
                'autocomplete': 'off'
            })
        user = kwargs.get("instance")
        try:
            self.fields['security_question_1'].initial=user.userprofile.securityquestionanswer_set.all()[0].security_question
            self.fields['security_question_2'].initial=user.userprofile.securityquestionanswer_set.all()[1].security_question
            self.fields['security_question_3'].initial=user.userprofile.securityquestionanswer_set.all()[2].security_question
        except UserProfile.DoesNotExist:
            # The super user won't have had security questions created already
            self.fields['security_question_1'].initial=SecurityQuestion.objects.all()[0]
            self.fields['security_question_2'].initial=SecurityQuestion.objects.all()[1]
            self.fields['security_question_3'].initial=SecurityQuestion.objects.all()[2]
            pass

    def clean_username(self):
        username = self.cleaned_data['username']
        if 'username' in self.changed_data:
            key = 'username_attempts_%s' % self.instance.username
            attempt = cache.get(key) or 0
            if attempt < 10:
                try:
                    reserved_validator = ReservedNameValidator(
                        reserved_names=DEFAULT_RESERVED_NAMES
                    )
                    reserved_validator(username)
                    validate_confusables(username)
                except forms.ValidationError as v:
                    self.add_error('username', v)

                attempt += 1
                cache.set(key, attempt, 300)
            else:
                raise forms.ValidationError('Maximum username change attempts exceeded')

        return username

    def clean(self):
        cleaned_data = super(EditProfileForm, self).clean()
        for data in self.changed_data:
            # Check if a security answer has been updated. If one is updated, they must all be
            # and each security question must be unique.
            if 'answer' in data:
                if 'answer_1' not in self.changed_data \
                  or 'answer_2' not in self.changed_data \
                  or 'answer_3' not in self.changed_data:
                    raise forms.ValidationError("Please provide answers for all three security questions.")
                security_question_1 = self.cleaned_data["security_question_1"]
                security_question_2 = self.cleaned_data["security_question_2"]
                security_question_3 = self.cleaned_data["security_question_3"]
                if security_question_1 == security_question_2:
                    raise forms.ValidationError({'security_question_2': ["Questions may only be chosen once."]})
                if security_question_1 == security_question_3 or security_question_2 == security_question_3:
                    raise forms.ValidationError({'security_question_3': ["Questions may only be chosen once."]})
        return cleaned_data


