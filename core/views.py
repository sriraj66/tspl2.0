from django.shortcuts import render,redirect,HttpResponse 
from .forms import PlayerRegistrationForm, LoginForm, RegisterForm, PlayerRegistration
from django.contrib.auth.decorators import login_required
from django.contrib.messages import success,warning,error
from django.contrib.auth import logout,login
from django.views.decorators.csrf import csrf_exempt
from .models import PlayerRegistration, Season, Payment
from .utils import get_general_settings
from .task import send_success_email
import logging
from . import paymentHandler
logger = logging.getLogger('core')

def index(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request, 'core/index.html', context= context)


@login_required
def register_form(request, id):
    user = request.user
    settings = get_general_settings()

    # Ensure settings exist
    if not settings:
        error(request, "Kindly contact admin, General settings not configured.")
        return redirect('index')

    # Ensure season exists
    try:
        season = Season.objects.get(id=id)
        if not season.accept_response or not settings.enable_registration:
            warning(request, "Registrations are closed currently.")
            return redirect('index')
    except Season.DoesNotExist:
        error(request, "Season does not exist.")
        return redirect('index')

    registration = PlayerRegistration.objects.filter(season=season, user=user).first()

    # ----------------------------
    # CASE 1: USER ALREADY REGISTERED
    # ----------------------------
    if registration:
        if season.registration_form_editable:
            if request.method == "POST":
                payment = Payment.objects.filter(user=user, registration=registration).first()
                form = PlayerRegistrationForm(request.POST, request.FILES, instance=registration)
                if form.is_valid():
                    registration = form.save()
                    if payment and (payment.is_compleated and payment.status == 'PAID' and registration.is_compleated):
                        success(request, "Details Updated")
                        return render(request, "core/success.html", {
                            "settings": settings,
                            "id": payment.payment_id,
                            "reg_id": registration.reg_id,
                            "order_id": payment.order_id,
                            "amount": payment.amount,
                            "zone": registration.zone,
                        })

                    if payment and payment.status == 'FAILED':
                        payment, err = paymentHandler.create_payment_for_registration(
                            user, registration, season.amount
                        )
                        if err:
                            error(request, f"Failed to create Razorpay order: {err}")
                            return redirect("index")

                        return render(request, "core/payment.html", {
                            "payment": payment,
                            "settings": settings,
                            "season": season,
                            "razorpay_key": settings.razorpay_key_id,
                            "callback_url": settings.callback_url,
                        })

                    if payment and not payment.is_compleated:
                        return render(request, "core/payment.html", {
                            "payment": payment,
                            "settings": settings,
                            "season": season,
                            "razorpay_key": settings.razorpay_key_id,
                            "callback_url": settings.callback_url,
                        })

                    payment, err = paymentHandler.create_payment_for_registration(
                        user, registration, season.amount
                    )
                    if err:
                        error(request, f"Failed to create Razorpay order: {err}")
                        return redirect("index")

                    return render(request, "core/payment.html", {
                        "payment": payment,
                        "settings": settings,
                        "season": season,
                        "razorpay_key": settings.razorpay_key_id,
                        "callback_url": settings.callback_url,
                    })
            else:
                form = PlayerRegistrationForm(instance=registration)
            
        
            print(registration.id)
            return render(request, "core/form.html", {
                "form": form,
                "settings": settings,
                "season": season,
                "button_message": "Save" if registration.is_paid  else "Compleate pending payment",
                "edit_mode": True,
            })

        else:
            try:
                payment = Payment.objects.filter(user=user, registration=registration).first()
                if payment is None:
                    raise Payment.DoesNotExist
                # If payment failed previously, create a new one to retry
                if payment.status == 'FAILED':
                    payment, err = paymentHandler.create_payment_for_registration(
                        user, registration, season.amount
                    )
                    if err:
                        error(request, f"Failed to create Razorpay order: {err}")
                        return redirect("index")

                    return render(request, "core/payment.html", {
                        "payment": payment,
                        "settings": settings,
                        "season": season,
                        "razorpay_key": settings.razorpay_key_id,
                        "callback_url": settings.callback_url,
                    })

                # If payment pending -> show the payment page
                if not payment.is_compleated:
                    print("Payment Pending")
                    return render(request, "core/payment.html", {
                        "payment": payment,
                        "season": season,
                        "settings": settings,
                        "razorpay_key": settings.razorpay_key_id,
                        "callback_url": settings.callback_url,
                    })

            except Payment.DoesNotExist:
                payment, err = paymentHandler.create_payment_for_registration(
                    user, registration, season.amount
                )
                if err:
                    error(request, f"Failed to create Razorpay order: {err}")
                    return redirect("index")

                return render(request, "core/payment.html", {
                    "payment": payment,
                    "season": season,
                    "settings": settings,
                    "razorpay_key": settings.razorpay_key_id,
                    "callback_url": settings.callback_url,
                })

            # If we reach here, payment exists and is completed -> render success
            return render(request, "core/success.html", {
                "settings": settings,
                "id": payment.payment_id,
                "reg_id": registration.reg_id,
                "order_id": payment.order_id,
                "amount": payment.amount,
                "zone": registration.zone,
            })

    # ----------------------------
    # CASE 2: USER REGISTERING FOR THE FIRST TIME
    # ----------------------------
    else:
        form = PlayerRegistrationForm()

        if request.method == 'POST':
            form = PlayerRegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                registration = form.save(commit=False)
                registration.user = user
                registration.season = season
                registration.save()

                payment, err = paymentHandler.create_payment_for_registration(
                    user, registration, season.amount
                )
                if err:
                    error(request, f"Failed to create Razorpay order: {err}")
                    return redirect("index")

                return render(request, "core/payment.html", {
                    "payment": payment,
                    "season": season,
                    "settings": settings,
                    
                    "razorpay_key": settings.razorpay_key_id,
                    "callback_url": settings.callback_url,
                })

        return render(request, 'core/form.html', {
            'form': form,
            "settings": settings,
            'season': season,
            'edit_mode': False,
        })


