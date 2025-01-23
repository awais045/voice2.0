from rest_framework import generics, status ,viewsets
from rest_framework.response import Response
from .models import AgentLogins , VirtualQueue , ccmCampaigns , VDN , QueueLog ,ManualCallsRecording
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
from django.db.models import F ,Sum, IntegerField, Case, When , TimeField , Func , ExpressionWrapper ,CharField ,Q,Value,Count
import json
from django.db.models.functions import  Ceil,Cast

# http://127.0.0.1:8000/api/manual_calls_report/?start_date=2024-08-01&end_date=2025-01-02&format=json&clients=Zitro-LLC&dial_status=Not%20Connected


class ManualCallsReportView(APIView):
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
        print(f"Campaigns: {data['campaigns']}")
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
            queryset = ManualCallsRecording.objects.filter(
                start_epoch__range=(start_timestamp, end_timestamp),
                campaign_name__in=data['campaigns']
            ).annotate(
                formatted_dateTime=Cast(Func(F('start_epoch'),Value('%Y-%m-%d %H:%i:%s'),function='FROM_UNIXTIME'),output_field=CharField()),
                dateTime= F('start_epoch')  ,
                billSec=F('length_in_sec'),
                cliNum=F('extension'),
                campaignName=F('campaign_name'),
                sourceName=F('vendor'),
                dialStatus=F('dial_status'),
                agentExt=F('user'),
                disconnectedBy=F('disconnected_by'),
                totalPulses=ExpressionWrapper(
                    Ceil(F('length_in_sec') / 60.0),  # Using custom CEIL function
                    output_field=IntegerField()
                ),
                ringing_time= 
                    Case(
                        When(end_epoch__gt=0, then=(F('end_epoch') - F('start_epoch') - F('duration'))),
                        default=0,
                    ) 
            )
            
            # Conditional Dial Status Filtering
            if dial_status and dial_status.strip() not in ["Connected", "Not Connected"]:
                queryset = queryset.filter(dial_status=dial_status.strip())
            elif dial_status and dial_status.strip() == "Connected":
                queryset = queryset.filter(dial_status="Answer")
            elif dial_status and dial_status.strip() == "Not Connected":
                queryset = queryset.exclude(dial_status="Answer")

            paginator = Paginator(queryset, page_size)  # `page_size` is the number of items per page
            page_obj = paginator.get_page(page_number)  # `page_number` is the current page number
            # Results for the current page
            results = list(queryset.values(
                        'formatted_dateTime',
                        'dateTime',
                        'billSec',
                        'cliNum',
                        'campaignName',
                        'sourceName',
                        'dialStatus',
                        'agentExt',
                        'disconnectedBy',
                        'ringing_time',
                        'totalPulses',
                        'lead_id'
                    ))

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
                                "data": results,
                            }, status=200)
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
 
class RoundUp(Func):
    function = 'CEIL'

class Ceil(Func):
    function = 'CEIL'
class TimeDiff(Func):
    function = 'SEC_TO_TIME'
    arity = 1
    output_field = TimeField()