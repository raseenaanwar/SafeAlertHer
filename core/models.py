# core/models.py
import json
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Mobile number must be in the format: '+911234567890'. Up to 15 digits allowed."
            )
        ],
        help_text="Enter mobile number with country code (e.g., +911234567890)"
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = [
        ('PARENT', 'Parent'),
        ('SPOUSE', 'Spouse'),
        ('SIBLING', 'Sibling'),
        ('CHILD', 'Child'),
        ('RELATIVE', 'Relative'),
        ('FRIEND', 'Friend'),
        ('OTHER', 'Other')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.relationship})"

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=10, default='High')
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_text = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
    def get_safety_tips(self):
        if self.safety_tips:
            return json.loads(self.safety_tips)
        return []

    def get_ai_analysis(self):
        if self.ai_analysis:
            return json.loads(self.ai_analysis)
        return {}
