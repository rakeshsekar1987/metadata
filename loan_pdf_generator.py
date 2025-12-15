#!/usr/bin/env python3
"""
Loan PDF Generator Module
Calculates loan amortization schedule and generates comprehensive PDF reports
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
import tempfile
import os


def format_indian_number(num):
    """Format number in Indian style (e.g., 10,00,000 for ten lakhs)"""
    if num == 0:
        return "0"
    
    num = int(round(num))
    is_negative = num < 0
    num = abs(num)
    
    s = str(num)
    if len(s) <= 3:
        result = s
    else:
        result = s[-3:]
        s = s[:-3]
        while s:
            result = s[-2:] + ',' + result
            s = s[:-2]
    
    return '-' + result if is_negative else result


def format_rupees(num):
    """Format as Indian Rupees with Rs. symbol"""
    return f"Rs. {format_indian_number(num)}"


def parse_month_year(date_str):
    """Parse YYYY-MM format to datetime"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m')
    except (ValueError, TypeError):
        return None


def get_month_name(dt):
    """Get month name with year"""
    return dt.strftime('%b %Y')


MONTH_NAME_TO_NUM = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12
}


def calculate_loan_schedule(land_loan, construction_loan, loan_start_date, 
                            construction_start_date, emi_amount, interest_rate, part_payments):
    """Calculate complete loan amortization schedule"""
    
    # Parse dates
    start_date = parse_month_year(loan_start_date)
    construction_date = parse_month_year(construction_start_date)
    
    if not start_date:
        raise ValueError("Invalid loan start date")
    
    # Monthly interest rate
    monthly_rate = interest_rate / 100 / 12
    
    # Initialize
    monthly_schedule = []
    yearly_summary = {}
    
    current_date = start_date
    opening_balance = 0
    month_number = 0
    total_interest = 0
    total_emi = 0
    total_prepay = 0
    total_principal = land_loan + construction_loan
    
    # Part payment months as numbers
    prepay_schedule = {}
    for pp in part_payments:
        month_num = MONTH_NAME_TO_NUM.get(pp['month'], 0)
        if month_num > 0:
            if month_num not in prepay_schedule:
                prepay_schedule[month_num] = 0
            prepay_schedule[month_num] += pp['amount']
    
    # Calculate until loan is paid off or max 360 months
    max_months = 360
    
    while month_number < max_months:
        month_number += 1
        month_name = get_month_name(current_date)
        year = current_date.year
        month_num = current_date.month
        
        # Disbursal
        disbursal = 0
        if month_number == 1:
            disbursal = land_loan
        if construction_date and current_date.year == construction_date.year and current_date.month == construction_date.month:
            disbursal += construction_loan
        
        # Initialize year summary if needed
        if year not in yearly_summary:
            yearly_summary[year] = {
                'opening': opening_balance,
                'closing': 0,
                'interest': 0,
                'emi': 0,
                'prepay': 0,
                'disbursal': 0
            }
        
        # Interest for the month (on opening + disbursal)
        balance_for_interest = opening_balance + disbursal
        interest = balance_for_interest * monthly_rate
        
        # EMI (starts from second month)
        emi = 0
        if month_number > 1:
            emi = min(emi_amount, opening_balance + disbursal + interest)
        
        # Prepayment (only if there's balance remaining after EMI)
        prepay = 0
        if month_num in prepay_schedule and month_number > 1:
            remaining_after_emi = opening_balance + disbursal + interest - emi
            if remaining_after_emi > 0:
                prepay = min(prepay_schedule[month_num], remaining_after_emi)
        
        # Closing balance
        closing_balance = opening_balance + disbursal + interest - emi - prepay
        
        # Handle final month adjustment
        if closing_balance < 0:
            closing_balance = 0
        if closing_balance < emi and closing_balance > 0 and month_number > 1:
            # This might be the last month
            pass
        
        # Record monthly data
        monthly_schedule.append({
            'month_number': month_number,
            'month_name': month_name,
            'opening': opening_balance,
            'interest': interest,
            'disbursal': disbursal,
            'emi': emi,
            'prepay': prepay,
            'closing': closing_balance
        })
        
        # Update yearly summary
        yearly_summary[year]['interest'] += interest
        yearly_summary[year]['emi'] += emi
        yearly_summary[year]['prepay'] += prepay
        yearly_summary[year]['disbursal'] += disbursal
        yearly_summary[year]['closing'] = closing_balance
        
        # Update totals
        total_interest += interest
        total_emi += emi
        total_prepay += prepay
        
        # Check if loan is closed
        if closing_balance <= 0 and month_number > 1:
            break
        
        # Move to next month
        opening_balance = closing_balance
        current_date = current_date + relativedelta(months=1)
    
    # Calculate tenure
    years = month_number // 12
    months = month_number % 12
    tenure_str = f"{years} years {months} months" if years > 0 else f"{months} months"
    
    closure_date = start_date + relativedelta(months=month_number-1)
    
    return {
        'monthly_schedule': monthly_schedule,
        'yearly_summary': yearly_summary,
        'total_principal': total_principal,
        'total_interest': round(total_interest),
        'total_paid': round(total_emi + total_prepay),
        'total_emi': round(total_emi),
        'total_prepayments': round(total_prepay),
        'tenure': tenure_str,
        'tenure_months': month_number,
        'closure_date': get_month_name(closure_date),
        'start_date': get_month_name(start_date),
        'construction_date': get_month_name(construction_date) if construction_date else None,
        'land_loan': land_loan,
        'construction_loan': construction_loan,
        'emi_amount': emi_amount,
        'interest_rate': interest_rate,
        'part_payments': part_payments
    }


