import os
import requests
from dotenv import load_dotenv
import time

def test_influxdb_connection():
    # Load environment variables
    load_dotenv()
    
    # Get InfluxDB settings from environment variables
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG', 'calculator')
    bucket = os.getenv('INFLUXDB_BUCKET', 'calculator_logs')
    
    print(f"Testing InfluxDB connection...")
    print(f"URL: {url}")
    print(f"Organization: {org}")
    print(f"Bucket: {bucket}")
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test 1: Check if InfluxDB is running
        health_url = f"{url}/health"
        health_response = requests.get(health_url)
        print(f"\nHealth check status: {health_response.status_code}")
        print(f"Health check response: {health_response.text}")
        
        # Test 2: Check if our organization exists
        org_url = f"{url}/api/v2/orgs"
        org_response = requests.get(org_url, headers=headers)
        print(f"\nOrganization check status: {org_response.status_code}")
        
        if org_response.status_code == 200:
            orgs = org_response.json().get('orgs', [])
            found_org = None
            for o in orgs:
                if o['name'] == org:
                    found_org = o
                    break
            
            if found_org:
                print(f"Found organization: {org}")
                print(f"Organization ID: {found_org['id']}")
            else:
                print(f"Organization '{org}' not found")
                return
        
        # Test 3: Check if our bucket exists
        bucket_url = f"{url}/api/v2/buckets"
        params = {'org': org}
        bucket_response = requests.get(bucket_url, headers=headers, params=params)
        print(f"\nBucket check status: {bucket_response.status_code}")
        
        if bucket_response.status_code == 200:
            buckets = bucket_response.json().get('buckets', [])
            found_bucket = None
            for b in buckets:
                if b['name'] == bucket:
                    found_bucket = b
                    break
            
            if found_bucket:
                print(f"Found bucket: {bucket}")
                print(f"Bucket ID: {found_bucket['id']}")
                print(f"Retention Rules: {found_bucket.get('retentionRules', [])}")
            else:
                print(f"Bucket '{bucket}' not found")
        
        print("\nInfluxDB connection test completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print(f"\nFailed to connect to InfluxDB at {url}")
        print("Please check if InfluxDB is running and the URL is correct")
    except Exception as e:
        print(f"\nError testing InfluxDB connection: {str(e)}")

if __name__ == "__main__":
    test_influxdb_connection() 