# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Databricks Cost Optimization - Detailed Business Presentation
With Data Pointers and 3-Phase Highlights
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
import os

# Page size
PAGE_WIDTH, PAGE_HEIGHT = landscape(LETTER)

# Color scheme
DARK_BG = colors.HexColor('#1e2130')
WHITE = colors.white
LIGHT_GRAY = colors.HexColor('#b0b0b0')
GREEN = colors.HexColor('#22c55e')
RED = colors.HexColor('#ef4444')
ORANGE = colors.HexColor('#f97316')
BLUE = colors.HexColor('#3b82f6')
PURPLE = colors.HexColor('#a855f7')
YELLOW = colors.HexColor('#eab308')


class DetailedPresentationPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=landscape(LETTER))
        self.width = PAGE_WIDTH
        self.height = PAGE_HEIGHT
        self.slide_num = 0
        
        # Data from user
        self.months = ["July", "August", "September", "October", "November"]
        self.dev_costs = [62960, 63937, 48987, 36521, 38865]  # Photon - Development
        self.prod_costs = [60602, 60877, 54517, 45419, 35740]  # Photon - Production
        self.totals = [d + p for d, p in zip(self.dev_costs, self.prod_costs)]
        
    def draw_background(self):
        self.c.setFillColor(DARK_BG)
        self.c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
    def new_slide(self):
        if self.slide_num > 0:
            self.c.showPage()
        self.slide_num += 1
        self.draw_background()
        
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawRightString(self.width - 40, 30, f"{self.slide_num} / 7")

    # =========== SLIDE 1: Title ===========
    def slide_1_title(self):
        self.new_slide()
        
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        total_saved = july_total - nov_total
        pct_saved = ((july_total - nov_total) / july_total) * 100
        
        self.c.setFont("Helvetica-Bold", 44)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 160, "Databricks Cost")
        self.c.drawCentredString(self.width/2, self.height - 215, "Optimization Results")
        
        # Big percentage
        self.c.setFont("Helvetica-Bold", 110)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, self.height/2 - 30, f"{pct_saved:.0f}%")
        
        self.c.setFont("Helvetica", 24)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, self.height/2 - 90, "Total Cost Reduction")
        
        # Key metrics row
        metrics = [
            (f"${total_saved:,.0f}", "Saved/Month"),
            (f"${total_saved * 12:,.0f}", "Saved/Year"),
            ("3 Phases", "Optimization")
        ]
        
        box_width = 180
        gap = 40
        start_x = (self.width - 3*box_width - 2*gap) / 2
        y = 100
        
        for i, (val, label) in enumerate(metrics):
            x = start_x + i * (box_width + gap)
            
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, y, box_width, 60, 8, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 18)
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + box_width/2, y + 35, val)
            
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y + 12, label)

    # =========== SLIDE 2: Before & After ===========
    def slide_2_before_after(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 70, "Before & After")
        
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        monthly_saved = july_total - nov_total
        
        # Before box
        left_x = 100
        box_width = 280
        box_height = 200
        y = self.height - 320
        
        self.c.setFillColor(colors.HexColor('#3d2020'))
        self.c.roundRect(left_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height - 30, "JULY 2025")
        
        self.c.setFont("Helvetica-Bold", 52)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height/2, f"${july_total/1000:.0f}K")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(left_x + box_width/2, y + 30, "per month")
        
        # Arrow
        arrow_x = left_x + box_width + 40
        self.c.setFont("Helvetica-Bold", 50)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(arrow_x + 60, y + box_height/2, "->")
        
        # After box
        right_x = self.width - 100 - box_width
        
        self.c.setFillColor(colors.HexColor('#1a3d1a'))
        self.c.roundRect(right_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(right_x + box_width/2, y + box_height - 30, "NOVEMBER 2025")
        
        self.c.setFont("Helvetica-Bold", 52)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(right_x + box_width/2, y + box_height/2, f"${nov_total/1000:.0f}K")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(right_x + box_width/2, y + 30, "per month")
        
        # Savings highlight
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 350)/2, 80, 350, 70, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 120, f"${monthly_saved:,.0f} saved/month")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 95, f"${monthly_saved * 12:,.0f} annually")

    # =========== SLIDE 3: 3 Phases with Data ===========
    def slide_3_phases(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "3-Phase Optimization Journey")
        
        # Calculate phase impacts
        aug_total = self.totals[1]  # $124,814
        sep_total = self.totals[2]  # $103,504
        phase1_savings = aug_total - sep_total
        phase1_pct = (phase1_savings / aug_total) * 100
        
        oct_total = self.totals[3]  # $81,940
        phase2_savings = sep_total - oct_total
        phase2_pct = (phase2_savings / sep_total) * 100
        
        nov_total = self.totals[4]  # $74,605
        phase3_savings = oct_total - nov_total
        phase3_pct = (phase3_savings / oct_total) * 100
        
        phases = [
            ("PHASE 1", "August 2025", "Pool Cluster\nDecommissioning",
             ["Removed 24/7 pool clusters", "Switched to on-demand compute", "Added auto-termination (15 min)"],
             f"${phase1_savings:,.0f}", f"{phase1_pct:.0f}%", BLUE),
            ("PHASE 2", "September 2025", "Right-Sizing\nCompute",
             ["Standard_D4s_v3 VMs", "3 to 5 workers per cluster", "100% resource utilization"],
             f"${phase2_savings:,.0f}", f"{phase2_pct:.0f}%", GREEN),
            ("PHASE 3", "October 2025", "Task Group\nClustering",
             ["Tables grouped by domain", "Dedicated cluster per group", "Reduced driver contention"],
             f"${phase3_savings:,.0f}", f"{phase3_pct:.0f}%", ORANGE)
        ]
        
        box_width = 230
        box_height = 320
        gap = 30
        start_x = (self.width - 3*box_width - 2*gap) / 2
        y = self.height - 420
        
        for i, (phase, date, title, points, savings, pct, color) in enumerate(phases):
            x = start_x + i * (box_width + gap)
            
            # Main box
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, y, box_width, box_height, 12, fill=1, stroke=0)
            
            # Colored header
            self.c.setFillColor(color)
            self.c.roundRect(x, y + box_height - 55, box_width, 55, 12, fill=1, stroke=0)
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.rect(x, y + box_height - 55, box_width, 25, fill=1, stroke=0)
            
            # Phase label
            self.c.setFont("Helvetica-Bold", 16)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + box_width/2, y + box_height - 38, phase)
            
            # Date
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y + box_height - 70, date)
            
            # Title
            self.c.setFont("Helvetica-Bold", 13)
            self.c.setFillColor(WHITE)
            title_lines = title.split('\n')
            for j, line in enumerate(title_lines):
                self.c.drawCentredString(x + box_width/2, y + box_height - 95 - j*16, line)
            
            # Bullet points
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            for j, point in enumerate(points):
                self.c.drawString(x + 15, y + box_height - 145 - j*18, f"* {point}")
            
            # Savings box at bottom
            self.c.setFillColor(colors.HexColor('#1a3a1a'))
            self.c.roundRect(x + 15, y + 15, box_width - 30, 55, 8, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 18)
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + box_width/2, y + 50, savings)
            
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y + 28, f"saved ({pct} reduction)")

    # =========== SLIDE 4: Data Table with Trends ===========
    def slide_4_data_table(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 55, "Monthly Cost Breakdown")
        
        # Table
        table_x = 60
        table_y = self.height - 110
        col_widths = [100, 120, 120, 120, 150]
        row_height = 45
        
        headers = ["Month", "Development", "Production", "Total", "Change"]
        
        # Header row
        self.c.setFillColor(colors.HexColor('#3a3d50'))
        self.c.rect(table_x, table_y - row_height, sum(col_widths), row_height, fill=1, stroke=0)
        
        x = table_x
        self.c.setFont("Helvetica-Bold", 13)
        self.c.setFillColor(WHITE)
        for i, header in enumerate(headers):
            self.c.drawCentredString(x + col_widths[i]/2, table_y - 28, header)
            x += col_widths[i]
        
        # Data rows with phase indicators
        phase_colors = {
            1: BLUE,    # August - Phase 1
            2: GREEN,   # September - Phase 2
            3: ORANGE,  # October - Phase 3
            4: ORANGE   # November - Phase 3 continued
        }
        
        prev_total = None
        for row_idx, (month, dev, prod, total) in enumerate(zip(self.months, self.dev_costs, self.prod_costs, self.totals)):
            row_y = table_y - (row_idx + 2) * row_height
            
            # Row background
            if row_idx % 2 == 0:
                self.c.setFillColor(colors.HexColor('#1a1d2e'))
            else:
                self.c.setFillColor(colors.HexColor('#22253a'))
            self.c.rect(table_x, row_y, sum(col_widths), row_height, fill=1, stroke=0)
            
            # Phase indicator bar on left
            if row_idx in phase_colors:
                self.c.setFillColor(phase_colors[row_idx])
                self.c.rect(table_x, row_y, 4, row_height, fill=1, stroke=0)
            
            x = table_x
            
            # Month
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[0]/2, row_y + 17, month)
            x += col_widths[0]
            
            # Development
            self.c.setFont("Helvetica", 12)
            self.c.setFillColor(BLUE)
            self.c.drawCentredString(x + col_widths[1]/2, row_y + 17, f"${dev:,.0f}")
            x += col_widths[1]
            
            # Production
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[2]/2, row_y + 17, f"${prod:,.0f}")
            x += col_widths[2]
            
            # Total
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[3]/2, row_y + 17, f"${total:,.0f}")
            x += col_widths[3]
            
            # Change
            if prev_total is not None:
                change = total - prev_total
                change_pct = (change / prev_total) * 100
                
                if change < 0:
                    self.c.setFillColor(GREEN)
                    self.c.setFont("Helvetica-Bold", 12)
                    self.c.drawCentredString(x + col_widths[4]/2, row_y + 17, 
                        f"v ${abs(change):,.0f} ({abs(change_pct):.1f}%)")
                else:
                    self.c.setFillColor(RED)
                    self.c.setFont("Helvetica-Bold", 12)
                    self.c.drawCentredString(x + col_widths[4]/2, row_y + 17, 
                        f"^ ${change:,.0f} (+{change_pct:.1f}%)")
            else:
                self.c.setFont("Helvetica", 12)
                self.c.setFillColor(LIGHT_GRAY)
                self.c.drawCentredString(x + col_widths[4]/2, row_y + 17, "Baseline")
            
            prev_total = total
        
        # Phase legend
        legend_y = row_y - 60
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(WHITE)
        self.c.drawString(table_x, legend_y, "Phase Legend:")
        
        legends = [
            (BLUE, "Phase 1: Pool Removal"),
            (GREEN, "Phase 2: Right-Sizing"),
            (ORANGE, "Phase 3: Task Groups")
        ]
        
        x = table_x + 120
        for color, label in legends:
            self.c.setFillColor(color)
            self.c.rect(x, legend_y - 3, 15, 15, fill=1, stroke=0)
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 22, legend_y, label)
            x += 180
        
        # Total summary
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        total_saved = july_total - nov_total
        total_pct = (total_saved / july_total) * 100
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 450)/2, 55, 450, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 85, f"Total Savings: ${total_saved:,.0f}/month ({total_pct:.0f}% reduction)")

    # =========== SLIDE 5: Key Data Insights ===========
    def slide_5_insights(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "Key Data Insights")
        
        # Calculate insights
        july_total = self.totals[0]
        aug_total = self.totals[1]
        sep_total = self.totals[2]
        oct_total = self.totals[3]
        nov_total = self.totals[4]
        
        peak_month = "August"
        peak_value = aug_total
        lowest_month = "November"
        lowest_value = nov_total
        
        biggest_drop_value = aug_total - sep_total
        biggest_drop_pct = (biggest_drop_value / aug_total) * 100
        
        dev_reduction = self.dev_costs[0] - self.dev_costs[-1]
        prod_reduction = self.prod_costs[0] - self.prod_costs[-1]
        
        insights = [
            ("1", "Peak Cost", f"${peak_value:,.0f}", f"{peak_month} 2025 - before optimization", ORANGE),
            ("2", "Lowest Cost", f"${lowest_value:,.0f}", f"{lowest_month} 2025 - after all phases", GREEN),
            ("3", "Biggest Monthly Drop", f"${biggest_drop_value:,.0f}", f"Aug to Sep ({biggest_drop_pct:.0f}% reduction)", BLUE),
            ("4", "Development Savings", f"${dev_reduction:,.0f}/mo", "Photon - Development (Dev + QA)", BLUE),
            ("5", "Production Savings", f"${prod_reduction:,.0f}/mo", "Photon - Production", GREEN),
            ("6", "Annual Projection", f"${(july_total - nov_total) * 12:,.0f}", "If maintained for 12 months", YELLOW)
        ]
        
        # 2x3 grid
        box_width = 230
        box_height = 110
        h_gap = 30
        v_gap = 20
        
        start_x = (self.width - 3*box_width - 2*h_gap) / 2
        start_y = self.height - 150
        
        for i, (icon, title, value, desc, color) in enumerate(insights):
            row = i // 3
            col = i % 3
            
            x = start_x + col * (box_width + h_gap)
            y = start_y - row * (box_height + v_gap) - box_height
            
            # Box
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, y, box_width, box_height, 10, fill=1, stroke=0)
            
            # Color accent line
            self.c.setFillColor(color)
            self.c.rect(x, y + box_height - 5, box_width, 5, fill=1, stroke=0)
            
            # Title
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(color)
            self.c.drawString(x + 15, y + box_height - 28, title)
            
            # Value
            self.c.setFont("Helvetica-Bold", 24)
            self.c.setFillColor(WHITE)
            self.c.drawString(x + 15, y + box_height - 60, value)
            
            # Description
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 15, y + 15, desc)

    # =========== SLIDE 6: Resource Group Comparison ===========
    def slide_6_resource_groups(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "Resource Group Comparison")
        
        # Visual comparison bars
        chart_y = self.height - 160
        bar_height = 35
        max_val = max(max(self.dev_costs), max(self.prod_costs))
        chart_width = self.width - 250
        
        # Headers
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(BLUE)
        self.c.drawString(100, chart_y + 30, "Photon - Development (Dev + QA)")
        
        self.c.setFillColor(GREEN)
        self.c.drawString(100, chart_y - 180, "Photon - Production")
        
        # Development bars
        for i, (month, val) in enumerate(zip(self.months, self.dev_costs)):
            y = chart_y - i * (bar_height + 5)
            bar_width = (val / max_val) * (chart_width - 100)
            
            # Month label
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawRightString(95, y + 10, month[:3])
            
            # Bar
            self.c.setFillColor(BLUE)
            self.c.roundRect(100, y, bar_width, bar_height - 5, 3, fill=1, stroke=0)
            
            # Value
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(WHITE)
            self.c.drawString(105, y + 10, f"${val:,.0f}")
        
        # Production bars
        prod_start_y = chart_y - 210
        for i, (month, val) in enumerate(zip(self.months, self.prod_costs)):
            y = prod_start_y - i * (bar_height + 5)
            bar_width = (val / max_val) * (chart_width - 100)
            
            # Month label
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawRightString(95, y + 10, month[:3])
            
            # Bar
            self.c.setFillColor(GREEN)
            self.c.roundRect(100, y, bar_width, bar_height - 5, 3, fill=1, stroke=0)
            
            # Value
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(WHITE)
            self.c.drawString(105, y + 10, f"${val:,.0f}")
        
        # Summary boxes on right
        dev_saved = self.dev_costs[0] - self.dev_costs[-1]
        dev_pct = (dev_saved / self.dev_costs[0]) * 100
        prod_saved = self.prod_costs[0] - self.prod_costs[-1]
        prod_pct = (prod_saved / self.prod_costs[0]) * 100
        
        box_x = self.width - 180
        
        # Dev summary
        self.c.setFillColor(colors.HexColor('#1e3a5f'))
        self.c.roundRect(box_x, chart_y - 80, 150, 100, 8, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(BLUE)
        self.c.drawCentredString(box_x + 75, chart_y - 20, f"-{dev_pct:.0f}%")
        
        self.c.setFont("Helvetica", 11)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(box_x + 75, chart_y - 50, f"${dev_saved:,.0f}")
        self.c.drawCentredString(box_x + 75, chart_y - 68, "saved/month")
        
        # Prod summary
        self.c.setFillColor(colors.HexColor('#1f3d2a'))
        self.c.roundRect(box_x, prod_start_y - 80, 150, 100, 8, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(box_x + 75, prod_start_y - 20, f"-{prod_pct:.0f}%")
        
        self.c.setFont("Helvetica", 11)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(box_x + 75, prod_start_y - 50, f"${prod_saved:,.0f}")
        self.c.drawCentredString(box_x + 75, prod_start_y - 68, "saved/month")

    # =========== SLIDE 7: Summary ===========
    def slide_7_summary(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "Summary")
        
        july_total = self.totals[0]
        nov_total = self.totals[-1]
        monthly_saved = july_total - nov_total
        annual_saved = monthly_saved * 12
        pct_saved = (monthly_saved / july_total) * 100
        
        # Big numbers
        metrics = [
            (f"${monthly_saved/1000:.0f}K", "Saved/Month", GREEN),
            (f"${annual_saved/1000:.0f}K", "Saved/Year", GREEN),
            (f"{pct_saved:.0f}%", "Reduction", BLUE)
        ]
        
        box_width = 200
        gap = 50
        start_x = (self.width - 3*box_width - 2*gap) / 2
        y = self.height - 180
        
        for i, (val, label, color) in enumerate(metrics):
            x = start_x + i * (box_width + gap)
            
            self.c.setFont("Helvetica-Bold", 56)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y, val)
            
            self.c.setFont("Helvetica", 16)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y - 35, label)
        
        # Phase summary
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 290, "Optimization Phases")
        
        phases = [
            ("Phase 1", "Pool Removal", "Aug", BLUE),
            ("Phase 2", "Right-Sizing", "Sep", GREEN),
            ("Phase 3", "Task Groups", "Oct", ORANGE)
        ]
        
        phase_width = 180
        phase_start = (self.width - 3*phase_width - 40) / 2
        phase_y = self.height - 370
        
        for i, (phase, action, month, color) in enumerate(phases):
            x = phase_start + i * (phase_width + 20)
            
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, phase_y, phase_width, 60, 8, fill=1, stroke=0)
            
            self.c.setFillColor(color)
            self.c.rect(x, phase_y + 55, phase_width, 5, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + phase_width/2, phase_y + 38, f"{phase} ({month})")
            
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + phase_width/2, phase_y + 15, action)
        
        # Bottom message
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect(120, 70, self.width - 240, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, 95, "Same workload, lower cost, better performance")

    def generate(self):
        print("Generating Detailed Business Presentation...")
        print("")
        print("Data Summary:")
        print(f"   Photon - Development: ${self.dev_costs[0]:,} -> ${self.dev_costs[-1]:,} (saved ${self.dev_costs[0] - self.dev_costs[-1]:,})")
        print(f"   Photon - Production:  ${self.prod_costs[0]:,} -> ${self.prod_costs[-1]:,} (saved ${self.prod_costs[0] - self.prod_costs[-1]:,})")
        print(f"   Total:                ${self.totals[0]:,} -> ${self.totals[-1]:,} (saved ${self.totals[0] - self.totals[-1]:,})")
        print("")
        
        self.slide_1_title()
        print("  Done: Slide 1 - Title & Key Metrics")
        
        self.slide_2_before_after()
        print("  Done: Slide 2 - Before & After Comparison")
        
        self.slide_3_phases()
        print("  Done: Slide 3 - 3-Phase Optimization (with savings per phase)")
        
        self.slide_4_data_table()
        print("  Done: Slide 4 - Monthly Data Table with Trends")
        
        self.slide_5_insights()
        print("  Done: Slide 5 - Key Data Insights")
        
        self.slide_6_resource_groups()
        print("  Done: Slide 6 - Resource Group Comparison")
        
        self.slide_7_summary()
        print("  Done: Slide 7 - Summary")
        
        self.c.save()
        print("")
        print(f"Presentation saved to: {self.filename}")
        print(f"File size: {os.path.getsize(self.filename) / 1024:.1f} KB")


if __name__ == "__main__":
    pdf = DetailedPresentationPDF("/workspace/Cost_Optimization_Detailed.pdf")
    pdf.generate()
