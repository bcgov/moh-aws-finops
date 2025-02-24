import json
import boto3
import datetime

# AWS S3 Clients
s3_client = boto3.client('s3')

# Define S3 Buckets
WORKING_BUCKET = "finops-working"
PROCESSED_BUCKET = "finops-processed"

# Project Set and Environment
PROJECT_SET = "FMDB"
ENVIRONMENT = "tools"

def lambda_handler(event, context):
    try:
        # Get the current date in YYYYMMDD format
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        prefix = f"CUR/{PROJECT_SET}_{ENVIRONMENT}_{current_date}"  # Only get files from today

        # List all files in the working bucket for today's date
        response = s3_client.list_objects_v2(Bucket=WORKING_BUCKET, Prefix=prefix)
        files = response.get("Contents", [])

        if not files:
            print("No files found for today.")
            return {
                'statusCode': 200,
                'body': json.dumps('No files to process for today.')
            }

        aggregated_data = []

        # Process each JSON file
        for file in files:
            file_key = file["Key"]
            print(f"Processing file: {file_key}")

            # Read the file content
            obj = s3_client.get_object(Bucket=WORKING_BUCKET, Key=file_key)
            file_content = json.loads(obj['Body'].read().decode('utf-8'))

            # Ensure it's a list before merging
            if isinstance(file_content, list):
                aggregated_data.extend(file_content)
            else:
                print(f"Skipping file {file_key} - not a JSON list.")

        # Define the output file name
        aggregated_filename = f"aggregated_{PROJECT_SET}_{ENVIRONMENT}_{current_date}.json"
        output_key = f"finops-processed/{aggregated_filename}"

        # Upload the aggregated file to the processed bucket
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=output_key,
            Body=json.dumps(aggregated_data, indent=4),
            ContentType='application/json'
        )

        print(f"Aggregated file saved: s3://{PROCESSED_BUCKET}/{output_key}")

        return {
            'statusCode': 200,
            'body': json.dumps(f"Aggregated file created: {aggregated_filename}")
        }

    except Exception as e:
        print(f"Error aggregating files: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing files: {str(e)}")
        }
