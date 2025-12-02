#!/usr/bin/env python3
"""
Databricks Cost Optimization - Simple Business Presentation
Clean, minimal design for executive/business audience
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
import os

# Page size
PAGE_WIDTH, PAGE_HEIGHT = landscape(LETTER)

# Simple color scheme
DARK_BG = colors.HexColor('#1e2130')
WHITE = colors.white
LIGHT_GRAY = colors.HexColor('#b0b0b0')
GREEN = colors.HexColor('#22c55e')
ORANGE = colors.HexColor('#f97316')
BLUE = colors.HexColor('#3b82f6')


class SimplePresentationPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=landscape(LETTER))
        self.width = PAGE_WIDTH
        self.height = PAGE_HEIGHT
        self.slide_num = 0
        
    def draw_background(self):
        """Simple dark background"""
        self.c.setFillColor(DARK_BG)
        self.c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
    def new_slide(self):
        """Start a new slide"""
        if self.slide_num > 0:
            self.c.showPage()
        self.slide_num += 1
        self.draw_background()
        
        # Simple footer
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawRightString(self.width - 40, 30, f"{self.slide_num} / 5")

    # =========== SLIDE 1: Title ===========
    def slide_1_title(self):
        self.new_slide()
        
        # Main title
        self.c.setFont("Helvetica-Bold", 48)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 200, "Cost Optimization")
        self.c.drawCentredString(self.width/2, self.height - 260, "Results")
        
        # Big number
        self.c.setFont("Helvetica-Bold", 120)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, self.height/2 - 60, "83%")
        
        # Subtitle
        self.c.setFont("Helvetica", 28)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, self.height/2 - 130, "Reduction in Monthly Costs")
        
        # Date
        self.c.setFont("Helvetica", 16)
        self.c.drawCentredString(self.width/2, 80, "August - November 2025")

    # =========== SLIDE 2: Before & After ===========
    def slide_2_before_after(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 80, "Before & After")
        
        # Left side - Before
        left_x = self.width/4
        
        self.c.setFont("Helvetica", 20)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x, self.height - 160, "BEFORE")
        
        self.c.setFont("Helvetica-Bold", 72)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x, self.height - 260, "$23K")
        
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(left_x, self.height - 300, "per month")
        self.c.drawCentredString(left_x, self.height - 330, "(August 2025)")
        
        # Arrow in middle
        self.c.setFont("Helvetica-Bold", 60)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 250, "→")
        
        # Right side - After
        right_x = 3*self.width/4
        
        self.c.setFont("Helvetica", 20)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(right_x, self.height - 160, "AFTER")
        
        self.c.setFont("Helvetica-Bold", 72)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(right_x, self.height - 260, "$4K")
        
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(right_x, self.height - 300, "per month")
        self.c.drawCentredString(right_x, self.height - 330, "(November 2025)")
        
        # Savings box at bottom
        box_width = 350
        box_x = (self.width - box_width) / 2
        box_y = 100
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect(box_x, box_y, box_width, 80, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, box_y + 45, "$19,000+ saved")
        
        self.c.setFont("Helvetica", 16)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, box_y + 15, "every month")

    # =========== SLIDE 3: What We Did ===========
    def slide_3_what_we_did(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 80, "What We Did")
        
        # Three phases - simple boxes
        phases = [
            ("1", "August", "Turned off\nalways-on servers", BLUE),
            ("2", "September", "Right-sized\nour machines", GREEN),
            ("3", "October", "Organized jobs\ninto groups", ORANGE)
        ]
        
        box_width = 200
        box_height = 180
        gap = 60
        total_width = 3 * box_width + 2 * gap
        start_x = (self.width - total_width) / 2
        y = self.height/2 - 80
        
        for i, (num, month, desc, color) in enumerate(phases):
            x = start_x + i * (box_width + gap)
            
            # Box
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, y, box_width, box_height, 12, fill=1, stroke=0)
            
            # Phase number circle
            self.c.setFillColor(color)
            self.c.circle(x + box_width/2, y + box_height - 30, 25, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 24)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + box_width/2, y + box_height - 40, num)
            
            # Month
            self.c.setFont("Helvetica", 14)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + box_height - 70, month)
            
            # Description
            self.c.setFont("Helvetica", 16)
            self.c.setFillColor(WHITE)
            lines = desc.split('\n')
            for j, line in enumerate(lines):
                self.c.drawCentredString(x + box_width/2, y + 60 - j*22, line)
        
        # Simple result
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 100, "Each phase reduced costs further")

    # =========== SLIDE 4: Simple Chart ===========
    def slide_4_chart(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 80, "Monthly Cost Trend")
        
        # Data
        months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        values = [15, 22, 23, 17, 5, 4]  # in thousands
        
        # Chart dimensions
        chart_x = 120
        chart_y = 120
        chart_width = self.width - 240
        chart_height = 280
        
        # Draw simple bars
        bar_width = 80
        gap = (chart_width - 6 * bar_width) / 7
        max_val = 25
        
        for i, (month, val) in enumerate(zip(months, values)):
            x = chart_x + gap + i * (bar_width + gap)
            bar_height = (val / max_val) * chart_height
            
            # Color: orange for high, transitioning to green
            if val > 15:
                color = ORANGE
            elif val > 8:
                color = colors.HexColor('#eab308')
            else:
                color = GREEN
            
            # Bar
            self.c.setFillColor(color)
            self.c.roundRect(x, chart_y, bar_width, bar_height, 5, fill=1, stroke=0)
            
            # Value on bar
            self.c.setFont("Helvetica-Bold", 18)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + bar_width/2, chart_y + bar_height + 15, f"${val}K")
            
            # Month label
            self.c.setFont("Helvetica", 14)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + bar_width/2, chart_y - 25, month)
        
        # Baseline
        self.c.setStrokeColor(colors.HexColor('#444444'))
        self.c.setLineWidth(2)
        self.c.line(chart_x, chart_y, chart_x + chart_width, chart_y)
        
        # Annotation
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawString(self.width - 200, chart_y - 25, "↓ Costs going down")

    # =========== SLIDE 5: Key Takeaways ===========
    def slide_5_takeaways(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 80, "Key Takeaways")
        
        # Three big numbers
        metrics = [
            ("$229K", "Saved Per Year", GREEN),
            ("83%", "Cost Reduction", BLUE),
            ("60%", "Faster Jobs", ORANGE)
        ]
        
        box_width = 200
        gap = 60
        total_width = 3 * box_width + 2 * gap
        start_x = (self.width - total_width) / 2
        y = self.height/2 - 20
        
        for i, (number, label, color) in enumerate(metrics):
            x = start_x + i * (box_width + gap)
            
            # Number
            self.c.setFont("Helvetica-Bold", 56)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + 30, number)
            
            # Label
            self.c.setFont("Helvetica", 18)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y - 20, label)
        
        # Bottom message
        self.c.setFillColor(colors.HexColor('#2a2d40'))
        self.c.roundRect(100, 80, self.width - 200, 70, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, 120, "Same work, lower cost, faster results")

    def generate(self):
        """Generate all slides"""
        print("Generating Simple Business Presentation...")
        
        self.slide_1_title()
        print("  ✓ Slide 1: Title (83% Reduction)")
        
        self.slide_2_before_after()
        print("  ✓ Slide 2: Before & After ($23K → $4K)")
        
        self.slide_3_what_we_did()
        print("  ✓ Slide 3: What We Did (3 Phases)")
        
        self.slide_4_chart()
        print("  ✓ Slide 4: Monthly Trend Chart")
        
        self.slide_5_takeaways()
        print("  ✓ Slide 5: Key Takeaways")
        
        self.c.save()
        print(f"\n✅ Presentation saved to: {self.filename}")
        print(f"   File size: {os.path.getsize(self.filename) / 1024:.1f} KB")


if __name__ == "__main__":
    pdf = SimplePresentationPDF("/workspace/Cost_Optimization_Simple.pdf")
    pdf.generate()
