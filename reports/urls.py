from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterAgentLoginsView , AgentLoginsView 
from .ivr_drop import RegisterIVRDropView
from .unanswered_calls_report import UnAnsweredCallsView ,UnAnsweredCallsGraphView 
from .manual_calls_report import ManualCallsReportView
from .lead_report import LeadsReportView
from .call_recording_report import CallsRecordingsView
from .call_recording_evaluation import CallsRecordingsEvaluationView

router = DefaultRouter()
router.register(r'agent_login', RegisterAgentLoginsView, basename='agent_login')

urlpatterns = [
    # path('', include(router.urls)),
    path('agent_logins/', AgentLoginsView.as_view(), name='agent_logins'),
    path('agent_login_logout/', AgentLoginsView.as_view(), name='agent_logins'),
    path('ivrdrop_report/', RegisterIVRDropView.as_view(), name='ivrdrop_report'),
    path('unanswered_calls_report/', UnAnsweredCallsView.as_view(), name='unanswered_calls_report'),
    path('unanswered_calls_report/graph/', UnAnsweredCallsGraphView.as_view(), name='unanswered_calls_report_graph'), 
    path('manual_calls_report/', ManualCallsReportView.as_view(), name='manual_calls_report'), 
    path('leads_report/', LeadsReportView.as_view(), name='leads_report'), 
    path('callcenter_recordings/', CallsRecordingsView.as_view(), name='callcenter_recordings'), 
    path('callcenter_recordings_evaluation/', CallsRecordingsView.as_view(), name='callcenter_recordings_evaluation'), 
    path('callcenterRecordingsEvaluationSave/', CallsRecordingsEvaluationView.as_view(), name='callcenterRecordingsEvaluationSave'),
]