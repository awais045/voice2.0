from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField ,LeadIn
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from django.db import connection
from datetime import datetime
import math
from django.core.paginator import Paginator 
from django.conf import settings
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q
import json
from collections import defaultdict
from django.db import connections

#http://127.0.0.1:8000/api/leads_report/?start_date=2024-09-01&end_date=2025-01-09&format=json&clients=Zitro-LLC&queue=IA-English&page_size=22&report_type=upload&lead_id=3

class LeadsReportView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
        report_type = request.GET.get('report_type') 
        lead_id = int(request.GET.get('lead_id', 0)) 
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

        selectedFields = formFieldsArray['select_fields']

        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())

            """
            Fetch leads from a dynamic database using the same query logic.

            :param new_database_name: The name of the database to connect dynamically.
            :param start_timestamp: Start timestamp for filtering.
            :param end_timestamp: End timestamp for filtering.
            :param data: Data containing the 'skills' for filtering.
            :param page_size: Number of items per page.
            :param page_number: Current page number.
            :return: List of results for the current page.
            """
            new_database_name = data['new_database_name']
            # Get the default database connection settings
            current_db_settings = connections.databases['default'].copy()
            # Update the NAME (database name) to the dynamic one
            current_db_settings['NAME'] = new_database_name

            # Add a new connection with a unique alias
            alias = f'dynamic_{new_database_name}'
            connections.databases[alias] = current_db_settings
            # Filter and annotate the query
            # queryset = LeadIn.objects.using(alias).filter(
            #     time_id__range=(start_timestamp, end_timestamp),
            #     queue__in=data['skills']
            # ).order_by('time_id')
            queryset = LeadIn.objects.using(alias)
            if report_type == 'upload':
                queryset = queryset.filter(
                    time_id__range=(start_timestamp, end_timestamp),
                    queue__in=data['skills']
                ).order_by('time_id')
            elif report_type == 'dialing':
                queryset = queryset.filter(
                    modify_time__range=(start_timestamp, end_timestamp),  # Use modify_time
                    queue__in=data['skills']
                ).order_by('modify_time')  # Order by modify_time

            if lead_id:
                queryset = queryset.filter(lead_id=lead_id)

            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page_number)

            # *** Apply values() to the page_obj.object_list ***
            results = list(page_obj.object_list.values(*selectedFields))

            # Pagination details (this remains the same)
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
                    'status' : 'Status', 
                    'call_id' : 'Call ID', 
                    'cli' : 'Phone Number', 
                    'queue' : 'Queue', 
                    'call_type' : 'Call Type', 
                    'manual_being_dialed' : 'Manual Dialed', 
                    'duration' : 'Duration (Secs)',
                    'manual_call_duration' : 'Manual Duration (Secs)',
                    'selected_option' : 'Selected Option' ,
                    'attempts' : 'Dial Attempts' ,
                    'disconnection_cause' : 'Disconnection Cause'}

    select_fields = list(formFields.keys())

    # Querying CcmCampaign and joining with Vdn model
    sql_lead_in = (
        CampaignField.objects
        .filter(
            campaign_id__in=formName,
            add_in_report='Y',
            active='Y'
            )
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


def add_dynamic_connection(alias, config):
    connections.databases[alias] = config

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

    parts = data['crm_table'][0].split('.')
    try:
        new_database_name = parts[0]
        print(f"First part of: {new_database_name}")
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
 
class RoundUp(Func):
    function = 'CEIL'

class Ceil(Func):
    function = 'CEIL'
class TimeDiff(Func):
    function = 'SEC_TO_TIME'
    arity = 1
    output_field = TimeField()