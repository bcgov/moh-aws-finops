import json
import boto3
import uuid
from datetime import datetime, timedelta

# Initialize AWS clients
ce_client = boto3.client('ce')  # Cost Explorer client
s3_client = boto3.client('s3')  # S3 client

def lambda_handler(event, context):

    # Define the S3 bucket where the report will be stored
    s3_bucket_name = 'ecs-dropbox-44'

    # Define project set and environment
    project_set = 'FMDB'
    environment = 'tools'

    # Define the time range for the CUR (last 28 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=28)

    # Format the date as YYYY-MM-DD
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Example: 20250218_123045
    report_filename = f'{project_set}_{environment}_{timestamp}.json'

    try:
        # Fetch the cost and usage data from AWS Cost Explorer, grouped by service
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date_str,
                'End': end_date_str
            },
            Granularity='DAILY',
            Metrics=['BlendedCost', 'UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )

        # Prepare the data
        report_data = []
        for result in response['ResultsByTime']:
            time_period_start = result['TimePeriod']['Start']
            time_period_end = result['TimePeriod']['End']
            for group in result['Groups']:
                service_name = group['Keys'][0]
                cost_amount = group['Metrics']['BlendedCost']['Amount']
                report_data.append({
                    'project_set': project_set,
                    'environment': environment,
                    'service': service_name,
                    'cost_amount': float(cost_amount),
                    'start_date': time_period_start,
                    'end_date': time_period_end
                })

        # Upload the formatted data to S3
        s3_client.put_object(
            Bucket=s3_bucket_name,
            Key=f'CUR/{report_filename}',
            Body=json.dumps(report_data, indent=4),
            ContentType='application/json'
        )

        print(f"Successfully uploaded report to s3://{s3_bucket_name}/CUR/{report_filename}")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Report successfully exported to S3 as {report_filename}')
        }

    except Exception as e:
        print(f"Error exporting report: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error exporting report')
        }
