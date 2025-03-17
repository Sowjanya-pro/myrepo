import boto3
import requests
import zipfile
import io
import os

# Initialize S3 client
s3 = boto3.client('s3')

# Environment variables
BUCKET_NAME = os.environ['BUCKET_NAME']  # S3 bucket name
URL = os.environ['URL']    # URL of the ZIP file

def lambda_handler(event, context):
    try:
        # Step 1: Download the ZIP file from the URL
        print(f"Downloading ZIP file from: {URL}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/zip, application/octet-stream, */*"
        }
        response = requests.get(URL, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download file. Status code: {response.status_code}")

        # Step 2: Extract the contents of the ZIP file
        print("Extracting ZIP file...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            for file_name in zip_file.namelist():
                print(f"Processing file: {file_name}")
                with zip_file.open(file_name) as file:
                    file_content = file.read()

                    # Step 3: Upload each file to S3
                    s3_key = f"raw-data/{file_name}"  # Store files under the 'raw-data' prefix
                    print(f"Uploading {file_name} to S3 at: s3://{BUCKET_NAME}/{s3_key}")
                    s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=file_content)

        print("Extraction and upload completed successfully.")
        return {
            "statusCode": 200,
            "body": "Files extracted and uploaded to S3 successfully."
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
