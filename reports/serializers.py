from rest_framework import serializers
from .models import AgentLogins,QueueLog , ManualCallsRecording ,AgentCallLog

from django.db.models import F, Func, IntegerField, ExpressionWrapper, Q
from django.db.models import TimeField
import datetime
import math

class AgentLoginsSerializer(serializers.ModelSerializer):
    formatted_starttime = serializers.CharField(read_only=True)
    formatted_endtime = serializers.CharField(read_only=True)

    class Meta:
        model = AgentLogins
        fields = ['id', 'extension', 'fullName', 'queue', 'startTime', 'endTime','formatted_starttime','formatted_endtime', 'server_ip', 'time_id', 'agent_ip' , 'calc_starttime', 'calc_endtime','duration']

    id = serializers.IntegerField()
    calc_starttime = serializers.SerializerMethodField()
    calc_endtime = serializers.SerializerMethodField()
    duration = serializers.IntegerField()

    def get_calc_starttime(self, obj):
        return obj['calc_starttime']

    def get_calc_endtime(self, obj):
        return obj['calc_endtime']
    

class QueueLogSerializer(serializers.ModelSerializer):
    formatted_time_id = serializers.CharField(read_only=True)

    class Meta:
        model = QueueLog
        fields = ['rowcount', 'time_id', 'formatted_time_id','call_id', 'queue', 'agent', 'event', 'arg1','arg2', 'arg3' , 'arg4', 'arg5','last_row','server_ip','agi_server']

class ManualRecordingLogSerializer(serializers.ModelSerializer):
    formatted_start_epoch = serializers.CharField(read_only=True)
    formatted_end_epoch = serializers.CharField(read_only=True)
    class Meta:
        model = ManualCallsRecording
        fields = [
                    'recording_id', 'channel', 'server_ip', 'extension', 'start_time',
                    'formatted_start_epoch','formatted_end_epoch' ,'start_epoch', 'end_time', 
                    'end_epoch', 'length_in_sec', 'duration',
                    'length_in_min', 'filename', 'location', 'lead_id', 'manual_id',
                    'user', 'hangup_cause', 'dial_status', 'campaign_name', 'unique_id',
                    'vendor', 'disconnected_by', 'enable_for_client', 'rating',
                    'evaluation_id', 'evaluated_by', 'evaluation_time', 'is_evaluated',
                    'comments', 'transcript', 'transcript_api'
                ]
        #'dateTime',  'ringing_time', 'totalPulses','agentExt'
        
class AgentCallLogSerializer(serializers.ModelSerializer):
    formatted_time_id = serializers.CharField(read_only=True)
    formatted_modify_time = serializers.CharField(read_only=True)
    formatted_wrapup_time = serializers.CharField(read_only=True)
    formatted_disconnected_at = serializers.CharField(read_only=True)
    class Meta:
        model = AgentCallLog
        fields = '__all__'  # Or specify fields explicitly for better control