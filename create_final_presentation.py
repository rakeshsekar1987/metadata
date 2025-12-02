#!/usr/bin/env python3
"""
Databricks Cost Optimization - Final Business Presentation
With Resource Groups and Monthly Decrease Trends
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
RED = colors.HexColor('#ef4444')
ORANGE = colors.HexColor('#f97316')
BLUE = colors.HexColor('#3b82f6')
PURPLE = colors.HexColor('#a855f7')


class FinalPresentationPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=landscape(LETTER))
        self.width = PAGE_WIDTH
        self.height = PAGE_HEIGHT
        self.slide_num = 0
        
        # Data
        self.months = ["July", "August", "September", "October", "November"]
        self.dev_costs = [62960, 63937, 48987, 36521, 38865]  # Photon - Development
        self.prod_costs = [60602, 60877, 54517, 45419, 35740]  # Photon - Production
        self.totals = [d + p for d, p in zip(self.dev_costs, self.prod_costs)]
        
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
        self.c.drawRightString(self.width - 40, 30, f"{self.slide_num} / 6")

    def format_currency(self, val):
        """Format as currency"""
        if val >= 1000:
            return f"${val/1000:.1f}K"
        return f"${val:.0f}"

    def calc_change(self, current, previous):
        """Calculate percentage change"""
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    # =========== SLIDE 1: Title ===========
    def slide_1_title(self):
        self.new_slide()
        
        # Main title
        self.c.setFont("Helvetica-Bold", 44)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 180, "Databricks Cost")
        self.c.drawCentredString(self.width/2, self.height - 235, "Optimization Results")
        
        # Total savings calculation
        total_july = self.totals[0]  # July total
        total_nov = self.totals[-1]  # November total
        total_saved = total_july - total_nov
        pct_saved = ((total_july - total_nov) / total_july) * 100
        
        # Big number
        self.c.setFont("Helvetica-Bold", 100)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, self.height/2 - 40, f"{pct_saved:.0f}%")
        
        # Subtitle
        self.c.setFont("Helvetica", 24)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, self.height/2 - 100, "Total Cost Reduction")
        
        # Savings amount
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, self.height/2 - 160, f"${total_saved:,.0f} saved per month")
        
        # Date
        self.c.setFont("Helvetica", 16)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 80, "July - November 2025")

    # =========== SLIDE 2: Before & After ===========
    def slide_2_before_after(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 80, "Before & After")
        
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        monthly_saved = july_total - nov_total
        
        # Left side - Before (July)
        left_x = self.width/4
        
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x, self.height - 150, "JULY 2025")
        
        self.c.setFont("Helvetica-Bold", 64)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x, self.height - 230, f"${july_total/1000:.0f}K")
        
        self.c.setFont("Helvetica", 16)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(left_x, self.height - 270, "per month")
        
        # Arrow in middle
        self.c.setFont("Helvetica-Bold", 60)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 220, "→")
        
        # Right side - After (November)
        right_x = 3*self.width/4
        
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(right_x, self.height - 150, "NOVEMBER 2025")
        
        self.c.setFont("Helvetica-Bold", 64)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(right_x, self.height - 230, f"${nov_total/1000:.0f}K")
        
        self.c.setFont("Helvetica", 16)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(right_x, self.height - 270, "per month")
        
        # Savings box at bottom
        box_width = 400
        box_x = (self.width - box_width) / 2
        box_y = 100
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect(box_x, box_y, box_width, 90, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 32)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, box_y + 55, f"${monthly_saved:,.0f}")
        
        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, box_y + 20, "saved every month")

    # =========== SLIDE 3: Resource Groups ===========
    def slide_3_resource_groups(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 70, "Cost by Resource Group")
        
        # Two resource groups side by side
        box_width = 320
        box_height = 320
        gap = 80
        start_x = (self.width - 2*box_width - gap) / 2
        y = self.height - 430
        
        # Development Resource Group
        dev_x = start_x
        dev_july = self.dev_costs[0]
        dev_nov = self.dev_costs[-1]
        dev_saved = dev_july - dev_nov
        dev_pct = ((dev_july - dev_nov) / dev_july) * 100
        
        # Box
        self.c.setFillColor(colors.HexColor('#1e3a5f'))
        self.c.roundRect(dev_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        # Header
        self.c.setFillColor(BLUE)
        self.c.roundRect(dev_x, y + box_height - 50, box_width, 50, 12, fill=1, stroke=0)
        self.c.setFillColor(colors.HexColor('#1e3a5f'))
        self.c.rect(dev_x, y + box_height - 50, box_width, 20, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 35, "Photon - Development")
        
        self.c.setFont("Helvetica", 12)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 65, "(Dev + QA Environments)")
        
        # July vs November
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 100, f"July: ${dev_july:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 130, "↓")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 160, f"November: ${dev_nov:,.0f}")
        
        # Savings
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(dev_x + box_width/2, y + 70, f"-{dev_pct:.0f}%")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(dev_x + box_width/2, y + 35, f"${dev_saved:,.0f} saved/month")
        
        # Production Resource Group
        prod_x = start_x + box_width + gap
        prod_july = self.prod_costs[0]
        prod_nov = self.prod_costs[-1]
        prod_saved = prod_july - prod_nov
        prod_pct = ((prod_july - prod_nov) / prod_july) * 100
        
        # Box
        self.c.setFillColor(colors.HexColor('#1f3d2a'))
        self.c.roundRect(prod_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        # Header
        self.c.setFillColor(GREEN)
        self.c.roundRect(prod_x, y + box_height - 50, box_width, 50, 12, fill=1, stroke=0)
        self.c.setFillColor(colors.HexColor('#1f3d2a'))
        self.c.rect(prod_x, y + box_height - 50, box_width, 20, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 35, "Photon - Production")
        
        self.c.setFont("Helvetica", 12)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 65, "(Production Environment)")
        
        # July vs November
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 100, f"July: ${prod_july:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 130, "↓")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 160, f"November: ${prod_nov:,.0f}")
        
        # Savings
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(prod_x + box_width/2, y + 70, f"-{prod_pct:.0f}%")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(prod_x + box_width/2, y + 35, f"${prod_saved:,.0f} saved/month")

    # =========== SLIDE 4: Monthly Trend with Decrease ===========
    def slide_4_monthly_trend(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "Monthly Cost Trend")
        
        # Table header
        table_x = 80
        table_y = self.height - 140
        col_widths = [120, 110, 110, 110]  # Month, Dev, Prod, Total
        row_height = 50
        
        headers = ["Month", "Development", "Production", "Total"]
        
        # Header row
        self.c.setFillColor(colors.HexColor('#2a2d40'))
        self.c.rect(table_x, table_y - row_height, sum(col_widths) + 200, row_height, fill=1, stroke=0)
        
        x = table_x
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(WHITE)
        for i, header in enumerate(headers):
            self.c.drawCentredString(x + col_widths[i]/2, table_y - 30, header)
            x += col_widths[i]
        
        # Add "Change" header
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(x + 100, table_y - 30, "Monthly Change")
        
        # Data rows
        prev_total = None
        for row_idx, (month, dev, prod, total) in enumerate(zip(self.months, self.dev_costs, self.prod_costs, self.totals)):
            row_y = table_y - (row_idx + 2) * row_height
            
            # Alternating row background
            if row_idx % 2 == 0:
                self.c.setFillColor(colors.HexColor('#1a1d2e'))
            else:
                self.c.setFillColor(colors.HexColor('#22253a'))
            self.c.rect(table_x, row_y, sum(col_widths) + 200, row_height, fill=1, stroke=0)
            
            x = table_x
            
            # Month
            self.c.setFont("Helvetica-Bold", 13)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[0]/2, row_y + 18, month)
            x += col_widths[0]
            
            # Development
            self.c.setFont("Helvetica", 13)
            self.c.setFillColor(BLUE)
            self.c.drawCentredString(x + col_widths[1]/2, row_y + 18, f"${dev:,.0f}")
            x += col_widths[1]
            
            # Production
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[2]/2, row_y + 18, f"${prod:,.0f}")
            x += col_widths[2]
            
            # Total
            self.c.setFont("Helvetica-Bold", 13)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[3]/2, row_y + 18, f"${total:,.0f}")
            x += col_widths[3]
            
            # Change from previous month
            if prev_total is not None:
                change = total - prev_total
                change_pct = (change / prev_total) * 100
                
                if change < 0:
                    self.c.setFillColor(GREEN)
                    arrow = "↓"
                    change_text = f"{arrow} ${abs(change):,.0f} ({abs(change_pct):.1f}%)"
                else:
                    self.c.setFillColor(RED)
                    arrow = "↑"
                    change_text = f"{arrow} ${change:,.0f} (+{change_pct:.1f}%)"
                
                self.c.setFont("Helvetica-Bold", 12)
                self.c.drawCentredString(x + 100, row_y + 18, change_text)
            else:
                self.c.setFont("Helvetica", 12)
                self.c.setFillColor(LIGHT_GRAY)
                self.c.drawCentredString(x + 100, row_y + 18, "—")
            
            prev_total = total
        
        # Total decrease summary box
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        total_decrease = july_total - nov_total
        total_pct = ((july_total - nov_total) / july_total) * 100
        
        box_y = 70
        box_width = 500
        box_x = (self.width - box_width) / 2
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect(box_x, box_y, box_width, 70, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, box_y + 42, f"Total Decrease: ${total_decrease:,.0f}/month ({total_pct:.0f}%)")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, box_y + 15, "from July to November 2025")

    # =========== SLIDE 5: What We Did ===========
    def slide_5_what_we_did(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 70, "What We Did")
        
        # Three phases
        phases = [
            ("1", "August", "Turned off\nalways-on servers", 
             "Removed pool clusters\nrunning 24/7", BLUE),
            ("2", "September", "Right-sized\nmachines", 
             "Standard_D4s_v3\n3-5 workers, 100% usage", GREEN),
            ("3", "October", "Organized\njob groups", 
             "Dedicated clusters\nper task group", ORANGE)
        ]
        
        box_width = 210
        box_height = 220
        gap = 40
        total_width = 3 * box_width + 2 * gap
        start_x = (self.width - total_width) / 2
        y = self.height - 360
        
        for i, (num, month, title, details, color) in enumerate(phases):
            x = start_x + i * (box_width + gap)
            
            # Box
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, y, box_width, box_height, 12, fill=1, stroke=0)
            
            # Phase number circle
            self.c.setFillColor(color)
            self.c.circle(x + box_width/2, y + box_height - 35, 28, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 26)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + box_width/2, y + box_height - 45, num)
            
            # Month
            self.c.setFont("Helvetica", 13)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + box_height - 75, month)
            
            # Title
            self.c.setFont("Helvetica-Bold", 15)
            self.c.setFillColor(WHITE)
            title_lines = title.split('\n')
            for j, line in enumerate(title_lines):
                self.c.drawCentredString(x + box_width/2, y + box_height - 105 - j*20, line)
            
            # Details
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            detail_lines = details.split('\n')
            for j, line in enumerate(detail_lines):
                self.c.drawCentredString(x + box_width/2, y + 50 - j*16, line)
        
        # Bottom note
        self.c.setFont("Helvetica", 16)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 80, "Each phase contributed to continuous cost reduction")

    # =========== SLIDE 6: Summary ===========
    def slide_6_summary(self):
        self.new_slide()
        
        # Title
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 70, "Summary")
        
        # Calculate totals
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        monthly_saved = july_total - nov_total
        annual_saved = monthly_saved * 12
        pct_saved = ((july_total - nov_total) / july_total) * 100
        
        # Big metrics
        metrics = [
            (f"${monthly_saved/1000:.0f}K", "Saved Per Month", GREEN),
            (f"${annual_saved/1000:.0f}K", "Saved Per Year", GREEN),
            (f"{pct_saved:.0f}%", "Cost Reduction", BLUE)
        ]
        
        box_width = 200
        gap = 60
        total_width = 3 * box_width + 2 * gap
        start_x = (self.width - total_width) / 2
        y = self.height - 220
        
        for i, (number, label, color) in enumerate(metrics):
            x = start_x + i * (box_width + gap)
            
            # Number
            self.c.setFont("Helvetica-Bold", 52)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y, number)
            
            # Label
            self.c.setFont("Helvetica", 16)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y - 35, label)
        
        # Resource group breakdown
        dev_saved = self.dev_costs[0] - self.dev_costs[-1]
        prod_saved = self.prod_costs[0] - self.prod_costs[-1]
        
        breakdown_y = self.height - 350
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, breakdown_y, "Savings by Resource Group")
        
        # Dev savings
        self.c.setFillColor(colors.HexColor('#1e3a5f'))
        self.c.roundRect(self.width/2 - 250, breakdown_y - 70, 220, 50, 8, fill=1, stroke=0)
        
        self.c.setFont("Helvetica", 12)
        self.c.setFillColor(BLUE)
        self.c.drawCentredString(self.width/2 - 140, breakdown_y - 35, "Photon - Development")
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2 - 140, breakdown_y - 55, f"${dev_saved:,.0f}/month")
        
        # Prod savings
        self.c.setFillColor(colors.HexColor('#1f3d2a'))
        self.c.roundRect(self.width/2 + 30, breakdown_y - 70, 220, 50, 8, fill=1, stroke=0)
        
        self.c.setFont("Helvetica", 12)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2 + 140, breakdown_y - 35, "Photon - Production")
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2 + 140, breakdown_y - 55, f"${prod_saved:,.0f}/month")
        
        # Bottom message
        self.c.setFillColor(colors.HexColor('#2a2d40'))
        self.c.roundRect(100, 70, self.width - 200, 60, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, 100, "Same performance, significantly lower cost")

    def generate(self):
        """Generate all slides"""
        print("Generating Final Business Presentation...")
        print(f"\nData Summary:")
        print(f"  Photon - Development: ${self.dev_costs[0]:,} → ${self.dev_costs[-1]:,}")
        print(f"  Photon - Production:  ${self.prod_costs[0]:,} → ${self.prod_costs[-1]:,}")
        print(f"  Total:                ${self.totals[0]:,} → ${self.totals[-1]:,}")
        print(f"  Savings:              ${self.totals[0] - self.totals[-1]:,}/month\n")
        
        self.slide_1_title()
        print("  ✓ Slide 1: Title & Key Metric")
        
        self.slide_2_before_after()
        print("  ✓ Slide 2: Before & After")
        
        self.slide_3_resource_groups()
        print("  ✓ Slide 3: Resource Groups Breakdown")
        
        self.slide_4_monthly_trend()
        print("  ✓ Slide 4: Monthly Trend with Changes")
        
        self.slide_5_what_we_did()
        print("  ✓ Slide 5: What We Did (3 Phases)")
        
        self.slide_6_summary()
        print("  ✓ Slide 6: Summary")
        
        self.c.save()
        print(f"\n✅ Presentation saved to: {self.filename}")
        print(f"   File size: {os.path.getsize(self.filename) / 1024:.1f} KB")


if __name__ == "__main__":
    pdf = FinalPresentationPDF("/workspace/Cost_Optimization_Final.pdf")
    pdf.generate()
