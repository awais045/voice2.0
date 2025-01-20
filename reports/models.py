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
    form_name = models.CharField(max_length=50, null=True, blank=True)
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

class ManualCallsRecording(models.Model):
    
    recording_id = models.AutoField(primary_key=True)
    channel = models.CharField(max_length=100, null=True, blank=True)
    server_ip = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    extension = models.CharField(max_length=100, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    start_epoch = models.IntegerField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    end_epoch = models.IntegerField(null=True, blank=True)
    length_in_sec = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    length_in_min = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    filename = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    lead_id = models.PositiveIntegerField(null=True, blank=True)
    manual_id = models.CharField(max_length=200, null=True, blank=True)
    user = models.CharField(max_length=20, null=True, blank=True)
    hangup_cause = models.CharField(max_length=100, null=True, blank=True)
    dial_status = models.CharField(max_length=20, null=True, blank=True)
    campaign_name = models.CharField(max_length=255, null=True, blank=True)
    unique_id = models.CharField(max_length=255, null=True, blank=True)
    vendor = models.CharField(max_length=30, null=True, blank=True)
    disconnected_by = models.CharField(
        max_length=10,
        choices=[
            ('Callee', 'Callee'),
            ('Unknown', 'Unknown'),
            ('Caller', 'Caller'),
            ('Agent', 'Agent'),
        ],
        default='Unknown',
    )
    enable_for_client = models.BooleanField(default=False)
    rating = models.IntegerField(null=True, blank=True)
    evaluation_id = models.IntegerField(null=True, blank=True)
    evaluated_by = models.IntegerField(null=True, blank=True)
    evaluation_time = models.IntegerField(null=True, blank=True)
    is_evaluated = models.BooleanField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    transcript = models.TextField(null=True, blank=True)
    transcript_api = models.CharField(
        max_length=10,
        choices=[
            ('deepgram', 'Deepgram'),
            ('assembly', 'Assembly'),
        ],
        default='deepgram',
    )

    class Meta:
        db_table = 'manual_recording_log'


class LeadIn(models.Model):
    
    lead_id = models.AutoField(primary_key=True)
    entry_date = models.IntegerField(null=True, blank=True)
    time_id = models.IntegerField()
    modify_date = models.IntegerField(null=True, blank=True)
    modify_time = models.IntegerField(null=True, blank=True)
    acd_status = models.CharField(max_length=64, null=True, blank=True)
    callback_no = models.CharField(max_length=128, null=True, blank=True)
    agent = models.CharField(max_length=100, null=True, blank=True)
    extension = models.CharField(max_length=10, null=True, blank=True)
    disposition = models.CharField(max_length=100, null=True, blank=True)
    sub_disposition = models.CharField(max_length=100, null=True, blank=True)
    campaign = models.CharField(max_length=50, null=True, blank=True)
    queue = models.CharField(max_length=50, null=True, blank=True)
    disconnection_cause = models.CharField(max_length=50, null=True, blank=True)
    call_id = models.CharField(max_length=100, null=True, blank=True)
    cli = models.CharField(max_length=20, null=True, blank=True)
    call_type = models.CharField(max_length=10, default='Inbound')
    duration = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    dial_attempts = models.IntegerField(default=0)
    call_category = models.CharField(max_length=255, null=True, blank=True)
    priority = models.BooleanField(null=True, blank=True)  # tinyint(1) becomes BooleanField
    cse_comments = models.TextField(null=True, blank=True)
    cro_comments = models.TextField(null=True, blank=True)
    other_details = models.TextField(null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=30, null=True, blank=True)
    lead_type = models.CharField(max_length=250, null=True, blank=True)
    full_name = models.CharField(max_length=250, null=True, blank=True)
    field1 = models.CharField(max_length=250, null=True, blank=True)
    field2 = models.CharField(max_length=250, null=True, blank=True)
    field3 = models.CharField(max_length=250, null=True, blank=True)
    field4 = models.CharField(max_length=250, null=True, blank=True)
    field5 = models.CharField(max_length=250, null=True, blank=True)
    field6 = models.CharField(max_length=250, null=True, blank=True)
    field7 = models.CharField(max_length=250, null=True, blank=True)
    field8 = models.CharField(max_length=250, null=True, blank=True)
    field9 = models.CharField(max_length=250, null=True, blank=True)
    field10 = models.CharField(max_length=250, null=True, blank=True)
    field11 = models.CharField(max_length=250, null=True, blank=True)
    field12 = models.CharField(max_length=250, null=True, blank=True)
    field13 = models.CharField(max_length=250, null=True, blank=True)
    field14 = models.CharField(max_length=250, null=True, blank=True)
    field15 = models.CharField(max_length=250, null=True, blank=True)
    field16 = models.CharField(max_length=250, null=True, blank=True)
    field17 = models.CharField(max_length=250, null=True, blank=True)
    field18 = models.CharField(max_length=250, null=True, blank=True)
    field19 = models.CharField(max_length=250, null=True, blank=True)
    field20 = models.CharField(max_length=250, null=True, blank=True)
    field21 = models.CharField(max_length=250, null=True, blank=True)
    field22 = models.CharField(max_length=250, null=True, blank=True)
    field23 = models.CharField(max_length=250, null=True, blank=True)
    field24 = models.CharField(max_length=250, null=True, blank=True)
    field25 = models.CharField(max_length=250, null=True, blank=True)
    field26 = models.CharField(max_length=250, null=True, blank=True)
    field27 = models.CharField(max_length=250, null=True, blank=True)
    field28 = models.CharField(max_length=250, null=True, blank=True)
    field29 = models.CharField(max_length=250, null=True, blank=True)
    field30 = models.CharField(max_length=250, null=True, blank=True)
    field31 = models.CharField(max_length=250, null=True, blank=True)
    field32 = models.CharField(max_length=250, null=True, blank=True)
    field33 = models.CharField(max_length=250, null=True, blank=True)
    field34 = models.CharField(max_length=250, null=True, blank=True)
    field35 = models.CharField(max_length=250, null=True, blank=True)
    field36 = models.CharField(max_length=250, null=True, blank=True)
    field37 = models.CharField(max_length=250, null=True, blank=True)
    field38 = models.CharField(max_length=250, null=True, blank=True)
    field39 = models.CharField(max_length=250, null=True, blank=True)
    field40 = models.CharField(max_length=250, null=True, blank=True)
    field41 = models.CharField(max_length=250, null=True, blank=True)
    field42 = models.CharField(max_length=250, null=True, blank=True)
    field43 = models.CharField(max_length=250, null=True, blank=True)
    field44 = models.CharField(max_length=250, null=True, blank=True)
    field45 = models.CharField(max_length=250, null=True, blank=True)
    field46 = models.TextField(null=True, blank=True)
    old_package = models.CharField(max_length=150, null=True, blank=True)
    new_package = models.CharField(max_length=150, null=True, blank=True)
    selected_plan = models.CharField(max_length=150, null=True, blank=True)
    credit_limit_required = models.IntegerField(default=0)
    credit_limit_current = models.IntegerField(default=0)
    conversation_date = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    deposit_amount = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    poc_name = models.CharField(max_length=255, null=True, blank=True)
    requested_created_at = models.CharField(max_length=50, null=True, blank=True)
    call_status = models.CharField(max_length=100, null=True, blank=True)
    agent_name = models.CharField(max_length=100, null=True, blank=True)
    caller_id = models.CharField(max_length=100, null=True, blank=True)
    flag_call = models.CharField(max_length=50, default='Inquiry')
    lead_status = models.CharField(max_length=30, null=True, blank=True)
    dnis = models.CharField(max_length=20, null=True, blank=True)
    ivr_callback = models.CharField(max_length=255, null=True, blank=True)
    ivr_callback_time = models.CharField(max_length=255, null=True, blank=True)
    ivr_callback_number = models.CharField(max_length=50, null=True, blank=True)
    off_callback = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')], default='N') #enum to CharField with choices
    inserted_by = models.CharField(max_length=100, null=True, blank=True)
    call_duration = models.IntegerField(null=True, blank=True)
    fwd_callid = models.CharField(max_length=50, null=True, blank=True)
    wrapup_time = models.IntegerField(null=True, blank=True)
    vm_path = models.TextField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    callback_time = models.IntegerField(null=True, blank=True)
    callback_comments = models.CharField(max_length=250, null=True, blank=True)
    uploaded_by = models.IntegerField(null=True, blank=True)
    batch = models.CharField(max_length=30, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    form_data = models.TextField(null=True, blank=True)
    priority_status = models.CharField(max_length=20, null=True, blank=True)
    ccm_sms_logs = models.TextField(null=True, blank=True)
    ccm_sms_mask = models.CharField(max_length=30, null=True, blank=True)
    ccm_sms_prefix = models.CharField(max_length=20, null=True, blank=True)
    ccm_sms_read = models.BooleanField(null=True, blank=True)
    ccm_sms_reply_count = models.IntegerField(null=True, blank=True)
    dialed_by = models.CharField(max_length=50, null=True, blank=True)
    batch_no = models.CharField(max_length=50, null=True, blank=True)
    broadcast_id = models.IntegerField(null=True, blank=True)
    broadcast_campaign = models.CharField(max_length=50, null=True, blank=True)
    is_auto_dialer = models.BooleanField(default=False)
    parent_lead_id = models.IntegerField(null=True, blank=True)
    avaya_call_id = models.CharField(max_length=45, null=True, blank=True)
    manual_call_duration = models.PositiveIntegerField(default=0) #unsigned int
    manual_call_connected = models.PositiveIntegerField(default=0) #unsigned int
    manual_being_dialed = models.CharField(
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='N'
    )
    table_show = models.CharField(max_length=30, null=True, blank=True)
    selected_option = models.CharField(max_length=155, null=True, blank=True)
    selected_fields = models.CharField(max_length=155, null=True, blank=True)
    agent_comments = models.TextField(null=True, blank=True)    
    class Meta:
        db_table = 'leads_in'


class CampaignField(models.Model):
    TYPE_CHOICES = [
        ('text', 'text'),
        ('checkbox', 'checkbox'),
        ('radio', 'radio'),
        ('select-one', 'select-one'),
        ('textarea', 'textarea'),
        ('label', 'label'),
        ('button', 'button'),
        ('date', 'date'),
        ('readonly', 'readonly'),
        ('url', 'url'),
        ('datetime', 'datetime'),
        ('report-only', 'report-only'),
    ]

    YN_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
    ]

    COLUMN_SIZE_CHOICES = [
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
        ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
    ]

    CAMPAIGN_REPORT_CHOICES = [
        ('complaint', 'complaint'), ('efax', 'efax'), ('inquiry', 'inquiry'),
        ('donor', 'donor'), ('general', 'general'), ('partner', 'partner'), ('volunteer', 'volunteer'),
    ]

    OTHER_FIELD_CHOICES = [
        ('radio', 'radio'), ('text', 'text'), ('select-one', 'select-one'), ('checkbox', 'checkbox'),
    ]
    FILTER_TYPE_CHOICES = [
        ('equal', 'equal'),
        ('contains', 'contains'),
        ('beginwith', 'beginwith'),
        ('endwith', 'endwith'),
        ('', ''),
    ]
    IS_JSON_CHOICES = [
        ('N', 'No'),
        ('Y', 'Yes'),
    ]

    CRM_FILTER_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
        ('', ''),  # For the empty string option
    ]
    FILTER_TYPE_CHOICES = [
        ('equal', 'equal'),
        ('contains', 'contains'),
        ('beginwith', 'beginwith'),
        ('endwith', 'endwith'),
        ('', ''),
    ]
    id = models.AutoField(primary_key=True)
    campaign_id = models.CharField(max_length=50, null=True, blank=True)
    q_id = models.IntegerField(null=True, blank=True)
    q_field = models.CharField(max_length=100, null=True, blank=True)
    question = models.TextField(null=True, blank=True)
    question_eng = models.CharField(max_length=255, null=True, blank=True)
    question_legend = models.CharField(max_length=255, null=True, blank=True)
    question_bribery = models.SmallIntegerField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    priority = models.FloatField(null=True, blank=True)
    options = models.TextField(null=True, blank=True)
    q_other = models.CharField(max_length=1, choices=YN_CHOICES, default='N')
    q_other_field = models.CharField(max_length=100, null=True, blank=True)
    default_value = models.CharField(max_length=100, null=True, blank=True)
    active = models.CharField(max_length=1, choices=YN_CHOICES, default='Y')
    upload_field = models.CharField(max_length=50, null=True, blank=True)
    revenue = models.CharField(max_length=1, choices=YN_CHOICES, default='N')
    revenue_value = models.TextField(null=True, blank=True)
    ret_database = models.CharField(max_length=1, choices=YN_CHOICES, null=True, blank=True)
    sql_query = models.TextField(null=True, blank=True)
    show_div = models.CharField(max_length=255, null=True, blank=True)
    event = models.CharField(max_length=255, null=True, blank=True)
    event_function = models.CharField(max_length=255, null=True, blank=True)
    show_column = models.IntegerField(null=True, blank=True)
    show_column_value = models.IntegerField(null=True, blank=True)
    column_size = models.CharField(max_length=2, choices=COLUMN_SIZE_CHOICES, default='6')
    label_column = models.IntegerField(null=True, blank=True)
    validation = models.CharField(max_length=1, choices=YN_CHOICES, null=True, blank=True)
    button_value = models.CharField(max_length=255, null=True, blank=True)
    button_click = models.CharField(max_length=255, null=True, blank=True)
    campaign_report = models.CharField(max_length=20, choices=CAMPAIGN_REPORT_CHOICES, null=True, blank=True)
    readonly_value = models.CharField(max_length=255, null=True, blank=True)
    is_other = models.CharField(max_length=1, choices=YN_CHOICES, null=True, blank=True)
    other_name = models.CharField(max_length=255, null=True, blank=True)
    other_field = models.CharField(max_length=20, choices=OTHER_FIELD_CHOICES, null=True, blank=True)
    other_value = models.CharField(max_length=255, null=True, blank=True)
    ret_field_db = models.CharField(max_length=255, null=True, blank=True)
    ret_field_value = models.CharField(max_length=255, null=True, blank=True)
    field_report = models.CharField(max_length=255, null=True, blank=True)
    show_fields = models.CharField(max_length=255, null=True, blank=True)
    max_length = models.CharField(max_length=255, null=True, blank=True)
    disabled = models.CharField(max_length=1, choices=YN_CHOICES, null=True, blank=True)
    add_in_report = models.CharField(max_length=1, choices=YN_CHOICES, default='Y')
    fc_survey = models.IntegerField(null=True, blank=True)
    type_fields_survey = models.CharField(max_length=20, null=True, blank=True)
    type_question_survey = models.CharField(max_length=20, null=True, blank=True)
    question_name = models.CharField(max_length=255, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    ques_replace_fields = models.CharField(max_length=255, null=True, blank=True)
    ques_replace_field1 = models.CharField(max_length=255, null=True, blank=True)
    ques_replace_field2 = models.CharField(max_length=255, null=True, blank=True)
    showPrevNext = models.CharField(max_length=255, null=True, blank=True)
    inc_fields = models.CharField(max_length=1, choices=YN_CHOICES, null=True, blank=True)
    ques_type = models.CharField(max_length=50, null=True, blank=True)
    accordion_name = models.CharField(max_length=255, null=True, blank=True)
    accordion_priority = models.IntegerField(null=True, blank=True)
    validations = models.TextField(null=True, blank=True)
    validation_key = models.CharField(max_length=100, null=True, blank=True)
    complaint_fields = models.CharField(max_length=1, choices=YN_CHOICES, null=True, blank=True)
    complaint_priority = models.IntegerField(null=True, blank=True)
    customize_field = models.CharField(max_length=255, null=True, blank=True)
    field_report_priority = models.CharField(max_length=255, null=True, blank=True)
    size_column = models.CharField(max_length=20, null=True, blank=True)
    question_no = models.CharField(max_length=255, null=True, blank=True)
    is_json = models.CharField(max_length=1, choices=IS_JSON_CHOICES, default='N')
    show_on_history = models.BooleanField(null=True, blank=True)  # Use BooleanField for tinyint(1)
    history_report_order = models.IntegerField(null=True, blank=True)
    crm_filter = models.CharField(max_length=1, choices=CRM_FILTER_CHOICES, default='N')
    filter_field_name = models.CharField(max_length=255, default='')
    filter_field_label = models.CharField(max_length=255, default='')
    show_in_form = models.CharField(max_length=1, choices=YN_CHOICES, default='Y')
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPE_CHOICES, default='equal')

    class Meta:
        db_table = 'campaign_fields'

