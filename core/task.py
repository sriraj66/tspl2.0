import concurrent.futures
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from core.models import PlayerRegistration, Season
from django.conf import settings
from django.template import Template, Context
import csv, io
import logging
import smtplib
import time, random
import atexit

email_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
bulk_email_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
csv_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

email_executor._shutdown = False
csv_executor._shutdown = False
bulk_email_executor._shutdown = False

# Register proper cleanup on application exit
def cleanup_executors():
    """Gracefully shutdown executors on application exit"""
    logger.info("Shutting down thread pool executors...")
    email_executor.shutdown(wait=False)
    csv_executor.shutdown(wait=False)
    bulk_email_executor.shutdown(wait=False)

atexit.register(cleanup_executors)

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

def send_batch_payment_reminder_emails(email_data_list, subject, settings_data):
    """
    Sends payment reminder emails in batches with rate limiting.
    
    Parameters:
    - email_data_list (list): List of dicts with keys: to_email, reg_id, tx_id, amount, zone, player_name
    - subject (str): Email subject
    - settings_data (dict): General settings data (current_season_title, etc.)
    """
    
    def _send_single_email(email_data, subject, attempt=1, max_retries=10):
        """Send a single email with retry logic"""
        try:
            # Build context for this email
            context = {
                "id": email_data.get("tx_id"),
                "reg_id": email_data["reg_id"],
                "amount": email_data["amount"],
                "zone": email_data["zone"],
                "player_name": email_data.get("player_name", ""),
                "season_id": email_data.get("season_id"),  # Pass season_id directly
                "settings": settings_data,
            }
            
            # Render HTML content
            html_content = render_to_string('email/payment_reminder_email.html', context)
            text_content = f"Hello {context.get('player_name', '')}, your remaining payment of {context.get('amount', '')} is due."
            
            from_email = settings.EMAIL_HOST_USER
            
            # Create fresh connection for each email to avoid connection issues
            with get_connection() as connection:
                message = EmailMultiAlternatives(
                    subject, 
                    text_content, 
                    from_email, 
                    [email_data["to_email"]],
                    connection=connection
                )
                message.attach_alternative(html_content, "text/html")
                message.send()
            
            logger.info(f"Payment reminder sent to {email_data['to_email']} (reg_id={email_data['reg_id']})")
            return True
            
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 421:
                logger.warning(f"Rate limited at {email_data['to_email']} (attempt {attempt}/{max_retries}). Sleeping 15s...")
                time.sleep(15)
            else:
                logger.error(f"SMTP error for {email_data['to_email']}: {e.smtp_code} {e.smtp_error}")
                time.sleep(3)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send payment reminder to {email_data['to_email']} after {max_retries} attempts")
                return False
                
        except (ConnectionError, BrokenPipeError, OSError) as e:
            logger.warning(f"Connection error for {email_data['to_email']} (attempt {attempt}/{max_retries}): {e}")
            sleep_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s
            time.sleep(sleep_time)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send payment reminder to {email_data['to_email']} after {max_retries} attempts")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error for {email_data['to_email']} (attempt {attempt}/{max_retries}): {e}")
            time.sleep(3)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send payment reminder to {email_data['to_email']} after {max_retries} attempts")
                return False
    
    def _send_batch():
        logger.info(f"Starting batch payment reminder emails for {len(email_data_list)} recipients")
        success_count = 0
        failed_count = 0
        
        for idx, email_data in enumerate(email_data_list):
            logger.info(f"[{idx+1}/{len(email_data_list)}] Processing {email_data['to_email']}...")
            
            # Rate limiting: sleep between emails (5-8 seconds)
            if idx > 0:
                sleep_duration = random.uniform(3.0, 5.0)
                logger.info(f"Sleeping {sleep_duration:.1f}s before next email...")
                time.sleep(sleep_duration)
            
            # Send with retry logic
            if _send_single_email(email_data, subject):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Batch payment reminder emails completed: {success_count} sent, {failed_count} failed out of {len(email_data_list)} total")
    
    # Submit to thread pool with error handling
    try:
        bulk_email_executor.submit(_send_batch)
        logger.info(f"Batch payment reminder task submitted successfully to bulk_email_executor")
    except RuntimeError as e:
        logger.error(f"Failed to submit batch payment task: {e}. Executing synchronously as fallback.")


