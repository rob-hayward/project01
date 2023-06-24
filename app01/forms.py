from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, Vote, VoteType, KeyWord, KeyWordDefinition, Question, AnswerType, QuestionTag
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django import forms
from django.contrib.contenttypes.models import ContentType
from django import forms
from .models import KeyWord, KeyWordDefinition, QuestionTag, Question


class KeyWordForm(forms.ModelForm):
    word = forms.CharField(max_length=255,
                           widget=forms.TextInput(attrs={'placeholder': 'Choose any word from the Definition text to propose a new Keyword.'}),
                           label="Propose Keyword")
    definition = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter your proposed Definition for this new Keyword, within the context of its use here on Digiocracy.'}),
                                 label="Propose Keyword Definition")

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
    question_tag = forms.ModelMultipleChoiceField(
        queryset=KeyWord.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text='Select one or more Key Words to create a unique Question Tag relating to your proposed question.',
        label="Question Tag"
    )
    question_text = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter your proposed question here.'}),
                                    label="Question Text")

    answer_type = forms.ChoiceField(choices=[(answer_type.name, answer_type.value) for answer_type in AnswerType],
                                    label="Answer Type")

    class Meta:
        model = QuestionTag
        fields = ['question_tag', 'question_text', 'answer_type']

    def save(self, commit=True, creator=None):  # Added creator parameter
        question_text = self.cleaned_data.get('question_text')
        question_tag = self.cleaned_data.get('question_tag')
        answer_type = self.cleaned_data.get('answer_type')

        question_tag = super(QuestionForm, self).save(commit=False)
        question = Question.objects.create(question_text=question_text, answer_type=answer_type, creator=creator)  # Assign the creator here
        question_tag.question = question

        if commit:
            question_tag.save()
            self.save_m2m()  # This is needed to save ManyToManyField data

        return question_tag


class VoteForm(forms.ModelForm):
    votable_object_id = forms.IntegerField(widget=forms.HiddenInput())
    votable_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=['keyword', 'keyword_definition', 'question_tag', 'question']),
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


class ProposeKeywordForm(forms.ModelForm):
    class Meta:
        model = KeyWord
        fields = ['word']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.creator = self.user
        return super().save(*args, **kwargs)


class ProposeKeywordDefinitionForm(forms.ModelForm):
    class Meta:
        model = KeyWordDefinition
        fields = ['keyword', 'definition']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.creator = self.user
        return super().save(*args, **kwargs)


class ProposeQuestionForm(forms.ModelForm):
    answer_type = forms.ChoiceField(choices=[(type.name, type.value) for type in AnswerType], widget=forms.Select())
    question_text = forms.CharField(widget=forms.Textarea)
    question_tag = forms.ModelChoiceField(queryset=QuestionTag.objects.all(), required=False)

    class Meta:
        model = Question
        fields = ['question_tag', 'question_text', 'answer_type']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.creator = self.user
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