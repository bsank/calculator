import requests
import json

def load_influxdb_settings():
    with open('influxdb_settings.json', 'r') as f:
        return json.load(f)

def cleanup_influxdb():
    settings = load_influxdb_settings()
    
    # Prepare the delete query
    delete_query = '''
    from(bucket: "calculator_logs")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "calculator_operation")
        |> drop()
    '''
    
    # Prepare the request
    url = f"{settings['url']}/api/v2/delete"
    headers = {
        'Authorization': f"Token {settings['token']}",
        'Content-Type': 'application/json'
    }
    params = {
        'org': settings['org'],
        'bucket': settings['bucket']
    }
    data = {
        'start': '1970-01-01T00:00:00Z',
        'stop': '2030-01-01T00:00:00Z'
    }
    
    try:
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