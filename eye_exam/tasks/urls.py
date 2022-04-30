from django.urls import path

from . import views


urlpatterns = [
    path('check', views.checkAnswer, name='check_answer'),
    path('<int:test_id>', views.test_list, name='test_list'),
    path('<str:slug>/excel', views.generate_excel, name='generate_excel')
]
