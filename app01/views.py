from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, Status, ProposalVote, VoteType
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegisterForm, UserProfileForm, UsernameForm, LoginForm, ProposeQuestionForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import ListView
from .models import Question, ProposalVoteData
from .forms import BinaryVoteForm, ProposalVoteForm, ChangeStatusForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django.http import HttpResponseForbidden


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
    print("Entered propose_question function.")
    if request.method == 'POST':
        form = ProposeQuestionForm(request.POST)
        print("Request is POST.")
        if form.is_valid():
            print("Form is valid.")
            question = form.save(commit=False)
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


@login_required
def submit_vote(request):
    print(f"VoteType.NO_VOTE.value: {VoteType.NO_VOTE.value}")
    if request.method == 'POST':
        form = ProposalVoteForm(request.POST, user=request.user)
        print(f"Form data: {request.POST}")  # Print the raw form data
        if form.is_valid():
            print("Form is valid")  # Print message if form is valid
            question = form.cleaned_data['question_id']
            vote = form.cleaned_data['vote']

            # Convert vote from string to int if needed
            if vote == '1':
                vote = VoteType.APPROVE.value
            elif vote == '-1':
                vote = VoteType.REJECT.value
            elif vote == '':
                vote = VoteType.NO_VOTE.value
            else:
                return JsonResponse({'error': 'Invalid vote value'}, status=400)

            # Create or update vote
            ProposalVote.objects.submit_vote(user=request.user, question=question, vote=vote)

            # Retrieve vote data
            vote_data = ProposalVoteData.objects.get(question=question)
            print(f"Vote data: {vote_data.__dict__}")  # Print the vote data object
            return JsonResponse({
                'total_votes': vote_data.total_votes,
                'total_approve_votes': vote_data.total_approve_votes,
                'total_reject_votes': vote_data.total_reject_votes,
                'approval_percentage': vote_data.approval_percentage,
                'participation_percentage': vote_data.participation_percentage,
            })
        else:
            print(f"Form errors: {form.errors}")  # Print form errors
            return JsonResponse({'error': 'Form is not valid'}, status=400)


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