class AgentCallLog(models.Model):
    id = models.AutoField(primary_key=True)  # AutoField is more idiomatic in Django
    lead_id = models.IntegerField(null=True, blank=True)
    time_id = models.IntegerField()
    modify_time = models.IntegerField(null=True, blank=True)
    agent = models.CharField(max_length=15, null=True, blank=True)
    call_id = models.CharField(max_length=30, null=True, blank=True)
    cli = models.CharField(max_length=50, null=True, blank=True)
    duration = models.IntegerField(default=0)
    wrapup_sec = models.IntegerField(default=0)
    wrapup_time = models.IntegerField(null=True, blank=True)
    wait_sec = models.IntegerField(default=0)
    hold_sec = models.IntegerField(default=0)
    disconnection_cause = models.CharField(
        max_length=15,  # Adjust length as needed
        choices=[
            ('COMPLETECALLER', 'COMPLETECALLER'),
            ('DROP', 'DROP'),
            ('TRANSFER', 'TRANSFER'),
            ('COMPLETEAGENT', 'COMPLETEAGENT'),
        ],
        null=True, blank=True
    )
    disconnected_by = models.CharField(
        max_length=6, # Adjust length as needed
        choices=[
            ('Agent', 'Agent'),
            ('Caller', 'Caller'),
        ],
        default='Caller'
    )
    queue = models.CharField(max_length=50, null=True, blank=True)
    selected_option = models.CharField(max_length=100, null=True, blank=True)
    disposition = models.CharField(max_length=100, null=True, blank=True)
    sub_dispositoin = models.CharField(max_length=100, null=True, blank=True)
    cat1 = models.CharField(max_length=100, null=True, blank=True)
    sub_cat1 = models.CharField(max_length=100, null=True, blank=True)
    cat2 = models.CharField(max_length=100, null=True, blank=True)
    sub_cat2 = models.CharField(max_length=100, null=True, blank=True)
    cro_comments = models.TextField(null=True, blank=True)
    rec_file_name = models.CharField(max_length=200, null=True, blank=True)
    rec_file_path = models.CharField(max_length=200, null=True, blank=True)
    call_type = models.CharField(
        max_length=10, # Adjust length as needed
        choices=[
            ('INBOUND', 'INBOUND'),
            ('MANUAL', 'MANUAL'),
            ('AUTODIALER', 'AUTODIALER'),
        ],
        default='INBOUND'
    )
    manual_id = models.CharField(max_length=30, null=True, blank=True)
    dial_status = models.CharField(max_length=40, null=True, blank=True)
    server_ip = models.CharField(max_length=20, null=True, blank=True)
    dnis = models.CharField(max_length=30, null=True, blank=True)
    audio_file_path = models.CharField(max_length=255, null=True, blank=True)
    video_file_path = models.CharField(max_length=255, null=True, blank=True)
    enable_for_client = models.BooleanField(default=False) # Use BooleanField
    transfer_count = models.SmallIntegerField(null=True, blank=True)
    answer_time = models.IntegerField(null=True, blank=True)
    ivr_at = models.IntegerField(default=0)
    disconnected_at = models.IntegerField(default=0)
    rating = models.IntegerField(null=True, blank=True)
    evaluation_id = models.IntegerField(null=True, blank=True)
    evaluated_by = models.IntegerField(null=True, blank=True)
    evaluation_time = models.PositiveIntegerField(null=True, blank=True) # Use PositiveIntegerField
    is_evaluated = models.BooleanField(default=False) # Use BooleanField
    comments = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'agent_call_log'  

