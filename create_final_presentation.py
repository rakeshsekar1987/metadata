# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Databricks Cost Optimization - Final Business Presentation
6-Month Data from Charts: Jun 2025 - Nov 2025
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
CYAN = colors.HexColor('#06b6d4')


class FinalPresentationPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=landscape(LETTER))
        self.width = PAGE_WIDTH
        self.height = PAGE_HEIGHT
        self.slide_num = 0
        
        # Data from the 3 charts (Jun 2025 - Nov 2025)
        self.months = ["Jun 2025", "Jul 2025", "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025"]
        
        # Dev (Blue chart) - photon-idp-dev-eus-db
        self.dev_costs = [61.52, 79.96, 78.61, 61.46, 20.72, 15.00]  # Nov estimated
        
        # QA (Yellow chart) - photon-idp-qa-eus-db  
        self.qa_costs = [5780, 8770, 9820, 5510, 1090, 1020]
        
        # Prod (Green chart) - photon-idp-prod-eus-db
        self.prod_costs = [9640, 13090, 13250, 11410, 4290, 2980]
        
        # Combined: Photon - Development (Dev + QA)
        self.photon_dev = [d + q for d, q in zip(self.dev_costs, self.qa_costs)]
        
        # Photon - Production
        self.photon_prod = self.prod_costs
        
        # Totals
        self.totals = [d + p for d, p in zip(self.photon_dev, self.photon_prod)]
        
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
        
        # Peak (Aug) vs Current (Nov)
        peak_total = max(self.totals)
        peak_idx = self.totals.index(peak_total)
        nov_total = self.totals[-1]
        total_saved = peak_total - nov_total
        pct_saved = ((peak_total - nov_total) / peak_total) * 100
        
        self.c.setFont("Helvetica-Bold", 44)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 150, "Databricks Cost")
        self.c.drawCentredString(self.width/2, self.height - 205, "Optimization Results")
        
        # Big percentage
        self.c.setFont("Helvetica-Bold", 120)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, self.height/2 - 20, f"{pct_saved:.0f}%")
        
        self.c.setFont("Helvetica", 24)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, self.height/2 - 85, "Cost Reduction from Peak")
        
        # Key metrics row
        metrics = [
            (f"${total_saved:,.0f}", "Saved/Month"),
            (f"${total_saved * 12:,.0f}", "Projected/Year"),
            ("6 Months", "Analysis Period")
        ]
        
        box_width = 180
        gap = 40
        start_x = (self.width - 3*box_width - 2*gap) / 2
        y = 90
        
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
        
        # Period
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 60, "June 2025 - November 2025")

    # =========== SLIDE 2: Before & After ===========
    def slide_2_before_after(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 70, "Before & After")
        
        # Peak (Aug) vs Current (Nov)
        peak_total = max(self.totals)
        peak_idx = self.totals.index(peak_total)
        peak_month = self.months[peak_idx]
        nov_total = self.totals[-1]
        monthly_saved = peak_total - nov_total
        
        # Before box (Peak - August)
        left_x = 100
        box_width = 280
        box_height = 200
        y = self.height - 320
        
        self.c.setFillColor(colors.HexColor('#3d2020'))
        self.c.roundRect(left_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height - 25, "PEAK (AUGUST 2025)")
        
        self.c.setFont("Helvetica-Bold", 52)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height/2, f"${peak_total/1000:.1f}K")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(left_x + box_width/2, y + 30, "per month")
        
        # Arrow
        arrow_x = left_x + box_width + 40
        self.c.setFont("Helvetica-Bold", 50)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(arrow_x + 60, y + box_height/2, "->")
        
        # After box (November)
        right_x = self.width - 100 - box_width
        
        self.c.setFillColor(colors.HexColor('#1a3d1a'))
        self.c.roundRect(right_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(right_x + box_width/2, y + box_height - 25, "CURRENT (NOVEMBER 2025)")
        
        self.c.setFont("Helvetica-Bold", 52)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(right_x + box_width/2, y + box_height/2, f"${nov_total/1000:.1f}K")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(right_x + box_width/2, y + 30, "per month")
        
        # Savings highlight
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 400)/2, 80, 400, 70, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 120, f"${monthly_saved:,.0f} saved/month")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 95, f"${monthly_saved * 12:,.0f} projected annually")

    # =========== SLIDE 3: 3 Phases ===========
    def slide_3_phases(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "3-Phase Optimization Strategy")
        
        # Phase 1: Aug (Pool removal) - Aug to Sep savings
        aug_total = self.totals[2]  # Aug
        sep_total = self.totals[3]  # Sep
        phase1_savings = aug_total - sep_total
        phase1_pct = (phase1_savings / aug_total) * 100
        
        # Phase 2: Sep (Right-sizing) - Sep to Oct savings
        oct_total = self.totals[4]  # Oct
        phase2_savings = sep_total - oct_total
        phase2_pct = (phase2_savings / sep_total) * 100
        
        # Phase 3: Oct (Task groups) - Oct to Nov savings
        nov_total = self.totals[5]  # Nov
        phase3_savings = oct_total - nov_total
        phase3_pct = (phase3_savings / oct_total) * 100
        
        phases = [
            ("PHASE 1", "August 2025", "Pool Cluster\nDecommissioning",
             ["Removed 24/7 pool clusters", "Switched to on-demand compute", "Added auto-termination (15 min)"],
             f"${phase1_savings:,.0f}", f"{phase1_pct:.0f}%", BLUE),
            ("PHASE 2", "September 2025", "Right-Sizing\nCompute",
             ["Standard_D4s_v3 VMs", "Min 3 to Max 5 workers", "100% resource utilization"],
             f"${phase2_savings:,.0f}", f"{phase2_pct:.0f}%", GREEN),
            ("PHASE 3", "October 2025", "Task Group\nClustering",
             ["Tables grouped by domain", "Dedicated cluster per group", "Reduced driver contention"],
             f"${phase3_savings:,.0f}", f"{phase3_pct:.0f}%", ORANGE)
        ]
        
        box_width = 230
        box_height = 310
        gap = 30
        start_x = (self.width - 3*box_width - 2*gap) / 2
        y = self.height - 410
        
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

    # =========== SLIDE 4: Full Data Table ===========
    def slide_4_data_table(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 32)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 50, "6-Month Cost Breakdown")
        
        # Table
        table_x = 50
        table_y = self.height - 100
        col_widths = [80, 55, 70, 70, 100, 90, 90, 105]
        row_height = 42
        
        headers = ["Month", "Dev", "QA", "Prod", "Development", "Production", "Total", "Change"]
        
        # Header row
        self.c.setFillColor(colors.HexColor('#3a3d50'))
        self.c.rect(table_x, table_y - row_height, sum(col_widths), row_height, fill=1, stroke=0)
        
        x = table_x
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(WHITE)
        for i, header in enumerate(headers):
            self.c.drawCentredString(x + col_widths[i]/2, table_y - 26, header)
            x += col_widths[i]
        
        # Subheader
        self.c.setFont("Helvetica", 7)
        self.c.setFillColor(LIGHT_GRAY)
        dev_col_x = table_x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3]
        self.c.drawCentredString(dev_col_x + col_widths[4]/2, table_y - 38, "(Dev + QA)")
        
        # Phase colors for rows
        phase_map = {
            0: (colors.HexColor('#555555'), ""),  # Jun - before
            1: (colors.HexColor('#555555'), ""),  # Jul - before
            2: (BLUE, "P1"),     # Aug - Phase 1
            3: (GREEN, "P2"),    # Sep - Phase 2
            4: (ORANGE, "P3"),   # Oct - Phase 3
            5: (ORANGE, "P3")    # Nov - Phase 3
        }
        
        prev_total = None
        for row_idx in range(len(self.months)):
            month = self.months[row_idx]
            dev = self.dev_costs[row_idx]
            qa = self.qa_costs[row_idx]
            prod = self.prod_costs[row_idx]
            photon_dev = self.photon_dev[row_idx]
            photon_prod = self.photon_prod[row_idx]
            total = self.totals[row_idx]
            
            row_y = table_y - (row_idx + 2) * row_height
            
            # Row background
            if row_idx % 2 == 0:
                self.c.setFillColor(colors.HexColor('#1a1d2e'))
            else:
                self.c.setFillColor(colors.HexColor('#22253a'))
            self.c.rect(table_x, row_y, sum(col_widths), row_height, fill=1, stroke=0)
            
            # Phase indicator
            phase_color, phase_label = phase_map[row_idx]
            self.c.setFillColor(phase_color)
            self.c.rect(table_x, row_y, 4, row_height, fill=1, stroke=0)
            
            x = table_x
            
            # Month
            self.c.setFont("Helvetica-Bold", 9)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[0]/2, row_y + 16, month)
            x += col_widths[0]
            
            # Dev
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(CYAN)
            self.c.drawCentredString(x + col_widths[1]/2, row_y + 16, f"${dev:.0f}")
            x += col_widths[1]
            
            # QA
            self.c.setFillColor(YELLOW)
            self.c.drawCentredString(x + col_widths[2]/2, row_y + 16, f"${qa:,.0f}")
            x += col_widths[2]
            
            # Prod
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[3]/2, row_y + 16, f"${prod:,.0f}")
            x += col_widths[3]
            
            # Photon - Development
            self.c.setFillColor(BLUE)
            self.c.drawCentredString(x + col_widths[4]/2, row_y + 16, f"${photon_dev:,.0f}")
            x += col_widths[4]
            
            # Photon - Production
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[5]/2, row_y + 16, f"${photon_prod:,.0f}")
            x += col_widths[5]
            
            # Total
            self.c.setFont("Helvetica-Bold", 9)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[6]/2, row_y + 16, f"${total:,.0f}")
            x += col_widths[6]
            
            # Change
            if prev_total is not None:
                change = total - prev_total
                change_pct = (change / prev_total) * 100
                
                if change < 0:
                    self.c.setFillColor(GREEN)
                    self.c.drawCentredString(x + col_widths[7]/2, row_y + 16, 
                        f"v ${abs(change):,.0f} ({abs(change_pct):.0f}%)")
                else:
                    self.c.setFillColor(RED)
                    self.c.drawCentredString(x + col_widths[7]/2, row_y + 16, 
                        f"^ ${change:,.0f} (+{change_pct:.0f}%)")
            else:
                self.c.setFont("Helvetica", 9)
                self.c.setFillColor(LIGHT_GRAY)
                self.c.drawCentredString(x + col_widths[7]/2, row_y + 16, "Baseline")
            
            prev_total = total
        
        # Legend
        legend_y = row_y - 45
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(WHITE)
        self.c.drawString(table_x, legend_y, "Phases:")
        
        legends = [
            (BLUE, "Phase 1: Pool Removal (Aug)"),
            (GREEN, "Phase 2: Right-Sizing (Sep)"),
            (ORANGE, "Phase 3: Task Groups (Oct-Nov)")
        ]
        
        x = table_x + 55
        for color, label in legends:
            self.c.setFillColor(color)
            self.c.rect(x, legend_y - 2, 12, 12, fill=1, stroke=0)
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 16, legend_y, label)
            x += 195
        
        # Total summary
        peak_total = max(self.totals)
        nov_total = self.totals[-1]
        total_saved = peak_total - nov_total
        total_pct = (total_saved / peak_total) * 100
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 500)/2, 45, 500, 50, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 17)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 70, 
            f"Total Reduction from Peak: ${total_saved:,.0f}/month ({total_pct:.0f}%)")

    # =========== SLIDE 5: Monthly Trend Chart ===========
    def slide_5_trend_chart(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 55, "Cost Reduction Trend")
        
        # Chart area
        chart_x = 100
        chart_y = 100
        chart_width = self.width - 200
        chart_height = 320
        
        # Y-axis
        max_val = 25000
        self.c.setStrokeColor(colors.HexColor('#444444'))
        self.c.setLineWidth(1)
        
        for i in range(6):
            val = i * 5000
            y = chart_y + (val / max_val) * chart_height
            
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawRightString(chart_x - 10, y - 4, f"${val/1000:.0f}K")
            
            self.c.setStrokeColor(colors.HexColor('#333333'))
            self.c.line(chart_x, y, chart_x + chart_width, y)
        
        # Bars - color by phase
        bar_width = (chart_width - 80) / len(self.months)
        
        # Before optimization (Jun-Jul), Phase 1 (Aug), Phase 2 (Sep), Phase 3 (Oct-Nov)
        bar_colors = [
            colors.HexColor('#666666'),  # Jun - before
            colors.HexColor('#666666'),  # Jul - before  
            BLUE,     # Aug - Phase 1
            GREEN,    # Sep - Phase 2
            ORANGE,   # Oct - Phase 3
            ORANGE    # Nov - Phase 3
        ]
        
        prev_total = None
        for i, (month, total) in enumerate(zip(self.months, self.totals)):
            x = chart_x + 25 + i * bar_width
            bar_height = (total / max_val) * chart_height
            
            # Bar
            self.c.setFillColor(bar_colors[i])
            self.c.roundRect(x, chart_y, bar_width - 12, bar_height, 4, fill=1, stroke=0)
            
            # Value on bar
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + (bar_width-12)/2, chart_y + bar_height + 8, f"${total/1000:.1f}K")
            
            # Month label
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + (bar_width-12)/2, chart_y - 18, month[:3])
            
            # Change indicator
            if prev_total is not None:
                change = total - prev_total
                change_pct = (change / prev_total) * 100
                if change < 0:
                    self.c.setFont("Helvetica-Bold", 9)
                    self.c.setFillColor(GREEN)
                    self.c.drawCentredString(x + (bar_width-12)/2, chart_y - 32, f"v{abs(change_pct):.0f}%")
                elif change > 0:
                    self.c.setFont("Helvetica-Bold", 9)
                    self.c.setFillColor(RED)
                    self.c.drawCentredString(x + (bar_width-12)/2, chart_y - 32, f"^{change_pct:.0f}%")
            
            prev_total = total
        
        # Trend line
        points = []
        for i, total in enumerate(self.totals):
            x = chart_x + 25 + i * bar_width + (bar_width-12)/2
            y = chart_y + (total / max_val) * chart_height
            points.append((x, y))
        
        self.c.setStrokeColor(WHITE)
        self.c.setLineWidth(2)
        for i in range(len(points) - 1):
            self.c.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Legend
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(WHITE)
        self.c.drawString(chart_x, chart_y - 55, "Phases:")
        
        for i, (color, label) in enumerate([
            (colors.HexColor('#666666'), "Before Optimization"),
            (BLUE, "P1: Pool Removal"), 
            (GREEN, "P2: Right-Sizing"), 
            (ORANGE, "P3: Task Groups")
        ]):
            x = chart_x + 60 + i * 160
            self.c.setFillColor(color)
            self.c.rect(x, chart_y - 58, 12, 12, fill=1, stroke=0)
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 16, chart_y - 55, label)

    # =========== SLIDE 6: Resource Groups ===========
    def slide_6_resource_groups(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 55, "Resource Group Summary")
        
        # Two boxes side by side
        box_width = 320
        box_height = 280
        gap = 80
        start_x = (self.width - 2*box_width - gap) / 2
        y = self.height - 380
        
        # Peak values for comparison
        dev_peak = max(self.photon_dev)
        dev_peak_idx = self.photon_dev.index(dev_peak)
        prod_peak = max(self.photon_prod)
        prod_peak_idx = self.photon_prod.index(prod_peak)
        
        # Photon - Development
        dev_x = start_x
        dev_end = self.photon_dev[-1]
        dev_saved = dev_peak - dev_end
        dev_pct = (dev_saved / dev_peak) * 100
        
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
        
        # Values
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 100, f"Peak ({self.months[dev_peak_idx][:3]}): ${dev_peak:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 130, "v")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 160, f"Nov 2025: ${dev_end:,.0f}")
        
        # Savings
        self.c.setFont("Helvetica-Bold", 42)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(dev_x + box_width/2, y + 70, f"-{dev_pct:.0f}%")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(dev_x + box_width/2, y + 30, f"${dev_saved:,.0f} saved/month")
        
        # Photon - Production
        prod_x = start_x + box_width + gap
        prod_end = self.photon_prod[-1]
        prod_saved = prod_peak - prod_end
        prod_pct = (prod_saved / prod_peak) * 100
        
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
        
        # Values
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 100, f"Peak ({self.months[prod_peak_idx][:3]}): ${prod_peak:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 130, "v")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 160, f"Nov 2025: ${prod_end:,.0f}")
        
        # Savings
        self.c.setFont("Helvetica-Bold", 42)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(prod_x + box_width/2, y + 70, f"-{prod_pct:.0f}%")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(prod_x + box_width/2, y + 30, f"${prod_saved:,.0f} saved/month")
        
        # Combined total
        total_saved = dev_saved + prod_saved
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 380)/2, 60, 380, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 92, f"Combined Savings: ${total_saved:,.0f}/month")

    # =========== SLIDE 7: Summary ===========
    def slide_7_summary(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 55, "Summary")
        
        peak_total = max(self.totals)
        nov_total = self.totals[-1]
        monthly_saved = peak_total - nov_total
        annual_saved = monthly_saved * 12
        pct_saved = (monthly_saved / peak_total) * 100
        
        # Big numbers
        metrics = [
            (f"${monthly_saved/1000:.0f}K", "Saved/Month", GREEN),
            (f"${annual_saved/1000:.0f}K", "Projected/Year", GREEN),
            (f"{pct_saved:.0f}%", "Reduction", BLUE)
        ]
        
        box_width = 200
        gap = 50
        start_x = (self.width - 3*box_width - 2*gap) / 2
        y = self.height - 170
        
        for i, (val, label, color) in enumerate(metrics):
            x = start_x + i * (box_width + gap)
            
            self.c.setFont("Helvetica-Bold", 52)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + box_width/2, y, val)
            
            self.c.setFont("Helvetica", 16)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + box_width/2, y - 30, label)
        
        # Phase summary
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 270, "Optimization Phases")
        
        phases = [
            ("Phase 1", "Pool Removal", "August 2025", BLUE),
            ("Phase 2", "Right-Sizing", "September 2025", GREEN),
            ("Phase 3", "Task Groups", "Oct-Nov 2025", ORANGE)
        ]
        
        phase_width = 200
        phase_start = (self.width - 3*phase_width - 40) / 2
        phase_y = self.height - 350
        
        for i, (phase, action, period, color) in enumerate(phases):
            x = phase_start + i * (phase_width + 20)
            
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, phase_y, phase_width, 65, 8, fill=1, stroke=0)
            
            self.c.setFillColor(color)
            self.c.rect(x, phase_y + 60, phase_width, 5, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + phase_width/2, phase_y + 42, phase)
            
            self.c.setFont("Helvetica", 11)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + phase_width/2, phase_y + 22, action)
            
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + phase_width/2, phase_y + 6, period)
        
        # Bottom message
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect(100, 70, self.width - 200, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, 97, "Same workload, lower cost, better performance")

    def generate(self):
        print("=" * 65)
        print("  Databricks Cost Optimization - Final Presentation")
        print("=" * 65)
        print("")
        print("  Data Source: LakeFlow System Tables Dashboard")
        print("  Period: June 2025 - November 2025 (6 Months)")
        print("")
        print("  6-Month Cost Data:")
        print("  " + "-" * 61)
        print(f"  {'Month':<12} {'Dev':>8} {'QA':>10} {'Prod':>10} {'Total':>12}")
        print("  " + "-" * 61)
        for i, month in enumerate(self.months):
            print(f"  {month:<12} ${self.dev_costs[i]:>6.0f} ${self.qa_costs[i]:>8,.0f} ${self.prod_costs[i]:>8,.0f} ${self.totals[i]:>10,.0f}")
        print("  " + "-" * 61)
        print("")
        print("  Resource Groups:")
        peak_dev = max(self.photon_dev)
        peak_prod = max(self.photon_prod)
        print(f"    Photon - Development: ${peak_dev:,.0f} -> ${self.photon_dev[-1]:,.0f} (saved ${peak_dev - self.photon_dev[-1]:,.0f})")
        print(f"    Photon - Production:  ${peak_prod:,.0f} -> ${self.photon_prod[-1]:,.0f} (saved ${peak_prod - self.photon_prod[-1]:,.0f})")
        peak_total = max(self.totals)
        print(f"    Total Savings:        ${peak_total - self.totals[-1]:,.0f}/month ({((peak_total - self.totals[-1])/peak_total)*100:.0f}% reduction)")
        print("")
        
        self.slide_1_title()
        print("  [OK] Slide 1: Title & Key Metrics")
        
        self.slide_2_before_after()
        print("  [OK] Slide 2: Before & After (Peak vs Current)")
        
        self.slide_3_phases()
        print("  [OK] Slide 3: 3-Phase Optimization Strategy")
        
        self.slide_4_data_table()
        print("  [OK] Slide 4: Full 6-Month Data Table")
        
        self.slide_5_trend_chart()
        print("  [OK] Slide 5: Cost Reduction Trend Chart")
        
        self.slide_6_resource_groups()
        print("  [OK] Slide 6: Resource Group Summary")
        
        self.slide_7_summary()
        print("  [OK] Slide 7: Final Summary")
        
        self.c.save()
        print("")
        print("=" * 65)
        print(f"  Presentation saved: {self.filename}")
        print(f"  File size: {os.path.getsize(self.filename) / 1024:.1f} KB")
        print("=" * 65)


if __name__ == "__main__":
    pdf = FinalPresentationPDF("/workspace/Cost_Optimization_Final.pdf")
    pdf.generate()
