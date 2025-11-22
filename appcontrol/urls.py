
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="con_index"),
    path("upload", views.data_upload,name="con_upload"),
    path('trigger-mail/', views.trigger_mail, name='con_trigger_mail'),

]


