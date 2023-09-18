from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import UserProfile, Status, VoteType, Keyword, Definition, QuestionTag, Question, Vote, AnswerBinary, Discussion, Comment
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegisterForm, UserProfileForm, LoginForm, VoteForm, QuestionForm, KeywordForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseNotAllowed
from django.views.generic import ListView
from django.contrib.auth.models import User, ContentType
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.http import HttpResponseForbidden
from .forms import KeywordForm, QuestionForm
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
def question_binary(request, question_tag):
    try:
        keyword = Keyword.objects.get(word=question_tag)
    except Keyword.DoesNotExist:
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

    answer_content_type = ContentType.objects.get_for_model(answer_obj)
    answer_user_vote = answer_obj.get_user_vote(request.user)

    context = {
        'question': question_obj,
        'question_text': question_obj.question_text,
        'question_tag': question_tag_obj,
        'answer': answer_obj,
        'answer_obj_id': answer_obj.id,
        'answer_content_type_id': answer_content_type.id,
        'answer_user_vote': answer_user_vote,
    }

    return render(request, 'app01/question_binary.html', context)


@login_required
def add_comment(request):
    if request.method == "POST":
        content = request.POST.get('content')
        question_tag_id = request.POST.get('question_tag')

        # Get the votable content type for Question
        content_type = ContentType.objects.get_for_model(QuestionTag)

        # Create the discussion if not exists
        discussion, created = Discussion.objects.get_or_create(
            votable_content_type=content_type,
            votable_object_id=question_tag_id,
            defaults={'title': 'Discussion on Creator Notes', 'created_by': request.user}
        )

        # Add the comment
        comment = Comment.objects.create(
            discussion=discussion,
            content=content,
            creator=request.user
        )

        # Redirect to the discussion page
        return redirect('app01:question_discussion', question_tag=question_tag_id)

    # Handle other HTTP methods if required.
    return HttpResponseNotAllowed(['POST'])


@login_required
def question_discussion(request, question_tag):
    try:
        keyword = Keyword.objects.get(word=question_tag)
    except Keyword.DoesNotExist:
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

    question_error = None
    keyword_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    question_content_type = ContentType.objects.get_for_model(question_obj)
    question_tag_content_type = ContentType.objects.get_for_model(question_tag_obj)

    question_vote_data = question_obj.get_vote_data()
    question_user_vote = question_obj.get_user_vote(request.user)
    content_type = ContentType.objects.get_for_model(QuestionTag)
    discussion = Discussion.objects.filter(votable_content_type=content_type,
                                           votable_object_id=question_obj.question_tag.id).first()
    comments = []
    if discussion:
        comments = Comment.objects.filter(discussion=discussion)

    context = {
        'total_users': total_users,
        'keyword_error': keyword_error,
        'question_error': question_error,
        'question': question_obj,
        'question_text': question_obj.question_text,
        'question_creator_notes': question_obj.creator_notes,
        'question_obj_id': question_obj.id,
        'question_content_type_id': question_content_type.id,
        'question_user_vote': question_user_vote,
        'question_tag': question_tag_obj,
        'question_tag_obj_id': question_tag_obj.id,
        'question_tag_content_type_id': question_tag_content_type.id,
        'comments': comments

    }
    context.update(question_vote_data)

    return render(request, 'app01/question_discussion.html', context)

