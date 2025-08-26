from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import time

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Get current timestamp
            current_time = time.time()
            
            # Get last activity from session
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Check if 30 minutes (1800 seconds) have passed
                if current_time - last_activity > 1800:
                    # Logout user due to inactivity
                    logout(request)
                    messages.warning(request, 'You have been logged out due to 30 minutes of inactivity.')
                    
                    # Redirect to login page
                    from django.shortcuts import redirect
                    return redirect('news:login')
            
            # Update last activity timestamp
            request.session['last_activity'] = current_time
        
        response = self.get_response(request)
        return response
