import requests
import json
from datetime import datetime, timedelta

def load_influxdb_settings():
    with open('influxdb_settings.json', 'r') as f:
        return json.load(f)

def format_operation(operation):
    """Format the operation string for better readability"""
    # Replace underscores with spaces
    operation = operation.replace('_', ' ')
    
    # Replace operation names with symbols
    replacements = {
        'multiply': '×',
        'divide': '÷',
        'plus': '+',
        'minus': '-',
        'equals': '='
    }
    
    for old, new in replacements.items():
        operation = operation.replace(old, new)
    
    return operation

def format_result(result):
    """Format the result for better readability"""
    try:
        # Convert to float and remove trailing zeros
        return f"{float(result):g}"
    except ValueError:
        return result

def query_calculator_operations():
    settings = load_influxdb_settings()
    
    # Prepare the Flux query
    flux_query = '''
    from(bucket: "calculator_logs")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "calculator_operation")
        |> filter(fn: (r) => r["operation"] != "Clear")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 25)
    '''
    
    # Prepare the request
    url = f"{settings['url']}/api/v2/query"
    headers = {
        'Authorization': f"Token {settings['token']}",
        'Content-Type': 'application/json',
        'Accept': 'application/csv'
    }
    params = {
        'org': settings['org']
    }
    data = {
        'query': flux_query,
        'type': 'flux'
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, params=params)
        if response.status_code == 200:
            print("\nLast 25 Calculator Operations:")
            print("=" * 80)
            print(f"{'Timestamp':<25} {'Operation':<30} {'Result':<15}")
            print("-" * 80)
            
            # Parse CSV response
            lines = response.text.split('\n')
            data_lines = [line for line in lines if line and not line.startswith('#')]
            
            for line in data_lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) >= 6:
                    timestamp = datetime.fromisoformat(parts[5].replace('Z', '+00:00'))
                    operation = parts[7]  # operation tag
                    result = parts[9]     # result field
                    
                    # Format operation and result
                    operation = format_operation(operation)
                    result = format_result(result)
                    
                    # Format timestamp for local time
                    local_time = timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"{local_time:<25} {operation:<30} {result:<15}")
        else:
            print(f"Error querying InfluxDB: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    query_calculator_operations() 