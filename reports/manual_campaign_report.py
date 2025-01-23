from rest_framework.response import Response
from .models import ccmCampaigns ,CampaignField  ,VirtualQueue ,ManualCallsRecording,AgentLogins , AgentLogOutbound
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from datetime import datetime 
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func  ,CharField ,Q,Value,Count
import json
from collections import defaultdict
from django.db import connections
from django.db.models.functions import Length

#http://127.0.0.1:8000/api/manual_campaign_report/?start_date=2024-11-01&end_date=2025-01-10&format=json&clients=infoarc&queue=infoarc&call_type=INBOUND&cli=&disposition=&lead_id=&duration=

class ManualCampaignReportView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
        groupOndate = get_int_from_request(request, 'groupOndate')

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

        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())

            resultData = outboundCampaignSummary(start_timestamp , end_timestamp ,data['skills'] ,groupOndate )
            dataResult = json.loads(resultData.content)

            response = {
                'message':"Manual Campaign Summary Report",
                'data': dataResult,
            }
            return JsonResponse(response)
        else:
            return Response({"error": "Start and end dates are required"}, status=400)


def outboundCampaignSummary(startDate , endDate ,skills ,groupOnDate =0 ):

    queryset = (
            ManualCallsRecording.objects
            .annotate(
                day_value=Func(F('start_epoch'),Value('%Y-%m-%d'),function='FROM_UNIXTIME',output_field=CharField()),
                user_length=Length('user'),
                duration_diff=F('end_epoch') - F('start_epoch')
            )
            .filter(
                start_epoch__range=(startDate, endDate),
                campaign_name__in=skills,
                user_length__lt=7 
            )
            .values('day_value', 'user')
            .annotate(
                lead_no=Count('manual_id', distinct=True),
                manual_count=Count('manual_id'),
                #call_process_time=Sum('length_in_sec'),
                total_time=Sum('length_in_sec'),
                answer_count=Sum(Case(When(length_in_sec__gt=0, then=Value(1)),default=Value(0),output_field=IntegerField())),
                call_process_time=Sum(
                            Case(
                                When(
                                    end_epoch__gt=0,
                                    then=Case(
                                        When(
                                            duration_diff__gt=3600,  # Use the 'duration_diff' annotation
                                            then=Value(1000, output_field=IntegerField())
                                        ),
                                        default=F('end_epoch') - F('start_epoch')  # Use the 'duration' annotation
                                    )
                                ),
                                default=Value(0, output_field=IntegerField())
                            )
                        )
            ).values( 'day_value', 'user', 'lead_no', 'manual_count', 'total_time', 'answer_count', 'call_process_time')
        )

    agent = {}
    for resAgent in queryset:
        # Calculate CALL_PROCESS_TIME if needed
        if resAgent['call_process_time'] < resAgent['total_time']:
            resAgent['call_process_time'] = resAgent['total_time'] + 1000

        totalRingtime = resAgent['call_process_time'] - resAgent['total_time']

        # Conditional processing based on groupOnDate
        if groupOnDate:
            day_value = resAgent['day_value']
            user = resAgent['user']

            if day_value not in agent:
                agent[day_value] = {}

            if user not in agent[day_value]:
                agent[day_value][user] = {}

            agent[day_value][user]["LEAD_NO"] = resAgent['lead_no']
            agent[day_value][user]["MANUAL"] = resAgent['manual_count']
            agent[day_value][user]["CALL_PROCESS_TIME"] = resAgent['call_process_time']
            agent[day_value][user]["TTIME"] = resAgent['total_time']
            agent[day_value][user]["ANSWER"] = resAgent['answer_count']
            agent[day_value][user]["totalRingtime"] = totalRingtime
            agent[day_value][user]["THT"] = 0
            agent[day_value][user]["bcwAcw"] = 0

        else:
            user = resAgent['user']

            if user not in agent:
                agent[user] = {}

            agent[user]["LEAD_NO"] = resAgent['lead_no']
            agent[user]["MANUAL"] = resAgent['manual_count']
            agent[user]["CALL_PROCESS_TIME"] = resAgent['call_process_time']
            agent[user]["TTIME"] = resAgent['total_time']
            agent[user]["ANSWER"] = resAgent['answer_count']
            agent[user]["totalRingtime"] = totalRingtime
            agent[user]["THT"] = 0
            agent[user]["bcwAcw"] = 0


    agentLogOutboundJson = agentLogOutBound(startDate , endDate ,skills ,groupOnDate)
    agentLogOutboundRows = json.loads(agentLogOutboundJson.content)


    if agentLogOutboundRows['agentData']:
        if groupOnDate:
            for date_key_val, user_detail in agentLogOutboundRows['agentData'].items():
                if date_key_val not in agent:
                    continue  

                for user, val_user in user_detail.items():
                    for m, val in val_user.items():
                        
                        tht_value = agent[date_key_val][user].get('THT', 0) 

                        if val.get('UNLOCKED') and val.get('LOCKED'):
                            agent[date_key_val][user]['THT'] =tht_value+ val['UNLOCKED'] - val['LOCKED']
                        else:
                            agent[date_key_val][user]['THT'] = tht_value+15
                        
                        # print(agent[date_key_val][user].get('CALL_PROCESS_TIME', 0))
                        agent[date_key_val][user]['bcwAcw'] = max(agent[date_key_val][user].get('THT', 0) - agent[date_key_val][user].get('CALL_PROCESS_TIME', 0), 0)
        else:
            for user, val_user in agentLogOutboundRows['agentData'].items():
                if user not in agent:
                    continue  

                for m, val in val_user.items():
                    tht_value = agent[user].get('THT', 0) 
                    if val.get('UNLOCKED') and val.get('LOCKED'):
                        agent[user]['THT'] = tht_value+val['UNLOCKED'] - val['LOCKED']
                    else:
                        agent[user]['THT'] = tht_value+15

                    agent[user]['bcwAcw'] = max(agent[user].get('THT', 0) - agent[user].get('CALL_PROCESS_TIME', 0),  0)

    response = {
        'agent': agent,
    }
    return JsonResponse(response)


