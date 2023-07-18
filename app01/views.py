from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import UserProfile, Status, VoteType, KeyWord, KeyWordDefinition, QuestionTag, Question, Vote, AnswerBinary
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegisterForm, UserProfileForm, LoginForm, VoteForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseNotAllowed
from django.views.generic import ListView
from django.contrib.auth.models import User, ContentType
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.http import HttpResponseForbidden
from .forms import KeyWordForm, QuestionForm
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.http import Http404


def submit_vote(request):
    if request.method == 'POST':
        form = VoteForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            votable_content_type = form.cleaned_data['votable_content_type']
            votable_object_id = form.cleaned_data['votable_object_id']
            vote_value = form.cleaned_data['vote']
            try:
                vote = Vote.objects.get(user=user, votable_content_type=votable_content_type, votable_object_id=votable_object_id)
            except Vote.DoesNotExist:
                vote = None

            if vote_value == VoteType.NO_VOTE.value:
                if vote:
                    vote.delete()
            else:
                if vote:
                    vote.vote = vote_value
                    vote.save()
                else:
                    form.save()

            votable_object = votable_content_type.get_object_for_this_type(id=votable_object_id)
            data = votable_object.get_vote_data()
            data['user_vote'] = votable_object.get_user_vote(request.user)

            return JsonResponse(data)
    else:
        return HttpResponseNotAllowed(['POST'])


@login_required
def question_detail(request, question_tag):
    try:
        keyword = KeyWord.objects.get(word=question_tag)
    except KeyWord.DoesNotExist:
        raise Http404("No Keyword matches the given query.")

    try:
        question_tag_obj = keyword.questiontag_set.first()
        if question_tag_obj is None:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        raise Http404("No QuestionTag matches the given query.")

    try:
        question_obj = Question.objects.get(question_tag=question_tag_obj)
    except Question.DoesNotExist:
        raise Http404("No Question matches the given query.")

    try:
        answer_obj = AnswerBinary.objects.get(question_tag=question_tag_obj)
    except AnswerBinary.DoesNotExist:
        raise Http404("No AnswerBinary matches the given query.")

    question_error = None
    keyword_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    question_content_type = ContentType.objects.get_for_model(question_obj)
    question_tag_content_type = ContentType.objects.get_for_model(question_tag_obj)
    answer_content_type = ContentType.objects.get_for_model(answer_obj)

    if request.method == 'POST' and 'question_submit' in request.POST:
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            try:
                new_question = question_form.save(commit=False)
                new_question.creator = request.user
                new_question.parent = question_obj
                new_question.save()
                return redirect(new_question.get_absolute_url())
            except forms.ValidationError as e:
                question_error = str(e)

    else:
        question_form = QuestionForm()

    if request.method == 'POST' and 'keyword_submit' in request.POST:
        keyword_form = KeyWordForm(request.POST)
        if keyword_form.is_valid():
            try:
                new_keyword = keyword_form.save(creator=request.user)
                return redirect(new_keyword.keyword.get_absolute_url())
            except forms.ValidationError as e:
                keyword_error = str(e)
    else:
        keyword_form = KeyWordForm()

    question_vote_data = question_obj.get_vote_data()
    question_user_vote = question_obj.get_user_vote(request.user)
    question_tag_vote_data = question_tag_obj.get_vote_data()
    question_tag_user_vote = question_tag_obj.get_user_vote(request.user)
    answer_vote_data = answer_obj.get_vote_data()
    answer_user_vote = answer_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
        'question_form': question_form,
        'question_error': question_error,
        'question': question_obj,
        'question_text': question_obj.question_text,
        'question_obj_id': question_obj.id,
        'question_content_type_id': question_content_type.id,
        'question_user_vote': question_user_vote,
        'question_tag': question_tag_obj,
        'question_tag_obj_id': question_tag_obj.id,
        'question_tag_content_type_id': question_tag_content_type.id,
        'question_tag_user_vote': question_tag_user_vote,
        'answer': answer_obj,
        'answer_obj_id': answer_obj.id,
        'answer_content_type_id': answer_content_type.id,
        'answer_user_vote': answer_user_vote,

    }
    context.update(question_vote_data)
    context.update(question_tag_vote_data)
    context.update(answer_vote_data)

    return render(request, 'app01/question_detail.html', context)


@login_required
def answer_binary(request, question_tag):
    try:
        keyword = KeyWord.objects.get(word=question_tag)
        question_tag_obj = keyword.questiontag_set.first()
        question_obj = Question.objects.get(question_tag=question_tag_obj)
    except ObjectDoesNotExist:
        raise Http404("No Question matches the given query.")

    question_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    question_content_type = ContentType.objects.get_for_model(question_obj)
    question_tag_content_type = ContentType.objects.get_for_model(question_tag_obj)

    if request.method == 'POST' and 'question_submit' in request.POST:
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            try:
                new_question = question_form.save(commit=False)
                new_question.creator = request.user
                new_question.parent = question_obj
                new_question.save()
                return redirect(new_question.get_absolute_url())
            except forms.ValidationError as e:
                question_error = str(e)

    else:
        question_form = QuestionForm()

    question_vote_data = question_obj.get_vote_data()
    question_user_vote = question_obj.get_user_vote(request.user)
    question_tag_vote_data = question_tag_obj.get_vote_data()
    question_tag_user_vote = question_tag_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'question': question_obj,
        'question_text': question_obj.question_text,
        'question_tag': question_tag_obj,
        'question_form': question_form,
        'question_error': question_error,
        'question_content_type_id': question_content_type.id,
        'question_obj_id': question_obj.id,
        'question_user_vote': question_user_vote,
        'question_tag_content_type_id': question_tag_content_type.id,
        'question_tag_obj_id': question_tag_obj.id,
        'question_tag_user_vote': question_tag_user_vote,
    }
    context.update(question_vote_data)
    context.update(question_tag_vote_data)

    return render(request, 'app01/answer_binary.html', context)


