from django.urls import path
from main import views

# routing views
app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home_view'),
    path('logout/', views.user_logout, name='logout'),
    path('identify-camera/', views.identify_camera, name='identify_camera'),
    path('my-endpoint/', views.my_endpoint, name='my_endpoint'),
    path('video-data/', views.video_data, name='video_data'),
    path("sse/", views.sse, name="sse"),
    path("monitoring/", views.user_monitoring, name="monitoring"),
    path('user_profile/', views.user_profile, name='profile'),
    path('user-records/', views.user_record, name='record'),
    path('user-feedback/', views.user_feedback, name='feedback'),
    path('user-records-search/', views.search_records, name='search'),
    path('user-incorrect-postures/', views.upload_posture_photos, name='upload_postures'),
    path('user-incorrect-posture-photos/', views.posture_photos, name='posture_photos'),   
]

