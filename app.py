#!/usr/bin/env python3
"""
Home Loan EMI Calculator Web Application
Generates comprehensive PDF reports for loan payoff plans
"""

from flask import Flask, render_template, request, send_file, jsonify
from loan_pdf_generator import generate_loan_pdf, calculate_loan_schedule
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main form page"""
    return render_template('index.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    """Generate PDF based on form inputs"""
    try:
        # Get form data
        data = request.get_json()
        
        # Parse loan amounts
        land_loan = float(data.get('land_loan', 0) or 0)
        construction_loan = float(data.get('construction_loan', 0) or 0)
        
        # Parse dates
        loan_start_date = data.get('loan_start_date', '')
        construction_start_date = data.get('construction_start_date', '')
        
        # Parse EMI
        emi_amount = float(data.get('emi_amount', 0) or 0)
        
        # Parse interest rate
        interest_rate = float(data.get('interest_rate', 7.5) or 7.5)
        
        # Parse part payments (up to 5)
        part_payments = []
        for i in range(1, 6):
            month = data.get(f'part_payment_month_{i}', '')
            amount = data.get(f'part_payment_amount_{i}', 0)
            if month and amount:
                part_payments.append({
                    'month': month,
                    'amount': float(amount)
                })
        
        # Validate inputs
        if land_loan <= 0 and construction_loan <= 0:
            return jsonify({'error': 'Please enter at least one loan amount'}), 400
        
        if not loan_start_date:
            return jsonify({'error': 'Please enter loan start date'}), 400
        
        if emi_amount <= 0:
            return jsonify({'error': 'Please enter a valid EMI amount'}), 400
        
        # Generate PDF
        pdf_path = generate_loan_pdf(
            land_loan=land_loan,
            construction_loan=construction_loan,
            loan_start_date=loan_start_date,
            construction_start_date=construction_start_date,
            emi_amount=emi_amount,
            interest_rate=interest_rate,
            part_payments=part_payments
        )
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Home_Loan_Payoff_Plan.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['POST'])
def preview():
    """Preview loan calculation without generating PDF"""
    try:
        data = request.get_json()
        
        # Parse inputs
        land_loan = float(data.get('land_loan', 0) or 0)
        construction_loan = float(data.get('construction_loan', 0) or 0)
        loan_start_date = data.get('loan_start_date', '')
        construction_start_date = data.get('construction_start_date', '')
        emi_amount = float(data.get('emi_amount', 0) or 0)
        interest_rate = float(data.get('interest_rate', 7.5) or 7.5)
        
        part_payments = []
        for i in range(1, 6):
            month = data.get(f'part_payment_month_{i}', '')
            amount = data.get(f'part_payment_amount_{i}', 0)
            if month and amount:
                part_payments.append({
                    'month': month,
                    'amount': float(amount)
                })
        
        # Calculate schedule
        result = calculate_loan_schedule(
            land_loan=land_loan,
            construction_loan=construction_loan,
            loan_start_date=loan_start_date,
            construction_start_date=construction_start_date,
            emi_amount=emi_amount,
            interest_rate=interest_rate,
            part_payments=part_payments
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
