import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
from datetime import datetime
import json
import os
import csv
import sqlite3
from tkinter import filedialog
import requests
import urllib.parse
import logging
import time
from dotenv import load_dotenv

# Set up logging - only log errors to file
logging.basicConfig(
    filename='calculator_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Disable other loggers
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Calculator")
        self.root.geometry("400x600")
        self.root.configure(bg="#2b2b2b")  # Reverted to dark gray
        
        # Configure styles
        style = ttk.Style()
        style.configure("Display.TEntry",
                       padding=20,
                       fieldbackground="#1a1a1a",  # Reverted to darker gray
                       foreground="#ffffff",        # White text
                       font=("Arial", 24, "bold"))  # Bold font for better visibility
        
        # Calculator state
        self.current_number = ""
        self.first_number = None
        self.operation = None
        self.should_clear_display = False
        self.scientific_mode = False
        
        # Logging setup
        self.log_file = "calculator_log.json"
        self.max_log_entries = 25
        self.load_log()
        
        # InfluxDB settings - try to get from environment variables first
        self.influxdb_url = os.environ.get("INFLUXDB_URL", "")
        self.influxdb_token = os.environ.get("INFLUXDB_TOKEN", "")
        self.influxdb_org = os.environ.get("INFLUXDB_ORG", "")
        self.influxdb_bucket = os.environ.get("INFLUXDB_BUCKET", "")
        
        # If environment variables are not set, try to load from file
        if not all([self.influxdb_url, self.influxdb_token, self.influxdb_org, self.influxdb_bucket]):
            self.load_influxdb_settings()
        
        # Create display
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            root,
            textvariable=self.display_var,
            font=('Arial', 20),
            justify='right',
            bd=5,
            fg='black',  # Set text color to black
            bg='white'   # Set background to white for better contrast
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky='nsew')
        
        # Create toggle button for scientific mode
        self.toggle_btn = tk.Button(root, text="Scientific", font=("Arial", 12),
                                  bg="#4b4b4b", fg="white",
                                  relief="flat", borderwidth=0,
                                  command=self.toggle_mode)
        self.toggle_btn.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        # Create export log button
        self.export_btn = tk.Button(root, text="Export Log", font=("Arial", 12),
                                  bg="#4b4b4b", fg="white",
                                  relief="flat", borderwidth=0,
                                  command=self.export_log)
        self.export_btn.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        # Create InfluxDB settings button
        self.influxdb_btn = tk.Button(root, text="InfluxDB Settings", font=("Arial", 12),
                                    bg="#4b4b4b", fg="white",
                                    relief="flat", borderwidth=0,
                                    command=self.show_influxdb_settings)
        self.influxdb_btn.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        # Button layout for standard mode
        self.standard_buttons = [
            ('C', '#a5a5a5'), ('±', '#a5a5a5'), ('%', '#a5a5a5'), ('÷', '#ff9500'),
            ('7', '#4b4b4b'), ('8', '#4b4b4b'), ('9', '#4b4b4b'), ('×', '#ff9500'),
            ('4', '#4b4b4b'), ('5', '#4b4b4b'), ('6', '#4b4b4b'), ('-', '#ff9500'),
            ('1', '#4b4b4b'), ('2', '#4b4b4b'), ('3', '#4b4b4b'), ('+', '#ff9500'),
            ('0', '#4b4b4b'), ('.', '#4b4b4b'), ('=', '#ff9500')
        ]
        
        # Button layout for scientific mode
        self.scientific_buttons = [
            ('C', '#a5a5a5'), ('±', '#a5a5a5'), ('%', '#a5a5a5'), ('÷', '#ff9500'),
            ('sin', '#4b4b4b'), ('cos', '#4b4b4b'), ('tan', '#4b4b4b'), ('π', '#ff9500'),
            ('7', '#4b4b4b'), ('8', '#4b4b4b'), ('9', '#4b4b4b'), ('×', '#ff9500'),
            ('4', '#4b4b4b'), ('5', '#4b4b4b'), ('6', '#4b4b4b'), ('-', '#ff9500'),
            ('1', '#4b4b4b'), ('2', '#4b4b4b'), ('3', '#4b4b4b'), ('+', '#ff9500'),
            ('0', '#4b4b4b'), ('.', '#4b4b4b'), ('=', '#ff9500')
        ]
        
        # Create buttons container
        self.buttons_frame = tk.Frame(root, bg="#2b2b2b")
        self.buttons_frame.grid(row=4, column=0, columnspan=4, sticky="nsew")
        
        # Configure grid weights
        for i in range(7):  # Increased for scientific mode
            root.grid_rowconfigure(i, weight=1)
        for i in range(4):
            root.grid_columnconfigure(i, weight=1)
        
        # Create buttons
        self.create_buttons()
        
    def load_log(self):
        """Load the log from file or create a new one if it doesn't exist"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.log = json.load(f)
            except:
                self.log = []
        else:
            self.log = []
    
    def save_log(self):
        """Save the log to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.log, f)
    
    def add_to_log(self, operation, result):
        """Add an operation to the log and maintain only the last 25 entries"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the operation string
        operation = str(operation).strip()
        operation = operation.replace('×', '*')
        operation = operation.replace('÷', '/')
        
        # Format the result
        if result:
            result = str(result).strip()
            try:
                # Try to convert to float and format
                result = f"{float(result):g}"
            except ValueError:
                # If not a number, keep as is
                pass
        else:
            result = "0"
        
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "result": result
        }
        
        self.log.append(log_entry)
        
        # Keep only the last max_log_entries
        if len(self.log) > self.max_log_entries:
            self.log = self.log[-self.max_log_entries:]
        
        self.save_log()
    
    def load_influxdb_settings(self):
        """Load InfluxDB settings from file if they exist"""
        settings_file = "influxdb_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.influxdb_url = settings.get("url", "")
                    self.influxdb_token = settings.get("token", "")
                    self.influxdb_org = settings.get("org", "")
                    self.influxdb_bucket = settings.get("bucket", "")
            except:
                pass
    
    def save_influxdb_settings(self):
        """Save InfluxDB settings to file"""
        settings = {
            "url": self.influxdb_url,
            "token": self.influxdb_token,
            "org": self.influxdb_org,
            "bucket": self.influxdb_bucket
        }
        with open("influxdb_settings.json", 'w') as f:
            json.dump(settings, f)
    
    def show_influxdb_settings(self):
        """Show dialog to configure InfluxDB settings"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("InfluxDB Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg="#2b2b2b")
        
        # Center the window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create and pack widgets
        tk.Label(settings_window, text="InfluxDB Configuration", 
                bg="#2b2b2b", fg="white", font=("Arial", 14, "bold")).pack(pady=10)
        
        # URL
        url_frame = tk.Frame(settings_window, bg="#2b2b2b")
        url_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(url_frame, text="URL:", bg="#2b2b2b", fg="white", width=10).pack(side=tk.LEFT)
        url_entry = tk.Entry(url_frame, width=30)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        url_entry.insert(0, self.influxdb_url)
        
        # Token
        token_frame = tk.Frame(settings_window, bg="#2b2b2b")
        token_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(token_frame, text="Token:", bg="#2b2b2b", fg="white", width=10).pack(side=tk.LEFT)
        token_entry = tk.Entry(token_frame, width=30, show="*")
        token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        token_entry.insert(0, self.influxdb_token)
        
        # Organization
        org_frame = tk.Frame(settings_window, bg="#2b2b2b")
        org_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(org_frame, text="Org:", bg="#2b2b2b", fg="white", width=10).pack(side=tk.LEFT)
        org_entry = tk.Entry(org_frame, width=30)
        org_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        org_entry.insert(0, self.influxdb_org)
        
        # Bucket
        bucket_frame = tk.Frame(settings_window, bg="#2b2b2b")
        bucket_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(bucket_frame, text="Bucket:", bg="#2b2b2b", fg="white", width=10).pack(side=tk.LEFT)
        bucket_entry = tk.Entry(bucket_frame, width=30)
        bucket_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        bucket_entry.insert(0, self.influxdb_bucket)
        
        # Test connection button
        tk.Button(settings_window, text="Test Connection", font=("Arial", 12),
                 bg="#ff9500", fg="white", relief="flat", borderwidth=0,
                 command=lambda: self.test_influxdb_connection(
                     url_entry.get(), token_entry.get(), org_entry.get(), bucket_entry.get()
                 )).pack(pady=10)
        
        # Save button
        tk.Button(settings_window, text="Save Settings", font=("Arial", 12),
                 bg="#4b4b4b", fg="white", relief="flat", borderwidth=0,
                 command=lambda: self.save_influxdb_settings_from_dialog(
                     settings_window, url_entry.get(), token_entry.get(), 
                     org_entry.get(), bucket_entry.get()
                 )).pack(pady=5)
    
    def test_influxdb_connection(self, url, token, org, bucket):
        """Test the connection to InfluxDB"""
        try:
            # Construct the health check URL
            health_url = f"{url.rstrip('/')}/health"
            
            # Make a request to check if the server is up
            response = requests.get(health_url, headers={"Authorization": f"Token {token}"})
            
            if response.status_code == 200:
                messagebox.showinfo("Connection Test", "Successfully connected to InfluxDB!")
            else:
                messagebox.showerror("Connection Test", f"Failed to connect: {response.text}")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Error connecting to InfluxDB: {str(e)}")
    
    def save_influxdb_settings_from_dialog(self, window, url, token, org, bucket):
        """Save InfluxDB settings from the dialog and close it"""
        self.influxdb_url = url
        self.influxdb_token = token
        self.influxdb_org = org
        self.influxdb_bucket = bucket
        
        self.save_influxdb_settings()
        window.destroy()
        messagebox.showinfo("Settings Saved", "InfluxDB settings have been saved.")
    
    def export_to_influxdb(self, operation, result):
        """Export operation data to InfluxDB"""
        try:
            # Force reload environment variables
            load_dotenv(override=True)
            
            # Get InfluxDB settings from environment variables
            url = os.getenv('INFLUXDB_URL')
            token = os.getenv('INFLUXDB_TOKEN')
            org = os.getenv('INFLUXDB_ORG')
            bucket = os.getenv('INFLUXDB_BUCKET')
            
            # If no settings, silently return
            if not all([url, token, org, bucket]):
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
                'Authorization': f'Token {token}',
                'Content-Type': 'text/plain; charset=utf-8'
            }
            
            # Send data to InfluxDB
            response = requests.post(
                f"{url}/api/v2/write?org={org}&bucket={bucket}",
                headers=headers,
                data=line.encode('utf-8')
            )
            
            if response.status_code != 204:
                error_msg = f"Data not exported: {response.status_code} - {response.text}"
                logging.error(error_msg)
            
        except Exception as e:
            error_msg = f"Data not exported: {str(e)}"
            logging.error(error_msg)
            # Don't raise the exception, just log it and continue
            pass
    
    def export_log(self):
        """Export the log in various formats for metrics and searching"""
        if not self.log:
            messagebox.showinfo("Export Log", "No log entries to export.")
            return
            
        # Create a dialog to select export format
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Log")
        export_window.geometry("300x250")
        export_window.configure(bg="#2b2b2b")
        
        # Center the window
        export_window.transient(self.root)
        export_window.grab_set()
        
        # Create format selection
        format_var = tk.StringVar(value="json")
        
        tk.Label(export_window, text="Select Export Format:", 
                bg="#2b2b2b", fg="white", font=("Arial", 12)).pack(pady=10)
        
        formats_frame = tk.Frame(export_window, bg="#2b2b2b")
        formats_frame.pack(pady=10)
        
        tk.Radiobutton(formats_frame, text="JSON", variable=format_var, value="json",
                      bg="#2b2b2b", fg="white", selectcolor="#4b4b4b", 
                      activebackground="#2b2b2b", activeforeground="white").pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(formats_frame, text="CSV", variable=format_var, value="csv",
                      bg="#2b2b2b", fg="white", selectcolor="#4b4b4b", 
                      activebackground="#2b2b2b", activeforeground="white").pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(formats_frame, text="SQLite", variable=format_var, value="sqlite",
                      bg="#2b2b2b", fg="white", selectcolor="#4b4b4b", 
                      activebackground="#2b2b2b", activeforeground="white").pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(formats_frame, text="InfluxDB", variable=format_var, value="influxdb",
                      bg="#2b2b2b", fg="white", selectcolor="#4b4b4b", 
                      activebackground="#2b2b2b", activeforeground="white").pack(side=tk.LEFT, padx=10)
        
        # Export button
        tk.Button(export_window, text="Export", font=("Arial", 12),
                 bg="#ff9500", fg="white", relief="flat", borderwidth=0,
                 command=lambda: self.do_export(format_var.get(), export_window)).pack(pady=20)
    
    def do_export(self, format_type, export_window):
        """Perform the actual export based on selected format"""
        if format_type == "influxdb":
            self.export_to_influxdb(self.operation, self.current_number)
            export_window.destroy()
            return
            
        # Get save location from user
        file_types = {
            "json": [("JSON files", "*.json")],
            "csv": [("CSV files", "*.csv")],
            "sqlite": [("SQLite database", "*.db")]
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=file_types[format_type][0][1],
            filetypes=file_types[format_type],
            title="Save Log As"
        )
        
        if not file_path:
            return
            
        try:
            if format_type == "json":
                self.export_json(file_path)
            elif format_type == "csv":
                self.export_csv(file_path)
            elif format_type == "sqlite":
                self.export_sqlite(file_path)
                
            messagebox.showinfo("Export Successful", f"Log exported to {file_path}")
            export_window.destroy()
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting log: {str(e)}")
    
    def export_json(self, file_path):
        """Export log as JSON"""
        with open(file_path, 'w') as f:
            json.dump(self.log, f, indent=2)
    
    def export_csv(self, file_path):
        """Export log as CSV"""
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "operation", "result"])
            writer.writeheader()
            writer.writerows(self.log)
    
    def export_sqlite(self, file_path):
        """Export log as SQLite database"""
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculator_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operation TEXT,
            result TEXT
        )
        ''')
        
        # Insert data
        for entry in self.log:
            cursor.execute('''
            INSERT INTO calculator_log (timestamp, operation, result)
            VALUES (?, ?, ?)
            ''', (entry["timestamp"], entry["operation"], entry["result"]))
        
        conn.commit()
        conn.close()
        
    def create_buttons(self):
        # Clear existing buttons
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
            
        # Configure grid weights for buttons frame
        for i in range(7 if self.scientific_mode else 5):
            self.buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1)
            
        # Select button layout based on mode
        buttons = self.scientific_buttons if self.scientific_mode else self.standard_buttons
        
        # Create buttons
        row = 0
        col = 0
        for (text, color) in buttons:
            if text == '0':
                # Make 0 button span 2 columns
                btn = tk.Button(self.buttons_frame, text=text, font=("Arial", 18),
                              bg=color, fg="white" if color != "#a5a5a5" else "black",
                              relief="flat", borderwidth=0)
                btn.grid(row=row, column=col, columnspan=2, padx=5, pady=5, sticky="nsew")
                col += 2
            else:
                btn = tk.Button(self.buttons_frame, text=text, font=("Arial", 18),
                              bg=color, fg="white" if color != "#a5a5a5" else "black",
                              relief="flat", borderwidth=0)
                btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                col += 1
            
            # Bind hover effects
            btn.bind("<Enter>", lambda e, b=btn, c=color: self.on_hover(b, c))
            btn.bind("<Leave>", lambda e, b=btn, c=color: self.on_leave(b, c))
            btn.bind("<Button-1>", lambda e, t=text: self.button_clicked(t))
            
            if col > 3:
                col = 0
                row += 1
    
    def toggle_mode(self):
        self.scientific_mode = not self.scientific_mode
        self.toggle_btn.config(text="Standard" if self.scientific_mode else "Scientific")
        self.create_buttons()
        self.add_to_log(f"Mode changed to {'Scientific' if self.scientific_mode else 'Standard'}", "")

    def on_hover(self, button, original_color):
        # Lighten the color on hover
        rgb = tuple(int(original_color[1:][i:i+2], 16) for i in (0, 2, 4))
        lighter_rgb = tuple(min(255, c + 20) for c in rgb)
        lighter_color = f"#{lighter_rgb[0]:02x}{lighter_rgb[1]:02x}{lighter_rgb[2]:02x}"
        button.configure(bg=lighter_color)

    def on_leave(self, button, original_color):
        button.configure(bg=original_color)

    def button_clicked(self, text):
        if text.isdigit() or text == '.':
            if self.should_clear_display:
                self.current_number = ""
                self.should_clear_display = False
            self.current_number += text
            self.display_var.set(self.current_number)
        
        elif text in ['÷', '×', '-', '+']:
            if self.first_number is None:
                self.first_number = float(self.current_number or '0')
            else:
                self.calculate()
            self.operation = text
            self.should_clear_display = True
        
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
                    self.display_var.set(formatted_result)
                    self.current_number = formatted_result
                    self.add_to_log(f"{self.operation}({angle}°)", formatted_result)
                    self.export_to_influxdb(f"{self.operation}({angle}°)", formatted_result)
                except ValueError:
                    self.display_var.set("Error: Invalid angle")
                    self.current_number = ""
                    self.add_to_log(f"{self.operation}", "Error")
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
            self.display_var.set("")
            self.current_number = ""
            self.first_number = None
            self.operation = None
            self.should_clear_display = False
            self.add_to_log("Clear", "")
            self.export_to_influxdb("Clear", "")
        
        elif text == '±':
            if self.current_number:
                if self.current_number[0] == '-':
                    self.current_number = self.current_number[1:]
                else:
                    self.current_number = '-' + self.current_number
                self.display_var.set(self.current_number)
                operation = f"{self.current_number} ±"
                self.add_to_log(operation, self.current_number)
                self.export_to_influxdb(operation, self.current_number)
                self.should_clear_display = True
        
        elif text == '%':
            if self.current_number:
                result = str(float(self.current_number) / 100)
                self.current_number = result
                self.display_var.set(self.current_number)
                operation = f"{self.current_number} %"
                self.add_to_log(operation, result)
                self.export_to_influxdb(operation, result)
                self.should_clear_display = True
                
        # Scientific calculator functions
        elif text in ['sin', 'cos', 'tan']:
            if self.current_number:
                try:
                    self.first_number = float(self.current_number)
                    self.operation = text
                    self.should_clear_display = True
                except ValueError:
                    self.display_var.set("Error: Invalid input")
                    self.current_number = ""
                    self.first_number = None
                    self.operation = None
                    self.should_clear_display = True
        
        elif text == 'π':
            self.current_number = str(math.pi)
            self.display_var.set(self.current_number)
            self.add_to_log("π", self.current_number)
            self.export_to_influxdb("π", self.current_number)
            self.should_clear_display = True

    def calculate(self):
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
                        self.display_var.set(result)
                        self.current_number = ""
                        self.first_number = None
                        self.operation = None
                        self.should_clear_display = True
                        return
                
                # Check for overflow
                if isinstance(result, float) and (abs(result) > 1e308 or (abs(result) < 1e-308 and result != 0)):
                    result = "Error: Number too large or small"
                    self.display_var.set(result)
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
                self.add_to_log(operation_str, str(result))
                self.export_to_influxdb(operation_str, str(result))
                
                self.display_var.set(str(result))
                self.current_number = str(result)
                self.first_number = float(result) if result != "Error" else None
                
            except ValueError:
                self.display_var.set("Error: Invalid input")
                self.current_number = ""
                self.first_number = None
                self.operation = None
                self.should_clear_display = True
            except Exception as e:
                self.display_var.set("Error: Calculation failed")
                self.current_number = ""
                self.first_number = None
                self.operation = None
                self.should_clear_display = True
                logging.error(f"Calculation error: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()