@csrf_exempt
def payment_handler(request, id):
    settings = get_general_settings()

    if not settings:
        error(request, "Kindly contact admin, General settings not configured.")
        return redirect('index')
    
    if request.method != "POST":
        return HttpResponse("Invalid Request Method")

    try:
        payment = Payment.objects.get(id=id)
    except Payment.DoesNotExist:
        return HttpResponse("Invalid Registration")
    
    registration = payment.registration
    payment_id = request.POST.get("razorpay_payment_id")
    order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")

    if not payment_id or not order_id or not signature:
        payment.status = "FAILED"
        payment.save()
        return render(request, "core/paymentfail.html", {"message": "Missing payment details.", "settings":settings})

    payment_details, err = paymentHandler.verify_payment_signature_and_fetch(
        payment_id, order_id, signature
    )
    if err:
        payment.status = "FAILED"
        payment.save()
        return render(request, "core/paymentfail.html", {"message": err, "settings":settings})

    payment.payment_id = payment_id
    payment.signature = signature
    payment.save()

    status = payment_details.get("status")

    # --------------------------------------------
    #       SUCCESS CASE
    # --------------------------------------------
    if status == "captured":
        registration = paymentHandler.handle_successful_capture(payment, payment_details)

        context = {
            "id": payment_id,
            "reg_id": registration.reg_id,
            "order_id": order_id,
            "amount": payment_details["amount"],
            "zone": registration.zone,
            "settings": settings
        
        }

        try:
            send_success_email(
                subject="Registration Completed",
                to=registration.user.email,
                context=context
            )
            registration.is_mail_sent = True
            registration.is_compleated = True
            registration.save()
        except:
            pass

        return render(request, "core/success.html", context)

    else:
        reason = payment_details.get("error_description", "Payment failed.")
        payment.status = "FAILED"
        payment.save()
        return render(request, "core/core/paymentfail.html", {"message": reason, "settings": settings})
