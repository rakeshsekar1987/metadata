#!/usr/bin/env python3
"""
Databricks Cost Optimization - PDF Presentation Generator
Creates a professional 7-slide presentation showcasing optimization achievements
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

# Page size - landscape for presentation style
PAGE_WIDTH, PAGE_HEIGHT = landscape(LETTER)

# Color scheme - professional dark theme inspired colors
DARK_BG = colors.HexColor('#1a1a2e')
ACCENT_BLUE = colors.HexColor('#4a9eff')
ACCENT_GREEN = colors.HexColor('#00d4aa')
ACCENT_YELLOW = colors.HexColor('#ffc107')
ACCENT_ORANGE = colors.HexColor('#ff6b35')
WHITE = colors.white
LIGHT_GRAY = colors.HexColor('#e0e0e0')
DARK_GRAY = colors.HexColor('#2d2d44')

# Environment colors matching the charts
DEV_BLUE = colors.HexColor('#4a90a4')
QA_YELLOW = colors.HexColor('#f0a030')
PROD_GREEN = colors.HexColor('#50b080')


class PresentationPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=landscape(LETTER))
        self.width = PAGE_WIDTH
        self.height = PAGE_HEIGHT
        self.slide_num = 0
        
    def draw_background(self):
        """Draw dark gradient-style background"""
        self.c.setFillColor(DARK_BG)
        self.c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Add subtle accent line at top
        self.c.setStrokeColor(ACCENT_BLUE)
        self.c.setLineWidth(4)
        self.c.line(0, self.height - 5, self.width, self.height - 5)
        
    def draw_slide_number(self):
        """Draw slide number in bottom right"""
        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawRightString(self.width - 40, 25, f"Slide {self.slide_num} of 7")
        
    def draw_footer(self):
        """Draw footer with date"""
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(colors.HexColor('#888888'))
        self.c.drawString(40, 25, "Databricks Cost Optimization Report | December 2025")
        
    def new_slide(self):
        """Start a new slide"""
        if self.slide_num > 0:
            self.c.showPage()
        self.slide_num += 1
        self.draw_background()
        self.draw_slide_number()
        self.draw_footer()
        
    def draw_title(self, title, subtitle=None, y_offset=0):
        """Draw slide title"""
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 80 + y_offset, title)
        
        if subtitle:
            self.c.setFont("Helvetica", 18)
            self.c.setFillColor(ACCENT_BLUE)
            self.c.drawCentredString(self.width/2, self.height - 115 + y_offset, subtitle)
            
    def draw_big_number(self, number, label, x, y, color=ACCENT_GREEN):
        """Draw a big metric number with label"""
        self.c.setFont("Helvetica-Bold", 48)
        self.c.setFillColor(color)
        self.c.drawCentredString(x, y, number)
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(x, y - 30, label)
        
    def draw_metric_box(self, x, y, width, height, number, label, color=ACCENT_BLUE):
        """Draw a metric box with number and label"""
        # Box background
        self.c.setFillColor(DARK_GRAY)
        self.c.roundRect(x, y, width, height, 10, fill=1, stroke=0)
        
        # Accent line at top
        self.c.setStrokeColor(color)
        self.c.setLineWidth(3)
        self.c.line(x + 10, y + height - 5, x + width - 10, y + height - 5)
        
        # Number
        self.c.setFont("Helvetica-Bold", 32)
        self.c.setFillColor(color)
        self.c.drawCentredString(x + width/2, y + height/2 + 5, number)
        
        # Label
        self.c.setFont("Helvetica", 11)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(x + width/2, y + 20, label)
        
    def draw_bar_chart(self, x, y, width, height, data, labels, chart_colors, title=""):
        """Draw a simple bar chart"""
        if title:
            self.c.setFont("Helvetica-Bold", 14)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + width/2, y + height + 20, title)
        
        max_val = max(data)
        bar_width = (width - 40) / len(data) - 10
        
        for i, (val, label, color) in enumerate(zip(data, labels, chart_colors)):
            bar_height = (val / max_val) * (height - 40)
            bar_x = x + 20 + i * (bar_width + 10)
            bar_y = y + 30
            
            # Draw bar
            self.c.setFillColor(color)
            self.c.rect(bar_x, bar_y, bar_width, bar_height, fill=1, stroke=0)
            
            # Draw value on top
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(WHITE)
            if val >= 1000:
                val_str = f"${val/1000:.1f}K"
            else:
                val_str = f"${val:.0f}"
            self.c.drawCentredString(bar_x + bar_width/2, bar_y + bar_height + 5, val_str)
            
            # Draw label below
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(bar_x + bar_width/2, bar_y - 15, label)

    # =========== SLIDE 1: Title Slide ===========
    def slide_1_title(self):
        self.new_slide()
        
        # Main title
        self.c.setFont("Helvetica-Bold", 44)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 180, "Databricks Infrastructure")
        self.c.drawCentredString(self.width/2, self.height - 235, "Cost Optimization Initiative")
        
        # Subtitle
        self.c.setFont("Helvetica", 24)
        self.c.setFillColor(ACCENT_BLUE)
        self.c.drawCentredString(self.width/2, self.height - 290, "Q3-Q4 2025 Business Impact Report")
        
        # Big savings number
        self.c.setFont("Helvetica-Bold", 72)
        self.c.setFillColor(ACCENT_GREEN)
        self.c.drawCentredString(self.width/2, self.height - 400, "$229,536")
        
        self.c.setFont("Helvetica", 28)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, self.height - 445, "Annual Savings Achieved")
        
        # Decorative elements
        self.c.setStrokeColor(ACCENT_GREEN)
        self.c.setLineWidth(2)
        self.c.line(self.width/2 - 150, self.height - 320, self.width/2 + 150, self.height - 320)

    # =========== SLIDE 2: The Challenge ===========
    def slide_2_challenge(self):
        self.new_slide()
        self.draw_title("The Challenge", "Infrastructure Costs Were Unsustainable")
        
        # Peak cost highlight
        self.c.setFont("Helvetica-Bold", 56)
        self.c.setFillColor(ACCENT_ORANGE)
        self.c.drawCentredString(self.width/2, self.height - 200, "$23,149/month")
        
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, self.height - 235, "Peak Monthly Cost (August 2025)")
        
        # Problem boxes
        problems = [
            ("Pool Clusters 24/7", "Always-on compute\nwasting resources"),
            ("Over-Provisioned VMs", "Mixed sizing with\n40-60% idle capacity"),
            ("Driver Bottleneck", "Single driver causing\nresource contention"),
            ("No Auto-Shutdown", "Clusters running\nnights & weekends")
        ]
        
        box_width = 170
        box_height = 100
        start_x = (self.width - (4 * box_width + 3 * 20)) / 2
        y = self.height - 400
        
        for i, (title, desc) in enumerate(problems):
            x = start_x + i * (box_width + 20)
            
            # Box
            self.c.setFillColor(DARK_GRAY)
            self.c.roundRect(x, y, box_width, box_height, 8, fill=1, stroke=0)
            
            # Red accent
            self.c.setStrokeColor(ACCENT_ORANGE)
            self.c.setLineWidth(3)
            self.c.line(x + 10, y + box_height - 8, x + box_width - 10, y + box_height - 8)
            
            # Title
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(ACCENT_ORANGE)
            self.c.drawCentredString(x + box_width/2, y + box_height - 30, title)
            
            # Description
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            lines = desc.split('\n')
            for j, line in enumerate(lines):
                self.c.drawCentredString(x + box_width/2, y + box_height - 50 - j*14, line)

    # =========== SLIDE 3: 3-Phase Solution ===========
    def slide_3_solution(self):
        self.new_slide()
        self.draw_title("The Solution", "3-Phase Optimization Strategy")
        
        phases = [
            ("PHASE 1", "August 2025", "Pool Cluster\nDecommissioning", 
             "Removed 24/7 pools\nOn-demand compute\nAuto-termination", "-14%", ACCENT_BLUE),
            ("PHASE 2", "September 2025", "Right-Sizing\nCompute", 
             "Standard_D4s_v3\n3-5 workers\n100% utilization", "-62%", ACCENT_GREEN),
            ("PHASE 3", "Oct-Nov 2025", "Task Group\nClustering", 
             "Dedicated clusters\nReduced driver load\nParallel execution", "-31%", ACCENT_YELLOW)
        ]
        
        box_width = 220
        box_height = 280
        start_x = (self.width - (3 * box_width + 2 * 30)) / 2
        y = self.height - 480
        
        for i, (phase, date, title, details, savings, color) in enumerate(phases):
            x = start_x + i * (box_width + 30)
            
            # Main box
            self.c.setFillColor(DARK_GRAY)
            self.c.roundRect(x, y, box_width, box_height, 10, fill=1, stroke=0)
            
            # Color accent at top
            self.c.setFillColor(color)
            self.c.roundRect(x, y + box_height - 50, box_width, 50, 10, fill=1, stroke=0)
            self.c.setFillColor(DARK_GRAY)
            self.c.rect(x, y + box_height - 50, box_width, 20, fill=1, stroke=0)
            
            # Phase label
            self.c.setFont("Helvetica-Bold", 16)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + box_width/2, y + box_height - 35, phase)
            
            # Date
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + box_height - 70, date)
            
            # Title
            self.c.setFont("Helvetica-Bold", 14)
            self.c.setFillColor(WHITE)
            title_lines = title.split('\n')
            for j, line in enumerate(title_lines):
                self.c.drawCentredString(x + box_width/2, y + box_height - 100 - j*18, line)
            
            # Details
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            detail_lines = details.split('\n')
            for j, line in enumerate(detail_lines):
                self.c.drawCentredString(x + box_width/2, y + box_height - 160 - j*16, line)
            
            # Savings badge
            self.c.setFont("Helvetica-Bold", 24)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + 30, savings)
            
            # Arrow between phases
            if i < 2:
                arrow_x = x + box_width + 5
                arrow_y = y + box_height/2
                self.c.setStrokeColor(colors.HexColor('#666666'))
                self.c.setLineWidth(2)
                self.c.line(arrow_x, arrow_y, arrow_x + 20, arrow_y)
                # Arrowhead
                self.c.line(arrow_x + 15, arrow_y + 5, arrow_x + 20, arrow_y)
                self.c.line(arrow_x + 15, arrow_y - 5, arrow_x + 20, arrow_y)

    # =========== SLIDE 4: Cost Comparison Chart ===========
    def slide_4_cost_chart(self):
        self.new_slide()
        self.draw_title("Cost Reduction by Environment", "Before vs After Optimization")
        
        # Before section
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(ACCENT_ORANGE)
        self.c.drawCentredString(self.width/4, self.height - 170, "BEFORE (August 2025)")
        
        # Before bars
        before_data = [79, 9820, 13250]
        before_labels = ["Dev", "QA", "Prod"]
        before_colors = [DEV_BLUE, QA_YELLOW, PROD_GREEN]
        
        self.draw_bar_chart(60, self.height - 450, 320, 200, before_data, before_labels, before_colors)
        
        # Total before
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(220, self.height - 480, "Total: $23,149/mo")
        
        # Arrow
        self.c.setStrokeColor(ACCENT_GREEN)
        self.c.setLineWidth(4)
        arrow_x = self.width/2
        self.c.line(arrow_x - 40, self.height - 350, arrow_x + 40, self.height - 350)
        self.c.line(arrow_x + 30, self.height - 340, arrow_x + 40, self.height - 350)
        self.c.line(arrow_x + 30, self.height - 360, arrow_x + 40, self.height - 350)
        
        self.c.setFont("Helvetica-Bold", 24)
        self.c.setFillColor(ACCENT_GREEN)
        self.c.drawCentredString(arrow_x, self.height - 310, "83%")
        self.c.setFont("Helvetica", 12)
        self.c.drawCentredString(arrow_x, self.height - 390, "REDUCTION")
        
        # After section
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(ACCENT_GREEN)
        self.c.drawCentredString(3*self.width/4, self.height - 170, "AFTER (November 2025)")
        
        # After bars
        after_data = [21, 1020, 2980]
        self.draw_bar_chart(self.width - 380, self.height - 450, 320, 200, after_data, before_labels, before_colors)
        
        # Total after
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width - 160, self.height - 480, "Total: $4,021/mo")
        
        # Savings summary boxes
        savings = [
            ("Production", "$10,270", "77%"),
            ("QA", "$8,800", "90%"),
            ("Dev", "$58", "73%")
        ]
        
        box_y = 80
        box_width = 180
        start_x = (self.width - 3*box_width - 40) / 2
        
        for i, (env, amount, pct) in enumerate(savings):
            x = start_x + i * (box_width + 20)
            
            self.c.setFillColor(DARK_GRAY)
            self.c.roundRect(x, box_y, box_width, 60, 8, fill=1, stroke=0)
            
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, box_y + 45, env)
            
            self.c.setFont("Helvetica-Bold", 16)
            self.c.setFillColor(ACCENT_GREEN)
            self.c.drawCentredString(x + box_width/2, box_y + 22, f"{amount}/mo saved ({pct})")

    # =========== SLIDE 5: Monthly Trend ===========
    def slide_5_trend(self):
        self.new_slide()
        self.draw_title("Monthly Cost Trend", "6-Month Optimization Journey")
        
        # Data
        months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        totals = [15482, 21940, 23149, 16981, 5401, 4021]
        
        # Chart area
        chart_x = 100
        chart_y = 120
        chart_width = self.width - 200
        chart_height = 300
        
        # Draw axes
        self.c.setStrokeColor(colors.HexColor('#444444'))
        self.c.setLineWidth(1)
        self.c.line(chart_x, chart_y, chart_x, chart_y + chart_height)
        self.c.line(chart_x, chart_y, chart_x + chart_width, chart_y)
        
        # Y-axis labels
        max_val = 25000
        for i in range(6):
            val = i * 5000
            y = chart_y + (val / max_val) * chart_height
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawRightString(chart_x - 10, y - 4, f"${val/1000:.0f}K")
            
            self.c.setStrokeColor(colors.HexColor('#333333'))
            self.c.setLineWidth(0.5)
            self.c.line(chart_x, y, chart_x + chart_width, y)
        
        # Draw bars and trend line
        bar_width = (chart_width - 100) / len(months)
        points = []
        
        for i, (month, total) in enumerate(zip(months, totals)):
            x = chart_x + 50 + i * bar_width
            bar_height = (total / max_val) * chart_height
            
            # Color based on phase
            if i <= 1:  # Before
                color = colors.HexColor('#666666')
            elif i == 2:  # Phase 1
                color = ACCENT_BLUE
            elif i == 3:  # Phase 2
                color = ACCENT_GREEN
            else:  # Phase 3
                color = ACCENT_YELLOW
            
            self.c.setFillColor(color)
            self.c.rect(x, chart_y, bar_width - 10, bar_height, fill=1, stroke=0)
            
            # Value on top
            self.c.setFont("Helvetica-Bold", 11)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + bar_width/2 - 5, chart_y + bar_height + 10, f"${total/1000:.1f}K")
            
            # Month label
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + bar_width/2 - 5, chart_y - 20, month)
            
            points.append((x + bar_width/2 - 5, chart_y + bar_height))
        
        # Draw trend line
        self.c.setStrokeColor(ACCENT_ORANGE)
        self.c.setLineWidth(2)
        for i in range(len(points) - 1):
            self.c.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Phase annotations
        annotations = [
            (2, "Phase 1", ACCENT_BLUE),
            (3, "Phase 2", ACCENT_GREEN),
            (4.5, "Phase 3", ACCENT_YELLOW)
        ]
        
        for idx, label, color in annotations:
            x = chart_x + 50 + idx * bar_width
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(color)
            self.c.drawCentredString(x, chart_y + chart_height + 35, label)

    # =========== SLIDE 6: Additional Optimizations ===========
    def slide_6_additional(self):
        self.new_slide()
        self.draw_title("Additional Optimizations", "Comprehensive Infrastructure Improvements")
        
        optimizations = [
            ("Photon Engine", "2-3x faster queries\nNative vectorized execution", ACCENT_BLUE),
            ("Delta Tables", "Z-ORDER clustering\nAuto-Optimize enabled", ACCENT_GREEN),
            ("Smart Scheduling", "Off-peak job execution\nDependency optimization", ACCENT_YELLOW),
            ("Storage Savings", "Delta Lake compression\n25% storage reduction", ACCENT_ORANGE),
            ("Monitoring", "Cost alerts at 80%\nReal-time dashboards", colors.HexColor('#9b59b6')),
            ("Governance", "Cluster policies\nPrevented over-provisioning", colors.HexColor('#1abc9c'))
        ]
        
        # 2x3 grid
        box_width = 220
        box_height = 120
        cols = 3
        rows = 2
        h_gap = 40
        v_gap = 30
        
        total_width = cols * box_width + (cols-1) * h_gap
        total_height = rows * box_height + (rows-1) * v_gap
        start_x = (self.width - total_width) / 2
        start_y = self.height - 180 - total_height
        
        for i, (title, details, color) in enumerate(optimizations):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (box_width + h_gap)
            y = start_y + (rows - 1 - row) * (box_height + v_gap)
            
            # Box
            self.c.setFillColor(DARK_GRAY)
            self.c.roundRect(x, y, box_width, box_height, 8, fill=1, stroke=0)
            
            # Color accent
            self.c.setFillColor(color)
            self.c.roundRect(x, y + box_height - 35, box_width, 35, 8, fill=1, stroke=0)
            self.c.setFillColor(DARK_GRAY)
            self.c.rect(x, y + box_height - 35, box_width, 15, fill=1, stroke=0)
            
            # Title
            self.c.setFont("Helvetica-Bold", 13)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + box_width/2, y + box_height - 25, title)
            
            # Details
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            lines = details.split('\n')
            for j, line in enumerate(lines):
                self.c.drawCentredString(x + box_width/2, y + box_height - 55 - j*16, line)

    # =========== SLIDE 7: Summary & ROI ===========
    def slide_7_summary(self):
        self.new_slide()
        self.draw_title("Results & ROI Summary", "Measurable Business Impact")
        
        # Key metrics row
        metrics = [
            ("$19,128", "Monthly Savings", ACCENT_GREEN),
            ("$229,536", "Annual Savings", ACCENT_GREEN),
            ("83%", "Cost Reduction", ACCENT_BLUE),
            ("1,430%", "ROI", ACCENT_YELLOW)
        ]
        
        box_width = 160
        start_x = (self.width - 4*box_width - 60) / 2
        y = self.height - 250
        
        for i, (value, label, color) in enumerate(metrics):
            x = start_x + i * (box_width + 20)
            
            self.c.setFillColor(DARK_GRAY)
            self.c.roundRect(x, y, box_width, 100, 10, fill=1, stroke=0)
            
            self.c.setStrokeColor(color)
            self.c.setLineWidth(3)
            self.c.line(x + 15, y + 95, x + box_width - 15, y + 95)
            
            self.c.setFont("Helvetica-Bold", 28)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + 50, value)
            
            self.c.setFont("Helvetica", 12)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y + 20, label)
        
        # Before vs After comparison
        compare_y = y - 140
        
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, compare_y + 100, "BEFORE vs AFTER")
        
        comparisons = [
            ("Monthly Cost", "$23,149", "$4,021"),
            ("Resource Utilization", "35%", "100%"),
            ("Pipeline Duration", "4.5 hours", "1.8 hours"),
            ("Weekly Failures", "15 jobs", "2 jobs")
        ]
        
        table_width = 500
        table_x = (self.width - table_width) / 2
        row_height = 30
        
        for i, (metric, before, after) in enumerate(comparisons):
            row_y = compare_y + 60 - i * row_height
            
            # Alternating row background
            if i % 2 == 0:
                self.c.setFillColor(colors.HexColor('#252540'))
                self.c.rect(table_x, row_y - 5, table_width, row_height, fill=1, stroke=0)
            
            # Metric name
            self.c.setFont("Helvetica", 12)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(table_x + 20, row_y + 5, metric)
            
            # Before value
            self.c.setFillColor(ACCENT_ORANGE)
            self.c.drawCentredString(table_x + 280, row_y + 5, before)
            
            # Arrow
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(table_x + 350, row_y + 5, "→")
            
            # After value
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(ACCENT_GREEN)
            self.c.drawCentredString(table_x + 420, row_y + 5, after)
        
        # Final message
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(ACCENT_GREEN)
        self.c.drawCentredString(self.width/2, 100, "🏆 Achievement: Cloud Cost Champion")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 70, "Data Engineering Team | Q3-Q4 2025")

    def generate(self):
        """Generate all slides"""
        print("Generating Databricks Cost Optimization Presentation...")
        
        self.slide_1_title()
        print("  ✓ Slide 1: Title")
        
        self.slide_2_challenge()
        print("  ✓ Slide 2: The Challenge")
        
        self.slide_3_solution()
        print("  ✓ Slide 3: 3-Phase Solution")
        
        self.slide_4_cost_chart()
        print("  ✓ Slide 4: Cost Comparison")
        
        self.slide_5_trend()
        print("  ✓ Slide 5: Monthly Trend")
        
        self.slide_6_additional()
        print("  ✓ Slide 6: Additional Optimizations")
        
        self.slide_7_summary()
        print("  ✓ Slide 7: Summary & ROI")
        
        self.c.save()
        print(f"\n✅ Presentation saved to: {self.filename}")
        print(f"   File size: {os.path.getsize(self.filename) / 1024:.1f} KB")


if __name__ == "__main__":
    pdf = PresentationPDF("/workspace/Databricks_Cost_Optimization_Presentation.pdf")
    pdf.generate()
