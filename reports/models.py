from django.db import models

app_name = ''
# Create your models here.
class AgentLogins(models.Model):
    extension = models.IntegerField()
    fullName = models.CharField(max_length=100)
    queue = models.CharField(max_length=50)    
    startTime = models.IntegerField()
    endTime = models.IntegerField()
    server_ip = models.CharField(max_length=20)    
    time_id = models.IntegerField()
    agent_ip = models.CharField(max_length=100)

    class Meta:
            db_table = 'agentlogins'
            managed = False

class QueueLog(models.Model):
    rowcount = models.IntegerField()
    time_id = models.IntegerField()
    call_id = models.CharField(max_length=100)
    queue = models.CharField(max_length=50)    
    agent = models.CharField(max_length=50)    
    event = models.CharField(max_length=50)    
    arg1 = models.CharField(max_length=200)    
    arg2 = models.CharField(max_length=200)    
    arg3 = models.CharField(max_length=200)    
    arg4 = models.CharField(max_length=200)    
    arg5 = models.CharField(max_length=200)    
    last_row = models.IntegerField()
    server_ip = models.CharField(max_length=20)    
    time_id = models.IntegerField()
    agi_server = models.CharField(max_length=100)

    class Meta:
            db_table = 'queue_log'
            managed = False