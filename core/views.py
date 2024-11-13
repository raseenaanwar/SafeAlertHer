# core/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import google.generativeai as genai
from .models import Profile
import requests

import json
from .models import EmergencyContact, Alert
from .forms import UserRegistrationForm, EmergencyContactForm
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
from .utils import SafetyAI  
import urllib.parse 
from django.views.decorators.csrf import csrf_protect
def home(request):
    return render(request, 'home.html')  


@csrf_protect
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # Get the mobile number from the form data, or set a default value
            mobile_number = request.POST.get('mobile_number', '')  # Assuming 'mobile_number' is a field in the form
            
            # Check if the mobile number is too long, if so, handle it
            if len(mobile_number) > 15:
                messages.error(request, "Mobile number is too long, it should be less than or equal to 15 characters.")
                return redirect('register')
            
            # Create the profile for the newly registered user
            Profile.objects.create(user=user, mobile_number=mobile_number)

            # Log the user in after registration
            login(request, user)
            
            # Add a success message
            messages.success(request, 'Account created successfully! Welcome to SafeAlert.')

            # Redirect to the dashboard or any other page
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    print("inside logout")
    if request.user.is_authenticated:
        print("Inside auth")
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard(request):
    contacts = EmergencyContact.objects.filter(user=request.user)
    alerts = Alert.objects.filter(user=request.user).order_by('-created_at')[:5]
    context = {
        'contacts': contacts,
        'alerts': alerts,
    }
    return render(request, 'dashboard.html', context)

@login_required
def manage_contacts(request):
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, f'Contact {contact.name} added successfully!')
            return redirect('contacts')
    else:
        form = EmergencyContactForm()
    
    contacts = EmergencyContact.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'contacts.html', {
        'form': form,
        'contacts': contacts
    })

@login_required
def edit_contact(request, contact_id):
    contact = get_object_or_404(EmergencyContact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user  # Ensure user is set
            contact.save()
            messages.success(request, f'{contact.name}\'s information has been updated.')
            return redirect('contacts')
    else:
        form = EmergencyContactForm(instance=contact)
    
    return render(request, 'edit_contact.html', {
        'form': form,
        'contact': contact
    })

@login_required
def delete_contact(request, contact_id):
    # Get contact and verify ownership
    contact = get_object_or_404(EmergencyContact, id=contact_id)
    if contact.user != request.user:
        messages.error(request, 'You do not have permission to delete this contact.')
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        contact_name = contact.name
        contact.delete()
        messages.success(request, f'Contact {contact_name} deleted successfully!')
        return redirect('contacts')
    
   
    return render(request, 'delete_contact.html', {'contact': contact})


@login_required
def validate_contact(request):
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST)
        if form.is_valid():
            return JsonResponse({'valid': True})
        else:
            return JsonResponse({
                'valid': False,
                'errors': form.errors
            })
    return JsonResponse({'valid': False, 'message': 'Invalid request method'})


