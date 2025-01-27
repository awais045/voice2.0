from rest_framework.response import Response
from .models import ccmCampaigns ,VirtualQueue ,CcmClients
from django.http import JsonResponse
from rest_framework.views import APIView
from collections import defaultdict

#http://127.0.0.1:8000/api/client_campaigns

class ClientCampaignView(APIView):
    def get(self, request):
         
        """
        Fetches all clients and their associated campaigns.

        Returns:
            dict: A dictionary where keys are client IDs and values 
                are lists of dictionaries containing campaign IDs and names.
        """
        clients = CcmClients.objects.all()
        client_campaigns = {}

        for client in clients:
            client_id = client.Id
            campaigns = ccmCampaigns.objects.filter(client_id=client_id)
            
            client_campaigns[client_id] = {
                "client_name": client.client_name,
                "client_id": client.Id,
                "campaigns": [
                    {"campaign_id": campaign.campaign_id, "campaign_name": campaign.name} 
                    for campaign in campaigns
                ]
            }

        response = {
            'message':"Filters Metadata ",
            'data': client_campaigns,
        }
        return JsonResponse(response)
        
