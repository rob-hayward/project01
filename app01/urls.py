from django.urls import path
from . import views

app_name = 'app01'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('propose_question/', views.propose_question, name='propose_question'),
    path('propose_question/<int:parent_question_id>/', views.propose_question, name='propose_question'),
    path('proposed_changes/', views.ProposedChangesView.as_view(), name='proposed_changes'),
    path('submit_vote/', views.submit_vote, name='submit_vote'),
    path('question_detail/<int:pk>/', views.QuestionDetailView.as_view(), name='question_detail'),
]




