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
    path('submit_vote/', views.submit_vote, name='submit_vote'),
]




