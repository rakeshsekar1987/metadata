# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Databricks Cost Optimization - Final Business Presentation
6-Month Data: Sep 2024 - Feb 2025
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
        
        # Final 6-month data: Sep 2024 - Feb 2025
        self.months = ["Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024", "Jan 2025", "Feb 2025"]
        self.dev_costs = [79.96, 65.00, 50.00, 40.00, 30.00, 20.72]      # Dev
        self.qa_costs = [9820, 8000, 5000, 3000, 1500, 1020]              # QA
        self.prod_costs = [13250, 11000, 8000, 6000, 4000, 2980]          # Production
        
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
        
        sep_total = self.totals[0]
        feb_total = self.totals[-1]
        total_saved = sep_total - feb_total
        pct_saved = ((sep_total - feb_total) / sep_total) * 100
        
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
        self.c.drawCentredString(self.width/2, self.height/2 - 85, "Total Cost Reduction")
        
        # Key metrics row
        metrics = [
            (f"${total_saved:,.0f}", "Saved/Month"),
            (f"${total_saved * 12:,.0f}", "Saved/Year"),
            ("6 Months", "Optimization Period")
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
        self.c.drawCentredString(self.width/2, 60, "September 2024 - February 2025")

    # =========== SLIDE 2: Before & After ===========
    def slide_2_before_after(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 70, "Before & After")
        
        sep_total = self.totals[0]
        feb_total = self.totals[-1]
        monthly_saved = sep_total - feb_total
        
        # Before box
        left_x = 100
        box_width = 280
        box_height = 200
        y = self.height - 320
        
        self.c.setFillColor(colors.HexColor('#3d2020'))
        self.c.roundRect(left_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height - 30, "SEPTEMBER 2024")
        
        self.c.setFont("Helvetica-Bold", 52)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height/2, f"${sep_total/1000:.1f}K")
        
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
        self.c.drawCentredString(right_x + box_width/2, y + box_height - 30, "FEBRUARY 2025")
        
        self.c.setFont("Helvetica-Bold", 52)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(right_x + box_width/2, y + box_height/2, f"${feb_total/1000:.1f}K")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(right_x + box_width/2, y + 30, "per month")
        
        # Savings highlight
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 380)/2, 80, 380, 70, 10, fill=1, stroke=0)
        
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
        
        # Phase 1: Sep-Oct (Pool removal)
        # Phase 2: Nov-Dec (Right-sizing)
        # Phase 3: Jan-Feb (Task groups)
        
        phase1_before = self.totals[0]  # Sep
        phase1_after = self.totals[1]   # Oct
        phase1_savings = phase1_before - phase1_after
        phase1_pct = (phase1_savings / phase1_before) * 100
        
        phase2_before = self.totals[2]  # Nov
        phase2_after = self.totals[3]   # Dec
        phase2_savings = phase2_before - phase2_after
        phase2_pct = (phase2_savings / phase2_before) * 100
        
        phase3_before = self.totals[4]  # Jan
        phase3_after = self.totals[5]   # Feb
        phase3_savings = phase3_before - phase3_after
        phase3_pct = (phase3_savings / phase3_before) * 100
        
        phases = [
            ("PHASE 1", "Sep - Oct 2024", "Pool Cluster\nDecommissioning",
             ["Removed 24/7 pool clusters", "Switched to on-demand compute", "Added auto-termination (15 min)"],
             f"${phase1_savings:,.0f}", f"{phase1_pct:.0f}%", BLUE),
            ("PHASE 2", "Nov - Dec 2024", "Right-Sizing\nCompute",
             ["Standard_D4s_v3 VMs", "3 to 5 workers per cluster", "100% resource utilization"],
             f"${phase2_savings:,.0f}", f"{phase2_pct:.0f}%", GREEN),
            ("PHASE 3", "Jan - Feb 2025", "Task Group\nClustering",
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
        
        # Table with all columns: Month, Dev, QA, Prod, Development (Dev+QA), Production, Total, Change
        table_x = 40
        table_y = self.height - 95
        col_widths = [75, 60, 70, 75, 95, 85, 85, 115]
        row_height = 40
        
        headers = ["Month", "Dev", "QA", "Prod", "Development", "Production", "Total", "Change"]
        
        # Header row
        self.c.setFillColor(colors.HexColor('#3a3d50'))
        self.c.rect(table_x, table_y - row_height, sum(col_widths), row_height, fill=1, stroke=0)
        
        x = table_x
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(WHITE)
        for i, header in enumerate(headers):
            self.c.drawCentredString(x + col_widths[i]/2, table_y - 25, header)
            x += col_widths[i]
        
        # Subheader for combined columns
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(table_x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4]/2, 
                                  table_y - 37, "(Dev + QA)")
        
        # Phase indicators
        phase_map = {
            0: (BLUE, "P1"),     # Sep - Phase 1
            1: (BLUE, "P1"),     # Oct - Phase 1
            2: (GREEN, "P2"),    # Nov - Phase 2
            3: (GREEN, "P2"),    # Dec - Phase 2
            4: (ORANGE, "P3"),   # Jan - Phase 3
            5: (ORANGE, "P3")    # Feb - Phase 3
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
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[0]/2, row_y + 15, month)
            x += col_widths[0]
            
            # Dev
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(CYAN)
            self.c.drawCentredString(x + col_widths[1]/2, row_y + 15, f"${dev:.0f}")
            x += col_widths[1]
            
            # QA
            self.c.setFillColor(YELLOW)
            self.c.drawCentredString(x + col_widths[2]/2, row_y + 15, f"${qa:,.0f}")
            x += col_widths[2]
            
            # Prod
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[3]/2, row_y + 15, f"${prod:,.0f}")
            x += col_widths[3]
            
            # Photon - Development
            self.c.setFillColor(BLUE)
            self.c.drawCentredString(x + col_widths[4]/2, row_y + 15, f"${photon_dev:,.0f}")
            x += col_widths[4]
            
            # Photon - Production
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[5]/2, row_y + 15, f"${photon_prod:,.0f}")
            x += col_widths[5]
            
            # Total
            self.c.setFont("Helvetica-Bold", 10)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + col_widths[6]/2, row_y + 15, f"${total:,.0f}")
            x += col_widths[6]
            
            # Change
            if prev_total is not None:
                change = total - prev_total
                change_pct = (change / prev_total) * 100
                
                if change < 0:
                    self.c.setFillColor(GREEN)
                    self.c.drawCentredString(x + col_widths[7]/2, row_y + 15, 
                        f"v ${abs(change):,.0f} ({abs(change_pct):.0f}%)")
                else:
                    self.c.setFillColor(RED)
                    self.c.drawCentredString(x + col_widths[7]/2, row_y + 15, 
                        f"^ ${change:,.0f} (+{change_pct:.0f}%)")
            else:
                self.c.setFont("Helvetica", 10)
                self.c.setFillColor(LIGHT_GRAY)
                self.c.drawCentredString(x + col_widths[7]/2, row_y + 15, "Baseline")
            
            prev_total = total
        
        # Legend
        legend_y = row_y - 50
        self.c.setFont("Helvetica-Bold", 11)
        self.c.setFillColor(WHITE)
        self.c.drawString(table_x, legend_y, "Phases:")
        
        legends = [
            (BLUE, "Phase 1: Pool Removal (Sep-Oct)"),
            (GREEN, "Phase 2: Right-Sizing (Nov-Dec)"),
            (ORANGE, "Phase 3: Task Groups (Jan-Feb)")
        ]
        
        x = table_x + 60
        for color, label in legends:
            self.c.setFillColor(color)
            self.c.rect(x, legend_y - 2, 12, 12, fill=1, stroke=0)
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 18, legend_y, label)
            x += 200
        
        # Total summary
        sep_total = self.totals[0]
        feb_total = self.totals[-1]
        total_saved = sep_total - feb_total
        total_pct = (total_saved / sep_total) * 100
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 480)/2, 50, 480, 50, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 75, 
            f"Total 6-Month Savings: ${total_saved:,.0f}/month ({total_pct:.0f}% reduction)")

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
        
        # Bars
        bar_width = (chart_width - 100) / len(self.months)
        
        phase_colors = [BLUE, BLUE, GREEN, GREEN, ORANGE, ORANGE]
        
        prev_total = None
        for i, (month, total) in enumerate(zip(self.months, self.totals)):
            x = chart_x + 30 + i * bar_width
            bar_height = (total / max_val) * chart_height
            
            # Bar
            self.c.setFillColor(phase_colors[i])
            self.c.roundRect(x, chart_y, bar_width - 15, bar_height, 4, fill=1, stroke=0)
            
            # Value on bar
            self.c.setFont("Helvetica-Bold", 11)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + (bar_width-15)/2, chart_y + bar_height + 8, f"${total/1000:.1f}K")
            
            # Month label
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + (bar_width-15)/2, chart_y - 18, month[:3])
            
            # Change indicator
            if prev_total is not None:
                change = total - prev_total
                change_pct = (change / prev_total) * 100
                if change < 0:
                    self.c.setFont("Helvetica-Bold", 9)
                    self.c.setFillColor(GREEN)
                    self.c.drawCentredString(x + (bar_width-15)/2, chart_y - 32, f"v{abs(change_pct):.0f}%")
            
            prev_total = total
        
        # Trend line
        points = []
        for i, total in enumerate(self.totals):
            x = chart_x + 30 + i * bar_width + (bar_width-15)/2
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
        
        for i, (color, label) in enumerate([(BLUE, "P1: Pool Removal"), (GREEN, "P2: Right-Sizing"), (ORANGE, "P3: Task Groups")]):
            x = chart_x + 70 + i * 180
            self.c.setFillColor(color)
            self.c.rect(x, chart_y - 58, 12, 12, fill=1, stroke=0)
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 18, chart_y - 55, label)

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
        
        # Photon - Development
        dev_x = start_x
        dev_start = self.photon_dev[0]
        dev_end = self.photon_dev[-1]
        dev_saved = dev_start - dev_end
        dev_pct = (dev_saved / dev_start) * 100
        
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
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 100, f"Sep 2024: ${dev_start:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 130, "v")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(dev_x + box_width/2, y + box_height - 160, f"Feb 2025: ${dev_end:,.0f}")
        
        # Savings
        self.c.setFont("Helvetica-Bold", 42)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(dev_x + box_width/2, y + 70, f"-{dev_pct:.0f}%")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(dev_x + box_width/2, y + 30, f"${dev_saved:,.0f} saved/month")
        
        # Photon - Production
        prod_x = start_x + box_width + gap
        prod_start = self.photon_prod[0]
        prod_end = self.photon_prod[-1]
        prod_saved = prod_start - prod_end
        prod_pct = (prod_saved / prod_start) * 100
        
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
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 100, f"Sep 2024: ${prod_start:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 130, "v")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 160, f"Feb 2025: ${prod_end:,.0f}")
        
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
        self.c.roundRect((self.width - 350)/2, 60, 350, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 92, f"Combined: ${total_saved:,.0f}/month")

    # =========== SLIDE 7: Summary ===========
    def slide_7_summary(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 55, "Summary")
        
        sep_total = self.totals[0]
        feb_total = self.totals[-1]
        monthly_saved = sep_total - feb_total
        annual_saved = monthly_saved * 12
        pct_saved = (monthly_saved / sep_total) * 100
        
        # Big numbers
        metrics = [
            (f"${monthly_saved/1000:.0f}K", "Saved/Month", GREEN),
            (f"${annual_saved/1000:.0f}K", "Saved/Year", GREEN),
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
            ("Phase 1", "Pool Removal", "Sep-Oct 2024", BLUE),
            ("Phase 2", "Right-Sizing", "Nov-Dec 2024", GREEN),
            ("Phase 3", "Task Groups", "Jan-Feb 2025", ORANGE)
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
        print("=" * 60)
        print("Generating Final Business Presentation")
        print("=" * 60)
        print("")
        print("6-Month Cost Data (Sep 2024 - Feb 2025):")
        print("-" * 60)
        print(f"{'Month':<12} {'Dev':>10} {'QA':>10} {'Prod':>10} {'Total':>12}")
        print("-" * 60)
        for i, month in enumerate(self.months):
            print(f"{month:<12} ${self.dev_costs[i]:>8.0f} ${self.qa_costs[i]:>8,.0f} ${self.prod_costs[i]:>8,.0f} ${self.totals[i]:>10,.0f}")
        print("-" * 60)
        print("")
        print("Resource Groups:")
        print(f"  Photon - Development (Dev+QA): ${self.photon_dev[0]:,.0f} -> ${self.photon_dev[-1]:,.0f}")
        print(f"  Photon - Production:           ${self.photon_prod[0]:,.0f} -> ${self.photon_prod[-1]:,.0f}")
        print(f"  Total Savings:                 ${self.totals[0] - self.totals[-1]:,.0f}/month")
        print("")
        
        self.slide_1_title()
        print("  [OK] Slide 1: Title & Key Metrics")
        
        self.slide_2_before_after()
        print("  [OK] Slide 2: Before & After")
        
        self.slide_3_phases()
        print("  [OK] Slide 3: 3-Phase Optimization")
        
        self.slide_4_data_table()
        print("  [OK] Slide 4: Full Data Table")
        
        self.slide_5_trend_chart()
        print("  [OK] Slide 5: Trend Chart")
        
        self.slide_6_resource_groups()
        print("  [OK] Slide 6: Resource Groups")
        
        self.slide_7_summary()
        print("  [OK] Slide 7: Summary")
        
        self.c.save()
        print("")
        print("=" * 60)
        print(f"Presentation saved: {self.filename}")
        print(f"File size: {os.path.getsize(self.filename) / 1024:.1f} KB")
        print("=" * 60)


if __name__ == "__main__":
    pdf = FinalPresentationPDF("/workspace/Cost_Optimization_Final.pdf")
    pdf.generate()
