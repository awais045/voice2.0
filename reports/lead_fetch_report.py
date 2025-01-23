from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField ,LeadIn ,VirtualQueue ,AgentLogOutbound,ManualCallsRecording
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from datetime import datetime
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q,Value,Count, Value as V 
import json
from collections import defaultdict
from django.db import connections
from .serializers import AgentCallLogSerializer,ManualRecordingLogSerializer
from django.db.models.functions import Cast ,Coalesce 
from django.db import models,connection
import math
from django_mysql.models import GroupConcat

class FetchLeadsReportView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
        disposition = request.GET.get('disposition') 

        duration = get_int_from_request(request, 'duration')
        lead_id = get_int_from_request(request, 'lead_id')
        agent = get_int_from_request(request, 'agent')
        cli = get_int_from_request(request, 'cli')

        page_number = int(request.GET.get('page_number', 1)) 
        page_size = int(request.GET.get('page_size', 10))  

        start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        # Check if both dates are provided
        if not start_date or not end_date:
            return JsonResponse({"error": "Both start_date and end_date must be provided."}, status=400)

        # Ensure start_date is less than end_date
        if start_date >= end_date:
            return JsonResponse({"error": "start_date must be earlier than end_date."}, status=400)

        call_type = request.GET.get('call_type') 
        allowed_call_types = ['INBOUND', 'MANUAL']
        if not call_type:  # Check if call_type is empty (None or "")
            return JsonResponse({'error': 'call_type parameter is required.'}, status=400)

        if call_type.upper() not in allowed_call_types: #case insensitive check
            return JsonResponse({'error': 'Invalid call_type. Allowed values are INBOUND and MANUAL.'}, status=400)

        ## get VQ for campaigns
        virtualQueues = get_campaigns(request)
        data = json.loads(virtualQueues.content)
        ## end get VQ 
        if not data['skills'] or data['crm_table'] is None: # Corrected condition
            return JsonResponse({"error": "No skill or Skill not properly Configured."}, status=404)  

        if not data['form_name'] or data['form_name'] is None:
            return JsonResponse({"error": "Form Name is Empty."}, status=404)  
    
        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())

            queryset = AgentLogOutbound.objects.raw("""
                SELECT a.lead_id, a.time_id, a.manual_id, COUNT(*) AS cnt,
                    SUM(b.end_epoch - b.start_epoch) AS total_call_duration,
                    SUM(b.length_in_sec) AS total_talk_time,
                    date_format(from_unixtime(a.time_id), "%%Y-%%m-%%d %%H:%%i:%%s") as formatted_time_id,
                    a.user, GROUP_CONCAT(DISTINCT b.extension) AS cli,
                    b.extension, a.status AS diposition,
                    GROUP_CONCAT(b.dial_status), b.dial_status,
                    a.time_spent, b.campaign_name, a.campaign , b.recording_id,a.id
                FROM agent_log_outbound AS a
                LEFT JOIN manual_recording_log AS b
                    ON a.lead_id = b.lead_id AND a.manual_id = b.manual_id
                WHERE a.time_id BETWEEN %s AND %s
                    AND a.status NOT LIKE %s
                GROUP BY a.manual_id
                ORDER BY a.id ASC
            """, [start_timestamp, end_timestamp,   "%lock%"])
           
            # Convert RawQuerySet results into a list of dictionaries manually
            results = [
                {
                    "lead_id": row.lead_id,
                    "time_id": row.time_id,
                    "manual_id": row.manual_id,
                    "cnt": row.cnt,
                    "total_call_duration": row.total_call_duration,
                    "total_talk_time": row.total_talk_time,
                    "formatted_time_id": row.formatted_time_id,
                    "user": row.user,
                    "diposition": row.diposition,
                    "dial_status": row.dial_status,
                    "time_spent": row.time_spent,
                    "campaign_name": row.campaign_name,
                    "campaign": row.campaign,
                    "recording_id": row.recording_id,
                    "id": row.id,
                }
                for row in queryset
            ]
            # Pagination
            paginator = Paginator(results, page_size)
            page_obj = paginator.get_page(page_number)
            # Pagination details
            pagination_info = {
                'total_items': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
            return Response({
                                "message":"Lead Fetch Report.",
                                "pagination": pagination_info,
                                "data": list(page_obj),
                            }, status=200)
 
        else:
            return Response({"error": "Start and end dates are required"}, status=400)
         
def get_campaigns(request):
    # Convert query results into an array
    # Base query filtering by client and active status
    res_campaigns_query = VirtualQueue.objects.filter(
        client=request.GET.get('clients'),
        active='Y'
    )

    # Additional filter if 'queue' is provided and not 'all'
    queue = request.GET.get('queue', '')
    if queue != 'all' and queue != '':
        res_campaigns_query = res_campaigns_query.filter(virtual_queue=queue)

    # Convert query results into an array
    campaigns = [res_campaign.queue for res_campaign in res_campaigns_query]

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
        data['client_ids'].append(row.get('client_id', None))  # Use None or an appropriate default
        data['client_campaigns_ids'].append(row.get('client_campaign_id', None))
        data['crm_table'].append(row.get('crm_table', None))
        data['skills'].append(row.get('name', None))
        data['form_name'].append(row.get('form_name', None))

    parts = data['crm_table'][0].split('.')
    try:
        new_database_name = parts[0]

    except IndexError:
        new_database_name = 'zitro'
    # Prepare the response 
    response = {
        'skills': data['skills'],
        'client_id': data['client_ids'],
        'client_campaigns_ids': data['client_campaigns_ids'],
        'dnis': [],
        'crm_table': data['crm_table'],
        'form_name': data['form_name'],
        'new_database_name': new_database_name
    }
    return JsonResponse(response)
 
def get_int_from_request(request, param_name, default=0):
    param_str = request.GET.get(param_name)
    return int(param_str) if param_str and param_str.isdigit() else default

class RoundUp(Func):
    function = 'CEIL'

class Ceil(Func):
    function = 'CEIL'
class TimeDiff(Func):
    function = 'SEC_TO_TIME'
    arity = 1
    output_field = TimeField()
