import os


ENVIRONMENT = os.environ.get("ENVIRONMENT", "prod")

ATHENA = {
    "db_name": "{}-datalake".format(ENVIRONMENT),
    "region": os.environ.get("AWS_DEFAULT_REGION", "eu-west-1"),
    "output_url": os.environ.get(
        "ATHENA_OUTPUT_URL", "s3://aws-glue-temporary-942231163599-eu-west-1/athena/"
    ),
    "save_results": False,
    "workgroup": "primary",
    "local_output_path": "local_output/stats/athena_query_stats.csv",
}

CONTEXT_MAPPING = {
            0:'mycampaign-main_page',
            1:'mycampaign-mediamix',
            2:'mycampaign-planning',
            3:'mycampaign-trafficking-adserver',
            4:'mycampaign-trafficking-analytics',
            5:'mycampaign-goals-and-progres ',
            6:'notifications-recommendations'
        }

ACTION_MAPPING = {
            0:'show',
            1:'interact'
        }


# Interaction actions list
interact_actions = {

    'create':[
        'implement','create','generate',
        'do','build','make','start',
        'initialize'
        ],
    'modify':[
         'add','expand','remove','copy',
         'cut','duplicate','allocate'
         ],
     'decision':[
          'export','accept',
          'reject','decline'
     ]}

# Showing Actions list
show_actions = [
    'display','exhibit','show',
     'expose','go','reveal',
     'unveil','what',"what's",
     'how',"how's",'see'
]

# Trigger actions list
trigger_actions = [
    'launch','trigger','run','suggest'
]

# Granularity Hierarchy
HIERARCHY = {
    'MEDIAPLAN':0,
    'CHANNEL':1,
    'PLATFORM':2,
    'MEDIAROW':3
}
