from rest_framework import generics, status ,viewsets
from rest_framework.response import Response
from .models import AgentLogins , VirtualQueue , ccmCampaigns , VDN ,QueueLog
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
import json
from django.db.models import F ,Sum, IntegerField, Case, When, TimeField , Func , ExpressionWrapper ,CharField ,Q,Value,Count
from django.db.models.functions import Cast

class RegisterIVRDropView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date') 
        end_date = request.GET.get('end_date') 
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

        selectedQueue = request.GET.getlist('queue')
        # Validation: Ensure at least one item is selected
        if not selectedQueue:
            return JsonResponse({'error': 'At least one Queue/Skill must be selected'}, status=400)
        
        ## get VQ for campaigns
        virtualQueues = get_campaigns(request)
        data = json.loads(virtualQueues.content)
        ## end get VQ 
        if not data['client_id'] or data['dnis'] is None: # Corrected condition
            return JsonResponse({'message': 'No records found'}, status=404) # Return error response with 404

        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())
            
            queryset = QueueLog.objects.filter(
                time_id__range=(start_timestamp, end_timestamp),
                # queue__in=data['campaigns'],
                event__in=['IVRDROP'],
                arg3__in=data['dnis'],
                arg2__in=data['client_id']
            ).annotate(
                phone=F('arg4'),
                status=F('event'),
                call_date=Cast(Func(F('time_id'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                call_duration=F('arg1'),
                duration=F('arg1')
            ).values(
                'phone', 'time_id','call_date', 'duration', 'queue', 'status','call_duration','duration'
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
                                "message":"Listing for IVR DROP.",
                                "pagination": pagination_info,
                                "data":results,
                            }, status=200)
            
        else:
            return Response({"error": "Start and end dates are required"}, status=400)


class IVRDropCallsGraphView(APIView):
    def get(self, request):
        no_of_intervals = []
        no_of_interval = int(request.GET.get('no_of_interval', 0)) #Get no_of_interval from request
        interval = int(request.GET.get('interval', 0)) #Get interval from request
        
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


        ## get VQ for campaigns
        virtualQueues = get_campaigns(request)
        dataCampaigns = json.loads(virtualQueues.content)

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
                            When(arg1__gte=0, arg1__lte=interval, then=1),
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
                            When(arg1__gte=interval_start, arg1__lte=interval_end, then=1),
                            default=0,
                            output_field=IntegerField()
                        )
                    )
                    interval_start_end.append((interval_start, interval_end))
            
            # Query the data
            queryset = QueueLog.objects.filter(
                time_id__gte=start_timestamp,
                time_id__lte=end_timestamp,
                event__in=['IVRDROP'],
                arg3__in=dataCampaigns['dnis'],
                arg2__in=dataCampaigns['client_id'],
            )

            # # Annotate with conditional sums
            for idx, condition in enumerate(interval_conditions):
                start, end = interval_start_end[idx]  # Proper unpacking of interval range
                queryset = queryset.annotate(
                    **{f"Wait_{end}": Sum(condition)}  # Using the 'end' value for dynamic field name
                )

            # Fetch the results
            dataSet = queryset.values(*[f"Wait_{end}" for start, end in interval_start_end]).all()
            data = {}
            for values in dataSet:
                for key, value in values.items():
                    data[key] = data.get(key, 0) + value

            series_data = list(data.values())

            if sum(series_data) <= 0:
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
    queue =request.GET.getlist('queue')
    if not any(str(item).lower() == 'all' for item in queue) and queue:
        res_campaigns_query = res_campaigns_query.filter(virtual_queue__in=queue)

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