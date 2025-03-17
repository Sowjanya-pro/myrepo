# myrepo
This repo is related to loading a zip file to Athena by using multiple AWS Lambda Functions 


Below is a step-by-step `README.md` file tailored for AWS SAM application.

## Data Processing Pipeline with AWS SAM

This repository contains an AWS Serverless Application Model (SAM) application that automates the process of downloading a dataset, processing it, converting it to Parquet format, partitioning it, and enabling querying via Amazon Athena. The application uses AWS Lambda, Step Functions, S3, Glue, and Athena to achieve this workflow.

## Overview

The application performs the following tasks:
1. Downloads a ZIP file from a public URL and uploads it to an S3 bucket.
2. Extracts and processes the ZIP file, storing the results in a partitioned format in S3.
3. Crawls the processed data with AWS Glue to create a table in a database.
4. Enables querying of the data using Amazon Athena.

The architecture includes:
- **S3 Bucket**: Stores raw and processed data.
- **Lambda Functions**: Handle downloading and processing tasks.
- **Step Functions**: Orchestrate the workflow.
- **AWS Glue Crawler**: Catalogs the processed data.
- **Amazon Athena**: Provides querying capabilities.

## Prerequisites

Before deploying this application, ensure you have the following:

- **AWS Account**: An active AWS account with permissions to create S3 buckets, Lambda functions, Step Functions, Glue crawlers, and Athena workgroups.
- **AWS CLI**: Installed and configured with your AWS credentials (`aws configure`).
- **AWS SAM CLI**: Installed (`pip install aws-sam-cli`).
- **Python 3.11**: Required for local testing of Lambda functions (optional).
- **Git**: For cloning and managing this repository.

## Project Structure
DataProcessingPipeline        # stack name of your project directory
```
.
├── fetch_file/               # Directory for DownloadfilesfromS3 Lambda code
│   └──downloadfilesfroms3.py # Lambda handler for downloading files
│   └── requirements.txt                       
├── process_file/             # Directory for extractzipfiles Lambda code
│   └── extractzipfiles.py    # Lambda handler for processing files
│   └── requirements.txt   
├── template.yaml             # AWS SAM template
└── README.md                 
```

## Setup Instructions

### 1. Clone the Repository
Clone this repository to your local machine:

```bash
git clone https://github.com/Sowjanya-pro/myrepo.git

```

### 2. Prepare Lambda Functions
Ensure the Lambda function code is present in the respective directories:
- **`fetch_file/downloadfilesfroms3.py`**: Contains the logic to download a ZIP file from `https://eforexcel.com/wp/wp-content/uploads/2020/09/2m-Sales-Records.zip` and upload it to the S3 bucket `sourcedata032025`.
- **`process_file/extractzipfiles.py`**: Contains the logic to extract the ZIP file, process it, and store the results in Parquet format under `s3://extractzipfiles/partitioned_data/`.


### 3. Configure AWS Credentials
-Ensure you have AWS_CLI installed in your local machine
-Ensure you have AWS_SAM_CLI installed in your local machine
-After installing both CLIs, you need to configure the AWS CLI with your AWS credentials so that SAM CLI (which relies on AWS CLI) can authenticate with your AWS account.

Configuration Command
Run the following command to configure AWS CLI:

```bash
aws configure
```
You’ll be prompted to enter:

AWS Access Key ID: Your access key from the AWS IAM user or role.
AWS Secret Access Key: The corresponding secret key.
Default region name: The AWS region (e.g., us-east-2 for your template’s Lambda ARNs).
Default output format: Typically json (press Enter for default).

once everything is done you are ready to deploy your code into AWS console

### 4. Process of executing the code

Build the application (from the root of your project directory):
```bash
sam build
```

### Package the Application
Package the SAM application by uploading the Lambda code to an S3 bucket:

```bash
sam package --output-template-file packaged.yaml --s3-bucket `<your-s3-bucket>`
```

Replace `<your-s3-bucket>` with an existing S3 bucket in your AWS account.

## Deployment Instructions

### 5. Deploy the Application
Deploy the packaged application to AWS:

```bash
sam deploy --template-file packaged.yaml --stack-name DataProcessingPipeline --capabilities CAPABILITY_IAM --parameter-overrides ParameterKey=DownloadLambdaName,ParameterValue=DataProcessingPipeline-DownloadFilesFromS3 ParameterKey=ExtractLambdaName,ParameterValue=DataProcessingPipeline-ExtractZipFiles
```

- `--stack-name`: Name of the CloudFormation stack (e.g., `DataProcessingPipeline`).
- `--capabilities CAPABILITY_IAM`: Grants SAM permission to create IAM roles.
- `--parameter-overrides`: here we are passing the parameters for step functions.The Step Functions state machine uses these exact names as the state names (StartAt and the keys in States) and links them to the corresponding ARNs.

### 6. Verify Deployment
After deployment:
- Check the AWS CloudFormation console for the stack status (`CREATE_COMPLETE`).
- Outputs will include:
  - `BucketName`: Name of the created S3 bucket.
  - `StepFunctionArn`: ARN of the Step Function.
  - `AthenaWorkGroupName`: Name of the Athena workgroup.

## Running the Pipeline

### 7. Start the Step Function
Trigger the Step Function manually via the AWS Console:
1. Go to the Step Functions console.
2. Find `SequentialFlowStepFunction`.
3. Click "Start Execution" and provide an optional input (e.g., `{}`).

Here while running the extractzipfiles lambda function make sure that we are providing the test event input to it.

required input:
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "sourcedata032025"
        },
        "object": {
          "key": "raw-data/2m Sales Records.csv"
        }
      }
    }
  ]
}
 after this execution you can see the results under s3://{bucket_name}/partitioned_data/

### 8. Monitor Execution
- View the execution progress in the Step Functions console.
- Check CloudWatch Logs for Lambda execution details (under log groups `/aws/lambda/DownloadfilesfromS3` and `/aws/lambda/extractzipfiles`).

### 9. Run the Glue Crawler
Manually run the Glue crawler to catalog the processed data:
1. Go to the AWS Glue console.
2. Find `sales-data-crawler`.
3. Click "Run crawler".


### 10. Query Data with Athena
Once the crawler finishes:
1. Go to the Athena console.
2. Select the `Primary` workgroup.
3. Set the query result location to `s3://sourcedatapipeline-sales/query_data/`.
4. Run a query against the `sales_db` database, e.g.:
   ```sql
   SELECT * FROM sales_db.<table_name> LIMIT 10;
   ```
   (The table name is generated by the crawler, typically based on the S3 path, e.g., `partitioned_data`.)

## Troubleshooting

- **Lambda Errors**: Check CloudWatch Logs for specific error messages.
- **Step Function Failure**: Review the execution history in the Step Functions console.
- **Glue Crawler Issues**: Ensure the S3 path `s3://sourcedatapipeline-sales/partitioned_data/` contains data and the IAM role has access.
