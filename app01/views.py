from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, QuestionStatus
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegisterForm, UserProfileForm, UsernameForm, LoginForm, ProposeQuestionForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import ListView
from .models import Question, BinaryVote
from .forms import BinaryVoteForm
from django.contrib.auth.models import User


@login_required
def propose_question(request, parent_question_id=None):
    if request.method == 'POST':
        form = ProposeQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.creator = request.user
            question.approved = False
            if parent_question_id is not None:
                question.parent = get_object_or_404(Question, id=parent_question_id)
            try:
                question.save()
                form.save_m2m()
                return redirect('app01:proposed_changes')
            except Exception as e:
                # catch the exception here and do something, like logging it or showing an error message to user.
                print(e)
    else:
        form = ProposeQuestionForm(initial={'parent_question': parent_question_id} if parent_question_id else None)
    return render(request, 'app01/propose_question.html', {'form': form})


# view for users to view all questions with proposed status and vote to either approve or reject them
class ProposedChangesView(ListView):
    model = Question
    template_name = 'app01/proposed_changes.html'

    def get_queryset(self):
        return Question.objects.filter(status=QuestionStatus.PROPOSED.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_users = User.objects.count()
        for question in context['object_list']:
            total_votes = BinaryVote.objects.filter(question=question).count()
            question.participation_percentage = (total_votes / total_users) * 100
            total_approve_votes = BinaryVote.objects.filter(question=question, vote=True).count()
            question.approval_rating = (total_approve_votes / total_votes) * 100 if total_votes > 0 else 0
            try:
                question.user_vote = BinaryVote.objects.get(user=self.request.user, question=question).vote
            except BinaryVote.DoesNotExist:
                question.user_vote = None
        return context


@login_required
def submit_vote(request):
    if request.method == 'POST':
        form = BinaryVoteForm(request.POST)
        if form.is_valid():
            question_id = form.cleaned_data['question_id']
            vote = form.cleaned_data['vote']
            if vote == '':
                vote = None

            question = Question.objects.get(id=question_id)
            try:
                existing_vote = BinaryVote.objects.get(user=request.user, question=question)
                if vote is None:
                    existing_vote.delete()
                else:
                    existing_vote.vote = vote
                    existing_vote.save()
            except BinaryVote.DoesNotExist:
                if vote is not None:
                    BinaryVote.objects.create(user=request.user, question=question, vote=vote)

            total_votes = question.total_votes()
            participation_percentage = question.participation_percentage()
            approval_percentage = question.approval_percentage()

            return JsonResponse({'total_votes': total_votes,
                                 'participation_percentage': participation_percentage,
                                 'approval_percentage': approval_percentage})
        else:
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
    users_count = UserProfile.objects.filter(is_live=True, is_verified=True).count()
    return render(request, 'app01/home.html', {'users_count': users_count})  # Updated template path


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



