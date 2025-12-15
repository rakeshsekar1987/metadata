#!/usr/bin/env python3
"""
Home Loan EMI Calculator Web Application
Generates comprehensive PDF reports for loan payoff plans
"""

from flask import Flask, render_template, request, send_file, jsonify, make_response
from flask_cors import CORS
from loan_pdf_generator import generate_loan_pdf, calculate_loan_schedule
from datetime import datetime
import os
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
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
    """Add headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/')
def index():
    """Render the main form page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})


@app.route('/generate_pdf', methods=['POST', 'OPTIONS'])
def generate_pdf():
    """Generate PDF based on form inputs"""
    if request.method == 'OPTIONS':
        return make_response('', 204)
    
    try:
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
        
        # Parse part payments (up to 5)
        part_payments = []
        for i in range(1, 6):
            month = data.get(f'part_payment_month_{i}', '')
            amount = parse_float(data.get(f'part_payment_amount_{i}'), 0)
            if month and amount > 0:
                part_payments.append({
                    'month': month,
                    'amount': amount
                })
        
        # Validate inputs
        if land_loan <= 0 and construction_loan <= 0:
            return jsonify({'error': 'Please enter at least one loan amount (Land or Construction loan)'}), 400
        
        if not loan_start_date:
            return jsonify({'error': 'Please enter a valid loan start date (format: YYYY-MM)'}), 400
        
        if emi_amount <= 0:
            return jsonify({'error': 'Please enter a valid EMI amount greater than 0'}), 400
        
        if interest_rate <= 0 or interest_rate > 30:
            return jsonify({'error': 'Interest rate must be between 0.01% and 30%'}), 400
        
        # Validate construction date if construction loan exists
        if construction_loan > 0 and not construction_start_date:
            return jsonify({'error': 'Construction start date is required when construction loan is specified'}), 400
        
        # Validate construction date is after loan start
        if construction_start_date and loan_start_date:
            if construction_start_date < loan_start_date:
                return jsonify({'error': 'Construction start date must be on or after loan start date'}), 400
        
        # Calculate monthly interest to validate EMI
        total_loan = land_loan + construction_loan
        monthly_interest = (total_loan * interest_rate / 100) / 12
        if emi_amount <= monthly_interest:
            return jsonify({
                'error': f'EMI (Rs. {emi_amount:,.0f}) must be greater than monthly interest (Rs. {monthly_interest:,.0f}) to reduce principal'
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
        
        # Read the PDF file and send it
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=Home_Loan_Payoff_Plan.pdf'
        response.headers['Content-Length'] = len(pdf_data)
        return response
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        print(f"Error generating PDF: {traceback.format_exc()}")
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500


@app.route('/preview', methods=['POST', 'OPTIONS'])
def preview():
    """Preview loan calculation without generating PDF"""
    if request.method == 'OPTIONS':
        return make_response('', 204)
    
    try:
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
        
        # Validate required fields
        if land_loan <= 0 and construction_loan <= 0:
            return jsonify({'error': 'Please enter at least one loan amount'}), 400
        
        if not loan_start_date:
            return jsonify({'error': 'Loan start date is required'}), 400
        
        if emi_amount <= 0:
            return jsonify({'error': 'EMI amount is required'}), 400
        
        # Validate EMI > monthly interest
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
                part_payments.append({
                    'month': month,
                    'amount': amount
                })
        
        # Calculate schedule
        result = calculate_loan_schedule(
            land_loan=land_loan,
            construction_loan=construction_loan,
            loan_start_date=loan_start_date,
            construction_start_date=construction_start_date or '',
            emi_amount=emi_amount,
            interest_rate=interest_rate,
            part_payments=part_payments
        )
        
        # Return only summary data (not full monthly schedule to keep response small)
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
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return jsonify({'error': f'Calculation error: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in preview: {traceback.format_exc()}")
        return jsonify({'error': f'Error calculating: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Home Loan EMI Calculator")
    print("=" * 50)
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
