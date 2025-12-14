#!/usr/bin/env python3
"""
Home Loan EMI Payoff Plan - Professional PDF Presentation Generator
Creates a comprehensive PDF report with Indian number formatting
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics import renderPDF
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
from datetime import datetime


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
        # Last 3 digits
        result = s[-3:]
        # Remaining digits in groups of 2
        s = s[:-3]
        while s:
            result = s[-2:] + ',' + result
            s = s[:-2]
    
    return '-' + result if is_negative else result


def format_rupees(num):
    """Format as Indian Rupees with ₹ symbol"""
    return f"₹{format_indian_number(num)}"


def create_styles():
    """Create custom paragraph styles"""
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Subtitle style
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#303f9f'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    # Section heading
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1565c0'),
        spaceBefore=20,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        borderPadding=5,
        leftIndent=0
    ))
    
    # Subsection heading
    styles.add(ParagraphStyle(
        name='SubsectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1976d2'),
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    # Body text
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#37474f'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=16
    ))
    
    # Highlight text
    styles.add(ParagraphStyle(
        name='Highlight',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#d32f2f'),
        fontName='Helvetica-Bold',
        spaceAfter=8
    ))
    
    # Key metric style
    styles.add(ParagraphStyle(
        name='KeyMetric',
        parent=styles['Normal'],
        fontSize=24,
        textColor=colors.HexColor('#2e7d32'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5
    ))
    
    # Metric label
    styles.add(ParagraphStyle(
        name='MetricLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#616161'),
        alignment=TA_CENTER,
        spaceAfter=15
    ))
    
    return styles


# Loan data - Month-wise schedule
MONTHLY_DATA = [
    # Month, Month Name, Opening, Interest, Disbursal, EMI, Prepay, Closing
    (1, "Mar 2026", 15000000, 94250, 15000000, 0, 0, 15094250),
    (2, "Apr 2026", 15094250, 94842, 0, 300000, 0, 14889092),
    (3, "May 2026", 14889092, 93553, 0, 300000, 0, 14682645),
    (4, "Jun 2026", 14682645, 92256, 0, 300000, 0, 14474901),
    (5, "Jul 2026", 14474901, 90951, 0, 300000, 0, 14265852),
    (6, "Aug 2026", 14265852, 89637, 0, 300000, 0, 14055489),
    (7, "Sep 2026", 14055489, 88315, 0, 300000, 0, 13843804),
    (8, "Oct 2026", 13843804, 86985, 0, 300000, 500000, 13130790),
    (9, "Nov 2026", 13130790, 82505, 0, 300000, 0, 12913295),
    (10, "Dec 2026", 12913295, 81139, 0, 300000, 0, 12694433),
    (11, "Jan 2027", 12694433, 79763, 0, 300000, 0, 12474197),
    (12, "Feb 2027", 12474197, 78380, 0, 300000, 100000, 12152576),
    (13, "Mar 2027", 12152576, 76359, 0, 300000, 0, 11928935),
    (14, "Apr 2027", 11928935, 74953, 0, 300000, 0, 11703888),
    (15, "May 2027", 11703888, 73539, 0, 300000, 0, 11477428),
    (16, "Jun 2027", 11477428, 72117, 0, 300000, 0, 11249544),
    (17, "Jul 2027", 11249544, 70685, 0, 300000, 0, 11020229),
    (18, "Aug 2027", 11020229, 69244, 0, 300000, 0, 10789473),
    (19, "Sep 2027", 10789473, 67794, 0, 300000, 0, 10557266),
    (20, "Oct 2027", 10557266, 66335, 0, 300000, 500000, 9823601),
    (21, "Nov 2027", 9823601, 61725, 0, 300000, 0, 9585326),
    (22, "Dec 2027", 9585326, 60228, 0, 300000, 0, 9345554),
    (23, "Jan 2028", 9345554, 58721, 0, 300000, 0, 9104275),
    (24, "Feb 2028", 9104275, 57205, 0, 300000, 100000, 8761481),
    (25, "Mar 2028", 18761481, 117885, 10000000, 300000, 0, 18579365),
    (26, "Apr 2028", 18579365, 116740, 0, 300000, 0, 18396105),
    (27, "May 2028", 18396105, 115589, 0, 300000, 0, 18211694),
    (28, "Jun 2028", 18211694, 114430, 0, 300000, 0, 18026124),
    (29, "Jul 2028", 18026124, 113264, 0, 300000, 0, 17839389),
    (30, "Aug 2028", 17839389, 112091, 0, 300000, 0, 17651479),
    (31, "Sep 2028", 17651479, 110910, 0, 300000, 0, 17462390),
    (32, "Oct 2028", 17462390, 109722, 0, 300000, 500000, 16772112),
    (33, "Nov 2028", 16772112, 105385, 0, 300000, 0, 16577496),
    (34, "Dec 2028", 16577496, 104162, 0, 300000, 0, 16381658),
    (35, "Jan 2029", 16381658, 102931, 0, 300000, 0, 16184590),
    (36, "Feb 2029", 16184590, 101693, 0, 300000, 100000, 15886283),
    (37, "Mar 2029", 15886283, 99819, 0, 300000, 0, 15686102),
    (38, "Apr 2029", 15686102, 98561, 0, 300000, 0, 15484663),
    (39, "May 2029", 15484663, 97295, 0, 300000, 0, 15281958),
    (40, "Jun 2029", 15281958, 96022, 0, 300000, 0, 15077980),
    (41, "Jul 2029", 15077980, 94740, 0, 300000, 0, 14872720),
    (42, "Aug 2029", 14872720, 93450, 0, 300000, 0, 14666170),
    (43, "Sep 2029", 14666170, 92152, 0, 300000, 0, 14458322),
    (44, "Oct 2029", 14458322, 90846, 0, 300000, 500000, 13749169),
    (45, "Nov 2029", 13749169, 86391, 0, 300000, 0, 13535559),
    (46, "Dec 2029", 13535559, 85048, 0, 300000, 0, 13320608),
    (47, "Jan 2030", 13320608, 83698, 0, 300000, 0, 13104306),
    (48, "Feb 2030", 13104306, 82339, 0, 300000, 100000, 12786644),
    (49, "Mar 2030", 12786644, 80343, 0, 300000, 0, 12566987),
    (50, "Apr 2030", 12566987, 78963, 0, 300000, 0, 12345950),
    (51, "May 2030", 12345950, 77574, 0, 300000, 0, 12123523),
    (52, "Jun 2030", 12123523, 76176, 0, 300000, 0, 11899700),
    (53, "Jul 2030", 11899700, 74770, 0, 300000, 0, 11674469),
    (54, "Aug 2030", 11674469, 73355, 0, 300000, 0, 11447824),
    (55, "Sep 2030", 11447824, 71930, 0, 300000, 0, 11219754),
    (56, "Oct 2030", 11219754, 70497, 0, 300000, 500000, 10490252),
    (57, "Nov 2030", 10490252, 65914, 0, 300000, 0, 10256166),
    (58, "Dec 2030", 10256166, 64443, 0, 300000, 0, 10020609),
    (59, "Jan 2031", 10020609, 62963, 0, 300000, 0, 9783571),
    (60, "Feb 2031", 9783571, 61473, 0, 300000, 100000, 9445045),
    (61, "Mar 2031", 9445045, 59346, 0, 300000, 0, 9204391),
    (62, "Apr 2031", 9204391, 57834, 0, 300000, 0, 8962225),
    (63, "May 2031", 8962225, 56313, 0, 300000, 0, 8718538),
    (64, "Jun 2031", 8718538, 54781, 0, 300000, 0, 8473320),
    (65, "Jul 2031", 8473320, 53241, 0, 300000, 0, 8226560),
    (66, "Aug 2031", 8226560, 51690, 0, 300000, 0, 7978250),
    (67, "Sep 2031", 7978250, 50130, 0, 300000, 0, 7728380),
    (68, "Oct 2031", 7728380, 48560, 0, 300000, 500000, 6976940),
    (69, "Nov 2031", 6976940, 43838, 0, 300000, 0, 6720779),
    (70, "Dec 2031", 6720779, 42229, 0, 300000, 0, 6463008),
    (71, "Jan 2032", 6463008, 40609, 0, 300000, 0, 6203617),
    (72, "Feb 2032", 6203617, 38979, 0, 300000, 100000, 5842596),
    (73, "Mar 2032", 5842596, 36711, 0, 300000, 0, 5579307),
    (74, "Apr 2032", 5579307, 35057, 0, 300000, 0, 5314364),
    (75, "May 2032", 5314364, 33392, 0, 300000, 0, 5047756),
    (76, "Jun 2032", 5047756, 31717, 0, 300000, 0, 4779473),
    (77, "Jul 2032", 4779473, 30031, 0, 300000, 0, 4509504),
    (78, "Aug 2032", 4509504, 28335, 0, 300000, 0, 4237838),
    (79, "Sep 2032", 4237838, 26628, 0, 300000, 0, 3964466),
    (80, "Oct 2032", 3964466, 24910, 0, 300000, 500000, 3189376),
    (81, "Nov 2032", 3189376, 20040, 0, 300000, 0, 2909416),
    (82, "Dec 2032", 2909416, 18281, 0, 300000, 0, 2627697),
    (83, "Jan 2033", 2627697, 16511, 0, 300000, 0, 2344208),
    (84, "Feb 2033", 2344208, 14729, 0, 300000, 100000, 1958937),
    (85, "Mar 2033", 1958937, 12309, 0, 300000, 0, 1671246),
    (86, "Apr 2033", 1671246, 10501, 0, 300000, 0, 1381747),
    (87, "May 2033", 1381747, 8682, 0, 300000, 0, 1090429),
    (88, "Jun 2033", 1090429, 6852, 0, 300000, 0, 797280),
    (89, "Jul 2033", 797280, 5010, 0, 300000, 0, 502290),
    (90, "Aug 2033", 502290, 3156, 0, 300000, 0, 205446),
    (91, "Sep 2033", 205446, 1291, 0, 206737, 0, 0),
]

# Year-wise summary
YEARLY_DATA = [
    # Year, Opening, Closing, Interest, EMI Paid, Prepay, Disbursal
    (2026, 15000000, 12694433, 894433, 2700000, 500000, 15000000),
    (2027, 12694433, 9345554, 851121, 3600000, 600000, 0),
    (2028, 9345554, 16381658, 1236104, 3600000, 600000, 10000000),
    (2029, 16381658, 13320608, 1138950, 3600000, 600000, 0),
    (2030, 13320608, 10020609, 900001, 3600000, 600000, 0),
    (2031, 10020609, 6463008, 642399, 3600000, 600000, 0),
    (2032, 6463008, 2627697, 364689, 3600000, 600000, 0),
    (2033, 2627697, 0, 79040, 2606737, 100000, 0),
]


def create_balance_chart():
    """Create outstanding balance trajectory chart"""
    months = [d[0] for d in MONTHLY_DATA]
    closing_balance = [d[7] / 10000000 for d in MONTHLY_DATA]  # In Crores
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Main line
    ax.fill_between(months, closing_balance, alpha=0.3, color='#1976d2')
    ax.plot(months, closing_balance, color='#1565c0', linewidth=2.5, marker='o', 
            markersize=3, markerfacecolor='#0d47a1')
    
    # Mark disbursement points
    ax.axvline(x=1, color='#4caf50', linestyle='--', alpha=0.7, linewidth=1.5)
    ax.axvline(x=25, color='#4caf50', linestyle='--', alpha=0.7, linewidth=1.5)
    
    # Add annotations
    ax.annotate('₹1.5 Cr Disbursed\n(Mar 2026)', xy=(1, 1.5), xytext=(5, 1.7),
                fontsize=9, color='#2e7d32', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#4caf50'))
    ax.annotate('₹1 Cr Additional\n(Mar 2028)', xy=(25, 1.86), xytext=(30, 2.0),
                fontsize=9, color='#2e7d32', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#4caf50'))
    ax.annotate('Loan Closure\n(Sep 2033)', xy=(91, 0), xytext=(80, 0.3),
                fontsize=9, color='#d32f2f', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#d32f2f'))
    
    # Styling
    ax.set_xlabel('Month Number', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_ylabel('Outstanding Balance (₹ Crores)', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_title('Outstanding Balance Trajectory Over Loan Tenure', 
                 fontsize=14, fontweight='bold', color='#1a237e', pad=15)
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, 95)
    ax.set_ylim(0, 2.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer


def create_payment_breakdown_chart():
    """Create pie chart for payment breakdown"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    total_principal = 25000000
    total_interest = 6106737
    total_prepay = 4100000
    total_emi = 27006737
    
    sizes = [total_principal, total_interest]
    labels = [f'Principal\n₹{format_indian_number(total_principal)}\n(80.4%)', 
              f'Interest\n₹{format_indian_number(total_interest)}\n(19.6%)']
    colors_pie = ['#4caf50', '#f44336']
    explode = (0.02, 0.02)
    
    wedges, texts = ax.pie(sizes, colors=colors_pie, explode=explode,
                           startangle=90, wedgeprops=dict(width=0.7, edgecolor='white'))
    
    # Add center text
    ax.text(0, 0, f'Total Paid\n₹{format_indian_number(31106737)}', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1a237e')
    
    # Add legend
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


def create_yearly_comparison_chart():
    """Create bar chart for yearly comparison"""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    years = [str(d[0]) for d in YEARLY_DATA]
    interest = [d[3] / 100000 for d in YEARLY_DATA]  # In Lakhs
    emi = [d[4] / 100000 for d in YEARLY_DATA]
    prepay = [d[5] / 100000 for d in YEARLY_DATA]
    
    x = range(len(years))
    width = 0.25
    
    bars1 = ax.bar([i - width for i in x], emi, width, label='EMI Paid', color='#1976d2', alpha=0.9)
    bars2 = ax.bar([i for i in x], interest, width, label='Interest', color='#f44336', alpha=0.9)
    bars3 = ax.bar([i + width for i in x], prepay, width, label='Prepayment', color='#4caf50', alpha=0.9)
    
    ax.set_xlabel('Calendar Year', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_ylabel('Amount (₹ Lakhs)', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_title('Year-wise Payment Analysis', fontsize=14, fontweight='bold', 
                 color='#1a237e', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
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


def create_interest_savings_chart():
    """Create chart showing interest saved due to prepayments"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Cumulative interest over time
    months = [d[0] for d in MONTHLY_DATA]
    cumulative_interest = []
    total = 0
    for d in MONTHLY_DATA:
        total += d[3]
        cumulative_interest.append(total / 100000)  # In Lakhs
    
    ax.fill_between(months, cumulative_interest, alpha=0.3, color='#f44336')
    ax.plot(months, cumulative_interest, color='#d32f2f', linewidth=2.5)
    
    ax.set_xlabel('Month Number', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_ylabel('Cumulative Interest (₹ Lakhs)', fontsize=11, fontweight='bold', color='#37474f')
    ax.set_title('Cumulative Interest Paid Over Time', fontsize=14, fontweight='bold', 
                 color='#1a237e', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Final annotation
    ax.annotate(f'Total Interest: ₹{format_indian_number(6106737)}', 
                xy=(91, cumulative_interest[-1]), xytext=(60, 55),
                fontsize=10, color='#d32f2f', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#d32f2f'))
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer


def build_pdf():
    """Build the complete PDF presentation"""
    doc = SimpleDocTemplate(
        "/workspace/Home_Loan_Payoff_Plan.pdf",
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
        [Paragraph("<b>September 2033</b>", 
                   ParagraphStyle('', fontSize=24, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
        [Paragraph("Month 91 • ≈ 7.58 Years", 
                   ParagraphStyle('', fontSize=14, textColor=colors.white, alignment=TA_CENTER))]
    ]
    
    highlight_table = Table(highlight_data, colWidths=[4*inch])
    highlight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1565c0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    story.append(highlight_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # Quick summary metrics
    metrics_data = [
        [Paragraph("<b>Total Principal</b>", styles['MetricLabel']),
         Paragraph("<b>Total Interest</b>", styles['MetricLabel']),
         Paragraph("<b>Total Paid</b>", styles['MetricLabel'])],
        [Paragraph(f"₹2.5 Crores", styles['KeyMetric']),
         Paragraph(f"₹61.07 Lakhs", 
                   ParagraphStyle('', fontSize=24, textColor=colors.HexColor('#d32f2f'), 
                                  fontName='Helvetica-Bold', alignment=TA_CENTER)),
         Paragraph(f"₹3.11 Crores", 
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
    
    # Date generated
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", 
                           ParagraphStyle('', fontSize=10, textColor=colors.HexColor('#757575'), 
                                          alignment=TA_CENTER)))
    
    story.append(PageBreak())
    
    # ==================== EXECUTIVE SUMMARY ====================
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['SectionHeading']))
    
    summary_text = """This comprehensive loan payoff plan outlines a strategic approach to repaying a home loan 
    with a total principal of <b>₹2,50,00,000 (2.5 Crores)</b>. The plan incorporates regular EMI payments 
    along with systematic prepayments to accelerate loan closure and minimize total interest outgo."""
    story.append(Paragraph(summary_text, styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Plan Overview Box
    story.append(Paragraph("Plan Overview", styles['SubsectionHeading']))
    
    overview_items = [
        f"<b>Start Date:</b> March 2026 (Initial Disbursal)",
        f"<b>EMI Commencement:</b> April 2026",
        f"<b>Monthly EMI:</b> ₹3,00,000 per month",
        f"<b>Annual Prepayments:</b> ₹1,00,000 (February) + ₹5,00,000 (October)",
        f"<b>Total Prepayment per Year:</b> ₹6,00,000",
        f"<b>Projected Closure:</b> September 2033 (Month 91)",
        f"<b>Effective Loan Tenure:</b> Approximately 7.58 years",
    ]
    
    for item in overview_items:
        story.append(Paragraph(f"• {item}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Key Financial Outcomes
    story.append(Paragraph("Key Financial Outcomes", styles['SubsectionHeading']))
    
    outcomes_data = [
        ["Metric", "Amount", "Remarks"],
        ["Total Principal Borrowed", format_rupees(25000000), "₹1.5 Cr (Mar 2026) + ₹1 Cr (Mar 2028)"],
        ["Total EMI Payments", format_rupees(27006737), "90 months of ₹3L + final ₹2.07L"],
        ["Total Prepayments", format_rupees(4100000), "₹1L × 8 (Feb) + ₹5L × 7 (Oct) + final year"],
        ["Total Amount Paid", format_rupees(31106737), "EMI + Prepayments"],
        ["Total Interest Paid", format_rupees(6106737), "24.4% of principal"],
        ["Interest as % of Total", "19.6%", "Efficient due to prepayments"],
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
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fafafa')),
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
        ["Interest Rate", "7.54% p.a.", "Monthly reducing balance method"],
        ["Monthly Interest Rate", "0.6283%", "7.54% ÷ 12 months"],
        ["Initial Disbursal", format_rupees(15000000), "March 2026 - ₹1.5 Crores"],
        ["Second Disbursal", format_rupees(10000000), "March 2028 - ₹1 Crore additional"],
        ["Total Principal", format_rupees(25000000), "Combined disbursal amount"],
        ["EMI Amount", format_rupees(300000), "Fixed monthly payment from Apr 2026"],
        ["February Prepayment", format_rupees(100000), "Annual prepayment in February"],
        ["October Prepayment", format_rupees(500000), "Annual prepayment in October"],
        ["Annual Prepay Total", format_rupees(600000), "Combined yearly prepayment"],
    ]
    
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
    
    story.append(Spacer(1, 0.3*inch))
    
    # Important Notes
    story.append(Paragraph("Important Notes", styles['SubsectionHeading']))
    
    notes = [
        "Interest is calculated on the outstanding principal at the beginning of each month.",
        "Prepayments are applied immediately after the EMI payment for that month.",
        "The second disbursal of ₹1 Crore in March 2028 adds to the outstanding balance.",
        "All prepayments should be accompanied by a request for <b>TENURE REDUCTION</b> (not EMI reduction).",
        "The final month's payment of ₹2,06,737 closes the loan completely.",
    ]
    
    for note in notes:
        story.append(Paragraph(f"• {note}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ==================== VISUAL ANALYTICS ====================
    story.append(Paragraph("VISUAL ANALYTICS", styles['SectionHeading']))
    
    # Balance trajectory chart
    story.append(Paragraph("Outstanding Balance Trajectory", styles['SubsectionHeading']))
    balance_chart = create_balance_chart()
    story.append(Image(balance_chart, width=6*inch, height=3*inch))
    
    story.append(Paragraph("""The chart above shows how the outstanding loan balance changes over the 91-month tenure. 
    Notice the jump in March 2028 due to the additional ₹1 Crore disbursal. The consistent decline thereafter 
    is a result of regular EMI payments combined with strategic prepayments.""", styles['CustomBody']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Payment breakdown chart
    story.append(Paragraph("Payment Composition Analysis", styles['SubsectionHeading']))
    payment_chart = create_payment_breakdown_chart()
    story.append(Image(payment_chart, width=5*inch, height=3.5*inch))
    
    story.append(PageBreak())
    
    # Yearly comparison
    story.append(Paragraph("Year-wise Payment Analysis", styles['SubsectionHeading']))
    yearly_chart = create_yearly_comparison_chart()
    story.append(Image(yearly_chart, width=6*inch, height=3*inch))
    
    story.append(Paragraph("""The bar chart illustrates the annual distribution of EMI payments, interest charges, 
    and prepayments. Notice how interest paid decreases year-over-year as the principal reduces, 
    demonstrating the benefit of the prepayment strategy.""", styles['CustomBody']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Cumulative interest
    story.append(Paragraph("Cumulative Interest Trend", styles['SubsectionHeading']))
    interest_chart = create_interest_savings_chart()
    story.append(Image(interest_chart, width=5*inch, height=3*inch))
    
    story.append(PageBreak())
    
    # ==================== YEAR-WISE SUMMARY ====================
    story.append(Paragraph("YEAR-WISE SUMMARY", styles['SectionHeading']))
    
    story.append(Paragraph("""This section provides a consolidated view of loan progression on a calendar year basis, 
    making it easier to understand annual cash outflows and plan finances accordingly.""", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    yearly_header = ["Year", "Opening\nBalance", "Closing\nBalance", "Interest\nPaid", 
                     "EMI\nPaid", "Prepay", "Disbursal"]
    yearly_rows = [yearly_header]
    
    for row in YEARLY_DATA:
        yearly_rows.append([
            str(row[0]),
            format_rupees(row[1]),
            format_rupees(row[2]),
            format_rupees(row[3]),
            format_rupees(row[4]),
            format_rupees(row[5]),
            format_rupees(row[6]) if row[6] > 0 else "-"
        ])
    
    # Add totals row
    total_interest = sum(d[3] for d in YEARLY_DATA)
    total_emi = sum(d[4] for d in YEARLY_DATA)
    total_prepay = sum(d[5] for d in YEARLY_DATA)
    total_disb = sum(d[6] for d in YEARLY_DATA)
    
    yearly_rows.append([
        "TOTAL", "-", "-", 
        format_rupees(total_interest), 
        format_rupees(total_emi),
        format_rupees(total_prepay),
        format_rupees(total_disb)
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
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#e3f2fd')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#bbdefb')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(yearly_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Year-wise insights
    story.append(Paragraph("Year-wise Insights", styles['SubsectionHeading']))
    
    insights = [
        "<b>2026:</b> Loan starts with ₹1.5 Cr disbursal. Only 9 months of EMI (Apr-Dec). First Oct prepayment of ₹5L reduces balance significantly.",
        "<b>2027:</b> Full year of 12 EMI payments. Both Feb (₹1L) and Oct (₹5L) prepayments made. Balance reduces from ₹1.27 Cr to ₹93.46 L.",
        "<b>2028:</b> Critical year - Additional ₹1 Cr disbursed in March. Despite high interest (₹12.36L), balance managed through consistent payments.",
        "<b>2029:</b> No new disbursal. Steady reduction with full prepayments. Interest decreases to ₹11.39L.",
        "<b>2030:</b> Balance crosses below ₹1 Cr mark by year end. Interest drops to ₹9L.",
        "<b>2031:</b> Accelerated reduction. Interest down to ₹6.42L. Closing balance at ₹64.63L.",
        "<b>2032:</b> Final full year. Interest reduces to ₹3.65L. Balance at ₹26.28L by December.",
        "<b>2033:</b> Final year with only 9 months. Last EMI of ₹2.07L closes the loan in September.",
    ]
    
    for insight in insights:
        story.append(Paragraph(f"• {insight}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ==================== MONTH-WISE SCHEDULE ====================
    story.append(Paragraph("DETAILED MONTH-WISE SCHEDULE", styles['SectionHeading']))
    
    story.append(Paragraph("""The following tables provide a complete month-by-month breakdown of the loan amortization. 
    Key columns explained:""", styles['CustomBody']))
    
    column_explanations = [
        "<b>Opening:</b> Outstanding balance at the start of the month",
        "<b>Interest:</b> Interest accrued for the month (Opening × 7.54% ÷ 12)",
        "<b>Disbursal:</b> Any new loan amount disbursed during the month",
        "<b>EMI:</b> Equated Monthly Installment paid",
        "<b>Prepay:</b> Additional prepayment made (Feb: ₹1L, Oct: ₹5L)",
        "<b>Closing:</b> Outstanding balance at end of month (Opening + Interest + Disbursal - EMI - Prepay)",
    ]
    
    for exp in column_explanations:
        story.append(Paragraph(f"• {exp}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Split monthly data into chunks for better readability
    def create_monthly_table(data_chunk, title):
        story.append(Paragraph(title, styles['SubsectionHeading']))
        
        header = ["#", "Month", "Opening", "Interest", "Disbursal", "EMI", "Prepay", "Closing"]
        rows = [header]
        
        for d in data_chunk:
            row = [
                str(d[0]),
                d[1],
                format_rupees(d[2]),
                format_rupees(d[3]),
                format_rupees(d[4]) if d[4] > 0 else "-",
                format_rupees(d[5]) if d[5] > 0 else "-",
                format_rupees(d[6]) if d[6] > 0 else "-",
                format_rupees(d[7])
            ]
            rows.append(row)
        
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
        
        # Highlight prepayment rows
        for i, d in enumerate(data_chunk, start=1):
            if d[6] > 0:  # Has prepayment
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#c8e6c9')))
            if d[4] > 0:  # Has disbursal
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff9c4')))
        
        table.setStyle(TableStyle(style_commands))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    # Part 1: Months 1-31
    create_monthly_table(MONTHLY_DATA[:31], "Schedule Part 1: March 2026 - September 2028 (Months 1-31)")
    story.append(PageBreak())
    
    # Part 2: Months 32-62
    create_monthly_table(MONTHLY_DATA[31:62], "Schedule Part 2: October 2028 - April 2031 (Months 32-62)")
    story.append(PageBreak())
    
    # Part 3: Months 63-91
    create_monthly_table(MONTHLY_DATA[62:], "Schedule Part 3: May 2031 - September 2033 (Months 63-91)")
    
    story.append(Spacer(1, 0.2*inch))
    
    # Legend
    legend_data = [
        [Paragraph("<b>Legend:</b>", ParagraphStyle('', fontSize=9))],
        [Paragraph("🟢 Green rows = Prepayment months (February/October)", 
                   ParagraphStyle('', fontSize=8, textColor=colors.HexColor('#2e7d32')))],
        [Paragraph("🟡 Yellow rows = Disbursal months (March 2026, March 2028)", 
                   ParagraphStyle('', fontSize=8, textColor=colors.HexColor('#f57f17')))],
    ]
    legend_table = Table(legend_data, colWidths=[5*inch])
    legend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(legend_table)
    
    story.append(PageBreak())
    
    # ==================== ACTION CHECKLIST ====================
    story.append(Paragraph("ACTION CHECKLIST", styles['SectionHeading']))
    
    story.append(Paragraph("""To successfully execute this loan payoff plan, follow the action items below diligently. 
    Setting up reminders and automations where possible will help ensure consistency.""", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Monthly Actions
    story.append(Paragraph("Monthly Actions (Every Month from April 2026)", styles['SubsectionHeading']))
    
    monthly_actions = [
        "Ensure ₹3,00,000 is available in your loan-linked account before EMI due date",
        "Verify EMI deduction has occurred and check updated outstanding balance",
        "Review bank statement to confirm correct EMI amount was debited",
        "Keep records of all EMI payments for tax documentation (if applicable)",
    ]
    
    for action in monthly_actions:
        story.append(Paragraph(f"☐ {action}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # February Actions
    story.append(Paragraph("February Actions (Annual Prepayment - ₹1,00,000)", styles['SubsectionHeading']))
    
    feb_actions = [
        "Transfer ₹1,00,000 to loan account or visit bank for prepayment",
        "<b>IMPORTANT:</b> Submit written request for <b>TENURE REDUCTION</b> (NOT EMI reduction)",
        "Collect acknowledgment receipt for the prepayment",
        "Verify the prepayment reflects in next month's statement",
        "Request updated amortization schedule from the bank",
    ]
    
    for action in feb_actions:
        story.append(Paragraph(f"☐ {action}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # October Actions
    story.append(Paragraph("October Actions (Annual Prepayment - ₹5,00,000)", styles['SubsectionHeading']))
    
    oct_actions = [
        "Transfer ₹5,00,000 to loan account or visit bank for prepayment",
        "<b>IMPORTANT:</b> Submit written request for <b>TENURE REDUCTION</b> (NOT EMI reduction)",
        "Collect acknowledgment receipt for the prepayment",
        "Verify the prepayment reflects in next month's statement",
        "Request updated amortization schedule from the bank",
        "Review year-to-date interest paid for tax planning purposes",
    ]
    
    for action in oct_actions:
        story.append(Paragraph(f"☐ {action}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Special Dates
    story.append(Paragraph("Key Dates to Remember", styles['SubsectionHeading']))
    
    key_dates_data = [
        ["Date", "Event", "Action Required"],
        ["March 2026", "Loan Starts", "Disbursal of ₹1,50,00,000"],
        ["April 2026", "First EMI", "Ensure ₹3,00,000 available"],
        ["October 2026", "First Oct Prepay", "Prepay ₹5,00,000 + Tenure reduction"],
        ["February 2027", "First Feb Prepay", "Prepay ₹1,00,000 + Tenure reduction"],
        ["March 2028", "Second Disbursal", "Additional ₹1,00,00,000 disbursed"],
        ["September 2033", "Loan Closure", "Final payment ₹2,06,737"],
    ]
    
    key_dates_table = Table(key_dates_data, colWidths=[1.2*inch, 1.5*inch, 3.3*inch])
    key_dates_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffebee')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(key_dates_table)
    
    story.append(PageBreak())
    
    # ==================== BENEFITS OF THIS PLAN ====================
    story.append(Paragraph("BENEFITS OF THIS REPAYMENT STRATEGY", styles['SectionHeading']))
    
    story.append(Paragraph("Interest Savings Analysis", styles['SubsectionHeading']))
    
    story.append(Paragraph("""By following this prepayment strategy, you benefit in multiple ways compared to 
    a standard loan repayment without prepayments:""", styles['CustomBody']))
    
    benefits_data = [
        ["Benefit", "Details"],
        ["Reduced Tenure", "Loan closes in ~7.58 years instead of typical 15-20 years"],
        ["Lower Total Interest", "Interest of ₹61.07 Lakhs (24.4% of principal) is significantly lower than standard loans"],
        ["Psychological Benefit", "Being debt-free sooner provides peace of mind"],
        ["Increased Cash Flow Later", "Once loan closes, ₹3L/month becomes available for investments"],
        ["Asset Ownership", "Full property ownership achieved 7-12 years earlier"],
    ]
    
    benefits_table = Table(benefits_data, colWidths=[1.8*inch, 4.2*inch])
    benefits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f5e9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(benefits_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Why Tenure Reduction
    story.append(Paragraph("Why Request TENURE REDUCTION?", styles['SubsectionHeading']))
    
    story.append(Paragraph("""When making prepayments, banks typically offer two options: reduce EMI amount or reduce 
    loan tenure. <b>Always choose TENURE REDUCTION</b> for the following reasons:""", styles['CustomBody']))
    
    tenure_reasons = [
        "<b>Faster Debt Freedom:</b> The loan closes earlier, freeing up your cash flow sooner.",
        "<b>More Interest Saved:</b> Shorter tenure means fewer months of interest accrual.",
        "<b>Compound Effect:</b> Each prepayment reduces principal, which reduces next month's interest, creating a compounding benefit.",
        "<b>Inflation Hedge:</b> Fixed EMI becomes relatively smaller over time due to inflation; maintaining it is advantageous.",
        "<b>Discipline:</b> Maintaining the same EMI ensures you don't reduce your repayment capacity.",
    ]
    
    for reason in tenure_reasons:
        story.append(Paragraph(f"• {reason}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Risk Considerations
    story.append(Paragraph("Risk Considerations", styles['SubsectionHeading']))
    
    risks = [
        "<b>Interest Rate Changes:</b> If the loan has a floating rate, interest rate increases will affect the schedule. Request updated amortization after rate changes.",
        "<b>Income Stability:</b> Ensure stable income to maintain ₹3L/month EMI + ₹6L annual prepayments.",
        "<b>Emergency Fund:</b> Maintain 6-12 months of EMI as emergency fund before aggressive prepayments.",
        "<b>Tax Benefits:</b> Consider Section 80C and Section 24 benefits before deciding prepayment amounts.",
        "<b>Opportunity Cost:</b> Evaluate if the prepayment amount could earn higher returns elsewhere (unlikely at 7.54% guaranteed savings).",
    ]
    
    for risk in risks:
        story.append(Paragraph(f"• {risk}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ==================== SUMMARY & CONCLUSION ====================
    story.append(Paragraph("SUMMARY & CONCLUSION", styles['SectionHeading']))
    
    # Final summary box
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
        ["", ""],
        ["Total Principal Borrowed", format_rupees(25000000) + " (₹2.5 Crores)"],
        ["Total Interest Paid", format_rupees(6106737) + " (₹61.07 Lakhs)"],
        ["Total Amount Paid", format_rupees(31106737) + " (₹3.11 Crores)"],
        ["Total EMI Payments", "91 months (₹3L × 90 + ₹2.07L final)"],
        ["Total Prepayments", format_rupees(4100000) + " (₹41 Lakhs)"],
        ["Loan Start Date", "March 2026"],
        ["Loan Closure Date", "September 2033"],
        ["Effective Tenure", "7 Years 7 Months (91 months)"],
        ["Interest as % of Principal", "24.4%"],
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
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    story.append(final_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Conclusion text
    story.append(Paragraph("""This loan payoff plan provides a clear, achievable path to complete debt freedom by 
    September 2033. By maintaining discipline with monthly EMI payments and strategic prepayments in February 
    and October each year, you can successfully close a ₹2.5 Crore loan in approximately 7.58 years while 
    paying only ₹61.07 Lakhs in interest - a testament to the power of systematic prepayment strategy.""", 
    styles['CustomBody']))
    
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("""<b>Next Steps:</b>""", styles['CustomBody']))
    
    next_steps = [
        "Share this plan with all stakeholders for alignment",
        "Set up calendar reminders for February and October prepayments",
        "Ensure loan account is set up for auto-debit of ₹3,00,000 monthly EMI",
        "Request the bank for updated schedule after each prepayment",
        "Review this plan annually and adjust if interest rates change significantly",
    ]
    
    for i, step in enumerate(next_steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Footer
    story.append(Paragraph("─" * 60, ParagraphStyle('', alignment=TA_CENTER, textColor=colors.HexColor('#bdbdbd'))))
    story.append(Paragraph("This document is for planning purposes only. Actual figures may vary based on interest rate changes and payment timings.", 
                           ParagraphStyle('', fontSize=8, textColor=colors.HexColor('#9e9e9e'), alignment=TA_CENTER)))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", 
                           ParagraphStyle('', fontSize=8, textColor=colors.HexColor('#9e9e9e'), alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(story)
    print("PDF generated successfully: /workspace/Home_Loan_Payoff_Plan.pdf")


if __name__ == "__main__":
    build_pdf()
