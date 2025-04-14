import tkinter as tk
from calculator import Calculator
import time
import os
import json
import requests
import random
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
            
            # Clear the display before each operation
            app.button_clicked('C')
            time.sleep(0.2)
            
            # Handle different types of operations
            if op in ['sin', 'cos', 'tan']:
                # For trig functions, enter the angle first
                for digit in num2:  # num2 contains the angle
                    app.button_clicked(digit)
                time.sleep(0.2)
                # Then press the function button
                app.button_clicked(op)
                time.sleep(0.2)
                # Press equals to get the result
                app.button_clicked('=')
                time.sleep(0.2)
            elif op == 'π':
                app.button_clicked('π')
                time.sleep(0.2)
            else:
                # For regular operations
                # Enter first number
                for digit in num1:
                    app.button_clicked(digit)
                time.sleep(0.2)
                
                # Enter operation
                if op:
                    app.button_clicked(op)
                    time.sleep(0.2)
                    
                    # Enter second number if exists
                    if num2:
                        for digit in num2:
                            app.button_clicked(digit)
                        time.sleep(0.2)
                        
                        # Press equals for arithmetic operations
                        if op in ['+', '-', '×', '÷']:
                            app.button_clicked('=')
                            time.sleep(0.2)
            
            # Get the result from the display
            result = app.display_var.get()
            
            # Compare with expected result
            try:
                result_float = float(result)
                expected_float = float(expected)
                if abs(result_float - expected_float) < 0.0001:  # Allow small floating point differences
                    print(f"Expected: {expected}, Got: {result}")
                else:
                    print(f"Expected: {expected}, Got: {result} (MISMATCH)")
            except ValueError:
                print(f"Expected: {expected}, Got: {result}")
            
            time.sleep(0.5)  # Wait between operations
            
        except Exception as e:
            print(f"Error performing operation: {str(e)}")
    
    # Close the calculator window
    root.destroy()

def test_calculator_operations():
    """Test calculator operations and export to InfluxDB"""
    print("Performing 10 calculator operations...")
    
    # Create calculator instance
    calc = Calculator()
    
    # Test cases with expected results
    test_cases = [
        ("33 + 54", 87),
        ("63 - 23", 40),
        ("7 × 17", 119),
        ("46 ÷ 2", 23.0),
        ("7 %", 0.07),
        ("80 ±", -80),
        ("sin 184", -0.06975647),
        ("cos 186", -0.9945219),
        ("tan 295", -2.14450692),
        ("π", math.pi)
    ]
    
    # Run test cases
    for i, (operation, expected) in enumerate(test_cases, 1):
        print(f"Operation {i}/10: {operation}")
        
        # Perform calculation
        if operation == "π":
            result = calc.pi()
        elif "sin" in operation:
            result = calc.sin(float(operation.split()[1]))
        elif "cos" in operation:
            result = calc.cos(float(operation.split()[1]))
        elif "tan" in operation:
            result = calc.tan(float(operation.split()[1]))
        elif "%" in operation:
            result = calc.percentage(float(operation.split()[0]))
        elif "±" in operation:
            result = calc.sign_change(float(operation.split()[0]))
        else:
            parts = operation.split()
            if len(parts) == 3:
                num1, op, num2 = parts
                if op == "+":
                    result = calc.add(float(num1), float(num2))
                elif op == "-":
                    result = calc.subtract(float(num1), float(num2))
                elif op == "×":
                    result = calc.multiply(float(num1), float(num2))
                elif op == "÷":
                    result = calc.divide(float(num1), float(num2))
            else:
                result = float(operation)
        
        print(f"Expected: {expected}, Got: {result}")
        
        # Export to InfluxDB
        try:
            calc.export_to_influxdb(operation, result)
        except Exception as e:
            print(f"Export failed for operation {operation}: {str(e)}")
    
    print("\nAll operations completed.")

if __name__ == "__main__":
    run_test() 