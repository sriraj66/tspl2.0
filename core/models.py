from django.db import models
import uuid
from .constants import *
from django.contrib.auth.models import User

class Season(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Admin User")
    
    title = models.CharField(max_length=100, verbose_name="Season Title")
    
    year = models.CharField(max_length=9, verbose_name="Season Year")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    
    amount = models.PositiveIntegerField(default=0,verbose_name="Registration Amount")
    accept_response = models.BooleanField(default=False,verbose_name="Accept Response")
    registration_form_editable = models.BooleanField(default=True,verbose_name="Is Registration Form Editable")
    
    update_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        ordering = ['-id']
    
    def get_amount(self):
        return self.amount/100
    
    def __str__(self):
        return self.title
    
class PlayerRegistration(models.Model):
    
    id = models.UUIDField( 
            primary_key = True, 
            default = uuid.uuid4, 
            editable = False)
    
    season = models.ForeignKey(Season, on_delete=models.CASCADE, verbose_name="Season Configuration")
    
    reg_id = models.CharField(
        max_length=20,
        editable=False,
        verbose_name="Register ID"
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    player_name = models.CharField(max_length=100, verbose_name='Player Name')
    father_name = models.CharField(max_length=100, verbose_name='Father’s Name')
    
    category = models.CharField(max_length=25, choices=REGISTRATION_CATEGORIES, verbose_name='Category')
    age = models.PositiveIntegerField( verbose_name='Player Age')

    dob = models.DateField(verbose_name='Date of Birth')
    gender = models.CharField(max_length=10, choices=GENDERS, verbose_name='Gender')
    tshirt_size = models.CharField(max_length=4, choices=TSHIRT_SIZES, verbose_name='T-Shirt Size')
    occupation = models.CharField(max_length=14,choices=OCCUPATION,default=3,verbose_name="Player Occupation")
    mobile = models.CharField(max_length=10, verbose_name='Mobile Number')
    
    wathsapp_number = models.CharField(max_length=10, verbose_name='Wathsapp Number')
    
    email = models.EmailField(verbose_name='Email Address')
    adhar_card = models.CharField(max_length=12, verbose_name="Adhar Card")
    player_image = models.ImageField(upload_to='player_images/', verbose_name='Player Image')
    
    district = models.CharField(max_length=100,choices=DISTRICT_CHOICES, verbose_name='District')
    
    zone = models.CharField(max_length=10, editable=False, verbose_name="Zone",default="ZONE A")
    
    pin_code = models.PositiveIntegerField(verbose_name='PIN Code')
    address = models.TextField(verbose_name='Address')
    first_preference = models.CharField(max_length=10,default=0,choices=FIRST_PREFERENCES, verbose_name='First Preference')
    batting_arm = models.CharField(max_length=10, default=0 ,choices=BOWLING_ARMS, verbose_name='Batting Arm')
    role = models.CharField(max_length=100,choices=ROLE,verbose_name="Player Role",default=0)


    tx_id = models.CharField(blank=True,max_length=255,verbose_name="Transition ID#")
    
    is_selected = models.BooleanField(default=False,verbose_name="Is the player got Selected")
    points = models.IntegerField(default=-99,verbose_name="Player Points on Trails")

    is_mail_sent = models.BooleanField(default=False,verbose_name="Is the Mail was Sent")
    is_compleated = models.BooleanField(default=False,verbose_name="Is Registration Compleated")

    created = models.DateTimeField(auto_now_add=True,verbose_name="Created At")

    class Meta:
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['season', 'reg_id'],
                name='unique_reg_id_per_season'
            ),
            models.UniqueConstraint(
                fields=['season', 'adhar_card'],
                name='unique_adhar_per_season'
            ),
        ]

    def save(self, *args, **kwargs):
        self.zone = DISTRICT_ZONE_MAP.get(self.district, 'Unknown')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.player_name


class Payment(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "PENDING"),
        ("PAID", "PAID"),
        ("FAILED", "FAILED"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    registration = models.ForeignKey(PlayerRegistration, on_delete=models.CASCADE, verbose_name="Player Registration")
    order_id = models.CharField(max_length=200, blank=True, unique=True)
    recpt_id = models.CharField(max_length=200, blank=True, unique=True)
    currency = models.CharField(max_length=10, default="INR")
    amount = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    payment_id = models.CharField(max_length=200, null=True, blank=True)
    signature = models.TextField(null=True, blank=True)
    is_compleated = models.BooleanField(default=False, verbose_name="Is Payment Completed")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_amount(self):
        return self.amount/100
    
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.order_id


class GeneralSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Admin User")
    enable_registration = models.BooleanField(default=True,verbose_name="Enable Player Registration")
    current_season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Current Season")
    show_points_table = models.BooleanField(default=False,verbose_name="Show Points Table to Public")
    enable_results = models.BooleanField(default=False,verbose_name="Enable Player Results Viewing")
    
    alert_message = models.TextField(default="Welcome", blank=True,null=True,verbose_name="Alert Message")
    
    # Payment Ids Credentials
    razorpay_key_id = models.CharField(max_length=255, default="", verbose_name="Razorpay Key ID")
    razorpay_key_secret = models.CharField(max_length=255, default="", verbose_name="Razorpay Key Secret")
    callback_url = models.URLField(max_length=500, default="", verbose_name="Payment Callback URL")
    points_table_url = models.URLField(max_length=500, default="", verbose_name="Points Table URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        ordering = ['-id']
        
    def __str__(self):
        return f"General Settings"
    
# Signals
from django.db.models.signals import pre_save
from django.dispatch import receiver
import datetime

@receiver(pre_save, sender=PlayerRegistration)
def generate_user_id(sender, instance, **kwargs):
    if not instance.reg_id:
        current_date = datetime.datetime.now()
        month = current_date.strftime('%m')
        year = current_date.strftime('%y')

        last_number = sender.objects.filter(season=instance.season).count()
        new_number = last_number + 1  # sequential number
        instance.reg_id = f"TSPL{month}{year}{new_number:04d}"
