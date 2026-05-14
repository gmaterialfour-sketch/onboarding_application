from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_view, name='upload'),
    path('api/onboarding/process/', views.process_api, name='onboarding-process-api'),
    path('api/onboarding/validate/', views.validate_api, name='onboarding-validate-api'),
]
