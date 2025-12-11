import csv
import io
import logging
from datetime import datetime
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, HttpResponse 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.models import PlayerRegistration, Season, Payment
from core.utils import get_general_settings
from core.task import send_success_email, send_payment_reminder_email, send_selection_status_email
from django.db.models import Q
import pandas as pd

logger = logging.getLogger("appcontrol")


# ---------- AGE CALCULATOR ----------
def calculate_age(dob_str):
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return 0


# ---------- INDEX ----------
@login_required
def index(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Invalid Access")

    context = {
        "settings": get_general_settings()
    }
    return render(request, "appcontrol/index.html", context)


# # ---------- CSV UPLOAD ----------
# @login_required
# def data_upload(request):
#     if not request.user.is_superuser:
#         return HttpResponseForbidden("Invalid Access")

#     if request.method == "POST":

#         data_file = request.FILES.get("data_file")
#         points_file = request.FILES.get("points_file")
#         season_id = request.POST.get("season_id")

#         if not data_file or not data_file.name.endswith(".csv"):
#             messages.error(request, "Invalid file. Upload a CSV file.")
#             return render(request, "appcontrol/dataupload.html", {"seasons": Season.objects.all()})

#         season = Season.objects.filter(id=season_id).first()
#         if not season:
#             messages.error(request, "Season is required.")
#             return render(request, "appcontrol/dataupload.html", {"seasons": Season.objects.all()})

#         # ------------ Optional Points CSV ------------
#         points_map = {}
#         if points_file and points_file.name.endswith(".csv"):
#             points_str = points_file.read().decode("utf-8")
#             p_reader = csv.reader(io.StringIO(points_str))
#             next(p_reader, None)  # skip header
#             for pid, pts in p_reader:
#                 points_map[pid.strip()] = int(pts)

#         # ------------ Main CSV Reader ------------
#         data_str = data_file.read().decode("utf-8")
#         csv_reader = csv.DictReader(io.StringIO(data_str))

#         created = 0
#         updated = 0
#         user_created = 0

#         for row in csv_reader:
#             try:
#                 reg_id = row["reg_id"].strip()
#                 username = row["user__username"].strip()
#                 player_name = row["player_name"].strip()
#                 email = row["email"].strip()
#                 dob = row["dob"].strip()
#                 mobile = row["mobile"].strip()

#                 # -------- Split first & last name --------
#                 name_parts = player_name.split(" ")
#                 if len(name_parts) > 0:
#                     first_name = name_parts[0]
#                     last_name = " ".join(name_parts[1:])
#                 else:
#                     first_name = player_name
#                     last_name = ""

#                 # -------- User password logic --------
#                 password = dob.replace("-", "") + mobile[-4:]

#                 # -------- User Create or Update --------
#                 user, new_user = User.objects.get_or_create(
#                     username=username,
#                     defaults={
#                         "first_name": first_name,
#                         "last_name": last_name,
#                         "email": email,
#                     }
#                 )

#                 if new_user:
#                     user.set_password(password)
#                     user.save()
#                     user_created += 1
#                     logger.info(f"[USER CREATED] {username}")
#                 else:
#                     # update name/email
#                     user.first_name = first_name
#                     user.last_name = last_name
#                     user.email = email
#                     user.save()
#                     logger.info(f"[USER UPDATED] {username}")

#                 # -------- Age + Category --------
#                 age = calculate_age(dob)
#                 category = "21 and Above"

#                 # -------- PlayerRegistration Create or Update --------
#                 pr, is_created = PlayerRegistration.objects.update_or_create(
#                     season=season,
#                     reg_id=reg_id,
#                     defaults={
#                         "user": user,
#                         "player_name": player_name,
#                         "father_name": row["father_name"],
#                         "category": category,
#                         "age": age,
#                         "dob": row["dob"],
#                         "gender": row["gender"],
#                         "tshirt_size": row["tshirt_size"],
#                         "occupation": 3,
#                         "mobile": row["mobile"],
#                         "wathsapp_number": row["wathsapp_number"],
#                         "email": row["email"],
#                         "adhar_card": row["adhar_card"],
#                         "player_image": row["player_image"],
#                         "district": row["district"],
#                         "zone": row["zone"],
#                         "pin_code": row["pin_code"],
#                         "address": row["address"],
#                         "first_preference": row["first_preference"],
#                         "batting_arm": row["batting_arm"],
#                         "role": row["role"],
#                         "is_compleated": bool(int(row["is_paid"])),
#                         "tx_id": row["tx_id"],
#                         "is_selected": bool(int(row["is_selected"])),
#                         "points": points_map.get(reg_id, int(row.get("points", 0))),
#                     }
#                 )

#                 if is_created:
#                     created += 1
#                     logger.info(f"[REGISTERED] {reg_id} CREATED")
#                 else:
#                     updated += 1
#                     logger.info(f"[REGISTERED] {reg_id} UPDATED")

#             except Exception as e:
#                 logger.error(f"[ERROR] reg_id={row.get('reg_id')} error={str(e)}")
#                 continue

#         messages.success(
#             request,
#             f"Completed: Players Created={created}, Updated={updated}, Users Created={user_created}"
#         )

#     return render(request, "appcontrol/dataupload.html", {
#         "seasons": Season.objects.all()
#     })


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

        # Trigger Celery task
        from core.task import process_csv_upload
        task = process_csv_upload.delay(data_bytes, points_bytes, season_id)

        messages.success(request, f"CSV uploaded. Task ID: {task.id}. Processing...")

        return redirect("data_upload")  # redirect to avoid re-POSTing

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