def create_styles():
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#303f9f'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1565c0'),
        spaceBefore=20,
        spaceAfter=15,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='SubsectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1976d2'),
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#37474f'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=16
    ))
    
    styles.add(ParagraphStyle(
        name='KeyMetric',
        parent=styles['Normal'],
        fontSize=24,
        textColor=colors.HexColor('#2e7d32'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5
    ))
    
    styles.add(ParagraphStyle(
        name='MetricLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#616161'),
        alignment=TA_CENTER,
        spaceAfter=15
    ))
    
    return styles


def create_balance_chart(monthly_schedule, land_loan, construction_loan, construction_date):
    """Create outstanding balance trajectory chart"""
    months = [d['month_number'] for d in monthly_schedule]
    closing_balance = [d['closing'] / 10000000 for d in monthly_schedule]  # In Crores
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.fill_between(months, closing_balance, alpha=0.3, color='#1976d2')
    ax.plot(months, closing_balance, color='#1565c0', linewidth=2.5, marker='o', 
            markersize=3, markerfacecolor='#0d47a1')
    
    # Mark disbursal points
    for i, d in enumerate(monthly_schedule):
        if d['disbursal'] > 0:
            ax.axvline(x=d['month_number'], color='#4caf50', linestyle='--', alpha=0.7, linewidth=1.5)
            label = f"Rs. {format_indian_number(d['disbursal'])}\n({d['month_name']})"
            y_pos = d['closing'] / 10000000 if d['closing'] > 0 else land_loan / 10000000
            ax.annotate(label, xy=(d['month_number'], y_pos), 
                       xytext=(d['month_number'] + 3, y_pos + 0.2),
                       fontsize=8, color='#2e7d32', fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color='#4caf50'))
    
    # Mark closure
    last_month = monthly_schedule[-1]
    ax.annotate(f'Loan Closure\n({last_month["month_name"]})', 
               xy=(last_month['month_number'], 0), xytext=(last_month['month_number'] - 10, 0.3),
               fontsize=9, color='#d32f2f', fontweight='bold',
               arrowprops=dict(arrowstyle='->', color='#d32f2f'))
    
    ax.set_xlabel('Month Number', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_ylabel('Outstanding Balance (Rs. Crores)', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_title('Outstanding Balance Trajectory Over Loan Tenure', 
                 fontsize=14, fontweight='bold', color='#1a237e', pad=15)
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, len(months) + 5)
    ax.set_ylim(0, max(closing_balance) * 1.2 if closing_balance else 1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer


def create_payment_breakdown_chart(total_principal, total_interest):
    """Create pie chart for payment breakdown"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sizes = [total_principal, total_interest]
    interest_pct = (total_interest / (total_principal + total_interest)) * 100
    principal_pct = 100 - interest_pct
    
    labels = [f'Principal\nRs. {format_indian_number(total_principal)}\n({principal_pct:.1f}%)', 
              f'Interest\nRs. {format_indian_number(total_interest)}\n({interest_pct:.1f}%)']
    colors_pie = ['#4caf50', '#f44336']
    explode = (0.02, 0.02)
    
    wedges, texts = ax.pie(sizes, colors=colors_pie, explode=explode,
                           startangle=90, wedgeprops=dict(width=0.7, edgecolor='white'))
    
    total_paid = total_principal + total_interest
    ax.text(0, 0, f'Total Paid\nRs. {format_indian_number(total_paid)}', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1a237e')
    
    ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0.5),
              fontsize=10, frameon=False)
    
    ax.set_title('Total Payment Breakdown', fontsize=14, fontweight='bold', 
                 color='#1a237e', pad=20)
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer


def create_yearly_comparison_chart(yearly_summary):
    """Create bar chart for yearly comparison"""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    years = sorted(yearly_summary.keys())
    interest = [yearly_summary[y]['interest'] / 100000 for y in years]  # In Lakhs
    emi = [yearly_summary[y]['emi'] / 100000 for y in years]
    prepay = [yearly_summary[y]['prepay'] / 100000 for y in years]
    
    x = range(len(years))
    width = 0.25
    
    ax.bar([i - width for i in x], emi, width, label='EMI Paid', color='#1976d2', alpha=0.9)
    ax.bar([i for i in x], interest, width, label='Interest', color='#f44336', alpha=0.9)
    ax.bar([i + width for i in x], prepay, width, label='Prepayment', color='#4caf50', alpha=0.9)
    
    ax.set_xlabel('Calendar Year', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_ylabel('Amount (Rs. Lakhs)', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_title('Year-wise Payment Analysis', fontsize=14, fontweight='bold', 
                 color='#1a237e', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.legend(loc='upper right', frameon=True, fancybox=True)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer


def generate_loan_pdf(land_loan, construction_loan, loan_start_date, 
                      construction_start_date, emi_amount, interest_rate, part_payments):
    """Generate complete PDF report"""
    
    # Calculate schedule
    result = calculate_loan_schedule(
        land_loan, construction_loan, loan_start_date,
        construction_start_date, emi_amount, interest_rate, part_payments
    )
    
    # Create PDF
    pdf_path = os.path.join(tempfile.gettempdir(), 'Home_Loan_Payoff_Plan.pdf')
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    styles = create_styles()
    story = []
    
    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 1.5*inch))
    
    story.append(Paragraph("HOME LOAN PAYOFF PLAN", styles['CustomTitle']))
    story.append(Paragraph("Comprehensive Month-wise Repayment Strategy", styles['CustomSubtitle']))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Key highlight box
    highlight_data = [
        [Paragraph("<b>PROJECTED LOAN CLOSURE</b>", 
                   ParagraphStyle('', fontSize=12, textColor=colors.white, alignment=TA_CENTER))],
        [Paragraph(f"<b>{result['closure_date']}</b>", 
                   ParagraphStyle('', fontSize=24, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
        [Paragraph(f"Month {result['tenure_months']} | {result['tenure']}", 
                   ParagraphStyle('', fontSize=14, textColor=colors.white, alignment=TA_CENTER))]
    ]
    
    highlight_table = Table(highlight_data, colWidths=[4*inch])
    highlight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1565c0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(highlight_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # Quick summary metrics
    total_principal_cr = result['total_principal'] / 10000000
    total_interest_l = result['total_interest'] / 100000
    total_paid_cr = result['total_paid'] / 10000000
    
    metrics_data = [
        [Paragraph("<b>Total Principal</b>", styles['MetricLabel']),
         Paragraph("<b>Total Interest</b>", styles['MetricLabel']),
         Paragraph("<b>Total Paid</b>", styles['MetricLabel'])],
        [Paragraph(f"Rs. {total_principal_cr:.2f} Cr", styles['KeyMetric']),
         Paragraph(f"Rs. {total_interest_l:.2f} L", 
                   ParagraphStyle('', fontSize=24, textColor=colors.HexColor('#d32f2f'), 
                                  fontName='Helvetica-Bold', alignment=TA_CENTER)),
         Paragraph(f"Rs. {total_paid_cr:.2f} Cr", 
                   ParagraphStyle('', fontSize=24, textColor=colors.HexColor('#1565c0'), 
                                  fontName='Helvetica-Bold', alignment=TA_CENTER))],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(metrics_table)
    
    story.append(Spacer(1, 0.8*inch))
    
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", 
                           ParagraphStyle('', fontSize=10, textColor=colors.HexColor('#757575'), 
                                          alignment=TA_CENTER)))
    
    story.append(PageBreak())
    
    # ==================== EXECUTIVE SUMMARY ====================
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['SectionHeading']))
    
    summary_text = f"""This comprehensive loan payoff plan outlines a strategic approach to repaying a home loan 
    with a total principal of <b>{format_rupees(result['total_principal'])}</b>. The plan incorporates regular EMI payments 
    along with systematic prepayments to accelerate loan closure and minimize total interest outgo."""
    story.append(Paragraph(summary_text, styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Plan Overview
    story.append(Paragraph("Plan Overview", styles['SubsectionHeading']))
    
    overview_items = [
        f"<b>Start Date:</b> {result['start_date']} (Initial Disbursal)",
        f"<b>Land Loan Amount:</b> {format_rupees(land_loan)}",
    ]
    
    if construction_loan > 0 and result['construction_date']:
        overview_items.append(f"<b>Construction Loan:</b> {format_rupees(construction_loan)} (Disbursed: {result['construction_date']})")
    
    overview_items.extend([
        f"<b>Monthly EMI:</b> {format_rupees(emi_amount)} per month",
        f"<b>Interest Rate:</b> {interest_rate}% p.a. (Monthly Reducing Balance)",
    ])
    
    if part_payments:
        prepay_desc = ", ".join([f"{pp['month']}: {format_rupees(pp['amount'])}" for pp in part_payments])
        overview_items.append(f"<b>Annual Prepayments:</b> {prepay_desc}")
    
    overview_items.extend([
        f"<b>Projected Closure:</b> {result['closure_date']} (Month {result['tenure_months']})",
        f"<b>Effective Loan Tenure:</b> {result['tenure']}",
    ])
    
    for item in overview_items:
        story.append(Paragraph(f"* {item}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Key Financial Outcomes
    story.append(Paragraph("Key Financial Outcomes", styles['SubsectionHeading']))
    
    outcomes_data = [
        ["Metric", "Amount", "Remarks"],
        ["Total Principal Borrowed", format_rupees(result['total_principal']), 
         f"Land: {format_rupees(land_loan)}" + (f" + Construction: {format_rupees(construction_loan)}" if construction_loan > 0 else "")],
        ["Total EMI Payments", format_rupees(result['total_emi']), f"{result['tenure_months']} months of payments"],
        ["Total Prepayments", format_rupees(result['total_prepayments']), "Sum of all part payments"],
        ["Total Amount Paid", format_rupees(result['total_paid']), "EMI + Prepayments"],
        ["Total Interest Paid", format_rupees(result['total_interest']), 
         f"{(result['total_interest']/result['total_principal']*100):.1f}% of principal"],
    ]
    
    outcomes_table = Table(outcomes_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
    outcomes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(outcomes_table)
    
    story.append(PageBreak())
    
    # ==================== LOAN ASSUMPTIONS ====================
    story.append(Paragraph("LOAN ASSUMPTIONS & PARAMETERS", styles['SectionHeading']))
    
    story.append(Paragraph("""The following assumptions form the basis of this loan payoff projection. 
    All calculations use monthly reducing balance method for interest computation.""", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    assumptions_data = [
        ["Parameter", "Value", "Details"],
        ["Interest Rate", f"{interest_rate}% p.a.", "Monthly reducing balance method"],
        ["Monthly Interest Rate", f"{interest_rate/12:.4f}%", f"{interest_rate}% / 12 months"],
        ["Land Loan", format_rupees(land_loan), f"Disbursed: {result['start_date']}"],
    ]
    
    if construction_loan > 0:
        assumptions_data.append(["Construction Loan", format_rupees(construction_loan), 
                                 f"Disbursed: {result['construction_date'] or 'N/A'}"])
    
    assumptions_data.extend([
        ["Total Principal", format_rupees(result['total_principal']), "Combined disbursal amount"],
        ["EMI Amount", format_rupees(emi_amount), "Fixed monthly payment"],
    ])
    
    # Add prepayment info
    for i, pp in enumerate(part_payments, 1):
        assumptions_data.append([f"Prepayment {i} ({pp['month']})", format_rupees(pp['amount']), "Annual prepayment"])
    
    assumptions_table = Table(assumptions_data, colWidths=[1.8*inch, 1.5*inch, 2.7*inch])
    assumptions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f5e9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(assumptions_table)
    
    story.append(PageBreak())
    
    # ==================== VISUAL ANALYTICS ====================
    story.append(Paragraph("VISUAL ANALYTICS", styles['SectionHeading']))
    
    # Balance trajectory chart
    story.append(Paragraph("Outstanding Balance Trajectory", styles['SubsectionHeading']))
    balance_chart = create_balance_chart(result['monthly_schedule'], land_loan, construction_loan, 
                                         result['construction_date'])
    story.append(Image(balance_chart, width=6*inch, height=3*inch))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Payment breakdown chart
    story.append(Paragraph("Payment Composition Analysis", styles['SubsectionHeading']))
    payment_chart = create_payment_breakdown_chart(result['total_principal'], result['total_interest'])
    story.append(Image(payment_chart, width=5*inch, height=3.5*inch))
    
    story.append(PageBreak())
    
    # Yearly comparison
    story.append(Paragraph("Year-wise Payment Analysis", styles['SubsectionHeading']))
    yearly_chart = create_yearly_comparison_chart(result['yearly_summary'])
    story.append(Image(yearly_chart, width=6*inch, height=3*inch))
    
    story.append(PageBreak())
    
    # ==================== YEAR-WISE SUMMARY ====================
    story.append(Paragraph("YEAR-WISE SUMMARY", styles['SectionHeading']))
    
    yearly_header = ["Year", "Opening", "Closing", "Interest", "EMI", "Prepay", "Disbursal"]
    yearly_rows = [yearly_header]
    
    for year in sorted(result['yearly_summary'].keys()):
        data = result['yearly_summary'][year]
        yearly_rows.append([
            str(year),
            format_rupees(data['opening']),
            format_rupees(data['closing']),
            format_rupees(data['interest']),
            format_rupees(data['emi']),
            format_rupees(data['prepay']) if data['prepay'] > 0 else "-",
            format_rupees(data['disbursal']) if data['disbursal'] > 0 else "-"
        ])
    
    yearly_table = Table(yearly_rows, colWidths=[0.6*inch, 1*inch, 1*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.9*inch])
    yearly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e3f2fd')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(yearly_table)
    
    story.append(PageBreak())
    
    # ==================== MONTH-WISE SCHEDULE ====================
    story.append(Paragraph("DETAILED MONTH-WISE SCHEDULE", styles['SectionHeading']))
    
    # Split into chunks of 30 rows for readability
    monthly_schedule = result['monthly_schedule']
    chunk_size = 30
    
    for chunk_start in range(0, len(monthly_schedule), chunk_size):
        chunk_end = min(chunk_start + chunk_size, len(monthly_schedule))
        chunk = monthly_schedule[chunk_start:chunk_end]
        
        if chunk_start > 0:
            story.append(PageBreak())
        
        story.append(Paragraph(f"Schedule: Months {chunk_start + 1} - {chunk_end}", styles['SubsectionHeading']))
        
        header = ["#", "Month", "Opening", "Interest", "Disbursal", "EMI", "Prepay", "Closing"]
        rows = [header]
        
        for d in chunk:
            rows.append([
                str(d['month_number']),
                d['month_name'],
                format_rupees(d['opening']),
                format_rupees(d['interest']),
                format_rupees(d['disbursal']) if d['disbursal'] > 0 else "-",
                format_rupees(d['emi']) if d['emi'] > 0 else "-",
                format_rupees(d['prepay']) if d['prepay'] > 0 else "-",
                format_rupees(d['closing'])
            ])
        
        col_widths = [0.35*inch, 0.7*inch, 0.9*inch, 0.7*inch, 0.8*inch, 0.75*inch, 0.7*inch, 0.9*inch]
        table = Table(rows, colWidths=col_widths)
        
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#303f9f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        
        # Highlight special rows
        for i, d in enumerate(chunk, start=1):
            if d['prepay'] > 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#c8e6c9')))
            if d['disbursal'] > 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff9c4')))
        
        table.setStyle(TableStyle(style_commands))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # ==================== ACTION CHECKLIST ====================
    story.append(Paragraph("ACTION CHECKLIST", styles['SectionHeading']))
    
    story.append(Paragraph("Monthly Actions", styles['SubsectionHeading']))
    
    monthly_actions = [
        f"Ensure {format_rupees(emi_amount)} is available in your loan-linked account before EMI due date",
        "Verify EMI deduction has occurred and check updated outstanding balance",
        "Review bank statement to confirm correct EMI amount was debited",
    ]
    
    for action in monthly_actions:
        story.append(Paragraph(f"[ ] {action}", styles['CustomBody']))
    
    if part_payments:
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Prepayment Actions", styles['SubsectionHeading']))
        
        for pp in part_payments:
            story.append(Paragraph(f"<b>{pp['month']} (Every Year):</b>", styles['CustomBody']))
            prepay_actions = [
                f"Transfer {format_rupees(pp['amount'])} to loan account for prepayment",
                "Submit written request for TENURE REDUCTION (NOT EMI reduction)",
                "Collect acknowledgment receipt for the prepayment",
            ]
            for action in prepay_actions:
                story.append(Paragraph(f"    [ ] {action}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ==================== SUMMARY ====================
    story.append(Paragraph("SUMMARY & CONCLUSION", styles['SectionHeading']))
    
    summary_box_data = [
        [Paragraph("<b>LOAN PAYOFF SUMMARY</b>", 
                   ParagraphStyle('', fontSize=14, textColor=colors.white, alignment=TA_CENTER))],
    ]
    
    summary_table = Table(summary_box_data, colWidths=[5.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(summary_table)
    
    story.append(Spacer(1, 0.2*inch))
    
    final_summary = [
        ["Total Principal Borrowed", format_rupees(result['total_principal'])],
        ["Total Interest Paid", format_rupees(result['total_interest'])],
        ["Total Amount Paid", format_rupees(result['total_paid'])],
        ["Total Prepayments", format_rupees(result['total_prepayments'])],
        ["Loan Start Date", result['start_date']],
        ["Loan Closure Date", result['closure_date']],
        ["Effective Tenure", result['tenure']],
    ]
    
    final_table = Table(final_summary, colWidths=[2.5*inch, 3*inch])
    final_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#37474f')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1565c0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    story.append(final_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph("---" * 30, ParagraphStyle('', alignment=TA_CENTER, textColor=colors.HexColor('#bdbdbd'))))
    story.append(Paragraph("This document is for planning purposes only. Actual figures may vary based on interest rate changes and payment timings.", 
                           ParagraphStyle('', fontSize=8, textColor=colors.HexColor('#9e9e9e'), alignment=TA_CENTER)))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", 
                           ParagraphStyle('', fontSize=8, textColor=colors.HexColor('#9e9e9e'), alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(story)
    
    return pdf_path
