import requests
import os
from dotenv import load_dotenv

def delete_bucket():
    """Delete the calculator_logs bucket from InfluxDB"""
    try:
        # Load settings from .env file
        load_dotenv()
        
        # Get settings from environment variables
        url = os.getenv('INFLUXDB_URL')
        token = os.getenv('INFLUXDB_TOKEN')
        org = os.getenv('INFLUXDB_ORG')
        bucket = os.getenv('INFLUXDB_BUCKET')
        
        if not all([url, token, org, bucket]):
            print("InfluxDB settings not found in .env file")
            return
        
        # Prepare the request
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        
        # First, get the bucket ID
        response = requests.get(
            f"{url}/api/v2/buckets",
            headers=headers,
            params={'org': org, 'name': bucket}
        )
        
        if response.status_code != 200:
            print(f"Error getting bucket info: {response.status_code} - {response.text}")
            return
            
        buckets = response.json().get('buckets', [])
        if not buckets:
            print(f"Bucket {bucket} not found")
            return
            
        bucket_id = buckets[0]['id']
        
        # Now delete the bucket using its ID
        response = requests.delete(
            f"{url}/api/v2/buckets/{bucket_id}",
            headers=headers
        )
        
        if response.status_code == 204:
            print(f"Successfully deleted bucket: {bucket}")
        else:
            print(f"Error deleting bucket: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    delete_bucket() 