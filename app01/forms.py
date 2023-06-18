from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, AnswerType, ProposalVote, VoteType
from django import forms
from .models import Question, Status, Tag, KeywordDefinition
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


class ChangeStatusForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget = forms.Select(choices=[(status.name, status.value) for status in Status if status != Status.PROPOSED])


class ProposalVoteForm(forms.ModelForm):
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    vote = forms.ChoiceField(choices=VoteType.choices(), widget=forms.RadioSelect, required=False)

    class Meta:
        model = ProposalVote
        fields = ['question_id', 'vote']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean_question_id(self):
        question_id = self.cleaned_data['question_id']
        question = Question.objects.filter(id=question_id).first()
        if not question:
            raise forms.ValidationError("Question does not exist")
        return question

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        return super().save(*args, **kwargs)


class BinaryVoteForm(forms.Form):
    NOVOTE = None
    YES = True
    NO = False
    VOTE_CHOICES = [
        (NOVOTE, '----'),
        (YES, 'Yes'),
        (NO, 'No'),
    ]

    vote = forms.ChoiceField(
        choices=VOTE_CHOICES,
        initial=NOVOTE,
        required=False,
    )
    question_id = forms.IntegerField(widget=forms.HiddenInput())


class ProposeQuestionForm(forms.ModelForm):
    answer_type = forms.ChoiceField(choices=[(type.name, type.value) for type in AnswerType], widget=forms.Select())
    existing_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    new_tags = forms.CharField(widget=forms.HiddenInput(), required=False)
    new_main_tag = forms.CharField(required=True)
    keywords = forms.ModelMultipleChoiceField(
        queryset=KeywordDefinition.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    definitions = forms.CharField(required=False, widget=forms.Textarea, help_text='Enter definitions for new keywords here, one per line.')

    parent_question = forms.ModelChoiceField(
        queryset=Question.objects.all(),
        required=False,  # Set the field as not required.
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Question
        fields = ['parent_question', 'question_text', 'answer_type', 'keywords']  # Removed 'status' field.

    def __init__(self, *args, **kwargs):
        super(ProposeQuestionForm, self).__init__(*args, **kwargs)
        self.fields['answer_type'].initial = AnswerType.BINARY.name

        parent_question_id = self.initial.get('parent_question')
        if parent_question_id:
            parent_question = Question.objects.get(id=parent_question_id)
            path_to_root = ' > '.join([tag.name for tag in parent_question.question_path()])
            self.path_to_root = f"Path: {path_to_root} > {parent_question.main_tag.name}"
        else:
            self.path_to_root = "Empty question tree. Please propose a root question"

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=False):  # Notice commit=False here.
        question = super().save(commit=False)
        question.status = Status.PROPOSED.value  # Set the status directly

        if self.cleaned_data.get('new_tags'):
            new_tags_list = self.cleaned_data.get('new_tags').split(',')
            for new_tag in new_tags_list:
                tag, created = Tag.objects.get_or_create(name=new_tag.strip())
                question.tags.add(tag)

        if self.cleaned_data.get('existing_tags'):
            for existing_tag in self.cleaned_data.get('existing_tags'):
                question.tags.add(existing_tag)

        main_tag, created = Tag.objects.get_or_create(
            name=self.cleaned_data['new_main_tag'])
        question.main_tag = main_tag

        if self.cleaned_data.get('keywords') and self.cleaned_data.get('definitions'):
            keywords = self.cleaned_data.get('keywords')
            definitions = self.cleaned_data.get('definitions').split('\n')

            for keyword, definition in zip(keywords, definitions):
                keyword_def, created = KeywordDefinition.objects.get_or_create(keyword=keyword.strip(), defaults={
                    'definition': definition.strip()})
                if not created and keyword_def.definition != definition.strip():
                    keyword_def.definition = definition.strip()
                    keyword_def.save()
                question.keyword_definitions.add(keyword_def)

        if self.cleaned_data.get('keywords'):
            for keyword in self.cleaned_data.get('keywords'):
                question.keyword_definitions.add(keyword)

        if commit:
            question.save()

        return question


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    address = forms.CharField()
    city = forms.CharField()
    post_code = forms.CharField()
    country = CountryField(blank_label='(select country)').formfield(
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }),
    )
    phone_number = forms.CharField()
    preferred_name = forms.CharField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Please choose a unique username to be addressed by whilst on this site'

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            userprofile = UserProfile.objects.get(user=user)
            userprofile.preferred_name = self.cleaned_data['preferred_name']
            userprofile.address = self.cleaned_data['address']
            userprofile.city = self.cleaned_data['city']
            userprofile.post_code = self.cleaned_data['post_code']
            userprofile.country = self.cleaned_data['country']
            userprofile.phone_number = self.cleaned_data['phone_number']
            userprofile.save()
        return user


class LoginForm(AuthenticationForm):
    pass


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['preferred_name', 'address', 'city', 'post_code', 'country', 'phone_number']


class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']