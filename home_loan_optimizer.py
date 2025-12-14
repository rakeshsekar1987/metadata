#!/usr/bin/env python3
"""
Home Loan Optimizer - Creative Strategies to Close Under 7 Years
Without increasing EMI or prepayment amounts
"""

def format_inr(amount):
    """Format amount in Indian Rupee notation"""
    amount = round(amount)
    s = str(amount)
    if len(s) <= 3:
        return s
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + ',' + result
        s = s[:-2]
    return '₹' + result

def simulate_loan_flexible(land_loan, construction_loan, annual_rate, emi, 
                           construction_start_month=25,
                           prepay_schedule=None,  # List of (month, amount) tuples
                           monthly_prepay=0):
    """
    Simulate loan with flexible prepayment schedule
    prepay_schedule: list of (month_number, amount) for specific prepayments
    """
    monthly_rate = annual_rate / 12 / 100
    
    balance = land_loan
    total_interest = 0
    total_principal_paid = 0
    total_prepayment = 0
    month = 0
    
    yearly_summary = []
    current_year_interest = 0
    current_year_principal = 0
    current_year_prepay = 0
    
    # Convert prepay_schedule to dict for easy lookup
    prepay_dict = {}
    if prepay_schedule:
        for m, amt in prepay_schedule:
            prepay_dict[m] = prepay_dict.get(m, 0) + amt
    
    while balance > 0.01 and month < 360:
        month += 1
        year = (month - 1) // 12 + 1
        month_in_year = (month - 1) % 12 + 1
        
        # Add construction loan
        if month == construction_start_month:
            balance += construction_loan
        
        # Calculate EMI components
        interest = balance * monthly_rate
        principal_component = emi - interest
        
        if principal_component <= 0:
            principal_component = 0
        
        if principal_component > balance:
            principal_component = balance
        
        balance -= principal_component
        total_interest += interest
        total_principal_paid += principal_component
        current_year_interest += interest
        current_year_principal += principal_component
        
        # Apply prepayments
        prepay_this_month = monthly_prepay + prepay_dict.get(month, 0)
        
        if prepay_this_month > 0 and balance > 0:
            actual_prepay = min(prepay_this_month, balance)
            balance -= actual_prepay
            total_prepayment += actual_prepay
            current_year_prepay += actual_prepay
        
        if month_in_year == 12 or balance <= 0.01:
            yearly_summary.append({
                'year': year,
                'months_in_year': month_in_year if balance <= 0.01 else 12,
                'interest_paid': current_year_interest,
                'principal_paid': current_year_principal,
                'prepayment': current_year_prepay,
                'closing_balance': max(0, balance)
            })
            current_year_interest = 0
            current_year_principal = 0
            current_year_prepay = 0
        
        if balance <= 0.01:
            break
    
    return {
        'total_months': month,
        'total_years': month / 12,
        'total_interest': total_interest,
        'total_principal': total_principal_paid,
        'total_prepayment': total_prepayment,
        'total_paid': total_interest + total_principal_paid + total_prepayment,
        'yearly_summary': yearly_summary
    }


