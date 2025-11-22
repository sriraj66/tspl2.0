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
            html_content = render_to_string('core/success_email.html', context)
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
