from django.http import JsonResponse
import google.generativeai as genai
from django.conf import settings
from django.contrib.auth.decorators import login_required
import json

from core.models import Alert

class SafetyAI:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')  # Free tier of Gemini

    def analyze_emergency(self, location, user_name):
        """Generate smart emergency response using Gemini AI"""
        prompt = f"""
        Create an emergency response plan for {user_name} at {location}.
        Format the response in JSON with these sections:
        1. An urgent but clear emergency message
        2. Three immediate safety tips
        3. Instructions for emergency contacts
        4. Next steps after help arrives
        
        Make it concise and practical.
        """
        
        try:
            response = self.model.generate_content(prompt)
            ai_response = json.loads(response.text)
            return ai_response
        except:
            # Fallback response if AI fails
            return {
                "emergency_message": f"Emergency Alert: {user_name} needs immediate assistance at {location}.",
                "safety_tips": [
                    "Stay in a safe location",
                    "Keep your phone charged and accessible",
                    "Wait for emergency contacts to reach you"
                ],
                "contact_instructions": "Please respond immediately and contact emergency services if needed.",
                "next_steps": "Stay calm and wait for help to arrive."
            }

    def get_location_context(self, lat, lng, time_of_day):
        """Generate location-based safety context"""
        prompt = f"""
        For a person at coordinates ({lat}, {lng}) at {time_of_day},
        provide safety information in JSON format including:
        1. General area description
        2. Time-specific safety considerations
        3. Nearest likely safe locations (generic)
        
        Keep it brief and helpful.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except:
            return {
                "area_description": "Current location",
                "time_safety": "Be aware of your surroundings",
                "safe_locations": ["Nearby public buildings", "Well-lit areas", "Population centers"]
            }

# core/views.py
@login_required
def create_alert(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')
            location_text = data.get('location_text', 'Unknown location')
            current_time = timezone.now().strftime('%I:%M %p')

            # Initialize AI helper
            safety_ai = SafetyAI()
            
            # Get AI-enhanced responses
            emergency_info = safety_ai.analyze_emergency(
                location_text, 
                request.user.get_full_name()
            )
            
            location_info = safety_ai.get_location_context(
                lat, 
                lng, 
                current_time
            )

            # Create alert
            alert = Alert.objects.create(
                user=request.user,
                latitude=lat,
                longitude=lng,
                location_text=location_text,
                message=emergency_info['emergency_message'],
                safety_tips=json.dumps(emergency_info['safety_tips']),
                ai_analysis=json.dumps(location_info)
            )

            # Prepare email content
            email_message = f"""
            EMERGENCY ALERT

            {emergency_info['emergency_message']}

            Location: {location_text}
            Maps Link: https://www.google.com/maps?q={lat},{lng}

            Safety Tips:
            {chr(10).join('- ' + tip for tip in emergency_info['safety_tips'])}

            Instructions for Emergency Contacts:
            {emergency_info['contact_instructions']}

            Area Information:
            {location_info['area_description']}
            {location_info['time_safety']}

            This is an automated emergency alert from {request.user.get_full_name()}.
            Please respond immediately.
            """

            # Send emails to emergency contacts
            contacts = EmergencyContact.objects.filter(user=request.user)
            for contact in contacts:
                send_mail(
                    f'EMERGENCY ALERT from {request.user.get_full_name()}',
                    email_message,
                    settings.EMAIL_HOST_USER,
                    [contact.email],
                    fail_silently=False,
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Alert sent successfully!',
                'safety_tips': emergency_info['safety_tips'],
                'next_steps': emergency_info['next_steps']
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