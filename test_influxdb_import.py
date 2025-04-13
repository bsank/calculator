import tkinter as tk
from calculator import Calculator
import time
import os
import json
import requests
import random
import math

def check_influxdb_connection():
    try:
        response = requests.get("http://localhost:8086/health")
        return response.status_code == 200
    except:
        return False

def run_test():
    # Check if InfluxDB is running
    if not check_influxdb_connection():
        print("Error: InfluxDB is not running. Please start InfluxDB first.")
        return

    # Create the main window
    root = tk.Tk()
    root.withdraw()  # Hide the window but keep it running
    app = Calculator(root)
    
    # Wait for the calculator to initialize
    time.sleep(1)
    
    # Generate test operations
    test_operations = []
    
    # Basic arithmetic operations (4 operations)
    # Addition
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)
    test_operations.append((str(num1), "+", str(num2), str(num1 + num2)))
    
    # Subtraction
    num1 = random.randint(1, 100)
    num2 = random.randint(1, num1)  # Ensure positive result
    test_operations.append((str(num1), "-", str(num2), str(num1 - num2)))
    
    # Multiplication
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    test_operations.append((str(num1), "×", str(num2), str(num1 * num2)))
    
    # Division
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 10)
    test_operations.append((str(num1), "÷", str(num2), str(round(num1 / num2, 4))))
    
    # Percentage and sign change operations (2 operations)
    # Percentage
    num = random.randint(1, 100)
    test_operations.append((str(num), "%", "", str(num / 100)))
    
    # Sign change
    num = random.randint(1, 100)
    test_operations.append((str(num), "±", "", str(-num)))
    
    # Scientific operations (4 operations)
    # Sine
    angle = random.randint(0, 360)
    test_operations.append(("sin", str(angle), "", str(round(math.sin(math.radians(angle)), 8))))
    
    # Cosine
    angle = random.randint(0, 360)
    test_operations.append(("cos", str(angle), "", str(round(math.cos(math.radians(angle)), 8))))
    
    # Tangent
    angle = random.randint(0, 360)
    test_operations.append(("tan", str(angle), "", str(round(math.tan(math.radians(angle)), 8))))
    
    # Pi
    test_operations.append(("π", "", "", str(math.pi)))
    
    # Perform operations
    print("Performing 10 calculator operations...")
    for i, (num1, op, num2, expected) in enumerate(test_operations):
        try:
            print(f"Operation {i+1}/10: {num1} {op} {num2}")
            
            # Enter first number
            for digit in num1:
                app.button_clicked(digit)
            time.sleep(0.2)  # Reduced sleep time
            
            # Enter operation
            if op:
                app.button_clicked(op)
                time.sleep(0.2)  # Reduced sleep time
                
                # Enter second number if exists
                if num2:
                    for digit in num2:
                        app.button_clicked(digit)
                    time.sleep(0.2)  # Reduced sleep time
            
            # Press equals
            app.button_clicked("=")
            time.sleep(0.2)  # Reduced sleep time
            
            # Verify result
            result = app.display_var.get()
            print(f"Expected: {expected}, Got: {result}")
            
            # Clear for next operation
            app.button_clicked("C")
            time.sleep(0.2)  # Reduced sleep time
            
            # Process events to keep GUI responsive
            root.update()
            
        except Exception as e:
            print(f"Error during operation {i+1}: {str(e)}")
            continue
    
    # Export to InfluxDB
    print("\nExporting logs to InfluxDB...")
    
    # Make sure the InfluxDB settings file exists
    if not os.path.exists("influxdb_settings.json"):
        print("Creating InfluxDB settings file...")
        with open("influxdb_settings.json", "w") as f:
            f.write('''{
    "url": "http://localhost:8086",
    "token": "my-super-secret-auth-token",
    "org": "calculator",
    "bucket": "calculator_logs"
}''')
    
    # Export directly using the method
    try:
        app.export_to_influxdb()
        print("Export successful!")
    except Exception as e:
        print(f"Export failed: {str(e)}")
    
    # Clean up
    root.quit()

if __name__ == "__main__":
    run_test() 