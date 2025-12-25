
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="con_index"),
    path("upload", views.data_upload,name="con_upload"),
    path('trigger-mail/', views.trigger_mail, name='con_trigger_mail'),
    path('update-points',views.updatePoints,name="con_updatePoints"),
    
    path("send-remaining-payment-mail/", views.send_remaining_payment_mail, name="con_send_remaining_payment_mail"),
    path("send-selection-payment-mail/", views.send_selection_status_mail, name="con_send_selection_status_mail"),
    path("send-mail",views.send_bulk_mail, name="con_send_bulk_mail"),
    path("migrate-reg-ids/", views.migrate_reg_ids, name="con_migrate_reg_ids")
]


