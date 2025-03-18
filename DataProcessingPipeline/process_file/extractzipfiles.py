import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io
import os
from datetime import datetime

# Initialize S3 client
s3 = boto3.client('s3')

# Environment variable
BUCKET_NAME = os.environ['BUCKET_NAME']  # S3 bucket name from Lambda env vars

def lambda_handler(event, context):
    try:
        print("Event received:", event)  # Log the event

        if 'Records' not in event:
            raise ValueError("Invalid event format: Expected S3 event with 'Records'")

        for record in event['Records']:
            source_bucket = record['s3']['bucket']['name']
            source_key = record['s3']['object']['key']

            if not source_key.startswith("raw-data/"):
                print(f"Skipping file {source_key} (not in raw-data/ prefix)")
                continue

            print(f"Processing file: s3://{source_bucket}/{source_key}")
            
            # Read the file from S3 as a stream
            response = s3.get_object(Bucket=source_bucket, Key=source_key)
            file_stream = response['Body']

            # Process the CSV file in chunks
            chunk_size = 50000  # Adjust this based on your file size
            for chunk in pd.read_csv(file_stream, chunksize=chunk_size):
                
                if 'Country' not in chunk.columns:
                    raise ValueError(f"'Country' column missing in {source_key}")
                
                # Group the chunk by 'Country' and process each group
                for country, data in chunk.groupby('Country'):
                    parquet_buffer = io.BytesIO()
                    
                    # Convert to Parquet format
                    table = pa.Table.from_pandas(data)
                    pq.write_table(table, parquet_buffer)
                    
                    # Reset buffer pointer to start
                    parquet_buffer.seek(0)
                    
                    # Define S3 path for partitioned data
                    parquet_key = f"partitioned-data/country_partition={country}/data.parquet"
                    
                    # Upload Parquet file directly to S3
                    print(f"Uploading Parquet to: s3://{BUCKET_NAME}/{parquet_key}")
                    s3.upload_fileobj(parquet_buffer, BUCKET_NAME, parquet_key)
                    print(f"Parquet for {country} uploaded successfully.")

            # Archive the original file
            archive_key = f"archive/{datetime.now().strftime('%Y-%m-%d')}/{os.path.basename(source_key)}"
            print(f"Archiving to: s3://{BUCKET_NAME}/{archive_key}")
            s3.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={'Bucket': source_bucket, 'Key': source_key},
                Key=archive_key
            )
            print("File archived successfully.")

            # Delete the original file
            print(f"Deleting: s3://{source_bucket}/{source_key}")
            s3.delete_object(Bucket=source_bucket, Key=source_key)
            print("Original file deleted successfully.")

        return {
            "statusCode": 200,
            "body": "Files processed successfully."
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }