from django.shortcuts import render,redirect,HttpResponse
from .forms import LoginForm, RegisterForm, PlayerRegistration
from django.contrib.auth.decorators import login_required
from django.contrib.messages import success,warning,error
from django.contrib.auth import logout,login
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger('core')
    
def user_login(request):
    if request.user.is_authenticated:
        return redirect("index")
    
    if request.POST:
        form = LoginForm(data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            success(request,f"Welcome back {user.get_full_name()} !!")
            logger.info("User Loged In")
            return redirect("index")
    else:
        form = LoginForm()
    return render(request,"registration/login.html",{
        "form": form
    })
    
    
def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False) 
            user.email = user.username  
            user.save()  
            login(request, user)
            success(request,f"Welcome {user.get_full_name()}")
            logger.info("User Loged In")
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {
        "form": form,
    })
    
    
@login_required
def user_logout(request):
    if request.POST:
        logout(request)
        logger.info("User Loged out")
    return redirect("login")