def agentLogOutBound(startDate , endDate ,skills ,groupOnDate):
    queryset = AgentLogOutbound.objects.filter(
                time_id__range=(startDate, endDate),
                campaign__in=skills,
                status__in=['LOCKED', 'UNLOCKED']
            ).exclude(user='').annotate(
                day_value=Func(F('time_id'),Value('%Y-%m-%d'),function='FROM_UNIXTIME',output_field=CharField()),
                # manual_id= F('lead_id')  ,
            ).values('day_value','time_id','user','status','lead_id')
    
    agentData = {}
    for resAgent in queryset:
        # Conditional processing based on groupOnDate
        if groupOnDate:
            day_value = resAgent['day_value']
            user = resAgent['user']

            if day_value not in agentData:
                agentData[day_value] = {}

            if user not in agentData[day_value]:
                agentData[day_value][user] = {}

            if resAgent['lead_id'] not in agentData[day_value][user]:
                agentData[day_value][user][resAgent['lead_id']] = {}
        
            agentData[day_value][user][resAgent['lead_id']][resAgent['status']] = resAgent['time_id']
        else:
            user = resAgent['user']

            if user not in agentData:
                agentData[user] = {}

            if resAgent['lead_id'] not in agentData[user]:
                agentData[user][resAgent['lead_id']] = {}

            agentData[user][resAgent['lead_id']][resAgent['status']] = resAgent['time_id']

    response = {
        'agentData': agentData
    }
    return JsonResponse(response)

def getAgentLogins(startDate,endDate,skills,groupBy,groupOnDate):
    
    orderBy = 'extension'
    if groupBy == 'campaign':
        orderBy = 'queue,extension'

    # Filter and annotate the query
    logins = (
        AgentLogins.objects.annotate(
            calc_starttime=Case(
                When(startTime__lt=startDate, then=Value(startDate)),
                default=F('startTime'),
                output_field=IntegerField()
            ),
            calc_endtime=Case(
                When(endTime__gt=endDate, then=Value(endDate)),
                default=F('endTime'),
                output_field=IntegerField()
            )
        )
        .filter(
            (
                Q(endTime__range=(startDate, endDate)) |
                (Q(startTime__lt=startDate) & Q(endTime__gt=endDate)) |
                (Q(startTime__range=(startDate, endDate)) & Q(endTime__gt=endDate))
            ),
            queue__in=skills,  
            #breakCode__notin=['MANUALDIAL', 'WRAPUP']
        )
        .values('id','time_id', 'extension', 'calc_starttime', 'calc_endtime','queue')
        .order_by('extension')
    )
    # Required mappings and placeholders (replace these appropriately)
    agent_names = {}  # Map extension to agent names
    queue_mapping = {}  # Map dbQueue to virtual queues
    added_rec = {}  # Record tracking for added entries
    agent_logins = {}  # Final structure for storing agent login data

    group_on_date = True  # Replace based on your logic
    group_by = "campaign"  # Example grouping condition

    for login_info in logins:

        extension = login_info['extension']
        full_name = " "
        db_queue = login_info['queue']
        calc_end = login_info['calc_endtime']
        calc_start = login_info['calc_starttime']
        db_calc_end = login_info['calc_starttime']
        start_time = datetime.fromtimestamp(calc_start).strftime("%Y-%m-%d")

        time_id = login_info['time_id']
        # diff_in_days = date_diff_in_days(calc_start, calc_end)
        diff_in_days = 0
        # Example use of fields
        print(f"Extension: {extension}, Queue: {db_queue}, Start: {calc_start}, End: {calc_end}, Time ID: {time_id}")
        i = 0
        is_added = False
        if group_on_date:
            while i <= diff_in_days:
                if i > 0:
                    calc_start = int((datetime.fromtimestamp(calc_start) + datetime.timedelta(days=1)).timestamp())
                    start_time = datetime.fromtimestamp(calc_start).strftime("%Y-%m-%d")

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
                    if added_rec.get(queue, {}).get(extension, {}).get(time_id):
                        continue

                    added_rec.setdefault(queue, {}).setdefault(extension, {})[time_id] = 1

                    if group_by == "campaign":
                        agent_logins.setdefault(queue, {}).setdefault(extension, {'login': 0, 'name': full_name})['login'] += diff_time
                    elif group_by == "agent":
                        agent_logins.setdefault(extension, {}).setdefault(queue, {'login': 0, 'name': full_name})['login'] += diff_time
            else:
                agent_logins.setdefault(extension, {'login': 0, 'name': full_name})['login'] += diff_time

    return agent_logins
        


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

def date_diff_in_days(start, end):
    """Calculate difference in days between two timestamps."""
    start_date = datetime.date.fromtimestamp(start)
    end_date = datetime.date.fromtimestamp(end)
    return (end_date - start_date).days

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
