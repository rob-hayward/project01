from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, Vote, VoteType, KeyWord, KeyWordDefinition, Question, AnswerType, QuestionTag, AnswerBinary
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

    def save(self, commit=True, creator=None):
        keywords = self.cleaned_data.get('keywords')
        question_text = self.cleaned_data.get('question_text')
        answer_type = self.cleaned_data.get('answer_type')

        with transaction.atomic():
            question_tag = QuestionTag.objects.create(creator=creator)  # set the creator here
            question_tag.keywords.set(keywords)
            question_tag.save()

            question = super(QuestionForm, self).save(commit=False)
            question.question_tag = question_tag
            question.creator = creator  # set the creator here

            if commit:
                question.save()
                if question.answer_type == AnswerType.BINARY.name:
                    AnswerBinary.objects.create(question_tag=question_tag, creator=creator)  # create AnswerBinary

        return question


class VoteForm(forms.ModelForm):
    votable_object_id = forms.IntegerField(widget=forms.HiddenInput())
    votable_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=['keyword', 'keyworddefinition', 'questiontag', 'question', 'answerbinary']),
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

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Unique username.'

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    preferred_name = forms.CharField()
    address = forms.CharField()
    city = forms.CharField()
    post_code = forms.CharField()
    country = CountryField(blank_label='(select country)').formfield(
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }),
    )
    phone_number = forms.CharField()

    class Meta:
        model = UserProfile
        fields = ['preferred_name', 'address', 'city', 'post_code', 'country', 'phone_number']


class LoginForm(AuthenticationForm):
    pass