@login_required
def create_alert(request):
    if not hasattr(request.user, 'profile'):
        return JsonResponse({
            'status': 'error',
            'message': 'User profile not found. Please create a profile first.'
        })
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')
            location_text = data.get('location_text', 'Unknown location')
            current_time = timezone.localtime().strftime('%I:%M %p')

            # Generate AI message for both email and WhatsApp
            try:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-pro')
                
                prompt = f"""
                Generate a concise emergency alert message.
                Location: {location_text}
                Time: {current_time}
                Include:
                1. Clear emergency statement
                2. Location details
                3. Immediate action needed
                Keep it brief and urgent.
                """
                
                response = model.generate_content(prompt)
                ai_message = response.text
                print(ai_message)
            except Exception as e:
                ai_message = f"Emergency Alert: {request.user.get_full_name()} needs immediate assistance!"

            # Unified message for both platforms
            message = f"""
🚨 EMERGENCY ALERT!

{ai_message}

📍 Location: {location_text}
🕒 Time: {current_time}
🗺️ Maps: https://www.google.com/maps?q={lat},{lng}

From: {request.user.get_full_name()}
Contact: {request.user.profile.mobile_number}

Please respond immediately!
"""

            success_count = 0
            whatsapp_count = 0
            contacts = EmergencyContact.objects.filter(user=request.user)

            for contact in contacts:
                # Send email
                try:
                    send_mail(
                        f'🚨 EMERGENCY ALERT from {request.user.get_full_name()}',
                        message,
                        settings.EMAIL_HOST_USER,
                        [contact.email],
                        fail_silently=False,
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Email failed for {contact.email}: {str(e)}")

                # Send WhatsApp using Click-to-Chat
                if contact.phone:
                    try:
                        clean_number = ''.join(filter(str.isdigit, contact.phone))
                        if not clean_number.startswith('+'):
                            clean_number = '+' + clean_number

                        # Create the WhatsApp link
                        encoded_message = urllib.parse.quote(message)  # URL-encode the message
                        whatsapp_url = f"https://wa.me/{clean_number}?text={encoded_message}"

                        # Open WhatsApp (you can choose to redirect the user, or trigger in backend)
                        # Here, we're just preparing the URL, you may need a frontend redirect or display the link
                        print(f"WhatsApp URL: {whatsapp_url}")

                        whatsapp_count += 1
                    except Exception as e:
                        print(f"WhatsApp failed for {contact.phone}: {str(e)}")

            # Create alert record
            alert = Alert.objects.create(
                user=request.user,
                latitude=lat,
                longitude=lng,
                location_text=location_text,
                message=ai_message
            )

            # Return success with counts
            return JsonResponse({
                'status': 'success',
                'message': f'Alert sent successfully! {success_count} emails and {whatsapp_count} WhatsApp messages prepared.',
                'alert_id': alert.id
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })
# @login_required
# def create_alert(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             lat = data.get('latitude')
#             lng = data.get('longitude')
#             location_text = data.get('location_text', 'Unknown location')
#             current_time = timezone.localtime().strftime('%I:%M %p')

#             # Enhanced AI message generation using Gemini
#             try:
#                 genai.configure(api_key=settings.GOOGLE_API_KEY)
#                 model = genai.GenerativeModel('gemini-pro')
                
#                 # Enhanced prompt for better AI response
#                 prompt = f"""
#                 Generate an emergency alert message for someone in immediate need of help.
#                 Context:
#                 - Location: {location_text}
#                 - Time: {current_time}
#                 - Name: {request.user.get_full_name()}

#                 Please generate a JSON response with these sections:
#                 1. main_alert: A clear, urgent message about the emergency
#                 2. safety_tips: 3 immediate actions for the person in emergency
#                 3. responder_actions: What emergency contacts should do
#                 4. priority_level: High/Medium/Low based on time and location

#                 Keep each section concise and actionable.
#                 """
                
#                 response = model.generate_content(prompt)
#                 try:
#                     ai_response = json.loads(response.text)
#                     ai_message = ai_response.get('main_alert', '')
#                     safety_tips = ai_response.get('safety_tips', [])
#                     responder_actions = ai_response.get('responder_actions', '')
#                     priority_level = ai_response.get('priority_level', 'High')
#                 except:
#                     # Fallback if JSON parsing fails
#                     ai_message = response.text
#                     safety_tips = ["Stay in a safe location", "Keep your phone charged", "Stay calm"]
#                     responder_actions = "Please respond immediately and contact emergency services if needed."
#                     priority_level = "High"
#             except Exception as e:
#                 print(f"AI Error: {str(e)}")
#                 ai_message = f"Emergency Alert: {request.user.get_full_name()} needs immediate assistance!"
#                 safety_tips = ["Stay in a safe location", "Keep your phone charged", "Stay calm"]
#                 responder_actions = "Please respond immediately and contact emergency services if needed."
#                 priority_level = "High"

#             # Create formatted messages for email and WhatsApp
#             email_message = f"""
# 🚨 EMERGENCY ALERT - {priority_level} PRIORITY 🚨

# {ai_message}

# 📍 Location: {location_text}
# 🕒 Time: {current_time}
# 🗺️ Maps: https://www.google.com/maps?q={lat},{lng}

# Safety Instructions for {request.user.get_full_name()}:
# {''.join(f'• {tip}\n' for tip in safety_tips)}

# For Emergency Contacts:
# {responder_actions}

# This is an AI-enhanced emergency alert system.
# Please respond immediately.
# """

#             # Shorter message for WhatsApp
#             whatsapp_message = f"""
# 🚨 *EMERGENCY ALERT*
# {ai_message}

# 📍 Location: {location_text}
# 🗺️ Maps: https://www.google.com/maps?q={lat},{lng}

# From: {request.user.get_full_name()}
# Please respond immediately!
# """

#             # Create alert record
#             alert = Alert.objects.create(
#                 user=request.user,
#                 latitude=lat,
#                 longitude=lng,
#                 location_text=location_text,
#                 message=ai_message,
#                 priority_level=priority_level
#             )

#             # Send alerts to contacts
#             contacts = EmergencyContact.objects.filter(user=request.user)
#             if not contacts.exists():
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Please add emergency contacts first'
#                 })

#             success_emails = 0
#             whatsapp_links = []

#             for contact in contacts:
#                 # Send email
#                 try:
#                     send_mail(
#                         f'🚨 EMERGENCY ALERT from {request.user.get_full_name()} - {priority_level} PRIORITY',
#                         email_message,
#                         settings.EMAIL_HOST_USER,
#                         [contact.email],
#                         fail_silently=False,
#                     )
#                     success_emails += 1
#                 except Exception as e:
#                     print(f"Email Error for {contact.email}: {str(e)}")

#                 # Generate WhatsApp link
#                 if contact.phone:
#                     try:
#                         # Clean and format phone number
#                         clean_number = ''.join(filter(str.isdigit, contact.phone))
#                         if not clean_number.startswith('+'):
#                             clean_number = '+' + clean_number
                        
#                         # Remove '+' and create WhatsApp link
#                         phone_number = clean_number.lstrip('+')
                        
#                         # Encode message for WhatsApp
#                         encoded_message = urllib.parse.quote(whatsapp_message)
                        
#                         # Create correct WhatsApp URL
#                         whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
                        
#                         whatsapp_links.append({
#                             'name': contact.name,
#                             'link': whatsapp_url
#                         })
#                     except Exception as e:
#                         print(f"WhatsApp Link Error for {contact.phone}: {str(e)}")

#             # Prepare response with AI insights
#             return JsonResponse({
#                 'status': 'success',
#                 'message': f'Alert sent successfully to {success_emails} contacts!',
#                 'whatsapp_links': whatsapp_links,
#                 'alert_id': alert.id,
#                 'priority': priority_level,
#                 'safety_tips': safety_tips,
#                 'responder_actions': responder_actions
#             })

    