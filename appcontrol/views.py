import logging
from datetime import datetime
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, HttpResponse 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.models import PlayerRegistration, Season, Payment, User
from core.utils import get_general_settings
from core.task import send_success_email, send_payment_reminder_email, send_selection_status_email, submit_csv_task, send_custom_email
from django.db.models import Q
import pandas as pd

logger = logging.getLogger("appcontrol")



# ---------- INDEX ----------
@login_required
def index(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")

    context = {
        "settings": get_general_settings()
    }
    return render(request, "appcontrol/index.html", context)

@login_required
def data_upload(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")

    if request.method == "POST":
        data_file = request.FILES.get("data_file")
        points_file = request.FILES.get("points_file")
        season_id = request.POST.get("season_id")

        if not data_file or not data_file.name.endswith(".csv"):
            messages.error(request, "Invalid file. Upload a CSV file.")
            return render(request, "appcontrol/dataupload.html", {"seasons": Season.objects.all()})

        if not Season.objects.filter(id=season_id).exists():
            messages.error(request, "Season is required.")
            return render(request, "appcontrol/dataupload.html", {"seasons": Season.objects.all()})

        # Read files as bytes to pass to Celery
        data_bytes = data_file.read()
        points_bytes = points_file.read() if points_file else None

        submit_csv_task(data_bytes,points_bytes, season_id)

        messages.success(request, f"Processing...")

        return redirect("con_upload")

    return render(request, "appcontrol/dataupload.html", {
        "seasons": Season.objects.all()
    })


@login_required
def trigger_mail(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")

    seasons = Season.objects.all()
    registrations = []

    season_id = request.GET.get("season_id")
    query = request.GET.get("q", "")
    mail_filter = request.GET.get("mail_filter", "all")  # all / sent / unsent

    if season_id:
        # Only completed players visible
        registrations = PlayerRegistration.objects.filter(
            season=season_id,
            is_compleated=True
        )

        # Mail Sent Filter
        if mail_filter == "sent":
            registrations = registrations.filter(is_mail_sent=True)
        elif mail_filter == "unsent":
            registrations = registrations.filter(is_mail_sent=False)

        # Search Filter
        if query:
            registrations = registrations.filter(
                Q(reg_id__icontains=query) |
                Q(user__username__icontains=query) |
                Q(player_name__icontains=query)
            )

    # POST → SEND EMAILS
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_ids")

        if not selected_ids:
            messages.error(request, "No players selected.")
            return redirect(f"{request.path}?season_id={season_id}&q={query}&mail_filter={mail_filter}")

        for reg in PlayerRegistration.objects.filter(id__in=selected_ids, is_compleated=True):

            payment = Payment.objects.filter(
                registration=reg.id,
                user=reg.user
            ).order_by("-created_at").first()

            if not payment:
                logger.warning(f"No payment found for reg_id={reg.reg_id}")
                continue

            context = {
                "id": reg.tx_id,
                "reg_id": reg.reg_id,
                "amount": payment.amount,
                "zone": reg.zone,
                "settings": get_general_settings()
            }

            try:
                send_success_email(
                    subject="Registration Completed",
                    to=reg.user.email,
                    context=context
                )

                reg.is_mail_sent = True
                reg.save()

                logger.info(f"[MAIL SENT] reg_id={reg.reg_id}")

            except Exception as e:
                logger.error(f"[MAIL ERROR] reg_id={reg.reg_id} error={str(e)}")

        messages.success(request, "Emails sent successfully!")
        return redirect(f"{request.path}?season_id={season_id}&q={query}&mail_filter={mail_filter}")

    return render(request, "appcontrol/trigger_mail.html", {
        "seasons": seasons,
        "registrations": registrations,
        "mail_filter": mail_filter,
    })

@login_required
def updatePoints(request):
    if not request.user.is_superuser:
        return HttpResponse("Access Denied", status=403)

    settings = get_general_settings()
    context = {
        "settings": settings,
        "seasons": Season.objects.all()
    }

    if request.method == "POST":
        try:
            # Season selection
            season_id = request.POST.get("season_id")
            if not season_id:
                return HttpResponse("Season is required.", status=400)

            try:
                season = Season.objects.get(id=season_id)
            except Season.DoesNotExist:
                return HttpResponse("Invalid season.", status=400)

            # CSV input
            csv_file = request.FILES.get("points_file")
            if not csv_file:
                return HttpResponse("Points CSV file is required.", status=400)

            # Read CSV (with header: reg_id,points)
            df = pd.read_csv(csv_file)

            # Required columns check
            if not {"reg_id", "points"}.issubset(df.columns):
                return HttpResponse("CSV must contain 'reg_id' and 'points' columns.", status=400)

            # Add status field
            df["status"] = False

            # Convert to list-of-lists for easy writing
            data_rows = df.values.tolist()

            def updateInDb(row):
                reg_id = str(row[0]).strip()
                points = row[1]

                # Validate points
                try:
                    points = float(points)
                except:
                    row[2] = False
                    return

                # Update DB
                try:
                    obj = PlayerRegistration.objects.get(reg_id=reg_id, season=season)
                    obj.points = points
                    obj.save()
                    row[2] = True
                except Exception as e:
                    logger.error(f"{reg_id} {e} ")
                    row[2] = False

            # Update each row
            for row in data_rows:
                updateInDb(row)

            # Apply the updated status back to dataframe
            df["status"] = [row[2] for row in data_rows]

            # color code
            def color_status(val):
                return (
                    'background-color: green; color: white;'
                    if val else
                    'background-color: red; color: white;'
                )

            # This is your ORIGINAL coloured table
            table_html = (
                df.style.map(color_status, subset=["status"])
                .set_table_attributes('class="table table-bordered"')
                .to_html()
            )

            # Build HTML: EXACT SAME STRUCTURE AS BEFORE + GO BACK
            html_response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Player Points Update</title>
                <link rel="stylesheet"
                    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
                <style> td, th {{ text-align: center; }} </style>
            </head>

            <body class="container mt-4">
                <h2 class="mb-3">{season.title} {season.year}</h2>
                <hr/>
                <p class="mb-3">Player Points updated</p>

                <a href="/master">Go Back</a>
                {table_html}
            </body>
            </html>
            """

            return HttpResponse(html_response)

        except Exception as e:
            logger.error(e)
            return HttpResponse(str(e))

    # GET request renders upload page
    return render(request, "appcontrol/updatePoints.html", context)

@login_required
def send_remaining_payment_mail(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")

    seasons = Season.objects.all()
    registrations = []
    settings = get_general_settings()

    season_id = request.GET.get("season_id")
    query = request.GET.get("q", "")

    if season_id:
        regs = PlayerRegistration.objects.filter(
            season=season_id
        )

        if query:
            regs = regs.filter(
                Q(reg_id__icontains=query) |
                Q(user__username__icontains=query) |
                Q(player_name__icontains=query)
            )

        # Attach payment info to each registration
        registrations = []
        for r in regs:
            payment = Payment.objects.filter(registration=r.id, user=r.user.id).first()
            registrations.append({
                "reg": r,
                "payment_amount": payment.amount if payment else "N/A"
            })

    # POST → Send emails
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_ids")
        print(selected_ids)
        if not selected_ids:
            messages.error(request, "No players selected.")
            return redirect(request.path + f"?season_id={season_id}&q={query}")

        for r in PlayerRegistration.objects.filter(id__in=selected_ids):
            payment = Payment.objects.filter(registration=r.id, user=r.user.id).order_by('-created_at').first()
            if not payment:
                continue
            context = {
                "id": r.tx_id,
                "reg_id": r.reg_id,
                "amount": payment.amount,
                "zone": r.zone,
                "settings": settings
            }
            try:
                send_payment_reminder_email(
                    subject=f"Remaining Payment Due for {settings.current_season.title}",
                    to_email=r.user.email,
                    context=context
                )
                logger.info(f"[REMAINING PAYMENT MAIL SENT] reg_id={r.reg_id}")
            except Exception as e:
                logger.error(f"[MAIL ERROR] reg_id={r.reg_id} error={str(e)}")

        messages.success(request, "Remaining payment mails sent successfully!")
        return redirect(request.path + f"?season_id={season_id}&q={query}")

    return render(request, "appcontrol/send_remaining_payment_mail.html", {
        "seasons": seasons,
        "registrations": registrations,
        "settings": settings
    })


@login_required
def send_selection_status_mail(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")

    seasons = Season.objects.all()
    registrations = []
    settings = get_general_settings()

    season_id = request.GET.get("season_id")
    query = request.GET.get("q", "")

    if season_id:
        regs = PlayerRegistration.objects.filter(season=season_id)

        if query:
            regs = regs.filter(
                Q(reg_id__icontains=query) |
                Q(user__username__icontains=query) |
                Q(player_name__icontains=query)
            )

        # Attach payment info for display
        registrations = []
        for r in regs:
            payment = Payment.objects.filter(registration=r.id, user=r.user.id).first()
            registrations.append({
                "reg": r,
                "payment_amount": payment.amount if payment else "N/A"
            })

    # POST → Send emails
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_ids")
        if not selected_ids:
            messages.error(request, "No players selected.")
            return redirect(request.path + f"?season_id={season_id}&q={query}")

        for r in PlayerRegistration.objects.filter(id__in=selected_ids, is_compleated=True):
            context = {
                "obj": r,
                "settings": settings
            }

            try:
                send_selection_status_email(
                    subject=f"Your Selection Status Update for {settings.current_season.title}",
                    to_email=r.user.email,
                    context=context
                )
                logger.info(f"[SELECTION STATUS MAIL SENT] reg_id={r.reg_id}")
            except Exception as e:
                logger.error(f"[MAIL ERROR] reg_id={r.reg_id} error={str(e)}")

        messages.success(request, "Selection status mails sent successfully!")
        return redirect(request.path + f"?season_id={season_id}&q={query}")

    return render(request, "appcontrol/send_selection_email.html", {
        "seasons": seasons,
        "registrations": registrations,
        "settings": settings
    })

@login_required
def send_bulk_mail(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")
    settings = get_general_settings()
    if request.method == "POST":
        html_content = request.POST.get("email_html", "").strip()
        subject = request.POST.get("subject", "").strip()

        if not subject or not html_content:
            messages.error(request, "Subject and HTML content are required.")
            return redirect(request.path)

        users = User.objects.filter(email__isnull=False).exclude(email="")

        for user in users:
            # Pass actual user info as context
            context = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "season_title": settings.current_season.title,
                "start_date": settings.current_season.start_date,
                "end_date": settings.current_season.end_date,
                "amount": settings.current_season.amount,
                "year": settings.current_season.year
            }

            send_custom_email(
                subject=subject,
                to_email=user.email,
                html_content=html_content,
                context=context
            )

        messages.success(
            request,
            f"Bulk email queued for {users.count()} users! Delivery will happen shortly."
        )
        return redirect(request.path)

    return render(request, "appcontrol/send_mail.html")




