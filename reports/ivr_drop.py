from rest_framework import generics, status ,viewsets
from rest_framework.response import Response
from .models import AgentLogins , VirtualQueue , ccmCampaigns , VDN
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
from django.db.models import F
import json

class RegisterIVRDropView(APIView):
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
        ## end get VQ 
        if not data['client_id'] or data['dnis'] is None: # Corrected condition
            return JsonResponse({'message': 'No records found'}, status=404) # Return error response with 404

        # Ensure the range is within 200 days
        if (end_date - start_date).days > 200:
            return JsonResponse({"error": "The date range cannot exceed 200 days."}, status=400)

        if start_date and end_date:
            start_timestamp = int(datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').timestamp())
            with connection.cursor() as cursor:

                # Fetch the total count
                cursor.execute("""
                    SELECT COUNT(*) as total_count
                    FROM queue_log 
                    WHERE time_id BETWEEN %s and %s
                        AND event = 'IVRDROP' AND arg2 IN(%s) AND arg3 IN %s
                """, [
                    start_timestamp, end_timestamp  ,data['client_id'], data['dnis']
                ])
                total_records = cursor.fetchone()[0]
                # Calculate total pages and the current offset
                total_pages = math.ceil(total_records / page_size)
                offset = (page_number - 1) * page_size
                ## end count

                ## get all counts 
                cursor.execute("""
                        SELECT queue_log.* ,date_format(from_unixtime(time_id), "%%Y-%%m-%%d %%H:%%i:%%s") as formatted_time_id
                        FROM queue_log WHERE  
                        time_id BETWEEN %s and %s  
                        AND event = 'IVRDROP' AND arg2 IN(%s) AND arg3 IN %s
                        LIMIT %s OFFSET %s
                    """, [start_timestamp, end_timestamp , data['client_id'], data['dnis'],
                            page_size, offset])
                rows = cursor.fetchall()
    
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
                # Close the connection
                cursor.close()
                connection.close()
                serializer = QueueLogSerializer(data, many=True)
                return Response({
                                    "message":"Listing for IVR DROP.",
                                    "pagination": {
                                        "current_page": page_number,
                                        "page_size": page_size,
                                        "total_pages": total_pages,
                                        "total_records": total_records,
                                        "has_next": page_number < total_pages,
                                        "has_previous": page_number > 1
                                    },
                                    "data":serializer.data,
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