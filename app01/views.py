from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from . import models
from .models import UserProfile, Status, VoteType, KeyWord, KeyWordDefinition, QuestionTag, Question, Vote
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegisterForm, UserProfileForm, UsernameForm, LoginForm, ProposeQuestionForm, VoteForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseNotAllowed
from django.views.generic import ListView
from django.contrib.auth.models import User, ContentType
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.http import HttpResponseForbidden
from .forms import KeyWordForm, QuestionForm
from django import forms
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.contenttypes.models import ContentType


@login_required
def submit_vote(request):
    if request.method == 'POST':
        form = VoteForm(request.POST, user=request.user)
        if form.is_valid():
            # Extract the user, votable_content_type, and votable_object_id from the form
            user = request.user
            votable_content_type = form.cleaned_data['votable_content_type']
            votable_object_id = form.cleaned_data['votable_object_id']
            vote_value = form.cleaned_data['vote']

            # Try to get an existing vote from this user for this object
            try:
                vote = Vote.objects.get(user=user, votable_content_type=votable_content_type, votable_object_id=votable_object_id)
            except Vote.DoesNotExist:
                vote = None

            if vote_value == VoteType.NO_VOTE.value:
                # If the user selected "No Vote", delete the vote if it exists
                if vote:
                    vote.delete()
            else:
                # If the user selected approve or reject, update the existing vote or create a new one
                if vote:
                    vote.vote = vote_value
                    vote.save()
                else:
                    form.save()

            votable_object = votable_content_type.get_object_for_this_type(id=votable_object_id)
            new_status = votable_object.calculate_status()
            user_vote = votable_object.get_user_vote(request.user)

            data = {
                'total_votes': votable_object.get_votes().exclude(vote=VoteType.NO_VOTE.value).count(),
                'status': new_status,
                'user_vote': user_vote,
                'approval_percentage': votable_object.approval_percentage,
                'rejection_percentage': 100 - votable_object.approval_percentage,
                'participation_percentage': votable_object.participation_percentage,
                'total_approve_votes': votable_object.total_approve_votes,  # added
                'total_reject_votes': votable_object.total_reject_votes,  # added
            }

            return JsonResponse(data)

        return HttpResponseNotAllowed(['POST'])


@login_required
def keyword_detail(request, keyword):
    # Fetch the keyword from the database
    keyword_obj = get_object_or_404(KeyWord, word=keyword)
    keyword_form = None
    keyword_error = None
    vote = None

    # Fetch the content type for the keyword model
    votable_content_type = ContentType.objects.get_for_model(keyword_obj)

    if request.method == 'POST':
        if 'keyword_submit' in request.POST:  # This is a keyword form submission
            keyword_form = KeyWordForm(request.POST)
            if keyword_form.is_valid():
                try:
                    new_keyword = keyword_form.save(creator=request.user, parent=keyword_obj)  # Pass the parent keyword
                    return redirect(new_keyword.keyword.get_absolute_url())  # Redirect to the new keyword detail view
                except forms.ValidationError as e:
                    keyword_error = str(e)
        elif 'vote_submit' in request.POST:  # This is a vote form submission
            vote_value = request.POST.get('vote')
            if vote_value:
                vote_value = int(vote_value)
                if vote:
                    vote.vote = vote_value
                    vote.save()
                else:
                    vote = Vote.objects.create(votable_object_id=keyword_obj.id, votable_content_type=votable_content_type, user=request.user, vote=vote_value)
                keyword_obj.calculate_status()  # Recalculate the status after the vote

    else:
        keyword_form = KeyWordForm()

    votes = keyword_obj.get_votes()
    total_votes = votes.count()
    total_approve_votes = votes.filter(vote=VoteType.APPROVE.value).count()
    total_reject_votes = votes.filter(vote=VoteType.REJECT.value).count()
    user_vote = keyword_obj.get_user_vote(request.user)

    context = {
        'keyword': keyword_obj,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
        'user_vote': user_vote,
        'participation_percentage': keyword_obj.participation_percentage,
        'approval_percentage': keyword_obj.approval_percentage,
        'votable_content_type': votable_content_type.id,  # Here's where we add the content type to the context
        'votable_object_id': keyword_obj.id,  # ... and the object id.
        'total_votes': total_votes,
        'total_approve_votes': total_approve_votes,
        'total_reject_votes': total_reject_votes,
    }

    return render(request, 'app01/keyword_detail.html', context)


