from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField ,LeadIn ,VirtualQueue ,AgentCallLog,ManualCallsRecording
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from django.db import connection
from datetime import datetime
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q
import json
from collections import defaultdict
from django.db import connections
from .serializers import AgentCallLogSerializer,ManualRecordingLogSerializer


class CallsRecordingsEvaluationView(APIView):
    
    def post(self, request): 
        call_type = request.POST.get('call_type') 
        rating = request.POST.get('rating') 
        comments = request.POST.get('comments') 

        recording_id = get_int_from_request(request, 'recording_id')
        duration = get_int_from_request(request, 'duration')
        lead_id = get_int_from_request(request, 'lead_id')

        call_type = request.POST.get('call_type') 
        allowed_call_types = ['INBOUND', 'MANUAL']
        if not call_type:  # Check if call_type is empty (None or "")
            return JsonResponse({'error': 'call_type parameter is required.'}, status=400)

        if call_type.upper() not in allowed_call_types: #case insensitive check
            return JsonResponse({'error': 'Invalid call_type. Allowed values are INBOUND and MANUAL.'}, status=400)


        # if(call_type == 'MANUAL'):

        if(call_type == 'INBOUND'):

            record = AgentCallLog.objects.filter(
                duration__gt=duration,
                id=recording_id
            ).order_by('time_id').first()

            print(record.call_type)
            print(record.queue)
            response = {
                'record': list(record),
            }
            return JsonResponse(response)

def get_int_from_request(request, param_name, default=0):
    param_str = request.POST.get(param_name)
    return int(param_str) if param_str and param_str.isdigit() else default