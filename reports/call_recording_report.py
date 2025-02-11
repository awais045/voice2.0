from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField ,LeadIn ,VirtualQueue ,AgentCallLog,ManualCallsRecording,ClientCampaign,RecordingTempFile
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from django.db import connection
from datetime import datetime
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q,Value,Count
import json
from collections import defaultdict
from django.db import connections
from .serializers import AgentCallLogSerializer,ManualRecordingLogSerializer
from django.db.models.functions import Cast 
import socket
import os
import base64

#http://127.0.0.1:8000/api/callcenter_recordings/?start_date=2024-11-01&end_date=2025-01-10&format=json&clients=infoarc&queue=infoarc&call_type=INBOUND&cli=&disposition=&lead_id=&duration=
#http://127.0.0.1:8000/api/callcenter_recordings/?start_date=2024-08-01&end_date=2025-01-10&format=json&clients=infoarc&queue=infoarc&call_type=MANUAL&cli=&disposition=&lead_id=&duration=&agent=

class PlayCallRecordingView(APIView):
    def get(self, request):
        
        root_path = '/recording/web-LHE/Audio/'
        
        client = request.GET.get('clients') # reuired 
        skill = request.GET.get('queue') #required 
        caller_id = request.GET.get('caller_id') #required 
        call_id = request.GET.get('call_id') #required 
        lead_id = get_int_from_request(request, 'lead_id') 
        transfer_count = get_int_from_request(request, 'transfer_count') # default =0  
        call_type = request.GET.get('call_type')  # required 
        agent = request.GET.get('agent')  # required 
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
        
        if not data['client_campaigns_ids'] or data['client_campaigns_ids'] is None:
            return JsonResponse({"error": "Client Campaign Empty."}, status=404)
        
        # Filter and annotate the query
        queryGetCampaignName = ClientCampaign.objects.filter(
            id__in=data['client_campaigns_ids'],
        ).first()
        campaign = queryGetCampaignName.campaign_name
        
        timestamp = float(call_id)
        month = datetime.fromtimestamp(timestamp).strftime("%m-%Y")
        dateA = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y") 
        dateB = datetime.fromtimestamp(timestamp).strftime("%d-%m-%y")
        
        if int(transfer_count) > 0:
            filename = f"{client}-{skill}-{caller_id}-{dateB}-{call_id}-{transfer_count}.mp3"
        else:
            filename = f"{client}-{skill}-{agent}-{caller_id}-{dateB}-{call_id}.mp3"

        file_path = f"{root_path}/{client}/{campaign}/{skill}/{call_type.lower()}/{month}/{dateA}/{filename}"

        if call_type.lower() == 'manual':
            call_type = 'manual'
            manual_id = request.GET.get('manual_id') #required 

            campaign_id = data['client_campaigns_ids'][0]
            if manual_id:
                filename = f"{agent}-{manual_id}_{caller_id}_{campaign_id}-{call_id}.mp3"
            else:
                filename = f"{agent}-{caller_id}-{call_id}.mp3"

            recording = ManualCallsRecording.objects.filter(
                recording_id=request.GET.get('recording_id')
            ).first()
            
            file_path = recording.filename
            path_parts = file_path.split('/')
            
            if len(path_parts) < 9:
                slice_index = -5
                root_path = root_path.replace("Audio/", "")
            else:
                slice_index = -7
                
            file_path = '/'.join(path_parts[slice_index:]) + '.mp3'
            final_path = root_path + file_path

            params = {
                'time': int(datetime.now().timestamp()),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'remote_ip': socket.gethostbyname(socket.gethostname()),
                'final_path': final_path
            }
            record = RecordingTempFile.objects.create(
                    mpd_file_path= 'path/to/mpd/file.mpd',
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    user_id=1,
                    mpd_file_deleted='N',
                    skill=skill,
                    type='Audio',
                    agent=agent,
                    caller_id=caller_id,
                    call_id=call_id,
                    rec_file_name=json.dumps(params),
                    enc_pass='securepass',
                    play_url=''
                )
            if os.path.exists(final_path):
                with open(final_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                return JsonResponse({
                    'status': 'success',
                    'audio_data': audio_base64,
                    'content_type': 'audio/mpeg'
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)
   
        params = {
            'time': int(datetime.now().timestamp()),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'remote_ip': socket.gethostbyname(socket.gethostname()),
            'file_path': file_path
        }
        record = RecordingTempFile.objects.create(
                    mpd_file_path= 'path/to/mpd/file.mpd',
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    user_id=1,
                    mpd_file_deleted='N',
                    skill=skill,
                    type='Audio',
                    agent=agent,
                    caller_id=caller_id,
                    call_id=call_id,
                    rec_file_name=json.dumps(params),
                    enc_pass='securepass',
                    play_url=''
                )
        if os.path.exists(file_path):
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            return JsonResponse({
                'status': 'success',
                'audio_data': audio_base64,
                'content_type': 'audio/mpeg'
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)
        
        
class CallsRecordingsView(APIView):
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

            if(call_type == 'MANUAL'):

                # Filter and annotate the query
                queryset = ManualCallsRecording.objects.filter(
                    start_epoch__range=(start_timestamp, end_timestamp),
                    campaign_name__in=data['skills'],
                    length_in_sec__gt=duration
                ).annotate(
                    formatted_start_epoch=Cast(Func(F('start_epoch'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                    formatted_end_epoch=Cast(Func(F('end_epoch'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                ).order_by('start_epoch').reverse().annotate(
                    dateTime= F('start_epoch')  ,
                    billSec=F('length_in_sec'),
                    cliNum=F('extension'),
                    sourceName=F('vendor'),
                    agentExt=F('user'),
                )

                if lead_id:
                    queryset = queryset.filter(lead_id=lead_id)

                if cli:
                    queryset = queryset.filter(extension=cli)

                if disposition:
                    queryset = queryset.filter(disposition=disposition)
                
                if agent:
                    queryset = queryset.filter(Q(user__iexact=agent) | Q(user__icontains=agent))
                
                paginator = Paginator(queryset, page_size)  # `page_size` is the number of items per page
                page_obj = paginator.get_page(page_number)  # `page_number` is the current page number
                # Results for the current page
                results = ManualRecordingLogSerializer(page_obj, many=True)
                # Pagination details (this remains the same)
                # Pagination details
                pagination_info = {
                    'total_items': paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page_obj.number,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
                return Response({
                                    "message":"Manual Calls Report.",
                                    "pagination": pagination_info,
                                    "data": results.data,
                                }, status=200)


            ## INBOUND Call REcordings
            if(call_type == 'INBOUND'):
                # Filter and annotate the query
                queryset = AgentCallLog.objects.filter(
                    time_id__range=(start_timestamp, end_timestamp),
                    queue__in=data['skills'],
                    call_type=call_type,
                    duration__gt=duration
                ).annotate(
                    formatted_time_id=Cast(Func(F('time_id'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                    formatted_modify_time=Cast(Func(F('modify_time'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                    formatted_wrapup_time=Cast(Func(F('wrapup_time'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                    formatted_disconnected_at=Cast(Func(F('disconnected_at'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                ).order_by('time_id')

                if lead_id:
                    queryset = queryset.filter(lead_id=lead_id)

                if cli:
                    queryset = queryset.filter(cli=cli)

                if disposition:
                    queryset = queryset.filter(disposition=disposition)
                
                if agent:
                    queryset = queryset.filter(Q(agent__iexact=agent) | Q(agent__icontains=agent))

                paginator = Paginator(queryset, page_size)
                page_obj = paginator.get_page(page_number)

                results = AgentCallLogSerializer(page_obj, many=True)
                # Pagination details (this remains the same)
                pagination_info = {
                    'total_items': paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page_obj.number,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
                return Response({
                                    "message":"Call Recordings Report.",
                                    "pagination": pagination_info,
                                    "data": results.data,
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
                    'dial_attempts' : 'Dial Attempts' ,
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

