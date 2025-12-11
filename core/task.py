import concurrent.futures
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from core.models import PlayerRegistration, Season
from django.conf import settings
import csv, io
import logging

email_executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
csv_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

logger = logging.getLogger('core')

def send_success_email(subject, to, context):
    logger.info("Submitting email task to thread pool")

    def send_email():
        try:
            html_content = render_to_string('email/success_email.html', context)
            text_content = 'Your registration has been completed successfully.'
            from_email = settings.EMAIL_HOST_USER

            message = EmailMultiAlternatives(subject, text_content, from_email, [to,])
            message.attach_alternative(html_content, "text/html")

            message.send()
            logger.info(f"Email sent to {to}")
        except Exception as e:
            logger.error(f"Error sending email to {to}: {e}")
            # print(f"Error sending email to {to}: {e}")

    email_executor.submit(send_email)

def send_payment_reminder_email(subject, to_email, context):
    """
    Sends a remaining payment reminder email asynchronously.
    
    Parameters:
    - subject (str): email subject
    - to_email (str): recipient email address
    - context (dict): template context for rendering HTML
    """
    logger.info(f"Submitting payment reminder email to {to_email}")

    def _send_email():
        try:
            # Render HTML content from template
            html_content = render_to_string('email/payment_reminder_email.html', context)
            
            # Fallback plain text content
            text_content = f"Hello {context.get('player_name', '')}, your remaining payment of {context.get('amount', '')} is due."

            from_email = settings.EMAIL_HOST_USER
            message = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            message.attach_alternative(html_content, "text/html")
            message.send()

            logger.info(f"Payment reminder email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send payment reminder email to {to_email}: {e}")

    # Submit the email task to the thread pool
    email_executor.submit(_send_email)


def send_selection_status_email(subject, to_email, context):
    """
    Sends a status email asynchronously depending on selection/completion.

    Parameters:
    - subject (str): email subject
    - to_email (str): recipient email address
    - context (dict): template context for rendering HTML
    """
    logger.info(f"Submitting selection status email to {to_email}")

    def _send_email():
        try:
            # Decide template based on completion and selection
            if context["obj"].is_selected:
                html_content = render_to_string('selected.html', {"data": context["obj"]})
            else:
                html_content = render_to_string('notSelected.html', {"data": context["obj"]})
           
            # Fallback plain text content
            text_content = f"Hello {context["obj"].player_name}, your selection status has been updated."

            from_email = settings.EMAIL_HOST_USER
            message = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            message.attach_alternative(html_content, "text/html")
            message.send()

            logger.info(f"Selection status email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send selection status email to {to_email}: {e}")

    # Submit to thread pool
    email_executor.submit(_send_email)

def process_csv_upload(data_bytes, points_bytes, season_id):
    """Process the entire CSV in a single safe background thread."""
    
    def calculate_age(dob_str):
        from datetime import datetime, date
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    try:
        season = Season.objects.get(id=season_id)
    except Season.DoesNotExist:
        logger.error("Season not found")
        return "SEASON_NOT_FOUND"

    # -------- Optional Points CSV --------
    points_map = {}
    if points_bytes:
        points_str = points_bytes.decode("utf-8")
        p_reader = csv.reader(io.StringIO(points_str))
        next(p_reader, None)
        for pid, pts in p_reader:
            points_map[pid.strip()] = int(pts)

    # -------- Main CSV --------
    data_str = data_bytes.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(data_str))

    created = 0
    updated = 0
    user_created = 0

    for row in csv_reader:
        try:
            reg_id = row["reg_id"].strip()
            username = row["user__username"].strip()
            player_name = row["player_name"].strip()
            email = row["email"].strip()
            dob = row["dob"].strip()
            mobile = row["mobile"].strip()

            # Split name
            name_parts = player_name.split(" ")
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            # Generate password
            password = dob.replace("-", "") + mobile[-4:]

            # Create / update user
            user, new_user = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                }
            )

            if new_user:
                user.set_password(password)
                user.save()
                user_created += 1
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()

            # Age
            age = calculate_age(dob)
            category = "21 and Above"

            # Create/update PlayerRegistration
            pr, is_created = PlayerRegistration.objects.update_or_create(
                season=season,
                reg_id=reg_id,
                defaults={
                    "user": user,
                    "player_name": player_name,
                    "father_name": row["father_name"],
                    "category": category,
                    "age": age,
                    "dob": row["dob"],
                    "gender": row["gender"],
                    "tshirt_size": row["tshirt_size"],
                    "occupation": 3,
                    "mobile": row["mobile"],
                    "wathsapp_number": row["wathsapp_number"],
                    "email": row["email"],
                    "adhar_card": row["adhar_card"],
                    "player_image": row["player_image"],
                    "district": row["district"],
                    "zone": row["zone"],
                    "pin_code": row["pin_code"],
                    "address": row["address"],
                    "first_preference": row["first_preference"],
                    "batting_arm": row["batting_arm"],
                    "role": row["role"],
                    "is_compleated": bool(int(row["is_paid"])),
                    "tx_id": row["tx_id"],
                    "is_selected": bool(int(row["is_selected"])),
                    "points": points_map.get(reg_id, int(row.get("points", 0))),
                }
            )

            if is_created:
                created += 1
                logger.info(f"reg_id={reg_id} - CREATED")
            else:
                updated += 1
                logger.info(f"reg_id={reg_id} - UPDATED")

        except Exception as e:
            logger.error(f"[ERROR] reg_id={row.get('reg_id')} - {e}")
            continue

    summary = f"Done: Players Created={created}, Updated={updated}, Users Created={user_created}"
    logger.info(summary)
    return summary


def submit_csv_task(data_bytes, points_bytes, season_id):
    """Submit CSV processing job to the single-thread executor."""
    return csv_executor.submit(process_csv_upload, data_bytes, points_bytes, season_id)

