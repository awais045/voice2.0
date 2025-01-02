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

class VirtualQueue(models.Model):
    id = models.AutoField(primary_key=True)
    client = models.CharField(max_length=50, null=True, blank=True)
    queue = models.CharField(max_length=50, null=True, blank=True)
    virtual_queue = models.CharField(max_length=50, null=True, blank=True)
    active = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')], null=True, blank=True)
    short_name = models.CharField(max_length=20, null=True, blank=True)
    client_id = models.IntegerField(null=True, blank=True)
    client_campaign_id = models.IntegerField(null=True, blank=True)
    ccm_campaign_id = models.IntegerField(null=True, blank=True)
    virtual_queue_type = models.CharField(
        max_length=8,
        choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')],
        null=True,
        blank=True
    )

    class Meta:
            db_table = 'virtual_queues'
            managed = False



class VDN(models.Model):
    dnis = models.CharField(max_length=255, null=True, blank=True)
    ext = models.CharField(max_length=100, default='s')
    context = models.CharField(max_length=200, default='main1')
    context_priority = models.CharField(max_length=100, default='1')
    active = models.CharField(max_length=15, choices=[('N', 'No'), ('Y', 'Yes')], default='Y')  
    client_campaign_id = models.IntegerField(null=True, blank=True)
    full_did = models.CharField(max_length=128, null=True, blank=True)
    vendor_id = models.IntegerField(null=True, blank=True)
    tfn = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    pri = models.CharField(max_length=255, null=True, blank=True)
    did = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'vdn'

class ccmCampaigns(models.Model):
    campaign_id = models.AutoField(primary_key=True)
    client = models.CharField(max_length=50, null=True, blank=True)
    campaign = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    crm_table = models.CharField(max_length=50, null=True, blank=True)
    virtual_queue = models.CharField(max_length=50, null=True, blank=True)
    virtual_queue_name = models.CharField(max_length=50, null=True, blank=True)
    active = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')], null=True, blank=True)
    type = models.CharField(max_length=20, choices=[('inbound','Inbound') ,('Manual' ,'Manual')], null=True, blank=True)
    short_name = models.CharField(max_length=20, null=True, blank=True)
    client_id = models.IntegerField(null=True, blank=True)
    client_campaign_id = models.IntegerField(null=True, blank=True)

     # Define the relationship
    # vdn = models.ForeignKey(
    #     VDN, on_delete=models.CASCADE, related_name='campaigns'
    # )
    class Meta:
            db_table = 'ccm_campaigns'
            managed = False