# @login_required
# def question_detail(request, question_tag):
#     try:
#         keyword = Keyword.objects.get(word=question_tag)
#     except Keyword.DoesNotExist:
#         raise Http404("No Keyword matches the given query.")
#
#     try:
#         question_tag_obj = keyword.questiontag_set.first()
#         if question_tag_obj is None:
#             raise ObjectDoesNotExist
#     except ObjectDoesNotExist:
#         raise Http404("No QuestionTag matches the given query.")
#
#     try:
#         question_obj = Question.objects.get(question_tag=question_tag_obj)
#     except Question.DoesNotExist:
#         raise Http404("No Question matches the given query.")
#
#     try:
#         answer_obj = AnswerBinary.objects.get(question_tag=question_tag_obj)
#     except AnswerBinary.DoesNotExist:
#         raise Http404("No AnswerBinary matches the given query.")
#
#     question_error = None
#     keyword_error = None
#     total_users = UserProfile.objects.filter(is_live=True).count()
#
#     question_content_type = ContentType.objects.get_for_model(question_obj)
#     question_tag_content_type = ContentType.objects.get_for_model(question_tag_obj)
#     answer_content_type = ContentType.objects.get_for_model(answer_obj)
#
#     if request.method == 'POST' and 'question_submit' in request.POST:
#         question_form = QuestionForm(request.POST)
#         if question_form.is_valid():
#             try:
#                 new_question = question_form.save(commit=False)
#                 new_question.creator = request.user
#                 new_question.parent = question_obj
#                 new_question.save()
#                 return redirect(new_question.get_absolute_url())
#             except forms.ValidationError as e:
#                 question_error = str(e)
#
#     else:
#         question_form = QuestionForm()
#
#     if request.method == 'POST' and 'keyword_submit' in request.POST:
#         keyword_form = KeywordForm(request.POST)
#         if keyword_form.is_valid():
#             try:
#                 new_keyword = keyword_form.save(creator=request.user)
#                 return redirect(new_keyword.keyword.get_absolute_url())
#             except forms.ValidationError as e:
#                 keyword_error = str(e)
#     else:
#         keyword_form = KeywordForm()
#
#     question_vote_data = question_obj.get_vote_data()
#     question_user_vote = question_obj.get_user_vote(request.user)
#     question_tag_vote_data = question_tag_obj.get_vote_data()
#     question_tag_user_vote = question_tag_obj.get_user_vote(request.user)
#     answer_vote_data = answer_obj.get_vote_data()
#     answer_user_vote = answer_obj.get_user_vote(request.user)
#
#     context = {
#         'total_users': total_users,
#         'keyword_form': keyword_form,
#         'keyword_error': keyword_error,
#         'question_form': question_form,
#         'question_error': question_error,
#         'question': question_obj,
#         'question_text': question_obj.question_text,
#         'question_obj_id': question_obj.id,
#         'question_content_type_id': question_content_type.id,
#         'question_user_vote': question_user_vote,
#         'question_tag': question_tag_obj,
#         'question_tag_obj_id': question_tag_obj.id,
#         'question_tag_content_type_id': question_tag_content_type.id,
#         'question_tag_user_vote': question_tag_user_vote,
#         'answer': answer_obj,
#         'answer_obj_id': answer_obj.id,
#         'answer_content_type_id': answer_content_type.id,
#         'answer_user_vote': answer_user_vote,
#
#     }
#     context.update(question_vote_data)
#     context.update(question_tag_vote_data)
#     context.update(answer_vote_data)
#
#     return render(request, 'app01/question_detail.html', context)


@login_required
def answer_binary(request, question_tag):
    keyword = get_object_or_404(Keyword, word=question_tag)
    question_tag_obj = get_object_or_404(keyword.questiontag_set.all())
    question_obj = get_object_or_404(Question, question_tag=question_tag_obj)
    answer_obj = get_object_or_404(AnswerBinary, question_tag=question_tag_obj)

    total_users = UserProfile.objects.filter(is_live=True).count()

    context = {
        'total_users': total_users,
        'question': question_obj,
        'question_text': question_obj.question_text,
        'question_obj_id': question_obj.id,
        'question_content_type_id': ContentType.objects.get_for_model(question_obj).id,
        'question_user_vote': question_obj.get_user_vote(request.user),
        'question_tag': question_tag_obj,
        'question_tag_obj_id': question_tag_obj.id,
        'question_tag_content_type_id': ContentType.objects.get_for_model(question_tag_obj).id,
        'question_tag_user_vote': question_tag_obj.get_user_vote(request.user),
        'answer': answer_obj,
        'answer_obj_id': answer_obj.id,
        'answer_content_type_id': ContentType.objects.get_for_model(answer_obj).id,
        'answer_user_vote': answer_obj.get_user_vote(request.user),
    }
    context.update({**question_obj.get_vote_data(), **question_tag_obj.get_vote_data(), **answer_obj.get_vote_data()})
    return render(request, 'app01/answer_binary.html', context)


@login_required
def content_vote(request, question_tag):
    try:
        keyword = Keyword.objects.get(word=question_tag)
    except Keyword.DoesNotExist:
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

    question_vote_data = question_obj.get_vote_data()
    question_user_vote = question_obj.get_user_vote(request.user)
    question_tag_vote_data = question_tag_obj.get_vote_data()
    question_tag_user_vote = question_tag_obj.get_user_vote(request.user)
    answer_vote_data = answer_obj.get_vote_data()
    answer_user_vote = answer_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword_error': keyword_error,
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

    return render(request, 'app01/content_vote.html', context)