def keyword_json(request):
    try:
        # Get the root keyword
        root_keyword = KeyWord.objects.get(id=2)  # ids start from 1 not 0
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


@login_required
def update_status(request, pk):
    # Check if the user is an admin
    if not request.user.is_staff:
        return HttpResponseForbidden()

    if request.method == 'POST':
        question = get_object_or_404(Question, pk=pk)
        form = ChangeStatusForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Status has been updated!')
        else:
            messages.error(request, 'An error occurred.')
        return redirect('app01:approved_changes')


class ApprovedChangesView(ListView):
    model = Question
    template_name = 'app01/approved_changes.html'
    context_object_name = 'questions'  # Change this to avoid confusion in the template

    def get_queryset(self):
        return Question.objects.filter(status=Status.APPROVED.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forms'] = {question.id: ChangeStatusForm(instance=question) for question in context['questions']}
        return context


class QuestionDetailView(DetailView):
    model = Question
    template_name = 'app01/question_detail.html'


class ProposedChangesView(ListView):
    model = Question
    template_name = 'app01/proposed_changes.html'

    def get_queryset(self):
        return Question.objects.filter(status=Status.PROPOSED.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = UserProfile.objects.filter(is_live=True).count()
        proposed_questions = []
        for question in context['object_list']:
            stats, created = ProposalVoteData.objects.get_or_create(question=question)
            question.total_votes = stats.total_votes
            question.participation_percentage = stats.participation_percentage
            question.total_approve_votes = stats.total_approve_votes
            question.total_reject_votes = stats.total_reject_votes
            question.approval_percentage = stats.approval_percentage  # This line has changed.
            try:
                question.user_vote = ProposalVote.objects.get(user=self.request.user, question=question).vote
            except ProposalVote.DoesNotExist:
                question.user_vote = None
            proposed_questions.append(question)
        context['proposed_questions'] = proposed_questions
        return context


@login_required
def propose_question(request, parent_question_id=None):
    if request.method == 'POST':
        form = ProposeQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.creator = request.user
            if parent_question_id is not None:
                question.parent_question = get_object_or_404(Question, id=parent_question_id)
            question.save()
            form.save_m2m()
            return redirect('app01:proposed_changes')
        else:
            print(form.errors.as_ul())
    else:
        form = ProposeQuestionForm(initial={'parent_question': parent_question_id} if parent_question_id else None)
    return render(request, 'app01/propose_question.html', {'form': form})




@login_required
def propose_keyword(request, parent_question_id=None):
    if request.method == 'POST':
        form = ProposeKeywordForm(request.POST)
        if form.is_valid():
            keyword = form.save(commit=False)
            question.creator = request.user
            if parent_question_id is not None:
                question.parent_question = get_object_or_404(Question, id=parent_question_id)
            question.save()
            form.save_m2m()
            print("Question saved.")
            return redirect('app01:proposed_changes')
        else:
            print("Form is not valid.")
            print(form.errors.as_ul())
    else:
        form = ProposeQuestionForm(initial={'parent_question': parent_question_id} if parent_question_id else None)
    return render(request, 'app01/propose_question.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}, your account has been created!')
            return redirect('app01:home')
    else:
        form = UserRegisterForm()
    return render(request, 'app01/register.html', {'form': form})  # Updated template path


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

        elif 'username_form' in request.POST:
            form = UsernameForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your username has been updated!')

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
    username_form = UsernameForm(instance=request.user)
    password_change_form = PasswordChangeForm(request.user)

    return render(request, 'app01/account.html', {
        'user_profile_form': user_profile_form,
        'username_form': username_form,
        'password_change_form': password_change_form
    })



