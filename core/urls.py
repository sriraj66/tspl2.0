
from django.urls import path
from core import views, auth

urlpatterns = [
    path("", views.index, name="index"),
    # For Auth IN and OUT using Custom Functions
    path("accounts/login/", auth.user_login, name="login"),
    path("accounts/register/", auth.user_register, name="user_register"),
    path("logout/", auth.user_logout, name="user_logout"),
]

urlpatterns += [
    path("form/<int:id>",views.register_form,name='register_form'),
    path("paymenthandler/<int:id>", views.payment_handler, name="payment_handler"),

    path("res",views.index,name="player_result"),
    path("res.all",views.index,name="allResults"),
    path("update/points",views.index)
]