@login_required
def content_vote_results(request, question_tag):
    try:
        keyword = Keyword.objects.get(word=question_tag)
    except Keyword.DoesNotExist:
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

    question_vote_data = question_obj.get_vote_data()
    question_user_vote = question_obj.get_user_vote(request.user)
    question_tag_vote_data = question_tag_obj.get_vote_data()
    question_tag_user_vote = question_tag_obj.get_user_vote(request.user)
    answer_vote_data = answer_obj.get_vote_data()
    answer_user_vote = answer_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword_error': keyword_error,
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

    return render(request, 'app01/content_vote_results.html', context)


@login_required
def keyword_dictionary(request):
    keyword_form = None
    keyword_error = None

    if request.method == 'POST':
        if 'keyword_submit' in request.POST:
            keyword_form = KeywordForm(request.POST)
            if keyword_form.is_valid():
                try:
                    keyword_form.save(creator=request.user)
                except forms.ValidationError as e:
                    keyword_error = str(e)

    else:
        keyword_form = KeywordForm()

    keywords = Keyword.objects.all().order_by('word')

    context = {
        'keywords': keywords,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
    }

    return render(request, 'app01/keyword_dictionary.html', context)


@login_required
def keyword_detail(request, keyword):
    keyword_obj = get_object_or_404(Keyword, word=keyword)
    definition_obj = keyword_obj.definitions.exclude(status=Status.ALTERNATIVE.value).first()
    keyword_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    keyword_votable_type = ContentType.objects.get_for_model(keyword_obj)
    definition_votable_type = ContentType.objects.get_for_model(definition_obj)

    if request.method == 'POST' and 'keyword_submit' in request.POST:
        keyword_form = KeywordForm(request.POST)
        if keyword_form.is_valid():
            try:
                new_keyword = keyword_form.save(creator=request.user)
                return redirect(new_keyword.keyword.get_absolute_url())
            except forms.ValidationError as e:
                keyword_error = str(e)
    else:
        keyword_form = KeywordForm()

    keyword_vote_data = keyword_obj.get_vote_data()
    keyword_user_vote = keyword_obj.get_user_vote(request.user)
    definition_vote_data = definition_obj.get_vote_data()
    definition_user_vote = definition_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword': keyword_obj,
        'keyword_definition': definition_obj,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
        'keyword_votable_type': keyword_votable_type.id,
        'keyword_obj': keyword_obj.id,
        'keyword_user_vote': keyword_user_vote,
        'definition_votable_type': definition_votable_type.id,
        'definition_obj': definition_obj.id,
        'definition_user_vote': definition_user_vote,
    }
    context.update(keyword_vote_data)
    context.update(definition_vote_data)

    return render(request, 'app01/keyword_detail.html', context)


@login_required
def keyword_results(request, keyword):
    keyword_obj = get_object_or_404(Keyword, word=keyword)
    definition_obj = keyword_obj.definitions.exclude(status=Status.ALTERNATIVE.value).first()
    keyword_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    keyword_votable_type = ContentType.objects.get_for_model(keyword_obj)
    definition_votable_type = ContentType.objects.get_for_model(definition_obj)

    if request.method == 'POST' and 'keyword_submit' in request.POST:
        keyword_form = KeywordForm(request.POST)
        if keyword_form.is_valid():
            try:
                new_keyword = keyword_form.save(creator=request.user)
                return redirect(new_keyword.keyword.get_absolute_url())
            except forms.ValidationError as e:
                keyword_error = str(e)
    else:
        keyword_form = KeywordForm()

    keyword_vote_data = keyword_obj.get_vote_data()
    keyword_user_vote = keyword_obj.get_user_vote(request.user)
    definition_vote_data = definition_obj.get_vote_data()
    definition_user_vote = definition_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword': keyword_obj,
        'definition': definition_obj,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
        'keyword_votable_type': keyword_votable_type.id,
        'keyword_obj': keyword_obj.id,
        'keyword_user_vote': keyword_user_vote,
        'definition_votable_type': definition_votable_type.id,
        'definition_obj': definition_obj.id,
        'definition_user_vote': definition_user_vote,
    }
    context.update(keyword_vote_data)
    context.update(definition_vote_data)

    return render(request, 'app01/keyword_results.html', context)


