from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField ,VirtualQueue ,AgentCallLog,LeadEvaluation,ManualCallsRecording
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from django.db import connection,IntegrityError
from datetime import datetime
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q
import json
from collections import defaultdict
from django.db import connections
from .serializers import AgentCallLogSerializer,ManualRecordingLogSerializer
import time

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

        evaluatedBy = 10

        if(call_type == 'MANUAL'):
            record = ManualCallsRecording.objects.filter(
                duration__gt=duration,
                recording_id=recording_id
            ).order_by('start_time').first()

            if not record:
                return JsonResponse({'error': 'Invalid Recording ID.'}, status=400)

            ## exception handling 
            resultEvaluation = create_lead_evaluation(record , rating , comments ,evaluatedBy ,call_type)
            
            record.rating = rating
            record.comments = comments
            record.evaluation_id = 1
            record.evaluated_by = evaluatedBy
            record.evaluation_time = time.time()
            record.is_evaluated = 1
            try:
                record.save()
                if record.is_evaluated >0:
                    return Response({
                            "message":"Evaluation has been saved.",
                            "evaluation_type" : call_type,
                            "recording_id" : recording_id,
                            "data": [],
                    }, status=200)
            except Exception as e:
                # Handle potential exceptions during save operation
                return Response({
                    "message": "Error saving evaluation: " + str(e),
                    "evaluation_type": call_type,
                    "recording_id": recording_id,
                    "data": [],
                }, status=500) 
            

        if(call_type == 'INBOUND'):

            record = AgentCallLog.objects.filter(
                duration__gt=duration,
                id=recording_id
            ).order_by('time_id').first()

            if not record:
                return JsonResponse({'error': 'Invalid Recording ID.'}, status=400)

            ## exception handling 
            resultEvaluation = create_lead_evaluation(record , rating , comments ,evaluatedBy, call_type)
            
            record.rating = rating
            record.comments = comments
            record.evaluation_id = 1
            record.evaluated_by = evaluatedBy
            record.evaluation_time = time.time()
            record.is_evaluated = 1
            try:
                record.save()
                if record.is_evaluated >0:
                    return Response({
                            "message":"Evaluation has been saved.",
                            "evaluation_type" : call_type,
                            "recording_id" : recording_id,
                            "data": [],
                    }, status=200)
            except Exception as e:
                # Handle potential exceptions during save operation
                return Response({
                    "message": "Error saving evaluation: " + str(e),
                    "evaluation_type": call_type,
                    "recording_id": recording_id,
                    "data": [],
                }, status=500) 

        return Response({
                            "message":"Something went wrong, please try again later.",
                            "evaluation_type" : call_type,
                            "recording_id" : recording_id,
                            "data": [],
                    }, status=400)

def create_lead_evaluation(record , rating , comments ,evaluatedBy ,call_type):
    try:
        if(call_type == 'INBOUND'):
            reference_id = record.id
            cli = record.cli        
            queue = record.queue
            agent = record.agent
            interaction_time = record.time_id
        if(call_type == 'MANUAL'):
            reference_id = record.recording_id
            cli = record.extension
            queue = record.campaign_name
            agent = record.user
            interaction_time = record.start_epoch

        data = {
                'channel': 'voice',
                'lead_id': record.lead_id,
                'reference_id':reference_id ,
                'direction': 'Inbound',
                'contact': cli,
                'client_id': 789,
                'queue': queue,
                'agent': agent,
                'interaction_time':interaction_time ,
                'duration': record.duration, 
                'rating': rating,
                'comments': comments,
                'evaluated_by': evaluatedBy,
                'evaluation_time': time.time()  
            }
        # Create and save the LeadEvaluation object
        lead_evaluation = LeadEvaluation(**data)
        lead_evaluation.save()
        message = "Lead Evaluation"
    except IntegrityError as e:
        if 'Duplicate entry' in str(e):
            message =  "A record with the same values already exists."
        else:
            # Handle other IntegrityError cases
            message = "IntegrityError: {e}"
    return message

def get_int_from_request(request, param_name, default=0):
    param_str = request.POST.get(param_name)
    return int(param_str) if param_str and param_str.isdigit() else default