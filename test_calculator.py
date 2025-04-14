import os
import requests
import time
import math
from dotenv import load_dotenv
import logging

# Set up logging - only log errors to file
logging.basicConfig(
    filename='calculator_test_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Disable other loggers
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

class CalculatorTest:
    def __init__(self):
        # Calculator state
        self.current_number = ""
        self.first_number = None
        self.operation = None
        self.should_clear_display = False
        self.scientific_mode = False
        
        # Load environment variables
        load_dotenv(override=True)
        
        # Get InfluxDB settings from environment variables
        self.url = os.getenv('INFLUXDB_URL')
        self.token = os.getenv('INFLUXDB_TOKEN')
        self.org = os.getenv('INFLUXDB_ORG')
        self.bucket = os.getenv('INFLUXDB_BUCKET')
        
        print("Calculator Test Initialized")
        print(f"InfluxDB URL: {self.url}")
        print(f"InfluxDB Org: {self.org}")
        print(f"InfluxDB Bucket: {self.bucket}")
        print(f"Token exists: {bool(self.token)}")
        
    def button_clicked(self, text):
        """Simulate button clicks in the calculator"""
        print(f"\nButton clicked: {text}")
        
        if text.isdigit() or text == '.':
            if self.should_clear_display:
                self.current_number = ""
                self.should_clear_display = False
            self.current_number += text
            print(f"Current number: {self.current_number}")
        
        elif text in ['÷', '×', '-', '+']:
            if self.first_number is None:
                self.first_number = float(self.current_number or '0')
            else:
                self.calculate()
            self.operation = text
            self.should_clear_display = True
            print(f"Operation set to: {self.operation}")
            print(f"First number: {self.first_number}")
        
        elif text == '=':
            if self.operation in ['sin', 'cos', 'tan']:
                try:
                    angle = float(self.current_number or '0')
                    if self.operation == 'sin':
                        result = math.sin(math.radians(angle))
                    elif self.operation == 'cos':
                        result = math.cos(math.radians(angle))
                    else:  # tan
                        result = math.tan(math.radians(angle))
                    formatted_result = f"{result:.8f}".rstrip('0').rstrip('.')
                    print(f"Result: {formatted_result}")
                    self.current_number = formatted_result
                    self.export_to_influxdb(f"{self.operation}({angle}°)", formatted_result)
                except ValueError:
                    print("Error: Invalid angle")
                    self.current_number = ""
                    self.export_to_influxdb(f"{self.operation}", "Error")
                self.should_clear_display = True
                self.operation = None
                self.first_number = None
            else:
                self.calculate()
                self.should_clear_display = True
                self.operation = None
                self.first_number = None
        
        elif text == 'C':
            print("Clear")
            self.current_number = ""
            self.first_number = None
            self.operation = None
            self.should_clear_display = False
            self.export_to_influxdb("Clear", "")
        
        elif text == '±':
            if self.current_number:
                if self.current_number[0] == '-':
                    self.current_number = self.current_number[1:]
                else:
                    self.current_number = '-' + self.current_number
                print(f"Current number: {self.current_number}")
                operation = f"{self.current_number} ±"
                self.export_to_influxdb(operation, self.current_number)
                self.should_clear_display = True
        
        elif text == '%':
            if self.current_number:
                result = str(float(self.current_number) / 100)
                self.current_number = result
                print(f"Current number: {self.current_number}")
                operation = f"{self.current_number} %"
                self.export_to_influxdb(operation, result)
                self.should_clear_display = True
                
        # Scientific calculator functions
        elif text in ['sin', 'cos', 'tan']:
            if self.current_number:
                try:
                    self.first_number = float(self.current_number)
                    self.operation = text
                    self.should_clear_display = True
                    print(f"Operation set to: {self.operation}")
                    print(f"First number: {self.first_number}")
                except ValueError:
                    print("Error: Invalid input")
                    self.current_number = ""
                    self.first_number = None
                    self.operation = None
                    self.should_clear_display = True
        
        elif text == 'π':
            self.current_number = str(math.pi)
            print(f"Current number: {self.current_number}")
            self.export_to_influxdb("π", self.current_number)
            self.should_clear_display = True
    
    def calculate(self):
        """Perform calculation based on current state"""
        if self.first_number is not None and self.operation and self.current_number:
            try:
                second_number = float(self.current_number)
                if self.operation == '+':
                    result = self.first_number + second_number
                elif self.operation == '-':
                    result = self.first_number - second_number
                elif self.operation == '×':
                    result = self.first_number * second_number
                elif self.operation == '÷':
                    if second_number != 0:
                        result = self.first_number / second_number
                    else:
                        result = "Error: Division by zero"
                        print(result)
                        self.current_number = ""
                        self.first_number = None
                        self.operation = None
                        self.should_clear_display = True
                        return
                
                # Check for overflow
                if isinstance(result, float) and (abs(result) > 1e308 or (abs(result) < 1e-308 and result != 0)):
                    result = "Error: Number too large or small"
                    print(result)
                    self.current_number = ""
                    self.first_number = None
                    self.operation = None
                    self.should_clear_display = True
                    return
                
                # Format the result
                if isinstance(result, float):
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = f"{result:.8f}".rstrip('0').rstrip('.')
                
                # Format the operation string consistently
                operation_str = f"{self.first_number} {self.operation} {second_number}"
                print(f"Operation: {operation_str}")
                print(f"Result: {result}")
                self.export_to_influxdb(operation_str, str(result))
                
                self.current_number = str(result)
                self.first_number = float(result) if result != "Error" else None
                
            except ValueError:
                print("Error: Invalid input")
                self.current_number = ""
                self.first_number = None
                self.operation = None
                self.should_clear_display = True
            except Exception as e:
                print("Error: Calculation failed")
                self.current_number = ""
                self.first_number = None
                self.operation = None
                self.should_clear_display = True
                logging.error(f"Calculation error: {str(e)}")
    
    def export_to_influxdb(self, operation, result):
        """Export operation data to InfluxDB"""
        try:
            # If no settings, silently return
            if not all([self.url, self.token, self.org, self.bucket]):
                print("InfluxDB settings not configured")
                return
            
            # Format the operation for better readability
            if operation is None:
                operation = "none"
            else:
                # Escape special characters and spaces in the operation string
                operation = operation.replace('×', 'mul').replace('÷', 'div').replace(' ', '\\ ')
                operation = operation.replace(',', '\\,').replace('=', '\\=')
            
            # Format the result - ensure it's a valid float
            try:
                result_float = float(result)
                result_str = f"{result_float}"
            except (ValueError, TypeError):
                result_str = "0"
            
            # Create line protocol with proper escaping
            timestamp = int(time.time() * 1e9)  # Current time in nanoseconds
            line = f"calculator_operation,operation={operation} result={result_str} {timestamp}"
            
            # Prepare the request
            headers = {
                'Authorization': f'Token {self.token}',
                'Content-Type': 'text/plain; charset=utf-8'
            }
            
            # Send data to InfluxDB
            response = requests.post(
                f"{self.url}/api/v2/write?org={self.org}&bucket={self.bucket}",
                headers=headers,
                data=line.encode('utf-8')
            )
            
            if response.status_code != 204:
                error_msg = f"Data not exported: {response.status_code} - {response.text}"
                print(error_msg)
                logging.error(error_msg)
            else:
                print("Data exported to InfluxDB successfully")
            
        except Exception as e:
            error_msg = f"Data not exported: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            # Don't raise the exception, just log it and continue
            pass
    
    def test_influxdb_connection(self):
        """Test the connection to InfluxDB"""
        try:
            # If no settings, return
            if not all([self.url, self.token, self.org, self.bucket]):
                print("InfluxDB settings not configured")
                return False
            
            # Construct the health check URL
            health_url = f"{self.url.rstrip('/')}/health"
            
            # Make a request to check if the server is up
            response = requests.get(health_url, headers={"Authorization": f"Token {self.token}"})
            
            if response.status_code == 200:
                print("Successfully connected to InfluxDB!")
                return True
            else:
                print(f"Failed to connect: {response.text}")
                return False
        except Exception as e:
            print(f"Error connecting to InfluxDB: {str(e)}")
            return False

def run_tests():
    """Run a series of tests on the calculator"""
    calculator = CalculatorTest()
    
    # Test InfluxDB connection
    print("\n=== Testing InfluxDB Connection ===")
    calculator.test_influxdb_connection()
    
    # Test basic arithmetic
    print("\n=== Testing Basic Arithmetic ===")
    calculator.button_clicked('5')
    calculator.button_clicked('+')
    calculator.button_clicked('3')
    calculator.button_clicked('=')
    
    # Test scientific functions
    print("\n=== Testing Scientific Functions ===")
    calculator.button_clicked('3')
    calculator.button_clicked('0')
    calculator.button_clicked('sin')
    calculator.button_clicked('=')
    
    # Test error handling
    print("\n=== Testing Error Handling ===")
    calculator.button_clicked('5')
    calculator.button_clicked('÷')
    calculator.button_clicked('0')
    calculator.button_clicked('=')
    
    # Test clear function
    print("\n=== Testing Clear Function ===")
    calculator.button_clicked('C')
    
    print("\n=== All Tests Completed ===")

def run_comprehensive_tests():
    """Run comprehensive tests covering all calculator operations"""
    calculator = CalculatorTest()
    
    print("\n=== Running Comprehensive Calculator Tests ===")
    
    # Test Case 1: Basic Addition
    print("\nTest Case 1: Addition")
    calculator.button_clicked('5')
    calculator.button_clicked('+')
    calculator.button_clicked('3')
    calculator.button_clicked('=')
    
    # Test Case 2: Subtraction with Negative Result
    print("\nTest Case 2: Subtraction")
    calculator.button_clicked('2')
    calculator.button_clicked('-')
    calculator.button_clicked('7')
    calculator.button_clicked('=')
    
    # Test Case 3: Multiplication
    print("\nTest Case 3: Multiplication")
    calculator.button_clicked('6')
    calculator.button_clicked('×')
    calculator.button_clicked('4')
    calculator.button_clicked('=')
    
    # Test Case 4: Division
    print("\nTest Case 4: Division")
    calculator.button_clicked('1')
    calculator.button_clicked('5')
    calculator.button_clicked('÷')
    calculator.button_clicked('3')
    calculator.button_clicked('=')
    
    # Test Case 5: Percentage
    print("\nTest Case 5: Percentage")
    calculator.button_clicked('5')
    calculator.button_clicked('0')
    calculator.button_clicked('%')
    
    # Test Case 6: Sine Function
    print("\nTest Case 6: Sine")
    calculator.button_clicked('3')
    calculator.button_clicked('0')
    calculator.button_clicked('sin')
    calculator.button_clicked('=')
    
    # Test Case 7: Cosine Function
    print("\nTest Case 7: Cosine")
    calculator.button_clicked('6')
    calculator.button_clicked('0')
    calculator.button_clicked('cos')
    calculator.button_clicked('=')
    
    # Test Case 8: Tangent Function
    print("\nTest Case 8: Tangent")
    calculator.button_clicked('4')
    calculator.button_clicked('5')
    calculator.button_clicked('tan')
    calculator.button_clicked('=')
    
    # Test Case 9: Pi Constant
    print("\nTest Case 9: Pi")
    calculator.button_clicked('π')
    
    # Test Case 10: Complex Operation (Pi × 2)
    print("\nTest Case 10: Complex Operation")
    calculator.button_clicked('π')
    calculator.button_clicked('×')
    calculator.button_clicked('2')
    calculator.button_clicked('=')
    
    print("\n=== Comprehensive Tests Completed ===")

def run_extended_tests():
    """Run extended tests with 25 test cases covering arithmetic and scientific operations"""
    calculator = CalculatorTest()
    
    print("\n=== Running Extended Calculator Tests ===")
    
    # Regular Arithmetic Operations (10 test cases)
    print("\n=== Regular Arithmetic Operations ===")
    
    # Test Case 1: Simple Addition
    print("\nTest Case 1: Simple Addition")
    calculator.button_clicked('1')
    calculator.button_clicked('2')
    calculator.button_clicked('+')
    calculator.button_clicked('3')
    calculator.button_clicked('4')
    calculator.button_clicked('=')
    
    # Test Case 2: Subtraction with Decimals
    print("\nTest Case 2: Decimal Subtraction")
    calculator.button_clicked('5')
    calculator.button_clicked('.')
    calculator.button_clicked('5')
    calculator.button_clicked('-')
    calculator.button_clicked('2')
    calculator.button_clicked('.')
    calculator.button_clicked('2')
    calculator.button_clicked('5')
    calculator.button_clicked('=')
    
    # Test Case 3: Multiplication with Large Numbers
    print("\nTest Case 3: Large Number Multiplication")
    calculator.button_clicked('9')
    calculator.button_clicked('9')
    calculator.button_clicked('9')
    calculator.button_clicked('×')
    calculator.button_clicked('9')
    calculator.button_clicked('9')
    calculator.button_clicked('9')
    calculator.button_clicked('=')
    
    # Test Case 4: Division with Decimals
    print("\nTest Case 4: Decimal Division")
    calculator.button_clicked('1')
    calculator.button_clicked('0')
    calculator.button_clicked('0')
    calculator.button_clicked('÷')
    calculator.button_clicked('3')
    calculator.button_clicked('.')
    calculator.button_clicked('3')
    calculator.button_clicked('3')
    calculator.button_clicked('=')
    
    # Test Case 5: Percentage Calculation
    print("\nTest Case 5: Percentage")
    calculator.button_clicked('7')
    calculator.button_clicked('5')
    calculator.button_clicked('%')
    
    # Test Case 6: Negative Number Addition
    print("\nTest Case 6: Negative Addition")
    calculator.button_clicked('-')
    calculator.button_clicked('5')
    calculator.button_clicked('0')
    calculator.button_clicked('+')
    calculator.button_clicked('2')
    calculator.button_clicked('5')
    calculator.button_clicked('=')
    
    # Test Case 7: Multiple Operations
    print("\nTest Case 7: Multiple Operations")
    calculator.button_clicked('1')
    calculator.button_clicked('0')
    calculator.button_clicked('×')
    calculator.button_clicked('2')
    calculator.button_clicked('+')
    calculator.button_clicked('5')
    calculator.button_clicked('=')
    
    # Test Case 8: Division by Small Number
    print("\nTest Case 8: Small Number Division")
    calculator.button_clicked('1')
    calculator.button_clicked('÷')
    calculator.button_clicked('0')
    calculator.button_clicked('.')
    calculator.button_clicked('1')
    calculator.button_clicked('=')
    
    # Test Case 9: Zero Multiplication
    print("\nTest Case 9: Zero Multiplication")
    calculator.button_clicked('0')
    calculator.button_clicked('×')
    calculator.button_clicked('5')
    calculator.button_clicked('0')
    calculator.button_clicked('0')
    calculator.button_clicked('=')
    
    # Test Case 10: Clear Operation
    print("\nTest Case 10: Clear")
    calculator.button_clicked('C')
    
    # Scientific Operations (15 test cases)
    print("\n=== Scientific Operations ===")
    
    # Test Case 11: Sine 30 degrees
    print("\nTest Case 11: Sine 30°")
    calculator.button_clicked('3')
    calculator.button_clicked('0')
    calculator.button_clicked('sin')
    calculator.button_clicked('=')
    
    # Test Case 12: Cosine 60 degrees
    print("\nTest Case 12: Cosine 60°")
    calculator.button_clicked('6')
    calculator.button_clicked('0')
    calculator.button_clicked('cos')
    calculator.button_clicked('=')
    
    # Test Case 13: Tangent 45 degrees
    print("\nTest Case 13: Tangent 45°")
    calculator.button_clicked('4')
    calculator.button_clicked('5')
    calculator.button_clicked('tan')
    calculator.button_clicked('=')
    
    # Test Case 14: Sine 90 degrees
    print("\nTest Case 14: Sine 90°")
    calculator.button_clicked('9')
    calculator.button_clicked('0')
    calculator.button_clicked('sin')
    calculator.button_clicked('=')
    
    # Test Case 15: Cosine 0 degrees
    print("\nTest Case 15: Cosine 0°")
    calculator.button_clicked('0')
    calculator.button_clicked('cos')
    calculator.button_clicked('=')
    
    # Test Case 16: Tangent 0 degrees
    print("\nTest Case 16: Tangent 0°")
    calculator.button_clicked('0')
    calculator.button_clicked('tan')
    calculator.button_clicked('=')
    
    # Test Case 17: Sine 180 degrees
    print("\nTest Case 17: Sine 180°")
    calculator.button_clicked('1')
    calculator.button_clicked('8')
    calculator.button_clicked('0')
    calculator.button_clicked('sin')
    calculator.button_clicked('=')
    
    # Test Case 18: Cosine 180 degrees
    print("\nTest Case 18: Cosine 180°")
    calculator.button_clicked('1')
    calculator.button_clicked('8')
    calculator.button_clicked('0')
    calculator.button_clicked('cos')
    calculator.button_clicked('=')
    
    # Test Case 19: Tangent 90 degrees
    print("\nTest Case 19: Tangent 90°")
    calculator.button_clicked('9')
    calculator.button_clicked('0')
    calculator.button_clicked('tan')
    calculator.button_clicked('=')
    
    # Test Case 20: Pi constant
    print("\nTest Case 20: Pi")
    calculator.button_clicked('π')
    
    # Test Case 21: Pi × 2
    print("\nTest Case 21: Pi × 2")
    calculator.button_clicked('π')
    calculator.button_clicked('×')
    calculator.button_clicked('2')
    calculator.button_clicked('=')
    
    # Test Case 22: Pi ÷ 2
    print("\nTest Case 22: Pi ÷ 2")
    calculator.button_clicked('π')
    calculator.button_clicked('÷')
    calculator.button_clicked('2')
    calculator.button_clicked('=')
    
    # Test Case 23: sin(π/2)
    print("\nTest Case 23: sin(π/2)")
    calculator.button_clicked('π')
    calculator.button_clicked('÷')
    calculator.button_clicked('2')
    calculator.button_clicked('sin')
    calculator.button_clicked('=')
    
    # Test Case 24: cos(π)
    print("\nTest Case 24: cos(π)")
    calculator.button_clicked('π')
    calculator.button_clicked('cos')
    calculator.button_clicked('=')
    
    # Test Case 25: tan(π/4)
    print("\nTest Case 25: tan(π/4)")
    calculator.button_clicked('π')
    calculator.button_clicked('÷')
    calculator.button_clicked('4')
    calculator.button_clicked('tan')
    calculator.button_clicked('=')
    
    print("\n=== Extended Tests Completed ===")

if __name__ == "__main__":
    run_extended_tests() 