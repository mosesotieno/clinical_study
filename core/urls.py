from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard and main pages
    path('', views.dashboard, name='dashboard'),
    
    # Participant management
    path('enroll/', views.enroll_participant, name='enroll_participant'),
    path('participants/', views.participant_list, name='participant_list'),
    path('participant/<int:participant_id>/', views.participant_detail, name='participant_detail'),
    path('participant/<int:participant_id>/delete/', views.delete_participant, name='delete_participant'),
    
    # Visit workflow URLs
    path('visit/<int:visit_id>/vitals/', views.take_vitals, name='vitals'),
    path('visit/<int:visit_id>/doctor/', views.doctor_assessment, name='doctor_assessment'),
    path('visit/<int:visit_id>/psychiatrist/', views.psychiatrist_assessment, name='psychiatrist_assessment'),
    path('visit/<int:visit_id>/lab/', views.create_lab_request, name='lab_request'),
    path('visit/<int:visit_id>/complete/', views.complete_visit, name='complete_visit'),
    
    # Visit management
    path('visits/active/', views.active_visits, name='active_visits'),
    path('visits/completed/', views.completed_visits, name='completed_visits'),
    path('visit/create/<int:participant_id>/', views.create_visit, name='create_visit'),
    
    # Reports and exports
    path('reports/study-progress/', views.study_progress_report, name='study_progress_report'),
    path('reports/participant-data/', views.participant_data_export, name='participant_data_export'),
    path('reports/visit-summary/', views.visit_summary_report, name='visit_summary_report'),
    
    # API endpoints (if needed)
    path('api/participant-search/', views.participant_search, name='participant_search'),
    path('api/visit-status/<int:visit_id>/', views.visit_status, name='visit_status'),
]