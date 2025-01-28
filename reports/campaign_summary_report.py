from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField  ,VirtualQueue ,ManualCallsRecording,AgentLogins , QueueLog,AgentBreak
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from datetime import datetime ,timedelta, date
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func  ,CharField ,Q,Value,Count,Min, Max,ExpressionWrapper,Value
import json
from collections import defaultdict
from django.db import connections ,connection
from django.db.models.functions import Length,Coalesce, Abs,Cast

#http://127.0.0.1:8000/api/campaign_summary_report/?start_date=2024-11-11&end_date=2024-12-14&format=json&clients=infoarc&queue=infoarc&groupOndate=1&groupBy=campaign

class CampaignSummaryReportView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
        groupOndate = get_int_from_request(request, 'groupOndate')
        groupBy = request.GET.get('groupBy') 

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

        # Ensure the range is within 30 days
        if (end_date - start_date).days > 30:
            return JsonResponse({"error": "The date range cannot exceed 30 days."}, status=400)
 
        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())

            resultData = getAgentLoginsAndBreaksData(start_timestamp , end_timestamp ,data['skills'] ,groupBy,groupOndate )
            dataResult = json.loads(resultData.content)
            
            callStatsJson = getCallStatResult(start_timestamp , end_timestamp ,data['skills'] ,groupBy,groupOndate )
            callStatsResult = json.loads(callStatsJson.content)

            response = {
                'message':"Campaign Summary Report",
                'callStatsResult': callStatsResult,
                'data': dataResult,
            }
            return JsonResponse(response)
        else:
            return Response({"error": "Start and end dates are required"}, status=400)

