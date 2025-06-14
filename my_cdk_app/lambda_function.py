import json
import boto3
import os

def handler(event, context):
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')
    
    # Get bucket and file information from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    
    # Skip processing if file is in incidents folder
    if file_key.startswith('incidents/'):
        return
    
    # Read the JSON file
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    file_content = json.loads(response['Body'].read().decode('utf-8'))
    
    # Check if value is greater than 20,000
    # Assuming the key to check is 'amount' - modify as needed
    if file_content.get('amount', 0) > 20000:
        # Create incident report
        incident_report = {
            'original_file': file_key,
            'timestamp': event['Records'][0]['eventTime'],
            'amount': file_content['amount']
        }
        
        # Save incident report
        incident_key = f"incidents/{file_key.split('/')[-1]}_incident.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=incident_key,
            Body=json.dumps(incident_report)
        )
        
        # Send SNS notification
        sns_client.publish(
            TopicArn=os.environ['TOPIC_ARN'],
            Message='There is a suspicious activity in the file',
            Subject='Suspicious Activity Detected'
        )
    
    return {
        'statusCode': 200,
        'body': 'Processing complete'
    }