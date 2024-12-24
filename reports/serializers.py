from rest_framework import serializers
from .models import AgentLogins,QueueLog

class AgentLoginsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AgentLogins
        fields = ['id', 'extension', 'fullName', 'queue', 'startTime', 'endTime', 'server_ip', 'time_id', 'agent_ip' , 'calc_starttime', 'calc_endtime','duration']

    id = serializers.IntegerField()
    calc_starttime = serializers.SerializerMethodField()
    calc_endtime = serializers.SerializerMethodField()
    duration = serializers.IntegerField()

    def get_calc_starttime(self, obj):
        return obj['calc_starttime']

    def get_calc_endtime(self, obj):
        return obj['calc_endtime']
    

class QueueLogSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = QueueLog
        fields = ['rowcount', 'time_id', 'call_id', 'queue', 'agent', 'event', 'arg1','arg2', 'arg3' , 'arg4', 'arg5','last_row','server_ip','agi_server']