def send_batch_selection_status_emails(email_data_list, subject, settings_data):
    """
    Sends selection status emails in batches with rate limiting.
    
    Parameters:
    - email_data_list (list): List of dicts with keys: to_email, reg_id, player_name, is_selected, points, zone, category
    - subject (str): Email subject
    - settings_data (dict): General settings data
    """
    
    def _send_single_email(email_data, subject, attempt=1, max_retries=10):
        """Send a single email with retry logic"""
        try:
            # Build a minimal object-like dict for templates
            player_obj = {
                "player_name": email_data["player_name"],
                "reg_id": email_data["reg_id"],
                "is_selected": email_data["is_selected"],
                "points": email_data.get("points", 0),
                "zone": email_data["zone"],
                "category": email_data.get("category", ""),
            }
            
            # Choose template based on selection status
            if email_data["is_selected"]:
                html_content = render_to_string('selected.html', {"data": player_obj})
            else:
                html_content = render_to_string('notSelected.html', {"data": player_obj})
            
            text_content = f"Hello {email_data['player_name']}, your selection status has been updated."
            from_email = settings.EMAIL_HOST_USER
            
            # Create fresh connection for each email to avoid connection issues
            with get_connection() as connection:
                message = EmailMultiAlternatives(
                    subject, 
                    text_content, 
                    from_email, 
                    [email_data["to_email"]],
                    connection=connection
                )
                message.attach_alternative(html_content, "text/html")
                message.send()
            
            logger.info(f"Selection status sent to {email_data['to_email']} (reg_id={email_data['reg_id']})")
            return True
            
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 421:
                logger.warning(f"Rate limited at {email_data['to_email']} (attempt {attempt}/{max_retries}). Sleeping 15s...")
                time.sleep(15)
            else:
                logger.error(f"SMTP error for {email_data['to_email']}: {e.smtp_code} {e.smtp_error}")
                time.sleep(3)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send selection status to {email_data['to_email']} after {max_retries} attempts")
                return False
                
        except (ConnectionError, BrokenPipeError, OSError) as e:
            logger.warning(f"Connection error for {email_data['to_email']} (attempt {attempt}/{max_retries}): {e}")
            sleep_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s
            time.sleep(sleep_time)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send selection status to {email_data['to_email']} after {max_retries} attempts")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error for {email_data['to_email']} (attempt {attempt}/{max_retries}): {e}")
            time.sleep(3)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send selection status to {email_data['to_email']} after {max_retries} attempts")
                return False
    
    def _send_batch():
        logger.info(f"Starting batch selection status emails for {len(email_data_list)} recipients")
        success_count = 0
        failed_count = 0
        
        for idx, email_data in enumerate(email_data_list):
            logger.info(f"[{idx+1}/{len(email_data_list)}] Processing {email_data['to_email']}...")
            
            # Rate limiting: sleep between emails (5-8 seconds)
            if idx > 0:
                sleep_duration = random.uniform(5.0, 8.0)
                logger.info(f"Sleeping {sleep_duration:.1f}s before next email...")
                time.sleep(sleep_duration)
            
            # Send with retry logic
            if _send_single_email(email_data, subject):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Batch selection status emails completed: {success_count} sent, {failed_count} failed out of {len(email_data_list)} total")
    
    # Submit to thread pool with error handling
    try:
        bulk_email_executor.submit(_send_batch)
        logger.info(f"Batch selection status task submitted successfully to bulk_email_executor")
    except RuntimeError as e:
        logger.error(f"Failed to submit batch selection task: {e}. Executing synchronously as fallback.")

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


def send_batch_custom_emails(email_data_list, subject, html_template):
    """
    Sends custom HTML emails in batches with rate limiting.
    
    Parameters:
    - email_data_list (list): List of dicts with keys: to_email, context (dict with template variables)
    - subject (str): Email subject
    - html_template (str): HTML template string with Django template variables
    """
    
    def _send_single_email(email_data, subject, html_template, attempt=1, max_retries=10):
        """Send a single custom email with retry logic"""
        try:
            # Render HTML content with user's context
            t = Template(html_template)
            c = Context(email_data["context"])
            rendered_html = t.render(c)
            
            text_content = "You have a new notification."
            from_email = settings.EMAIL_HOST_USER
            
            # Create fresh connection for each email to avoid connection issues
            with get_connection() as connection:
                message = EmailMultiAlternatives(
                    subject, 
                    text_content, 
                    from_email, 
                    [email_data["to_email"]],
                    connection=connection
                )
                message.attach_alternative(rendered_html, "text/html")
                message.send()
            
            logger.info(f"Custom bulk email sent to {email_data['to_email']}")
            return True
            
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 421:
                logger.warning(f"Rate limited at {email_data['to_email']} (attempt {attempt}/{max_retries}). Sleeping 15s...")
                time.sleep(8)
            else:
                logger.error(f"SMTP error for {email_data['to_email']}: {e.smtp_code} {e.smtp_error}")
                time.sleep(3)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, html_template, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send custom email to {email_data['to_email']} after {max_retries} attempts")
                return False
                
        except (ConnectionError, BrokenPipeError, OSError) as e:
            logger.warning(f"Connection error for {email_data['to_email']} (attempt {attempt}/{max_retries}): {e}")
            sleep_time = min(2 ** attempt, 15)  # Exponential backoff, max 30s
            time.sleep(sleep_time)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, html_template, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send custom email to {email_data['to_email']} after {max_retries} attempts")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error for {email_data['to_email']} (attempt {attempt}/{max_retries}): {e}")
            time.sleep(3)
            
            if attempt < max_retries:
                return _send_single_email(email_data, subject, html_template, attempt + 1, max_retries)
            else:
                logger.error(f"Failed to send custom email to {email_data['to_email']} after {max_retries} attempts")
                return False
    
    def _send_batch():
        logger.info(f"Starting batch custom emails for {len(email_data_list)} recipients")
        success_count = 0
        failed_count = 0
        
        for idx, email_data in enumerate(email_data_list):
            logger.info(f"[{idx+1}/{len(email_data_list)}] Processing {email_data['to_email']}...")
            
            # Rate limiting: sleep between emails (5-8 seconds)
            if idx > 0:
                sleep_duration = random.uniform(3.0, 8.0)
                logger.info(f"Sleeping {sleep_duration:.1f}s before next email...")
                time.sleep(sleep_duration)
            
            # Send with retry logic
            if _send_single_email(email_data, subject, html_template):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Batch custom emails completed: {success_count} sent, {failed_count} failed out of {len(email_data_list)} total")
    
    # Submit to thread pool with error handling
    try:
        bulk_email_executor.submit(_send_batch)
        logger.info(f"Batch custom email task submitted successfully to bulk_email_executor")
    except RuntimeError as e:
        logger.error(f"Failed to submit batch custom email task: {e}. Executing synchronously as fallback.")


def submit_csv_task(data_bytes, points_bytes, season_id):
    """Submit CSV processing job to the single-thread executor."""
    return csv_executor.submit(process_csv_upload, data_bytes, points_bytes, season_id)

