from rest_framework import generics, status ,viewsets
from rest_framework.response import Response
from .models import AgentLogins , VirtualQueue
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

# Create your views here. 
class RegisterAgentLoginsView(viewsets.ReadOnlyModelViewSet):
    queryset = AgentLogins.objects.all()
    serializer_class = AgentLoginsSerializer

class AgentLoginsView(APIView):
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
                    FROM agentLogins as logins
                    WHERE (endtime BETWEEN %s AND %s OR
                        (starttime < %s AND endtime > %s) OR
                        (starttime BETWEEN %s AND %s AND endtime > %s))
                """, [
                    start_timestamp, end_timestamp,  # For the first condition
                    start_timestamp, end_timestamp,  # For the second condition
                    start_timestamp, end_timestamp,  # For the third condition
                    end_timestamp                    # For the third condition's endtime
                ])
                total_records = cursor.fetchone()[0]
                # Calculate total pages and the current offset
                total_pages = math.ceil(total_records / page_size)
                offset = (page_number - 1) * page_size
                
                cursor.execute("""
                        SELECT logins.*,
                            FROM_UNIXTIME(logins.starttime) as starttime,
                            FROM_UNIXTIME(logins.endtime) as endtime,
                            date_format(from_unixtime(starttime), "%%Y-%%m-%%d %%H:%%i:%%s") as formatted_starttime,
                            date_format(from_unixtime(endtime), "%%Y-%%m-%%d %%H:%%i:%%s") as formatted_endtime,
                            if(starttime < %s, %s, starttime) as calc_starttime,
                            if(endtime > %s, %s, endtime) as calc_endtime,
                            (logins.endtime - logins.starttime) as duration
                        FROM agentLogins as logins 
                        WHERE (endtime BETWEEN %s AND %s OR
                        (starttime < %s AND endtime > %s) OR
                        (starttime BETWEEN %s and %s and endtime > %s))
                        GROUP BY logins.id, logins.time_id, logins.extension
                        ORDER BY logins.extension, logins.startTime
                        LIMIT %s OFFSET %s
                    """, [start_timestamp, start_timestamp, end_timestamp, end_timestamp,
                        start_timestamp, end_timestamp, start_timestamp, end_timestamp,
                        start_timestamp, end_timestamp, end_timestamp ,
                        page_size, offset])
                rows = cursor.fetchall()

                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]

                # Close the connection
                cursor.close()
                connection.close()
                serializer = AgentLoginsSerializer(data, many=True)
                return Response({
                                    "message":"Listing for Agent Logins.",
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
        