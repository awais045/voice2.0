from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterAgentLoginsView , AgentLoginsView 
from .ivr_drop import RegisterIVRDropView ,IVRDropCallsGraphView
from .unanswered_calls_report import UnAnsweredCallsView ,UnAnsweredCallsGraphView 
from .manual_calls_report import ManualCallsReportView
from .lead_report import LeadsReportView
from .call_recording_report import CallsRecordingsView
from .call_recording_evaluation import CallsRecordingsEvaluationView
from .manual_campaign_report import ManualCampaignReportView
from .campaign_summary_report import CampaignSummaryReportView
from .client_campaigns import ClientCampaignView
from .lead_fetch_report import FetchLeadsReportView

router = DefaultRouter()
router.register(r'agent_login', RegisterAgentLoginsView, basename='agent_login')

urlpatterns = [
    # path('', include(router.urls)),
    path('agent_logins/', AgentLoginsView.as_view(), name='agent_logins'),
    path('agent_login_logout/', AgentLoginsView.as_view(), name='agent_logins'),
    path('ivrdrop_report/', RegisterIVRDropView.as_view(), name='ivrdrop_report'),
    path('ivrdrop_report/graph/', IVRDropCallsGraphView.as_view(), name='ivrdrop_report_graph'),
    path('unanswered_calls_report/', UnAnsweredCallsView.as_view(), name='unanswered_calls_report'),
    path('unanswered_calls_report/graph/', UnAnsweredCallsGraphView.as_view(), name='unanswered_calls_report_graph'), 
    path('manual_calls_report/', ManualCallsReportView.as_view(), name='manual_calls_report'), 
    path('leads_report/', LeadsReportView.as_view(), name='leads_report'), 
    path('callcenter_recordings/', CallsRecordingsView.as_view(), name='callcenter_recordings'), 
    path('callcenter_recordings_evaluation/', CallsRecordingsView.as_view(), name='callcenter_recordings_evaluation'), 
    path('callcenterRecordingsEvaluationSave/', CallsRecordingsEvaluationView.as_view(), name='callcenterRecordingsEvaluationSave'),
    path('manual_campaign_report/', ManualCampaignReportView.as_view(), name='manual_campaign_report'),
    path('campaign_summary_report/', CampaignSummaryReportView.as_view(), name='campaign_summary_report'),
    path('client_campaigns/', ClientCampaignView.as_view(), name='client_campaigns'),
    path('lead_fetch_report/', FetchLeadsReportView.as_view(), name='lead_fetch_report'),
]