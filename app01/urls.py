from django.urls import path
from . import views

app_name = 'app01'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('create_keyword/', views.create_keyword, name='create_keyword'),
    path('create_question/', views.create_question, name='create_question'),
    path('create_proposals/', views.create_proposals, name='create_proposals'),
    path('keyword_dictionary/', views.keyword_dictionary, name='keyword_dictionary'),
    path('keyword_detail/<str:keyword>/', views.keyword_detail, name='keyword_detail'),
    path('keyword_results/<str:keyword>/', views.keyword_results, name='keyword_results'),
    path('keyword_discussion/<str:keyword>/', views.keyword_discussion, name='keyword_discussion'),
    path('question_json/', views.question_json, name='question_json'),
    path('question_tree/', views.question_tree, name='question_tree'),
    path('question/<str:question_tag>/', views.question_binary, name='question_binary'),
    path('question_discussion/<str:question_tag>/', views.question_discussion, name='question_discussion'),
    path('add_comment/', views.add_comment, name='add_comment'),
    path('answer_binary/<str:question_tag>/', views.answer_binary, name='answer_binary'),
    path('content_vote/<str:question_tag>/', views.content_vote, name='content_vote'),
    path('content_vote_results/<str:question_tag>/', views.content_vote_results, name='content_vote_results'),
    # path('question/<str:question_tag>/', views.question_detail, name='question_detail'),
    path('submit_vote/', views.submit_vote, name='submit_vote'),
]




