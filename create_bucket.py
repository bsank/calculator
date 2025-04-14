import requests
import os
from dotenv import load_dotenv

def create_bucket():
    """Create a new calculator_logs bucket in InfluxDB"""
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
        
        # First, get the organization ID
        response = requests.get(
            f"{url}/api/v2/orgs",
            headers=headers,
            params={'org': org}
        )
        
        if response.status_code != 200:
            print(f"Error getting organization info: {response.status_code} - {response.text}")
            return
            
        orgs = response.json().get('orgs', [])
        if not orgs:
            print(f"Organization {org} not found")
            return
            
        org_id = orgs[0]['id']
        
        # Bucket configuration
        data = {
            'orgID': org_id,
            'name': bucket,
            'retentionRules': [
                {
                    'type': 'expire',
                    'everySeconds': 30 * 24 * 60 * 60  # 30 days retention
                }
            ]
        }
        
        # Create the bucket
        response = requests.post(
            f"{url}/api/v2/buckets",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            print(f"Successfully created bucket: {bucket}")
            print("Bucket settings:")
            print(f"- Name: {bucket}")
            print(f"- Organization: {org}")
            print("- Retention: 30 days")
        else:
            print(f"Error creating bucket: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_bucket() 