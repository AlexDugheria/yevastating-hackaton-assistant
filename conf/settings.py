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
