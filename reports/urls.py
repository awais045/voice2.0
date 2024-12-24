from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterAgentLoginsView , AgentLoginsView ,RegisterIVRDropView

router = DefaultRouter()
router.register(r'agent_login', RegisterAgentLoginsView, basename='agent_login')

urlpatterns = [
    # path('', include(router.urls)),
    path('agent_logins/', AgentLoginsView.as_view(), name='agent_logins'),
    path('agent_login_logout/', AgentLoginsView.as_view(), name='agent_logins'),
    path('ivrdrop_report/', RegisterIVRDropView.as_view(), name='ivrdrop_report'),
]