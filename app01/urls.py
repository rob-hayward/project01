from django.urls import path
from . import views

app_name = 'app01'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('create_proposals/', views.create_proposals, name='create_proposals'),
    path('keyword_json/', views.keyword_json, name='keyword_json'),
    path('keyword_tree/', views.keyword_tree, name='keyword_tree'),
    path('keyword/<str:keyword>/', views.keyword_detail, name='keyword_detail'),
    path('propose_keyword/', views.propose_keyword, name='propose_keyword'),
    path('propose_question/', views.propose_question, name='propose_question'),
    path('propose_question/<int:parent_question_id>/', views.propose_question, name='propose_question'),
    path('proposed_changes/', views.ProposedChangesView.as_view(), name='proposed_changes'),
    path('submit_vote/', views.submit_vote, name='submit_vote'),
    path('question_detail/<int:pk>/', views.QuestionDetailView.as_view(), name='question_detail'),
    path('approved_changes/', views.ApprovedChangesView.as_view(), name='approved_changes'),
    path('update_status/<int:pk>/', views.update_status, name='update_status'),

]




