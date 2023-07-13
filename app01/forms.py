from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, Vote, VoteType, KeyWord, KeyWordDefinition, Question, AnswerType, QuestionTag
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.contrib.contenttypes.models import ContentType
from django import forms
from django_select2 import forms as s2forms
from .models import KeyWord, QuestionTag, Question, AnswerType
from django.db import transaction


class KeyWordForm(forms.ModelForm):
    word = forms.CharField(max_length=255,
                           widget=forms.TextInput(attrs={'placeholder': 'Choose any word from the Definition text to propose a new Keyword.'}),
                           label="Keyword")
    definition = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter your proposed Definition for this new Keyword, within the context of its use here on Digiocracy.'}),
                                 label="Definition")

    class Meta:
        model = KeyWordDefinition
        fields = ['word', 'definition']

    def clean_word(self):
        word = self.cleaned_data.get('word')
        if KeyWord.objects.filter(word__iexact=word).exists():
            raise forms.ValidationError('This keyword already exists.')
        return word

    def save(self, commit=True, creator=None, parent=None):  # Add a parent parameter
        word = self.cleaned_data.get('word')
        keyword, created = KeyWord.objects.get_or_create(word=word, defaults={'creator': creator})
        if not created and keyword.creator != creator:
            raise forms.ValidationError('This keyword already exists.')
        keyword_definition = super(KeyWordForm, self).save(commit=False)
        keyword_definition.keyword = keyword
        keyword_definition.creator = creator

        if commit:
            keyword_definition.save()
            if parent:  # If a parent keyword is passed, add the new keyword as its child
                parent.children.add(keyword)

        return keyword_definition


class QuestionForm(forms.ModelForm):
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter your question text.'}),
        label="Question Text"
    )
    answer_type = forms.ChoiceField(
        choices=[(answer_type.name, answer_type.value) for answer_type in AnswerType],
        label="Answer Type"
    )
    keywords = forms.ModelMultipleChoiceField(
        queryset=KeyWord.objects.all(),
        widget=s2forms.Select2MultipleWidget
    )

    class Meta:
        model = Question
        fields = ['keywords', 'question_text', 'answer_type']

    def save(self, commit=True):
        keywords = self.cleaned_data.get('keywords')
        question_text = self.cleaned_data.get('question_text')
        answer_type = self.cleaned_data.get('answer_type')

        # Use atomic transaction to ensure all db operations are successful
        with transaction.atomic():
            # Create QuestionTag instance first
            question_tag = QuestionTag.objects.create()
            question_tag.keywords.set(keywords)
            question_tag.save()

            # Then, create Question instance and assign the created QuestionTag to the Question
            question = super(QuestionForm, self).save(commit=False)
            question.question_tag = question_tag

            if commit:
                question.save()

        return question


class VoteForm(forms.ModelForm):
    votable_object_id = forms.IntegerField(widget=forms.HiddenInput())
    votable_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=['keyword', 'keyworddefinition', 'question_tag', 'question']),
        widget=forms.HiddenInput()
    )
    vote = forms.ChoiceField(choices=VoteType.choices(), widget=forms.RadioSelect, required=False)

    class Meta:
        model = Vote
        fields = ['votable_content_type', 'votable_object_id', 'vote']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.user = self.user
        return super().save(*args, **kwargs)


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
        fields = ['preferred_name', 'username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Unique username.'
        self.fields['preferred_name'].label = 'Please enter your preferred name to be addressed by whilst on this site.'

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            userprofile = UserProfile.objects.create(user=user)  # Create UserProfile
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