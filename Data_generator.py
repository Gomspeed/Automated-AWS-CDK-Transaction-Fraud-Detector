import json
import random
import boto3
from datetime import datetime
import time
import faker

def generate_transaction():
    fake = faker.Faker()
    
    # Generate random amount between 0 and 100,000
    amount = round(random.uniform(0, 100000), 2)
    
    # Generate random timestamp within last 24 hours
    timestamp = datetime.now().isoformat()
    
    # Create transaction object
    transaction = {
        "amount": amount,  # Amount at the top level
        "transaction_id": fake.uuid4(),
        "timestamp": timestamp,
        "customer": {
            "name": fake.name(),
            "email": fake.email(),
            "account_number": fake.bban(),
            "phone": fake.phone_number()
        },
        "transaction": {
            "type": random.choice(['purchase', 'withdrawal', 'transfer', 'deposit', 'payment']),
            "currency": "USD",
            "payment_method": random.choice(['credit_card', 'debit_card', 'bank_transfer', 'digital_wallet']),
            "status": "completed" if random.random() < 0.95 else "failed"
        },
        "merchant": {
            "name": fake.company(),
            "category": random.choice([
                'Restaurant', 'Retail', 'Travel', 'Electronics', 'Groceries', 
                'Entertainment', 'Healthcare', 'Automotive', 'Education', 'Utilities'
            ]),
            "location": {
                "address": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "country": fake.country(),
                "coordinates": {
                    "latitude": str(fake.latitude()),
                    "longitude": str(fake.longitude())
                }
            }
        },
        "risk_score": round(random.uniform(0, 100), 2),
        "ip_address": fake.ipv4(),
        "device_id": fake.sha256(),
        "user_agent": fake.user_agent()
    }
    
    return transaction

def upload_to_s3(bucket_name, json_data):
    s3_client = boto3.client('s3')
    
    # Create unique filename using timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"data/transaction_{timestamp}.json"
    
    try:
        json_string = json.dumps(json_data, indent=2)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json_string
        )
        print(f"Successfully uploaded {file_name} to {bucket_name}")
        
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")

def main():
    # Replace with your bucket name
    bucket_name = "bucketname"
    
    print("Starting continuous transaction generation. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Generate transaction
            transaction = generate_transaction()
            
            # Upload to S3
            upload_to_s3(bucket_name, transaction)
            
            # Print the generated transaction (optional)
            print("\nGenerated Transaction:")
            print(json.dumps(transaction, indent=2))
            
            # Wait for 10 seconds before next iteration
            time.sleep(10)
    
    except KeyboardInterrupt:
        print("\nStopped transaction generation.")

if __name__ == "__main__":
    main()
