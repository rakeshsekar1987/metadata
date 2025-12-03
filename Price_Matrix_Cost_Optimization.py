# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Price Matrix Application - Cost Optimization Presentation
6-Month Data: Jun 2025 - Nov 2025
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
TEAL = colors.HexColor('#14b8a6')


class PriceMatrixCostPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=landscape(LETTER))
        self.width = PAGE_WIDTH
        self.height = PAGE_HEIGHT
        self.slide_num = 0
        
        # Data from the table (Jun 2025 - Nov 2025)
        self.months = ["Jun 2025", "Jul 2025", "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025"]
        
        # Individual environment costs
        self.dev_costs = [751.37, 913.00, 828.11, 307.28, 260.41, 249.96]
        self.qa_costs = [1019.94, 1053.10, 1069.06, 481.54, 372.43, 363.39]
        self.uat_costs = [1946.39, 1953.30, 1853.00, 1082.04, 1188.66, 999.36]
        self.prod_costs = [1951.00, 2528.00, 2582.00, 2512.00, 2613.00, 2518.00]
        
        # Combined: Non-Production (Dev + QA + UAT)
        self.non_prod = [d + q + u for d, q, u in zip(self.dev_costs, self.qa_costs, self.uat_costs)]
        
        # Production (as is)
        self.production = self.prod_costs
        
        # Totals
        self.totals = [np + p for np, p in zip(self.non_prod, self.production)]
        
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
        
        # Peak (Jul) vs Current (Nov)
        peak_total = max(self.totals)
        peak_idx = self.totals.index(peak_total)
        nov_total = self.totals[-1]
        total_saved = peak_total - nov_total
        pct_saved = ((peak_total - nov_total) / peak_total) * 100
        
        self.c.setFont("Helvetica-Bold", 44)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 150, "Price Matrix Application")
        self.c.drawCentredString(self.width/2, self.height - 205, "Cost Optimization Results")
        
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
        
        # Peak (Jul) vs Current (Nov)
        peak_total = max(self.totals)
        peak_idx = self.totals.index(peak_total)
        peak_month = self.months[peak_idx]
        nov_total = self.totals[-1]
        monthly_saved = peak_total - nov_total
        
        # Before box (Peak - July)
        left_x = 100
        box_width = 280
        box_height = 200
        y = self.height - 320
        
        self.c.setFillColor(colors.HexColor('#3d2020'))
        self.c.roundRect(left_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(left_x + box_width/2, y + box_height - 25, "PEAK (JULY 2025)")
        
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

    # =========== SLIDE 3: Optimization Actions ===========
    def slide_3_optimization_actions(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 60, "Optimization Strategy - August 2025")
        
        # Calculate savings from Aug to Sep (when optimizations took effect)
        aug_total = self.totals[2]  # Aug
        sep_total = self.totals[3]  # Sep
        phase1_savings = aug_total - sep_total
        phase1_pct = (phase1_savings / aug_total) * 100
        
        # Main content box
        main_box_x = 80
        main_box_width = self.width - 160
        main_box_height = 320
        main_box_y = self.height - 420
        
        self.c.setFillColor(colors.HexColor('#2a2d40'))
        self.c.roundRect(main_box_x, main_box_y, main_box_width, main_box_height, 12, fill=1, stroke=0)
        
        # Header bar
        self.c.setFillColor(BLUE)
        self.c.roundRect(main_box_x, main_box_y + main_box_height - 55, main_box_width, 55, 12, fill=1, stroke=0)
        self.c.setFillColor(colors.HexColor('#2a2d40'))
        self.c.rect(main_box_x, main_box_y + main_box_height - 55, main_box_width, 25, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, main_box_y + main_box_height - 38, "Resource Cleanup & Consolidation")
        
        # Three action items
        actions = [
            ("Database Cleanup", "Deleted unused databases in\nDEV, QA and UAT environments", CYAN),
            ("Network Optimization", "Removed unused network instances\nfrom Azure SQL servers", PURPLE),
            ("Redis Cache Consolidation", "Consolidated Redis cache instances\ninto shared UAT infrastructure", TEAL)
        ]
        
        action_width = 190
        action_height = 180
        action_gap = 25
        action_start_x = main_box_x + (main_box_width - 3*action_width - 2*action_gap) / 2
        action_y = main_box_y + 35
        
        for i, (title, desc, color) in enumerate(actions):
            x = action_start_x + i * (action_width + action_gap)
            
            # Action box
            self.c.setFillColor(colors.HexColor('#1e2130'))
            self.c.roundRect(x, action_y, action_width, action_height, 10, fill=1, stroke=0)
            
            # Color accent at top
            self.c.setFillColor(color)
            self.c.roundRect(x, action_y + action_height - 8, action_width, 8, 4, fill=1, stroke=0)
            
            # Icon circle
            self.c.setFillColor(color)
            self.c.circle(x + action_width/2, action_y + action_height - 45, 18, fill=1, stroke=0)
            
            # Checkmark
            self.c.setFont("Helvetica-Bold", 18)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + action_width/2, action_y + action_height - 52, "✓")
            
            # Title
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + action_width/2, action_y + action_height - 85, title)
            
            # Description
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            desc_lines = desc.split('\n')
            for j, line in enumerate(desc_lines):
                self.c.drawCentredString(x + action_width/2, action_y + action_height - 110 - j*14, line)
        
        # Savings box at bottom
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 450)/2, 60, 450, 60, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 95, f"${phase1_savings:,.0f} saved in first month")
        
        self.c.setFont("Helvetica", 13)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(self.width/2, 72, f"({phase1_pct:.0f}% reduction after optimization)")

    # =========== SLIDE 4: Full Data Table ===========
    def slide_4_data_table(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 32)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 50, "6-Month Cost Breakdown")
        
        # Table
        table_x = 50
        table_y = self.height - 100
        col_widths = [80, 70, 70, 70, 70, 100, 90, 110]
        row_height = 42
        
        headers = ["Month", "DEV", "QA", "UAT", "PROD", "Non-Prod", "Production", "Change"]
        
        # Header row
        self.c.setFillColor(colors.HexColor('#3a3d50'))
        self.c.rect(table_x, table_y - row_height, sum(col_widths), row_height, fill=1, stroke=0)
        
        x = table_x
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(WHITE)
        for i, header in enumerate(headers):
            self.c.drawCentredString(x + col_widths[i]/2, table_y - 26, header)
            x += col_widths[i]
        
        # Subheader for Non-Prod
        self.c.setFont("Helvetica", 7)
        self.c.setFillColor(LIGHT_GRAY)
        nonprod_col_x = table_x + sum(col_widths[:5])
        self.c.drawCentredString(nonprod_col_x + col_widths[5]/2, table_y - 38, "(Dev+QA+UAT)")
        
        # Phase colors for rows
        phase_map = {
            0: (colors.HexColor('#555555'), ""),  # Jun - before
            1: (colors.HexColor('#555555'), ""),  # Jul - before (peak)
            2: (BLUE, "P1"),     # Aug - Phase 1 implemented
            3: (BLUE, "P1"),     # Sep - Phase 1 results
            4: (BLUE, "P1"),     # Oct - continued
            5: (BLUE, "P1")      # Nov - continued
        }
        
        prev_total = None
        for row_idx in range(len(self.months)):
            month = self.months[row_idx]
            dev = self.dev_costs[row_idx]
            qa = self.qa_costs[row_idx]
            uat = self.uat_costs[row_idx]
            prod = self.prod_costs[row_idx]
            non_prod = self.non_prod[row_idx]
            production = self.production[row_idx]
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
            
            # DEV
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(CYAN)
            self.c.drawCentredString(x + col_widths[1]/2, row_y + 16, f"${dev:,.0f}")
            x += col_widths[1]
            
            # QA
            self.c.setFillColor(YELLOW)
            self.c.drawCentredString(x + col_widths[2]/2, row_y + 16, f"${qa:,.0f}")
            x += col_widths[2]
            
            # UAT
            self.c.setFillColor(PURPLE)
            self.c.drawCentredString(x + col_widths[3]/2, row_y + 16, f"${uat:,.0f}")
            x += col_widths[3]
            
            # Prod
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[4]/2, row_y + 16, f"${prod:,.0f}")
            x += col_widths[4]
            
            # Non-Production (combined)
            self.c.setFillColor(BLUE)
            self.c.drawCentredString(x + col_widths[5]/2, row_y + 16, f"${non_prod:,.0f}")
            x += col_widths[5]
            
            # Production
            self.c.setFillColor(GREEN)
            self.c.drawCentredString(x + col_widths[6]/2, row_y + 16, f"${production:,.0f}")
            x += col_widths[6]
            
            # Change (based on total)
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
        legend_y = table_y - (len(self.months) + 2) * row_height - 15
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(WHITE)
        self.c.drawString(table_x, legend_y, "Legend:")
        
        legends = [
            (colors.HexColor('#555555'), "Before Optimization"),
            (BLUE, "Phase 1: Resource Cleanup (Aug onwards)")
        ]
        
        x = table_x + 55
        for color, label in legends:
            self.c.setFillColor(color)
            self.c.rect(x, legend_y - 2, 12, 12, fill=1, stroke=0)
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 16, legend_y, label)
            x += 230
        
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
        max_val = 8000
        self.c.setStrokeColor(colors.HexColor('#444444'))
        self.c.setLineWidth(1)
        
        for i in range(5):
            val = i * 2000
            y = chart_y + (val / max_val) * chart_height
            
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawRightString(chart_x - 10, y - 4, f"${val/1000:.0f}K")
            
            self.c.setStrokeColor(colors.HexColor('#333333'))
            self.c.line(chart_x, y, chart_x + chart_width, y)
        
        # Bars - color by phase
        bar_width = (chart_width - 80) / len(self.months)
        
        # Before optimization (Jun-Jul), Phase 1 (Aug onwards)
        bar_colors = [
            colors.HexColor('#666666'),  # Jun - before
            colors.HexColor('#666666'),  # Jul - before (peak)
            BLUE,     # Aug - Phase 1
            BLUE,     # Sep - Phase 1
            BLUE,     # Oct - Phase 1
            BLUE      # Nov - Phase 1
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
        self.c.drawString(chart_x, chart_y - 55, "Legend:")
        
        for i, (color, label) in enumerate([
            (colors.HexColor('#666666'), "Before Optimization"),
            (BLUE, "Phase 1: Resource Cleanup & Consolidation")
        ]):
            x = chart_x + 60 + i * 250
            self.c.setFillColor(color)
            self.c.rect(x, chart_y - 58, 12, 12, fill=1, stroke=0)
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawString(x + 16, chart_y - 55, label)

    # =========== SLIDE 6: Environment Breakdown ===========
    def slide_6_environment_breakdown(self):
        self.new_slide()
        
        self.c.setFont("Helvetica-Bold", 36)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 55, "Environment Cost Summary")
        
        # Two main boxes side by side
        box_width = 320
        box_height = 280
        gap = 80
        start_x = (self.width - 2*box_width - gap) / 2
        y = self.height - 380
        
        # Peak values for comparison
        non_prod_peak = max(self.non_prod)
        non_prod_peak_idx = self.non_prod.index(non_prod_peak)
        prod_peak = max(self.production)
        prod_peak_idx = self.production.index(prod_peak)
        
        # Non-Production (Dev + QA + UAT)
        np_x = start_x
        np_end = self.non_prod[-1]
        np_saved = non_prod_peak - np_end
        np_pct = (np_saved / non_prod_peak) * 100
        
        self.c.setFillColor(colors.HexColor('#1e3a5f'))
        self.c.roundRect(np_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        # Header
        self.c.setFillColor(BLUE)
        self.c.roundRect(np_x, y + box_height - 50, box_width, 50, 12, fill=1, stroke=0)
        self.c.setFillColor(colors.HexColor('#1e3a5f'))
        self.c.rect(np_x, y + box_height - 50, box_width, 20, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(np_x + box_width/2, y + box_height - 35, "Non-Production")
        
        self.c.setFont("Helvetica", 12)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(np_x + box_width/2, y + box_height - 65, "(DEV + QA + UAT)")
        
        # Values
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(np_x + box_width/2, y + box_height - 100, f"Peak ({self.months[non_prod_peak_idx][:3]}): ${non_prod_peak:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(np_x + box_width/2, y + box_height - 130, "v")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(np_x + box_width/2, y + box_height - 160, f"Nov 2025: ${np_end:,.0f}")
        
        # Savings
        self.c.setFont("Helvetica-Bold", 42)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(np_x + box_width/2, y + 70, f"-{np_pct:.0f}%")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(np_x + box_width/2, y + 30, f"${np_saved:,.0f} saved/month")
        
        # Production
        prod_x = start_x + box_width + gap
        prod_end = self.production[-1]
        prod_change = prod_end - prod_peak
        prod_pct = abs(prod_change / prod_peak) * 100
        
        self.c.setFillColor(colors.HexColor('#1f3d2a'))
        self.c.roundRect(prod_x, y, box_width, box_height, 12, fill=1, stroke=0)
        
        # Header
        self.c.setFillColor(GREEN)
        self.c.roundRect(prod_x, y + box_height - 50, box_width, 50, 12, fill=1, stroke=0)
        self.c.setFillColor(colors.HexColor('#1f3d2a'))
        self.c.rect(prod_x, y + box_height - 50, box_width, 20, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 35, "Production")
        
        self.c.setFont("Helvetica", 12)
        self.c.setFillColor(LIGHT_GRAY)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 65, "(PROD Environment)")
        
        # Values
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(ORANGE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 100, f"Peak ({self.months[prod_peak_idx][:3]}): ${prod_peak:,.0f}")
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 130, "v")
        
        self.c.setFont("Helvetica", 14)
        if prod_change <= 0:
            self.c.setFillColor(GREEN)
        else:
            self.c.setFillColor(YELLOW)
        self.c.drawCentredString(prod_x + box_width/2, y + box_height - 160, f"Nov 2025: ${prod_end:,.0f}")
        
        # Status
        self.c.setFont("Helvetica-Bold", 28)
        self.c.setFillColor(YELLOW)
        self.c.drawCentredString(prod_x + box_width/2, y + 70, "Stable")
        
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(LIGHT_GRAY)
        if prod_change < 0:
            self.c.drawCentredString(prod_x + box_width/2, y + 30, f"${abs(prod_change):,.0f} saved/month")
        else:
            self.c.drawCentredString(prod_x + box_width/2, y + 30, f"${prod_change:,.0f} increase (capacity)")
        
        # Combined total at bottom
        total_saved = np_saved + (prod_peak - prod_end if prod_change < 0 else 0)
        if prod_change > 0:
            total_saved = np_saved - prod_change
        else:
            total_saved = np_saved + abs(prod_change)
            
        peak_total = max(self.totals)
        nov_total = self.totals[-1]
        actual_saved = peak_total - nov_total
        
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect((self.width - 400)/2, 60, 400, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(GREEN)
        self.c.drawCentredString(self.width/2, 92, f"Net Savings: ${actual_saved:,.0f}/month")

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
            (f"${monthly_saved/1000:.1f}K", "Saved/Month", GREEN),
            (f"${annual_saved/1000:.1f}K", "Projected/Year", GREEN),
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
        
        # Optimization actions summary
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 260, "Key Optimization Actions (August 2025)")
        
        actions = [
            ("Database Cleanup", "Deleted unused databases", CYAN),
            ("Network Optimization", "Removed unused instances", PURPLE),
            ("Redis Consolidation", "Shared infrastructure", TEAL)
        ]
        
        action_width = 200
        action_start = (self.width - 3*action_width - 40) / 2
        action_y = self.height - 340
        
        for i, (title, desc, color) in enumerate(actions):
            x = action_start + i * (action_width + 20)
            
            self.c.setFillColor(colors.HexColor('#2a2d40'))
            self.c.roundRect(x, action_y, action_width, 65, 8, fill=1, stroke=0)
            
            self.c.setFillColor(color)
            self.c.rect(x, action_y + 60, action_width, 5, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(color)
            self.c.drawCentredString(x + action_width/2, action_y + 42, title)
            
            self.c.setFont("Helvetica", 10)
            self.c.setFillColor(LIGHT_GRAY)
            self.c.drawCentredString(x + action_width/2, action_y + 18, desc)
        
        # Impact areas
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, self.height - 395, "Impact: DEV, QA, and UAT Environments")
        
        # Environments impacted
        env_colors = [CYAN, YELLOW, PURPLE]
        env_names = ["DEV", "QA", "UAT"]
        env_start = (self.width - 3*80 - 40) / 2
        
        for i, (name, color) in enumerate(zip(env_names, env_colors)):
            x = env_start + i * 100
            self.c.setFillColor(color)
            self.c.roundRect(x, self.height - 440, 70, 28, 6, fill=1, stroke=0)
            self.c.setFont("Helvetica-Bold", 12)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(x + 35, self.height - 432, name)
        
        # Bottom message
        self.c.setFillColor(colors.HexColor('#1a3a1a'))
        self.c.roundRect(100, 70, self.width - 200, 55, 10, fill=1, stroke=0)
        
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(WHITE)
        self.c.drawCentredString(self.width/2, 97, "Optimized resources, reduced costs, maintained performance")

    def generate(self):
        print("=" * 70)
        print("  Price Matrix Application - Cost Optimization Presentation")
        print("=" * 70)
        print("")
        print("  Data Source: Azure Cost Management")
        print("  Period: June 2025 - November 2025 (6 Months)")
        print("")
        print("  6-Month Cost Data:")
        print("  " + "-" * 66)
        print(f"  {'Month':<12} {'DEV':>10} {'QA':>10} {'UAT':>10} {'PROD':>10} {'Total':>12}")
        print("  " + "-" * 66)
        for i, month in enumerate(self.months):
            total = self.totals[i]
            print(f"  {month:<12} ${self.dev_costs[i]:>8,.0f} ${self.qa_costs[i]:>8,.0f} ${self.uat_costs[i]:>8,.0f} ${self.prod_costs[i]:>8,.0f} ${total:>10,.0f}")
        print("  " + "-" * 66)
        print("")
        print("  Environment Groups:")
        np_peak = max(self.non_prod)
        prod_peak = max(self.production)
        print(f"    Non-Production: ${np_peak:,.0f} -> ${self.non_prod[-1]:,.0f} (saved ${np_peak - self.non_prod[-1]:,.0f})")
        print(f"    Production:     ${prod_peak:,.0f} -> ${self.production[-1]:,.0f}")
        peak_total = max(self.totals)
        print(f"    Total Savings:  ${peak_total - self.totals[-1]:,.0f}/month ({((peak_total - self.totals[-1])/peak_total)*100:.0f}% reduction)")
        print("")
        
        self.slide_1_title()
        print("  [OK] Slide 1: Title & Key Metrics")
        
        self.slide_2_before_after()
        print("  [OK] Slide 2: Before & After (Peak vs Current)")
        
        self.slide_3_optimization_actions()
        print("  [OK] Slide 3: Optimization Strategy & Actions")
        
        self.slide_4_data_table()
        print("  [OK] Slide 4: Full 6-Month Data Table")
        
        self.slide_5_trend_chart()
        print("  [OK] Slide 5: Cost Reduction Trend Chart")
        
        self.slide_6_environment_breakdown()
        print("  [OK] Slide 6: Environment Cost Summary")
        
        self.slide_7_summary()
        print("  [OK] Slide 7: Final Summary")
        
        self.c.save()
        print("")
        print("=" * 70)
        print(f"  Presentation saved: {self.filename}")
        print(f"  File size: {os.path.getsize(self.filename) / 1024:.1f} KB")
        print("=" * 70)


if __name__ == "__main__":
    pdf = PriceMatrixCostPDF("/workspace/Price_Matrix_Cost_Optimization.pdf")
    pdf.generate()
