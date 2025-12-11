import concurrent.futures
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

email_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
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