def getCallStatResult(startDate,endDate,skills,group_by,group_on_date):

    start_date_value = Value(startDate) 
    queryset = (
            QueueLog.objects
            .annotate(
                dte=Func(F('time_id'),Value('%Y-%m-%d'),function='FROM_UNIXTIME',output_field=CharField()),
            ).filter(
                time_id__range=(startDate, endDate),
                event__in=['COMPLETECALLER', 'COMPLETEAGENT', 'TRANSFER' , 'NONVOICEEND'],
            )
            .filter(Q(arg2__gte=0))
            .values('agent', 'queue', 'dte','time_id' )
            .annotate(
                calls1=Count('*'),
                talk_time = Sum(
                    Case(
                        # Handling TRANSFER event
                        When(
                            event='TRANSFER',
                            then=Case(
                                # If (time_id - abs(arg3)) is less than startDate, use (time_id - startDate)
                                When(
                                    time_id__lt=F('time_id') - Abs(F('arg3')) - Value(startDate),
                                    then=F('time_id') - Value(startDate),
                                ),
                                default=Abs(F('arg3')),
                                output_field=IntegerField(),
                            ),
                        ),
                        # Handling all other events except NONVOICEEND
                        When(
                            ~Q(event='NONVOICEEND'),
                            then=Case(
                                # If (time_id - abs(arg2)) is less than startDate, use (time_id - startDate)
                                When(
                                    time_id__lt=F('time_id') - Abs(F('arg2')) - Value(startDate),
                                    then=F('time_id') - Value(startDate),
                                ),
                                default=Abs(F('arg2')),
                                output_field=IntegerField(),
                            ),
                        ),
                        # Default case
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
                inside=Sum(Case( When(event='TRANSFER', then=Value(1)),default=Value(0),output_field=CharField())),
                hold=Sum(Case(When(event='HOLD', then=F('time_id')),default=Value(0))),
                un_hold=Sum(Case(When(event='UNHOLD', then=F('time_id')),default=Value(0))),
                non_voice=Sum(Case(When(event='NONVOICEEND', then=Value(1)),default=Value(0))),
                calls=Sum(Case(When(event__in=['COMPLETECALLER', 'COMPLETEAGENT', 'TRANSFER'], then=Value(1)),default=Value(0)))
            ).order_by('agent').values( 'hold','un_hold','non_voice','calls','calls1' ,'inside','dte','talk_time' )
        )
    print(queryset.query)

    response = {
        'getCallStatResult': list(queryset.values()),
    }
    return JsonResponse(response)

def getAgentLoginsAndBreaksData(startDate,endDate,skills,group_by,group_on_date):
    
    # Filter and annotate the query
    logins = AgentLogins.objects.filter(
            Q(endTime__range=(startDate, endDate)) | 
            Q(startTime__lt=startDate, endTime__gt=endDate)
        ).filter(
            queue__in=skills
        ).values('time_id', 'extension', 'queue').annotate(
            calc_starttime=Min(
                Case(
                    When(startTime__lt=startDate, then=Value(startDate)),
                    default=F('startTime'),
                    output_field=IntegerField()
                )
            ),
            calc_endtime=Max(
                Case(
                    When(endTime__gt=endDate, then=Value(endDate)),
                    default=F('endTime'),
                    output_field=IntegerField()
                )
            )
        ).order_by('queue', 'extension').values('time_id', 'extension', 'calc_starttime', 'calc_endtime','queue')

    # Required mappings and placeholders (replace these appropriately)
    agent_names = {}   
    queue_mapping = {}  
    for skill in skills:
        queue_mapping[skill] = {skill}
        
    added_rec = {}   
    agent_logins = {}   

    # group_on_date = True   
    # group_by = "agent"   

    for login_info in logins:

        extension = login_info['extension']
        full_name = extension
        db_queue = login_info['queue']

        calc_start = login_info['calc_starttime']
        db_calc_start = login_info['calc_starttime']
        start_time = datetime.fromtimestamp(calc_start).strftime("%Y-%m-%d")

        calc_end = login_info['calc_endtime']
        db_calc_end = login_info['calc_endtime']

        time_id = login_info['time_id']
        diff_in_days = date_diff_in_days(calc_start, calc_end)
        # Example use of fields
        # print(f"Extension: {extension}, Queue: {db_queue}, Start: {calc_start}, End: {calc_end}, Time ID: {time_id}")
        i = 0
        is_added = False
        if group_on_date:
            while i <= diff_in_days:
                if i > 0:
                    calc_start_datetime = datetime.fromtimestamp(calc_start)  # Convert to datetime object
                    start_time = calc_start_datetime + timedelta(days=1)  # Add one day
                    start_time = start_time.strftime("%Y-%m-%d") 

                if diff_in_days > 0 and i < diff_in_days:
                    calc_end = int(datetime.fromtimestamp(calc_start + 86400).replace(hour=0, minute=0, second=0).timestamp())
                elif i == diff_in_days:
                    calc_end = db_calc_end

                diff_time = calc_end - calc_start
                if diff_time > 0:
                    if group_by in ["campaign", "agent"]:
                        for queue in queue_mapping.get(db_queue, []):
                            if added_rec.get(queue, {}).get(extension, {}).get(time_id):
                                continue

                            added_rec.setdefault(queue, {}).setdefault(extension, {})[time_id] = 1

                            if group_by == "campaign":
                                agent_logins.setdefault(queue, {}).setdefault(extension, {}).setdefault(start_time, {'login': 0, 'name': full_name})['login'] += diff_time
                            elif group_by == "agent":
                                agent_logins.setdefault(extension, {}).setdefault(queue, {}).setdefault(start_time, {'login': 0, 'name': full_name})['login'] += diff_time
                    else:
                        agent_logins.setdefault(start_time, {}).setdefault(extension, {'login': 0, 'name': full_name})['login'] += diff_time

                i += 1
        else:
            diff_time = calc_end - calc_start
            if diff_time == 0:
                continue

            if group_by in ["campaign", "agent"]:
                for queue in queue_mapping.get(db_queue, []):
                    print(queue)
                    if added_rec.get(queue, {}).get(extension, {}).get(time_id):
                        continue

                    added_rec.setdefault(queue, {}).setdefault(extension, {})[time_id] = 1

                    if group_by == "campaign":
                        agent_logins.setdefault(queue, {}) \
                                    .setdefault(extension, {}) \
                                    .setdefault(start_time, {'login': 0, 'name': full_name})['login'] += diff_time
                        agent_logins[queue][extension][start_time]['name'] = full_name 

                    elif group_by == "agent":
                        agent_logins.setdefault(extension, {}) \
                        .setdefault(start_time, {'login': 0, 'name': full_name})['login'] += diff_time
                        agent_logins[extension][start_time]['name'] = full_name 
            else:
                agent_logins.setdefault(extension, {'login': 0, 'name': full_name})['login'] += diff_time

    agentBreaksResponse = getAgentBreak(startDate,endDate,skills,group_by,group_on_date , agent_logins )
    agentBreaksResult = json.loads(agentBreaksResponse.content)
    response = {
        # 'agent_logins': agent_logins,
        'agentBreaks': agentBreaksResult,
    }
    return JsonResponse(response)
        

def getAgentBreak(startDate,endDate,skills,group_by,group_on_date , agent_queue_logins ):
    
    # Filter and annotate the query
    breakResult = AgentBreak.objects.filter(
            Q(endTime__range=(startDate, endDate)) | 
            Q(startTime__lt=startDate, endTime__gt=endDate)
        ).filter(
            queue__in=skills
        ).values('time_id', 'extension', 'queue','breakCode').annotate(
            calc_starttime=Min(
                Case(
                    When(startTime__lt=startDate, then=Value(startDate)),
                    default=F('startTime'),
                    output_field=IntegerField()
                )
            ),
            calc_endtime=Max(
                Case(
                    When(endTime__gt=endDate, then=Value(endDate)),
                    default=F('endTime'),
                    output_field=IntegerField()
                )
            )
        ).order_by( 'extension').values('time_id', 'extension','breakCode', 'calc_starttime', 'calc_endtime','queue','fullName')

    # Required mappings and placeholders (replace these appropriately)
    agent_names = {}   
    queue_mapping = {}  
    for skill in skills:
        queue_mapping[skill] = {skill}
    
    added_rec = {}
    for row in breakResult:
        extension = row['extension']
        db_queue = row['queue']
        diff_time = row['calc_endtime'] - row['calc_starttime']
        start_time = datetime.fromtimestamp(row['calc_starttime']).strftime("%Y-%m-%d")
        time_id = row['time_id']
        break_code = row['breakCode']

        if diff_time == 0:
            continue

        if group_on_date:
            i = 0
            calc_end = row['calc_endtime']
            db_calc_end = row['calc_endtime']
            calc_start = row['calc_starttime']
            diff_in_days = date_diff_in_days(calc_start, calc_end)
            start_time = datetime.fromtimestamp(calc_start).strftime("%Y-%m-%d")

            while i <= diff_in_days:
                if i > 0:
                    calc_start = int((datetime.fromtimestamp(calc_start) + timedelta(days=1)).timestamp())
                    start_time = datetime.fromtimestamp(calc_start).strftime("%Y-%m-%d")

                if diff_in_days > 0 and i < diff_in_days:
                    calc_end = int((datetime.fromtimestamp(calc_start) + timedelta(days=1)).timestamp())
                elif i == diff_in_days:
                    calc_end = db_calc_end
                
                diff_time = calc_end - calc_start

                if diff_time > 0:
                    process_queue_logic(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time)
                i += 1
        else:
            process_queue_logic(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time)
    
    response = {
        'agent_logins': agent_queue_logins,
    }
    return JsonResponse(response)
      

def process_queue_logic(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time):
    if break_code == "WRAPUP":
        return
    
    if break_code == "MANUALDIAL":
        process_manual_dial(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time)
    else:
        process_aux(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time)

def process_manual_dial(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time):
    if group_by in ["campaign", "agent"]:
        for queue in queue_mapping.get(db_queue, []):
            if added_rec.get(queue, {}).get(extension, {}).get(time_id, {}).get(break_code):
                continue
            added_rec.setdefault(queue, {}).setdefault(extension, {}).setdefault(time_id, {})[break_code] = 1
            
            if group_by == "campaign":
                agent_queue_logins.setdefault(queue, {}).setdefault(extension, {}).setdefault(start_time, {}).setdefault('manual', 0)
                agent_queue_logins[queue][extension][start_time]['manual'] += diff_time
            elif group_by == "agent":
                agent_queue_logins.setdefault(extension, {}).setdefault(queue, {}).setdefault(start_time, {}).setdefault('manual', 0)
                agent_queue_logins[extension][queue][start_time]['manual'] += diff_time
    else:
        agent_queue_logins.setdefault(start_time, {}).setdefault(extension, {}).setdefault('manual', 0)
        agent_queue_logins[start_time][extension]['manual'] += diff_time

def process_aux(queue_mapping, db_queue, extension, time_id, break_code, agent_queue_logins, added_rec, group_by, start_time, diff_time):
    if group_by in ["campaign", "agent"]:
        for queue in queue_mapping.get(db_queue, []):
            if added_rec.get(queue, {}).get(extension, {}).get(time_id, {}).get(break_code):
                continue
            added_rec.setdefault(queue, {}).setdefault(extension, {}).setdefault(time_id, {})[break_code] = 1
            
            if group_by == "campaign":
                agent_queue_logins.setdefault(queue, {}).setdefault(extension, {}).setdefault(start_time, {}).setdefault('aux', 0)
                agent_queue_logins[queue][extension][start_time]['aux'] += diff_time
            elif group_by == "agent":
                agent_queue_logins.setdefault(extension, {}).setdefault(queue, {}).setdefault(start_time, {}).setdefault('aux', 0)
                agent_queue_logins[extension][queue][start_time]['aux'] += diff_time
    else:
        agent_queue_logins.setdefault(start_time, {}).setdefault(extension, {}).setdefault('aux', 0)
        agent_queue_logins[start_time][extension]['aux'] += diff_time


def date_diff_in_days(start, end):
    """Calculate difference in days between two timestamps."""
    start_date = datetime.fromtimestamp(start)
    end_date = datetime.fromtimestamp(end)
    return (end_date - start_date).days

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

# def FROM_UNIXTIME(timestamp):
#     return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
