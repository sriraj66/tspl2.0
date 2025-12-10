import time
import logging

import razorpay
from django.conf import settings

from .models import Payment, PlayerRegistration

logger = logging.getLogger('core')


# Initialize Razorpay client once for the module
try:
	client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
	logger.info("Razorpay client initialized")
except Exception as e:
	client = None
	logger.exception("Failed to initialize Razorpay client: %s", e)


def create_payment_for_registration(user, registration, amount):
	"""Create a Payment DB record and corresponding Razorpay order.

	Returns (payment, None) on success or (None, error_message) on failure.
	"""
	if client is None:
		return None, "Payment gateway is not configured."

	payment = Payment.objects.create(
		user=user,
		registration=registration,
		amount=int(amount),
		status="PENDING",
	)

	order_receipt = f"rcpt_{user.id}_{payment.id}_{int(time.time())}"[:40]
	payment.recpt_id = order_receipt

	try:
		razorpay_order = client.order.create({
			"amount": payment.amount * 100,
			"currency": payment.currency,
			"receipt": order_receipt,
			"payment_capture": 1,
		})
	except Exception as e:
		logger.exception("Failed to create Razorpay order: %s", e)
		payment.status = "FAILED"
		payment.save()
		return None, str(e)

	payment.order_id = razorpay_order.get('id')
	payment.save()
	return payment, None


def get_or_create_pending_payment(user, registration, amount_cents):
	"""Return an existing pending payment for (user, registration) or create a new one.

	Returns (payment, None) or (None, error_message).
	"""
	try:
		payment = Payment.objects.get(user=user, registration=registration)
		# If payment exists and is not completed, return it
		if not payment.is_compleated:
			return payment, None
		# If already completed, return it as-is (caller can decide next steps)
		return payment, None
	except Payment.DoesNotExist:
		return create_payment_for_registration(user, registration, amount_cents)


def verify_payment_signature_and_fetch(payment_id, order_id, signature):
	"""Verify Razorpay signature and fetch payment details.

	Returns (payment_details, None) on success or (None, error_message) on failure.
	"""
	if client is None:
		return None, "Payment gateway is not configured."

	params_dict = {
		"razorpay_order_id": order_id,
		"razorpay_payment_id": payment_id,
		"razorpay_signature": signature,
	}

	try:
		client.utility.verify_payment_signature(params_dict)
	except Exception as e:
		logger.exception("Signature verification failed: %s", e)
		return None, "Signature verification failed."

	try:
		payment_details = client.payment.fetch(payment_id)
	except Exception as e:
		logger.exception("Failed to fetch payment details: %s", e)
		return None, "Failed to fetch payment details."

	return payment_details, None


def handle_successful_capture(payment_obj, payment_details):
	"""Mark payment and registration as completed and return the registration."""
	# update payment record
	payment_obj.payment_id = payment_details.get('id') or payment_obj.payment_id
	payment_obj.signature = payment_obj.signature or ''
	payment_obj.is_compleated = True
	payment_obj.status = "PAID"
	payment_obj.save()

	# update registration
	registration = payment_obj.registration
	registration.is_compleated = True
	registration.tx_id = payment_obj.payment_id
	registration.save()

	return registration




