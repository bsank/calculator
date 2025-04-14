import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

def load_influxdb_settings():
    """Load InfluxDB settings from environment variables"""
    load_dotenv()
    return {
        'url': os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
        'token': os.getenv('INFLUXDB_TOKEN', ''),
        'org': os.getenv('INFLUXDB_ORG', 'calculator'),
        'bucket': os.getenv('INFLUXDB_BUCKET', 'calculator_logs')
    }

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
        'equals': '=',
        'pi': 'π',
        '*': '×',
        '/': '÷'
    }
    
    for old, new in replacements.items():
        operation = operation.replace(old, new)
    
    return operation.strip()

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
        |> range(start: -24h)
        |> filter(fn: (r) => r["_measurement"] == "calculator_operations")
        |> filter(fn: (r) => r["_field"] == "result")
        |> filter(fn: (r) => r["operation"] != "Clear")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 25)
        |> yield(name: "results")
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
            print("\nRaw Response:")
            print(response.text)
            print("\nRecent Calculator Operations:")
            print("-" * 100)
            print(f"{'Timestamp':<20} {'Operation':<30} {'Result':<20}")
            print("-" * 100)
            
            # Parse CSV response
            lines = response.text.split('\n')
            data_lines = [line for line in lines if line and not line.startswith('#')]
            
            if len(data_lines) < 2:  # No data if less than header + 1 row
                print("No calculator operations found in the last 24 hours.")
                return
                
            # Get header line to find column positions
            header = data_lines[0].split(',')
            print("\nHeader columns:", header)
            
            try:
                time_index = header.index('_time')
                operation_index = header.index('operation')
                value_index = header.index('_value')
                print(f"\nIndices - Time: {time_index}, Operation: {operation_index}, Value: {value_index}")
            except ValueError as e:
                print(f"\nError finding column: {e}")
                return
            
            # Process data lines
            records_found = 0
            for line in data_lines[1:]:
                parts = line.split(',')
                print(f"\nProcessing line: {parts}")
                if len(parts) <= max(time_index, operation_index, value_index):
                    print(f"Skipping line - not enough parts ({len(parts)} <= {max(time_index, operation_index, value_index)})")
                    continue
                    
                timestamp = datetime.fromisoformat(parts[time_index].replace('Z', '+00:00'))
                operation = parts[operation_index]
                result = parts[value_index]
                
                # Format timestamp to show only local time
                local_time = timestamp.astimezone().strftime('%H:%M:%S')
                formatted_operation = format_operation(operation)
                formatted_result = format_result(result)
                print(f"{local_time:<20} {formatted_operation:<30} {formatted_result:<20}")
                records_found += 1
            
            print("-" * 100)
            print(f"\nTotal non-Clear operations found: {records_found}")
        else:
            print(f"Error querying InfluxDB: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {str(e)}")

def clean_operation(operation):
    """Clean up the operation string for display"""
    operation = operation.strip().rstrip('\r')
    if operation == 'none':
        return 'Clear'
    parts = operation.split('_')
    if len(parts) == 3:
        num1, op, num2 = parts
        op = op.replace('*', '×').replace('/', '÷')
        return f"{num1} {op} {num2}"
    return operation

def query_calculator_data():
    # Load environment variables
    load_dotenv()
    
    # Get InfluxDB settings from environment variables
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG', 'calculator')
    bucket = os.getenv('INFLUXDB_BUCKET', 'calculator_logs')
    
    print(f"Querying InfluxDB for all calculator operations...")
    print(f"URL: {url}")
    print(f"Organization: {org}")
    print(f"Bucket: {bucket}")
    
    # Prepare the Flux query - no limit, show all records
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -365d)
      |> filter(fn: (r) => r["_measurement"] == "calculator_operation")
      |> sort(columns: ["_time"], desc: true)
    '''
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Send the query to InfluxDB
        response = requests.post(
            f"{url}/api/v2/query?org={org}",
            headers=headers,
            json={"query": query}
        )
        
        if response.status_code == 200:
            print("\nCalculator operations:")
            print("=" * 100)
            
            # Parse the CSV response
            lines = response.text.strip().split('\n')
            if len(lines) > 1:  # Check if we have data (header + at least one row)
                headers = lines[0].split(',')
                record_count = 0
                
                # Print column headers
                print(f"{'Timestamp':<25} {'Operation':<30} {'Result':<20}")
                print("-" * 100)
                
                for line in lines[1:]:
                    values = line.split(',')
                    if len(values) >= len(headers):
                        try:
                            # Get indices for the columns we need
                            time_idx = headers.index('_time')
                            value_idx = headers.index('_value')
                            operation_str = values[-1]  # Operation is always the last column
                            
                            # Parse the timestamp
                            time_str = values[time_idx]
                            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Get the result value
                            result = values[value_idx]
                            
                            # Clean up and format the operation
                            operation = clean_operation(operation_str)
                            
                            print(f"{formatted_time:<25} {operation:<30} {result:<20}")
                            record_count += 1
                        except Exception as e:
                            print(f"Error processing row: {e}")
                
                print("-" * 100)
                print(f"\nTotal records found: {record_count}")
            else:
                print("No calculator operations found.")
        else:
            print(f"Error querying InfluxDB: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error querying InfluxDB: {str(e)}")

if __name__ == "__main__":
    query_calculator_data() 