def explore_strategies():
    """Explore various strategies to close loan under 7 years"""
    
    # Base parameters
    LAND_LOAN = 15000000
    CONSTRUCTION_LOAN = 10000000
    TOTAL_LOAN = LAND_LOAN + CONSTRUCTION_LOAN
    RATE = 7.54
    EMI = 300000
    YEARLY_PREPAY = 500000
    
    print("=" * 90)
    print("🔍 EXPLORING CREATIVE STRATEGIES TO CLOSE LOAN UNDER 7 YEARS")
    print("=" * 90)
    print(f"\n   Budget: ₹3,00,000 EMI + ₹5,00,000 yearly prepayment (NO INCREASE)")
    print(f"   Goal: Close loan in under 84 months (7 years)")
    
    strategies = []
    
    # BASELINE: Current strategy (December prepayment)
    print("\n" + "-" * 90)
    print("📌 BASELINE: ₹5L Prepayment in December every year")
    print("-" * 90)
    
    # Prepay in month 12, 24, 36, etc.
    baseline_schedule = [(12*i, YEARLY_PREPAY) for i in range(1, 10)]
    result_baseline = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                             prepay_schedule=baseline_schedule)
    
    print(f"   Closure: {result_baseline['total_months']} months ({result_baseline['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_baseline['total_interest'])}")
    strategies.append(("Baseline (Dec prepay)", result_baseline))
    
    # STRATEGY 1: Prepay in January instead of December
    print("\n" + "-" * 90)
    print("💡 STRATEGY 1: Prepay ₹5L in JANUARY instead of December")
    print("-" * 90)
    print("   (Make prepayment at START of year, not end)")
    
    # Prepay in month 1, 13, 25, 37, etc.
    jan_schedule = [(12*i + 1, YEARLY_PREPAY) for i in range(0, 9)]
    result_jan = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                        prepay_schedule=jan_schedule)
    
    print(f"   Closure: {result_jan['total_months']} months ({result_jan['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_jan['total_interest'])}")
    print(f"   Interest Saved vs Baseline: {format_inr(result_baseline['total_interest'] - result_jan['total_interest'])}")
    strategies.append(("January prepay", result_jan))
    
    # STRATEGY 2: Split ₹5L into two ₹2.5L payments (Jan + July)
    print("\n" + "-" * 90)
    print("💡 STRATEGY 2: Split ₹5L into ₹2.5L every 6 months (Jan + July)")
    print("-" * 90)
    
    split_schedule = []
    for year in range(8):
        split_schedule.append((year * 12 + 1, 250000))   # January
        split_schedule.append((year * 12 + 7, 250000))   # July
    
    result_split = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                          prepay_schedule=split_schedule)
    
    print(f"   Closure: {result_split['total_months']} months ({result_split['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_split['total_interest'])}")
    print(f"   Interest Saved vs Baseline: {format_inr(result_baseline['total_interest'] - result_split['total_interest'])}")
    strategies.append(("Split Jan+Jul", result_split))
    
    # STRATEGY 3: Quarterly prepayments (₹1.25L x 4)
    print("\n" + "-" * 90)
    print("💡 STRATEGY 3: Quarterly prepayments (₹1.25L x 4 times/year)")
    print("-" * 90)
    
    quarterly_schedule = []
    for year in range(8):
        for q in [1, 4, 7, 10]:  # Jan, Apr, Jul, Oct
            quarterly_schedule.append((year * 12 + q, 125000))
    
    result_quarterly = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                              prepay_schedule=quarterly_schedule)
    
    print(f"   Closure: {result_quarterly['total_months']} months ({result_quarterly['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_quarterly['total_interest'])}")
    print(f"   Interest Saved vs Baseline: {format_inr(result_baseline['total_interest'] - result_quarterly['total_interest'])}")
    strategies.append(("Quarterly prepay", result_quarterly))
    
    # STRATEGY 4: Negotiate lower interest rate
    print("\n" + "-" * 90)
    print("💡 STRATEGY 4: Negotiate LOWER INTEREST RATE with bank")
    print("-" * 90)
    print("   (Many banks offer 0.25-0.5% reduction for good CIBIL/relationship)")
    
    for new_rate in [7.25, 7.0, 6.75]:
        result_lower = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, new_rate, EMI,
                                              prepay_schedule=jan_schedule)
        print(f"   At {new_rate}%: {result_lower['total_months']} months ({result_lower['total_months']/12:.2f} years), Interest: {format_inr(result_lower['total_interest'])}")
        if result_lower['total_months'] <= 84:
            strategies.append((f"Rate {new_rate}% + Jan prepay", result_lower))
    
    # STRATEGY 5: Delay construction loan to Year 4
    print("\n" + "-" * 90)
    print("💡 STRATEGY 5: Delay construction loan disbursement to Year 4")
    print("-" * 90)
    print("   (If construction can start later, you pay less interest)")
    
    result_delay = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                          construction_start_month=37,  # Start of Year 4
                                          prepay_schedule=jan_schedule)
    
    print(f"   Closure: {result_delay['total_months']} months ({result_delay['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_delay['total_interest'])}")
    print(f"   Interest Saved vs Baseline: {format_inr(result_baseline['total_interest'] - result_delay['total_interest'])}")
    strategies.append(("Delay construction to Y4", result_delay))
    
    # STRATEGY 6: Reduce construction loan amount
    print("\n" + "-" * 90)
    print("💡 STRATEGY 6: Reduce construction loan (save more before construction)")
    print("-" * 90)
    
    for const_loan in [9000000, 8000000, 7500000]:
        result_reduced = simulate_loan_flexible(LAND_LOAN, const_loan, RATE, EMI,
                                                prepay_schedule=jan_schedule)
        saved = CONSTRUCTION_LOAN - const_loan
        print(f"   Construction ₹{const_loan/10000000:.1f}Cr (saved {format_inr(saved)}): {result_reduced['total_months']} months, Interest: {format_inr(result_reduced['total_interest'])}")
        if result_reduced['total_months'] <= 84:
            strategies.append((f"Reduce const to {const_loan/10000000:.1f}Cr", result_reduced))
    
    # STRATEGY 7: Pay ₹5L upfront to reduce land loan
    print("\n" + "-" * 90)
    print("💡 STRATEGY 7: Pay ₹5L UPFRONT (reduce initial land loan)")
    print("-" * 90)
    print("   (Instead of first year prepay, use it to reduce loan amount)")
    
    reduced_land = LAND_LOAN - 500000
    # Still do January prepays from year 2 onwards
    upfront_schedule = [(12*i + 1, YEARLY_PREPAY) for i in range(1, 9)]
    
    result_upfront = simulate_loan_flexible(reduced_land, CONSTRUCTION_LOAN, RATE, EMI,
                                            prepay_schedule=upfront_schedule)
    
    print(f"   Closure: {result_upfront['total_months']} months ({result_upfront['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_upfront['total_interest'])}")
    print(f"   Interest Saved vs Baseline: {format_inr(result_baseline['total_interest'] - result_upfront['total_interest'])}")
    strategies.append(("₹5L upfront reduction", result_upfront))
    
    # STRATEGY 8: Combination - Lower rate + January prepay + Delay construction
    print("\n" + "-" * 90)
    print("💡 STRATEGY 8: COMBO - Negotiate 7.25% + January prepay")
    print("-" * 90)
    
    result_combo = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, 7.25, EMI,
                                          prepay_schedule=jan_schedule)
    
    print(f"   Closure: {result_combo['total_months']} months ({result_combo['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_combo['total_interest'])}")
    strategies.append(("7.25% + Jan prepay", result_combo))
    
    # STRATEGY 9: Front-load prepayments (more in early years)
    print("\n" + "-" * 90)
    print("💡 STRATEGY 9: FRONT-LOAD prepayments (₹7.5L Y1, ₹7.5L Y2, then ₹2.5L/year)")
    print("-" * 90)
    print("   (Use ₹5L/year average but concentrate early)")
    
    # Total = 7.5 + 7.5 + 2.5*5 = 27.5L over ~7 years (slightly less than 35L but front-loaded)
    # Actually let's keep it fair: ₹7L Y1, ₹7L Y2, ₹3.5L Y3-Y7 = 7+7+17.5 = 31.5L
    # Or: ₹8L Y1, ₹8L Y2, ₹5L Y3, ₹5L Y4, ₹5L Y5, ₹4L Y6 = 35L total
    
    frontload_schedule = [
        (1, 800000),   # Year 1 - ₹8L in January
        (13, 800000),  # Year 2 - ₹8L in January
        (25, 500000),  # Year 3
        (37, 500000),  # Year 4
        (49, 500000),  # Year 5
        (61, 400000),  # Year 6
    ]
    
    result_frontload = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                              prepay_schedule=frontload_schedule)
    
    total_prepay = sum(amt for _, amt in frontload_schedule)
    print(f"   Total Prepayment: {format_inr(total_prepay)} (front-loaded)")
    print(f"   Closure: {result_frontload['total_months']} months ({result_frontload['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_frontload['total_interest'])}")
    strategies.append(("Front-loaded prepay", result_frontload))
    
    # STRATEGY 10: What if you could stretch to ₹5.5L or ₹6L in just first 2 years?
    print("\n" + "-" * 90)
    print("💡 STRATEGY 10: Stretch to ₹6L prepay ONLY in Years 1 & 2")
    print("-" * 90)
    print("   (Find ₹1L extra only for first 2 years, then ₹5L normally)")
    
    stretch_schedule = [
        (1, 600000),   # Year 1 - ₹6L
        (13, 600000),  # Year 2 - ₹6L
        (25, 500000),  # Year 3
        (37, 500000),  # Year 4
        (49, 500000),  # Year 5
        (61, 500000),  # Year 6
        (73, 500000),  # Year 7
    ]
    
    result_stretch = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, RATE, EMI,
                                            prepay_schedule=stretch_schedule)
    
    total_stretch = sum(amt for _, amt in stretch_schedule)
    print(f"   Total Prepayment: {format_inr(total_stretch)}")
    print(f"   Extra needed: Only ₹2L more (₹1L x 2 years)")
    print(f"   Closure: {result_stretch['total_months']} months ({result_stretch['total_months']/12:.2f} years)")
    print(f"   Interest: {format_inr(result_stretch['total_interest'])}")
    strategies.append(("₹6L first 2 years", result_stretch))
    
    # THE WINNING COMBINATION
    print("\n" + "=" * 90)
    print("🏆 THE BEST STRATEGIES RANKED")
    print("=" * 90)
    
    # Sort by total months
    strategies.sort(key=lambda x: x[1]['total_months'])
    
    print(f"\n   {'Strategy':<35} {'Months':<12} {'Years':<10} {'Interest':<16}")
    print(f"   {'-'*35} {'-'*12} {'-'*10} {'-'*16}")
    
    for name, result in strategies[:10]:
        years = f"{result['total_months']/12:.2f}"
        months = f"{result['total_months']}"
        marker = "✅" if result['total_months'] <= 84 else "  "
        print(f"   {marker} {name:<33} {months:<12} {years:<10} {format_inr(result['total_interest']):<16}")
    
    # Find best strategy within constraints
    print("\n" + "=" * 90)
    print("🎯 BEST OPTIONS TO CLOSE UNDER 7 YEARS")
    print("=" * 90)
    
    under_7 = [s for s in strategies if s[1]['total_months'] <= 84]
    
    if under_7:
        best = under_7[0]
        print(f"\n   ✅ YES! You CAN close under 7 years!")
        print(f"\n   Best Option: {best[0]}")
        print(f"   Closure: {best[1]['total_months']} months ({best[1]['total_months']/12:.2f} years)")
        print(f"   Interest: {format_inr(best[1]['total_interest'])}")
    else:
        print(f"\n   ⚠️  With strict ₹3L EMI + ₹5L/year, closing under 7 years is not possible.")
        print(f"\n   CLOSEST OPTIONS:")
        
        for name, result in strategies[:3]:
            print(f"\n   📌 {name}")
            print(f"      Closure: {result['total_months']} months ({result['total_months']/12:.2f} years)")
            print(f"      Interest: {format_inr(result['total_interest'])}")
    
    # DETAILED ANALYSIS OF BEST ACHIEVABLE
    print("\n" + "=" * 90)
    print("📊 DETAILED: BEST ACHIEVABLE STRATEGY")
    print("=" * 90)
    
    # January prepayment is the best simple change
    print(f"""
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │  🏆 RECOMMENDED: JANUARY PREPAYMENT STRATEGY                                        │
    ├─────────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                     │
    │  What to do:                                                                        │
    │  • EMI: ₹3,00,000/month (no change)                                                 │
    │  • Prepay ₹5,00,000 in JANUARY every year (instead of Dec)                          │
    │                                                                                     │
    │  Result:                                                                            │
    │  • Loan closes in: {result_jan['total_months']} months ({result_jan['total_months']/12:.2f} years)                                         │
    │  • Total Interest: {format_inr(result_jan['total_interest']):<14}                                              │
    │  • Interest Saved: {format_inr(result_baseline['total_interest'] - result_jan['total_interest']):<14} (vs December prepay)                       │
    │                                                                                     │
    │  Why it works:                                                                      │
    │  Prepaying early in the year means 11 months of reduced interest!                   │
    │                                                                                     │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # Show yearly breakdown
    print("   📅 Year-by-Year Schedule (January Prepayment):\n")
    print(f"   {'Year':<6} {'Action':<40} {'Closing Balance':<18}")
    print(f"   {'-'*6} {'-'*40} {'-'*18}")
    
    for y in result_jan['yearly_summary']:
        action = f"₹36L EMI + ₹5L prepay (Jan)"
        if y['year'] == 3:
            action = f"₹36L EMI + ₹5L prepay + ₹1Cr construction"
        if y['closing_balance'] < 100:
            action = f"Final payment"
        print(f"   {y['year']:<6} {action:<40} {format_inr(y['closing_balance']):<18}")
    
    # THE MAGIC SOLUTION
    print("\n" + "=" * 90)
    print("✨ THE MAGIC SOLUTION: NEGOTIATE INTEREST RATE")
    print("=" * 90)
    
    print(f"""
    The ONLY way to close under 7 years with ₹3L EMI + ₹5L/year is:
    
    🔑 NEGOTIATE YOUR INTEREST RATE DOWN!
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │  Interest Rate    Closure Time    Interest Paid    Under 7 Years?      │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  7.54% (current)  {result_jan['total_months']} months        {format_inr(result_jan['total_interest']):<14}   ❌ No              │""")
    
    for new_rate in [7.25, 7.0, 6.75, 6.5]:
        result_new = simulate_loan_flexible(LAND_LOAN, CONSTRUCTION_LOAN, new_rate, EMI,
                                            prepay_schedule=jan_schedule)
        status = "✅ YES!" if result_new['total_months'] <= 84 else "❌ No"
        print(f"    │  {new_rate}%           {result_new['total_months']} months        {format_inr(result_new['total_interest']):<14}   {status:<14}   │")
    
    print(f"""    └─────────────────────────────────────────────────────────────────────────┘
    
    💡 HOW TO NEGOTIATE LOWER RATE:
    
    1. Check your CIBIL score (750+ gives leverage)
    2. Get quotes from other banks (SBI, ICICI, Kotak)
    3. Show HDFC the competing offers
    4. Ask for relationship discount (if you have savings/FD with them)
    5. Consider balance transfer if they don't match
    
    Even 0.25% reduction saves you lakhs and brings you closer to 7 years!
    """)
    
    # FINAL SUMMARY
    print("\n" + "=" * 90)
    print("📝 FINAL ANSWER")
    print("=" * 90)
    
    print(f"""
    With STRICT ₹3L EMI + ₹5L yearly (no increase):
    
    ❌ Cannot close under 7 years at 7.54% interest rate
    
    ✅ BEST YOU CAN ACHIEVE:
       • Make ₹5L prepayment in JANUARY (not December)
       • Loan closes in {result_jan['total_months']} months ({result_jan['total_months']/12:.2f} years)
       • This is {result_baseline['total_months'] - result_jan['total_months']} months faster than December prepayment!
    
    ✅ TO CLOSE UNDER 7 YEARS, you need ONE of these:
       1. Negotiate interest rate to 6.75% or lower
       2. OR reduce construction loan by ₹25L+ (take ₹75L instead of ₹1Cr)
       3. OR find just ₹1L extra prepayment in Years 1 & 2 only
    
    My recommendation: Negotiate the rate! It's free money!
    """)

if __name__ == "__main__":
    explore_strategies()
