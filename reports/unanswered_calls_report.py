from rest_framework import generics, status ,viewsets
from rest_framework.response import Response
from .models import AgentLogins , VirtualQueue , ccmCampaigns , VDN , QueueLog
from .serializers import AgentLoginsSerializer ,QueueLogSerializer
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from django.db.models.expressions import RawSQL
from django.db import connection
from datetime import datetime
import math
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import F ,Sum, IntegerField, Case, When
import json
from django.db.models.functions import Cast

# http://127.0.0.1:8000/api/unanswered_calls_report/?start_date=2024-06-17&end_date=2024-12-24&format=json&page_size=20&page_number=1&clients=Zitro-LLC&queue=Zitro-All
#http://127.0.0.1:8000/api/unanswered_calls_report/graph/?start_date=2024-01-01&end_date=2025-01-02&format=json&no_of_interval=5&interval=20&campaign=Processor-MD&campaign=IA-English

class UnAnsweredCallsView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
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
        # print("\nAccessing data after response:")
        print(f"Campaigns: {data['campaigns']}")
        # print(f"Client IDs: {data['client_id']}")
        # print(f"Client Campaign IDs: {data['client_campaigns_ids']}")
        # print(f"DNIS: {data['dnis']}")
        ## end get VQ 
        if not data['campaigns'] or data['client_id'] is None: # Corrected condition
            return JsonResponse({"error": "No Campaigns."}, status=404) # Return error response with 404

        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())
                # Filter and annotate the query
        
            queryset = QueueLog.objects.filter(
                time_id__range=(start_timestamp, end_timestamp),
                queue__in=data['campaigns'],
                event__in=['ABANDON', 'EXITWITHTIMEOUT', 'EXITWITHKEY']
            ).annotate(
                CALLID=F('arg4'),
                START_DATE=F('time_id'),
                WAIT=F('arg3')
            ).values(
                'CALLID', 'START_DATE', 'WAIT', 'queue', 'event'
            ).order_by('time_id')

            # Apply pagination
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
                                "message":"UnAnswered Calls Report.",
                                "pagination": pagination_info,
                                "data":results,
                            }, status=200)
        else:
            return Response({"error": "Start and end dates are required"}, status=400)
        

class UnAnsweredCallsGraphView(APIView):
    def get(self, request):
        no_of_intervals = []
        QRY = []  # Use a list to build the query parts

        no_of_interval = int(request.GET.get('no_of_interval', 0)) #Get no_of_interval from request
        interval = int(request.GET.get('interval', 0)) #Get interval from request
        campaign_str = request.GET.get('campaign')
        campaign = campaign_str.split(',') if campaign_str else []

        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
        start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        # Check if both dates are provided
        if not start_date or not end_date:
            return JsonResponse({"error": "Both start_date and end_date must be provided."}, status=400)

        # Ensure start_date is less than end_date
        if start_date >= end_date:
            return JsonResponse({"error": "start_date must be earlier than end_date."}, status=400)

        if not all([no_of_interval, interval ]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())

            no_of_intervals = []
            interval_conditions = []
            interval_start_end = []

            for i in range(no_of_interval):
                interval_end = interval + interval * i
                if i == 0:
                    no_of_intervals.append(f"0 - {interval_end}")
                    interval_conditions.append(
                        Case(
                            When(arg3__gte=0, arg3__lte=interval, then=1),
                            default=0,
                            output_field=IntegerField()
                        )
                    )
                    interval_start_end.append((0, interval))
                else:
                    interval_start = interval + interval * (i - 1) + 1
                    interval_end = interval_start + interval
                    no_of_intervals.append(f"{interval_start} - {interval_end}")
                    interval_conditions.append(
                        Case(
                            When(arg3__gte=interval_start, arg3__lte=interval_end, then=1),
                            default=0,
                            output_field=IntegerField()
                        )
                    )
                    interval_start_end.append((interval_start, interval_end))
            
            # Query the data
            queryset = QueueLog.objects.filter(
                time_id__gte=start_timestamp,
                time_id__lte=end_timestamp,
                queue__in=campaign,
                event__in=['ABANDON', 'EXITWITHTIMEOUT', 'EXITWITHKEY']
            )

            # # Annotate with conditional sums
            for idx, condition in enumerate(interval_conditions):
                start, end = interval_start_end[idx]  # Proper unpacking of interval range
                queryset = queryset.annotate(
                    **{f"Wait_{end}": Sum(condition)}  # Using the 'end' value for dynamic field name
                )

            # Fetch the results
            data = queryset.values(*[f"Wait_{end}" for start, end in interval_start_end]).first()

            series_data = []
            if data:
                for key, value in data.items():
                    series_data.append(int(value))

            # # Check if series data is empty
            if sum(series_data) <= 0:
                no_of_intervals = []
                series_data = []

            return JsonResponse({
                'data': series_data,
                'no_of_intervals': no_of_intervals
            })
        else:
            return Response({"error": "Start and end dates are required"}, status=400)


def get_campaigns(request):
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
        .values( 'client_campaign_id','client_id')
        .distinct()
    )
    # Process results
    crm_table = []
    client_ids = []
    client_campaigns_ids = []

    for sql_lead_in_res_row in sql_lead_in:
        client_ids.append(sql_lead_in_res_row['client_id'])
        client_campaigns_ids.append(sql_lead_in_res_row['client_campaign_id'])


    sql_lead_in = (
        VDN.objects
        .filter(client_campaign_id__in=client_campaigns_ids)
        .values( 'dnis')
        .distinct()
    )
    # Process results
    dnis = []
    for sql_lead_in_res_row in sql_lead_in:
        dnis.append(sql_lead_in_res_row['dnis'])

    return JsonResponse({'campaigns': campaigns,'client_id': client_ids ,'client_campaigns_ids':client_campaigns_ids ,'dnis':dnis})

def gettime(time, with_hour=True):
    min_time = time % 3600
    hr = (time - min_time) // 3600
    if hr == 24:
        hr = 0
    sec = min_time % 60
    min_time = (min_time - sec) // 60
    if hr < 10:
        hr = f"0{hr}"
    if min_time < 10:
        min_time = f"0{min_time}"
    if sec < 10:
        sec = f"0{sec}"

    # Use proper formatting
    return f"{hr}:{min_time}:{sec}" if with_hour else f"{min_time}:{sec}"

# Function to convert Unix timestamp to human-readable date
def from_unixtimestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
