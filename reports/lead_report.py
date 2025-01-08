from rest_framework import generics, status ,viewsets
from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField ,LeadIn
from .serializers import ManualRecordingLogSerializer
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from django.db.models.expressions import RawSQL
from django.db import connection
from datetime import datetime
import math
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from django.conf import settings
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q
import json
from django.db.models.functions import  Ceil
from collections import defaultdict

# http://127.0.0.1:8000/api/leads_report/?start_date=2024-08-01&end_date=2025-01-02&format=json&clients=Zitro-LLC&dial_status=Not%20Connected

class LeadsReportView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
        dial_status = request.GET.get('dial_status') 
        page_number = int(request.GET.get('page_number', 1)) 
        page_size = int(request.GET.get('page_size', 10))  
        offset = (page_number - 1) * page_size

        start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        # Check if both dates are provided
        if not start_date or not end_date:
            return JsonResponse({"error": "Both start_date and end_date must be provided."}, status=400)

        # Ensure start_date is less than end_date
        if start_date >= end_date:
            return JsonResponse({"error": "start_date must be earlier than end_date."}, status=400)

        ## get VQ for campaigns
        virtualQueues = get_campaigns(request)
        data = json.loads(virtualQueues.content)
        ## end get VQ 
        if not data['skills'] or data['crm_table'] is None: # Corrected condition
            return JsonResponse({"error": "No skill or Skill not properly Configured."}, status=404)  

        if not data['form_name'] or data['form_name'] is None:
            return JsonResponse({"error": "Form Name is Empty."}, status=404)  
        
        # get form fields and mapping with data 
        form_name = data['form_name']
        formFieldsArray = getCampaignFields(form_name)
        formFieldsArray = json.loads(formFieldsArray.content)

        print(formFieldsArray['select_fields'])
        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())


            # Filter and annotate the query
            queryset = LeadIn.objects.filter(
                time_id__range=(start_timestamp, end_timestamp),
                queue__in=data['skills']
            ).order_by('time_id')

            paginator = Paginator(queryset, page_size)  # `page_size` is the number of items per page
            page_obj = paginator.get_page(page_number)  # `page_number` is the current page number
            # Results for the current page
            results = list(page_obj)

            # Pagination details
            pagination_info = {
                'total_items': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
            return Response({
                                "message":"Leads Report.",
                                "mapping": formFieldsArray['mapping'],
                                "pagination": pagination_info,
                                "data": results,
                            }, status=200)
        else:
            return Response({"error": "Start and end dates are required"}, status=400)
         
def getCampaignFields(formName):

    formFields = { 'lead_id' : 'Lead ID', 
                'time_id' : 'Entry Date',
                 'modify_time' : 'Modify Time', 
                 'agent' : 'User Extension',
                 'ccm_agent_full_name' : 'User Name', 
                 'status' : 'Status', 
                 'cli' : 'Phone Number', 
                 'queue' : 'Queue', 
                 'call_type' : 'Call Type', 
                 'manual_being_dialed' : 'Manual Dialed', 
                 'duration' : 'Duration (Secs)',
                 'manual_call_duration' : 'Manual Duration (Secs)',
                 'selected_option' : 'Selected Option' ,
                 'disconnection_cause' : 'Disconnection Cause'}

    select_fields = list(formFields.keys())

    # Querying CcmCampaign and joining with Vdn model
    sql_lead_in = (
        CampaignField.objects
        .filter(campaign_id__in=formName)
        .values( 'q_field','question','priority','field_report','type')
        .distinct()
    )
    for row in sql_lead_in:
        #formFields.append({row['q_field']:row['question']})
        formFields[row['q_field']] = row['question']
        select_fields.append(row['q_field'])

    response = {
        'mapping': formFields,
        'select_fields': select_fields,
    }
    return JsonResponse(response)


def get_campaigns(request):
    # Convert query results into an array
    queue = request.GET.get('queue', '')
    campaigns = [queue]
    # Querying CcmCampaign and joining with Vdn model
    sql_lead_in = (
        ccmCampaigns.objects
        .filter(name__in=campaigns, crm_table__isnull=False)
        .values( 'client_campaign_id','client_id','crm_table','name','form_name')
        .distinct()
    )
    # Process results
    # Process the data directly into structured output
    data = defaultdict(list)
    for row in sql_lead_in:
        data['client_ids'].append(row['client_id'])
        data['client_campaigns_ids'].append(row['client_campaign_id'])
        data['crm_table'].append(row['crm_table'])
        data['skills'].append(row['name'])
        data['form_name'].append(row['form_name'])

    # Prepare the response
    response = {
        'skills': data['skills'],
        'client_id': data['client_ids'],
        'client_campaigns_ids': data['client_campaigns_ids'],
        'dnis': [],
        'crm_table': data['crm_table'],
        'form_name': data['form_name']
    }
    return JsonResponse(response)
 
class RoundUp(Func):
    function = 'CEIL'

class Ceil(Func):
    function = 'CEIL'
class TimeDiff(Func):
    function = 'SEC_TO_TIME'
    arity = 1
    output_field = TimeField()