@login_required
def keyword_detail(request, keyword):
    keyword_obj = get_object_or_404(KeyWord, word=keyword)
    keyword_definition_obj = keyword_obj.definition
    keyword_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    keyword_votable_type = ContentType.objects.get_for_model(keyword_obj)
    keyword_definition_votable_type = ContentType.objects.get_for_model(keyword_definition_obj)

    if request.method == 'POST' and 'keyword_submit' in request.POST:
        keyword_form = KeyWordForm(request.POST)
        if keyword_form.is_valid():
            try:
                new_keyword = keyword_form.save(creator=request.user)
                return redirect(new_keyword.keyword.get_absolute_url())
            except forms.ValidationError as e:
                keyword_error = str(e)
    else:
        keyword_form = KeyWordForm()

    keyword_vote_data = keyword_obj.get_vote_data()
    keyword_user_vote = keyword_obj.get_user_vote(request.user)
    keyword_definition_vote_data = keyword_definition_obj.get_vote_data()
    keyword_definition_user_vote = keyword_definition_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword': keyword_obj,
        'keyword_definition': keyword_definition_obj,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
        'keyword_votable_type': keyword_votable_type.id,
        'keyword_obj': keyword_obj.id,
        'keyword_user_vote': keyword_user_vote,
        'keyword_definition_votable_type': keyword_definition_votable_type.id,
        'keyword_definition_obj': keyword_definition_obj.id,
        'keyword_definition_user_vote': keyword_definition_user_vote,
    }
    context.update(keyword_vote_data)
    context.update(keyword_definition_vote_data)

    return render(request, 'app01/keyword_detail.html', context)


def question_json(request):
    try:
        # Get the root question
        root_question = Question.objects.first()  # ID of first question == 10
    except ObjectDoesNotExist:
        return HttpResponse("Root question does not exist.", status=404)

    # Recursive function to build the tree
    def build_tree(question):
        return {
            "name": str(question.question_tag),  # Add this line to ensure the question_tag is serialized
            "children": [build_tree(child) for child in question.children.all()],
            "question_text": question.question_text if hasattr(question, 'question_text') else ""
        }

    # Build the tree and return as JSON
    tree = build_tree(root_question)
    return JsonResponse(tree, safe=False)


def question_tree(request):
    return render(request, 'app01/question_tree.html')


def keyword_json(request):
    try:
        # Get the root keyword
        root_keyword = KeyWord.objects.first()  # changed from: KeyWord.objects.get(id=2)
    except ObjectDoesNotExist:
        return HttpResponse("Root keyword does not exist.", status=404)

    # Recursive function to build the tree
    def build_tree(keyword):
        return {
            "name": keyword.word,
            "children": [build_tree(child) for child in keyword.children.all()],
            "definition": keyword.definition.definition if hasattr(keyword, 'definition') else ""
        }

    # Build the tree and return as JSON
    tree = build_tree(root_keyword)
    return JsonResponse(tree, safe=False)


def keyword_tree(request):
    return render(request, 'app01/keyword_tree.html')


@login_required
def create_proposals(request):
    keyword_form = None
    question_form = None
    keyword_error = None
    question_error = None

    if request.method == 'POST':
        if 'keyword_submit' in request.POST:
            keyword_form = KeyWordForm(request.POST)
            if keyword_form.is_valid():
                try:
                    keyword_form.save(creator=request.user)
                except forms.ValidationError as e:
                    keyword_error = str(e)
        elif 'question_submit' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                try:
                    question_form.save(creator=request.user)
                except forms.ValidationError as e:
                    question_error = str(e)
    else:
        keyword_form = KeyWordForm()
        question_form = QuestionForm()

    context = {
        'keyword_form': keyword_form,
        'question_form': question_form,
        'keyword_error': keyword_error,
        'question_error': question_error,
    }
    return render(request, 'app01/create_proposals.html', context)


def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}, your account has been created!')
            return redirect('app01:home')
    else:
        user_form = UserRegisterForm()
        profile_form = UserProfileForm()
    return render(request, 'app01/register.html', {'user_form': user_form, 'profile_form': profile_form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('app01:home')
    else:
        form = AuthenticationForm()
    return render(request, 'app01/login.html', {'form': form})  # Updated template path


def home(request):
    total_users = UserProfile.objects.filter(is_live=True, is_verified=True).count()
    return render(request, 'app01/home.html', {'total_users': total_users})  # Updated template path


def logout_view(request):
    logout(request)
    return redirect('app01:home')


@login_required
def account(request):
    if request.method == 'POST':
        # Check which form has been submitted
        if 'user_profile_form' in request.POST:
            form = UserProfileForm(request.POST, instance=request.user.userprofile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your account details have been updated!')

        elif 'user_form' in request.POST:
            form = UserChangeForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your user details have been updated!')

        elif 'password_change_form' in request.POST:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password has been updated!')
        else:
            messages.error(request, 'An error occurred.')

    # Initialize forms
    user_profile_form = UserProfileForm(instance=request.user.userprofile)
    user_form = UserChangeForm(instance=request.user)
    password_change_form = PasswordChangeForm(request.user)

    return render(request, 'app01/account.html', {
        'user_profile_form': user_profile_form,
        'user_form': user_form,
        'password_change_form': password_change_form
    })