@login_required
def keyword_discussion(request, keyword):
    keyword_obj = get_object_or_404(Keyword, word=keyword)
    definition_obj = keyword_obj.definitions.exclude(status=Status.ALTERNATIVE.value).first()
    keyword_error = None
    total_users = UserProfile.objects.filter(is_live=True).count()

    keyword_votable_type = ContentType.objects.get_for_model(keyword_obj)
    definition_votable_type = ContentType.objects.get_for_model(definition_obj)

    if request.method == 'POST' and 'keyword_submit' in request.POST:
        keyword_form = KeywordForm(request.POST)
        if keyword_form.is_valid():
            try:
                new_keyword = keyword_form.save(creator=request.user)
                return redirect(new_keyword.keyword.get_absolute_url())
            except forms.ValidationError as e:
                keyword_error = str(e)
    else:
        keyword_form = KeywordForm()

    keyword_vote_data = keyword_obj.get_vote_data()
    keyword_user_vote = keyword_obj.get_user_vote(request.user)
    definition_vote_data = definition_obj.get_vote_data()
    definition_user_vote = definition_obj.get_user_vote(request.user)

    context = {
        'total_users': total_users,
        'keyword': keyword_obj,
        'definition': definition_obj,
        'keyword_form': keyword_form,
        'keyword_error': keyword_error,
        'keyword_votable_type': keyword_votable_type.id,
        'keyword_obj': keyword_obj.id,
        'keyword_user_vote': keyword_user_vote,
        'definition_votable_type': definition_votable_type.id,
        'definition_obj': definition_obj.id,
        'definition_user_vote': definition_user_vote,
    }
    context.update(keyword_vote_data)
    context.update(definition_vote_data)

    return render(request, 'app01/keyword_discussion.html', context)


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


@login_required
@transaction.atomic  # To ensure atomicity
def create_keyword(request):
    if request.method == 'POST':
        form = KeywordForm(request.POST)

        if form.is_valid():
            keyword = form.save(commit=True, creator=request.user)
            messages.success(request, 'Keyword, definition, discussion, and initial comment successfully created.')
            return redirect('app01:keyword_detail', keyword=keyword.word)
        else:
            messages.error(request, 'There was an error with your submission. Please review the form and try again.')

    else:
        form = KeywordForm()

    context = {
        'form': form,
    }
    return render(request, 'app01/create_keyword.html', context)


@login_required
def create_question(request):
    question_form = None
    question_error = None

    if request.method == 'POST':
        if 'question_submit' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                try:
                    question = question_form.save(creator=request.user)

                    # Create a Discussion & Comment for the new Question
                    discussion = Discussion.objects.create(
                        votable_content_type=ContentType.objects.get_for_model(question),
                        votable_object_id=question.id,
                        title=f"Discussion on Question: {question}",
                        created_by=request.user
                    )
                    Comment.objects.create(
                        discussion=discussion,
                        creator=request.user,
                        comment=f"Creator's note for {question}"
                    )

                except forms.ValidationError as e:
                    question_error = str(e)
    else:
        question_form = QuestionForm()

    context = {
        'question_form': question_form,
        'question_error': question_error,
    }
    return render(request, 'app01/create_question.html', context)


@login_required
def create_proposals(request):
    keyword_form = None
    question_form = None
    keyword_error = None
    question_error = None

    if request.method == 'POST':
        if 'keyword_submit' in request.POST:
            keyword_form = KeywordForm(request.POST)
            if keyword_form.is_valid():
                try:
                    keyword = keyword_form.save(creator=request.user)

                    # Create a Discussion & Comment for the new Keyword
                    discussion = Discussion.objects.create(
                        votable_content_type=ContentType.objects.get_for_model(keyword),
                        votable_object_id=keyword.id,
                        title=f"Discussion on Keyword: {keyword}",
                        created_by=request.user
                    )
                    Comment.objects.create(
                        discussion=discussion,
                        creator=request.user,
                        comment=f"Creator's note for {keyword}"
                    )

                except forms.ValidationError as e:
                    keyword_error = str(e)

        elif 'question_submit' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                try:
                    question = question_form.save(creator=request.user)

                    # Create a Discussion & Comment for the new Question
                    discussion = Discussion.objects.create(
                        votable_content_type=ContentType.objects.get_for_model(question),
                        votable_object_id=question.id,
                        title=f"Discussion on Question: {question}",
                        created_by=request.user
                    )
                    Comment.objects.create(
                        discussion=discussion,
                        creator=request.user,
                        comment=f"Creator's note for {question}"
                    )

                except forms.ValidationError as e:
                    question_error = str(e)
    else:
        keyword_form = KeywordForm()
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




