from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('file-manager/', views.file_manager, name='file_manager'),
    re_path(r'^file-manager/(?P<directory>.*)?/$', views.file_manager, name='file_manager'),
    path('delete-file/<str:file_path>/', views.delete_file, name='delete_file'),
    path('download-file/<str:file_path>/', views.download_file, name='download_file'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('mk-dir/', views.mk_dir, name='mk_dir'),
    path('delete-dir/', views.delete_dir, name='delete_dir'),
    path('save-info/<str:file_path>/', views.save_info, name='save_info'),
    path('download_all/', views.download_all, name='download_all'),
    path('chat/', views.chat, name='chat'),
    path("ask_question/", views.ask_question, name="ask_question"),

]
