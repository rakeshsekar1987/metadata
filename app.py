#!/usr/bin/env python3
"""
Home Loan EMI Calculator Web Application
Generates comprehensive PDF reports for loan payoff plans
Cross-platform compatible (Windows, Mac, Linux)
"""

import sys
import os

# Set matplotlib backend before importing
import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, send_file, jsonify, make_response
from datetime import datetime
import traceback
import tempfile

# Try to import flask-cors, but make it optional
try:
    from flask_cors import CORS
    HAS_CORS = True
except ImportError:
    HAS_CORS = False
    print("Warning: flask-cors not installed. Run: pip install flask-cors")

app = Flask(__name__)

# Enable CORS if available
if HAS_CORS:
    CORS(app)

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['JSON_SORT_KEYS'] = False


def parse_float(value, default=0):
    """Safely parse float from string"""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_date(date_str):
    """Validate date string format YYYY-MM"""
    if not date_str:
        return None
    try:
        datetime.strptime(date_str, '%Y-%m')
        return date_str
    except ValueError:
        return None


@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response


@app.route('/')
def index():
    """Render the main form page"""
    return render_template('index.html')


@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return make_response('', 204)
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'platform': sys.platform,
        'python_version': sys.version
    })


@app.route('/test')
def test_page():
    """Simple test page to verify server is accessible"""
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Server Test</title></head>
    <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
        <h1>✅ Server is Running!</h1>
        <p>If you can see this page, the Flask server is working correctly.</p>
        <p><a href="/" style="color: blue; font-size: 1.2em;">Go to Loan Calculator →</a></p>
        <hr>
        <h3>API Test:</h3>
        <button onclick="testAPI()" style="padding: 10px 20px; font-size: 1em; cursor: pointer;">
            Test API Connection
        </button>
        <p id="result" style="margin-top: 20px;"></p>
        <script>
            async function testAPI() {
                const resultEl = document.getElementById('result');
                resultEl.innerHTML = 'Testing...';
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    resultEl.innerHTML = '<span style="color: green;">✅ API Working! ' + JSON.stringify(data) + '</span>';
                } catch (error) {
                    resultEl.innerHTML = '<span style="color: red;">❌ Error: ' + error.message + '</span>';
                }
            }
        </script>
    </body>
    </html>
    '''


@app.route('/generate_pdf', methods=['POST', 'OPTIONS'])
def generate_pdf():
    """Generate PDF based on form inputs"""
    if request.method == 'OPTIONS':
        return make_response('', 204)
    
    try:
        # Import here to avoid startup issues
        from loan_pdf_generator import generate_loan_pdf
        
        # Get form data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Parse loan amounts
        land_loan = parse_float(data.get('land_loan'), 0)
        construction_loan = parse_float(data.get('construction_loan'), 0)
        
        # Parse dates
        loan_start_date = parse_date(data.get('loan_start_date', ''))
        construction_start_date = parse_date(data.get('construction_start_date', ''))
        
        # Parse EMI
        emi_amount = parse_float(data.get('emi_amount'), 0)
        
        # Parse interest rate
        interest_rate = parse_float(data.get('interest_rate'), 7.5)
        
        # Parse part payments
        part_payments = []
        for i in range(1, 6):
            month = data.get(f'part_payment_month_{i}', '')
            amount = parse_float(data.get(f'part_payment_amount_{i}'), 0)
            if month and amount > 0:
                part_payments.append({'month': month, 'amount': amount})
        
        # Validate inputs
        if land_loan <= 0 and construction_loan <= 0:
            return jsonify({'error': 'Please enter at least one loan amount'}), 400
        
        if not loan_start_date:
            return jsonify({'error': 'Please enter loan start date'}), 400
        
        if emi_amount <= 0:
            return jsonify({'error': 'Please enter a valid EMI amount'}), 400
        
        if interest_rate <= 0 or interest_rate > 30:
            return jsonify({'error': 'Interest rate must be between 0.01% and 30%'}), 400
        
        if construction_loan > 0 and not construction_start_date:
            return jsonify({'error': 'Construction start date required for construction loan'}), 400
        
        if construction_start_date and loan_start_date and construction_start_date < loan_start_date:
            return jsonify({'error': 'Construction date must be after loan start date'}), 400
        
        # Validate EMI
        total_loan = land_loan + construction_loan
        monthly_interest = (total_loan * interest_rate / 100) / 12
        if emi_amount <= monthly_interest:
            return jsonify({
                'error': f'EMI must be greater than monthly interest (Rs. {monthly_interest:,.0f})'
            }), 400
        
        # Generate PDF
        pdf_path = generate_loan_pdf(
            land_loan=land_loan,
            construction_loan=construction_loan,
            loan_start_date=loan_start_date,
            construction_start_date=construction_start_date or '',
            emi_amount=emi_amount,
            interest_rate=interest_rate,
            part_payments=part_payments
        )
        
        # Read and send PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=Home_Loan_Payoff_Plan.pdf'
        response.headers['Content-Length'] = len(pdf_data)
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/preview', methods=['POST', 'OPTIONS'])
def preview():
    """Preview loan calculation"""
    if request.method == 'OPTIONS':
        return make_response('', 204)
    
    try:
        # Import here to avoid startup issues
        from loan_pdf_generator import calculate_loan_schedule
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Parse inputs
        land_loan = parse_float(data.get('land_loan'), 0)
        construction_loan = parse_float(data.get('construction_loan'), 0)
        loan_start_date = parse_date(data.get('loan_start_date', ''))
        construction_start_date = parse_date(data.get('construction_start_date', ''))
        emi_amount = parse_float(data.get('emi_amount'), 0)
        interest_rate = parse_float(data.get('interest_rate'), 7.5)
        
        # Validate
        if land_loan <= 0 and construction_loan <= 0:
            return jsonify({'error': 'Please enter at least one loan amount'}), 400
        
        if not loan_start_date:
            return jsonify({'error': 'Loan start date is required'}), 400
        
        if emi_amount <= 0:
            return jsonify({'error': 'EMI amount is required'}), 400
        
        # Validate EMI
        total_loan = land_loan + construction_loan
        monthly_interest = (total_loan * interest_rate / 100) / 12
        if emi_amount <= monthly_interest:
            return jsonify({
                'error': f'EMI must be greater than monthly interest (Rs. {monthly_interest:,.0f})'
            }), 400
        
        part_payments = []
        for i in range(1, 6):
            month = data.get(f'part_payment_month_{i}', '')
            amount = parse_float(data.get(f'part_payment_amount_{i}'), 0)
            if month and amount > 0:
                part_payments.append({'month': month, 'amount': amount})
        
        # Calculate
        result = calculate_loan_schedule(
            land_loan=land_loan,
            construction_loan=construction_loan,
            loan_start_date=loan_start_date,
            construction_start_date=construction_start_date or '',
            emi_amount=emi_amount,
            interest_rate=interest_rate,
            part_payments=part_payments
        )
        
        return jsonify({
            'total_principal': result['total_principal'],
            'total_interest': result['total_interest'],
            'total_paid': result['total_paid'],
            'total_emi': result['total_emi'],
            'total_prepayments': result['total_prepayments'],
            'tenure': result['tenure'],
            'tenure_months': result['tenure_months'],
            'closure_date': result['closure_date'],
            'start_date': result['start_date']
        })
        
    except Exception as e:
        print(f"Error in preview: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


def check_dependencies():
    """Check if all dependencies are installed"""
    missing = []
    
    try:
        import flask
    except ImportError:
        missing.append('flask')
    
    try:
        import reportlab
    except ImportError:
        missing.append('reportlab')
    
    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')
    
    try:
        from dateutil.relativedelta import relativedelta
    except ImportError:
        missing.append('python-dateutil')
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"Run: pip install {' '.join(missing)}")
        return False
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("  Home Loan EMI Calculator")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        sys.exit(1)
    
    print(f"\n✅ All dependencies installed")
    print(f"📍 Platform: {sys.platform}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    port = int(os.environ.get('PORT', 4999))
    
    print(f"\n🚀 Starting server...")
    print(f"\n" + "=" * 60)
    print(f"  Open your browser and go to:")
    print(f"  👉 http://localhost:{port}")
    print(f"  👉 http://127.0.0.1:{port}")
    print(f"\n  Test page: http://localhost:{port}/test")
    print("=" * 60)
    print(f"\nPress Ctrl+C to stop the server\n")
    
    try:
        app.run(
            host='127.0.0.1',  # Use 127.0.0.1 instead of 0.0.0.0 for Mac compatibility
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid issues
        )
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n❌ Port {port} is already in use!")
            print(f"   Try: kill $(lsof -t -i:{port})")
            print(f"   Or use a different port: PORT=5001 python3 app.py")
        else:
            raise