class LeadEvaluation(models.Model):
    id = models.AutoField(primary_key=True)   
    channel = models.CharField(max_length=20, null=True)
    lead_id = models.IntegerField(null=True)
    reference_id = models.IntegerField(null=True)
    direction = models.CharField(max_length=20, null=True)
    contact = models.CharField(max_length=50, null=True)
    client_id = models.IntegerField(null=True)
    queue = models.CharField(max_length=50, null=True)
    agent = models.CharField(max_length=15, null=True)
    interaction_time = models.IntegerField(null=True)
    duration = models.IntegerField(null=True)
    rating = models.IntegerField(null=True)
    comments = models.TextField(null=True)
    evaluated_by = models.IntegerField(null=True)
    evaluation_time = models.IntegerField(null=True)

    class Meta:
        db_table = 'lead_evaluations'

class AgentLogOutbound(models.Model):
    time_id = models.IntegerField()
    lead_id = models.IntegerField(null=True)
    user = models.CharField(max_length=30, null=True)
    status = models.CharField(max_length=100, null=True)
    sub_disposition = models.CharField(max_length=100, null=True)
    comments = models.TextField(null=True)
    manual_id = models.CharField(max_length=25, null=True)
    campaign = models.CharField(max_length=50, null=True)
    time_spent = models.IntegerField(default=0)
    id = models.AutoField(primary_key=True) 

    class Meta:
        db_table = 'agent_log_outbound'

class AgentBreak(models.Model):
    id = models.AutoField(primary_key=True)
    extension = models.IntegerField(blank=True, null=True)
    fullName = models.CharField(max_length=100, blank=True, null=True)
    queue = models.CharField(max_length=50, blank=True, null=True)
    startTime = models.IntegerField(blank=True, null=True)
    endTime = models.IntegerField(blank=True, null=True)
    breakCode = models.CharField(max_length=30, blank=True, null=True)
    server_ip = models.CharField(max_length=20, blank=True, null=True)
    time_id = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'agentbreaks'