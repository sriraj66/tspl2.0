from .models import GeneralSettings
import logging

logger = logging.getLogger('core')

def get_general_settings():
    try:
        settings = GeneralSettings.objects.first()
        return settings
    except GeneralSettings.DoesNotExist:
        logging.error("GeneralSettings does not exist.")
        return None