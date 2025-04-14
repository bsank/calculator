import os
import requests
from dotenv import load_dotenv

def cleanup_influxdb():
    # Load environment variables
    load_dotenv()
    
    # Get InfluxDB settings from environment variables
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG', 'calculator')
    bucket = os.getenv('INFLUXDB_BUCKET', 'calculator_logs')
    
    print(f"Preparing to clean up all calculator operations from InfluxDB...")
    print(f"Organization: {org}")
    print(f"Bucket: {bucket}")
    
    # Prepare the request
    url = f"{url}/api/v2/delete"
    headers = {
        'Authorization': f"Token {token}",
        'Content-Type': 'application/json'
    }
    params = {
        'org': org,
        'bucket': bucket
    }
    data = {
        'start': '1970-01-01T00:00:00Z',
        'stop': '2030-01-01T00:00:00Z',
        'predicate': '_measurement="calculator_operation"'
    }
    
    try:
        # Ask for confirmation
        confirm = input("Are you sure you want to delete all calculator operations? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled.")
            return
        
        response = requests.post(url, json=data, headers=headers, params=params)
        if response.status_code == 204:
            print("Successfully cleaned up InfluxDB data!")
        else:
            print(f"Error cleaning up InfluxDB: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    cleanup_influxdb() 