# Calculator with InfluxDB Integration

A modern calculator application with InfluxDB integration for logging operations and metrics.

## Features

- Basic arithmetic operations
- Scientific calculator functions
- InfluxDB integration for operation logging
- Configurable settings
- Secure credential management

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/calculator.git
cd calculator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your actual credentials.

## Security Notes

- Never commit the `.env` file or any files containing real credentials
- Keep your InfluxDB token secure
- Use environment variables for sensitive information
- Regularly rotate your tokens and credentials

## Usage

Run the calculator:
```bash
python calculator.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
