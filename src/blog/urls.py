from . import views
from django.urls import path

urlpatterns = [
    path('blog', views.PostList.as_view(), name='blog'),
    path('blog/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.post_detail, name='post_detail'),
]