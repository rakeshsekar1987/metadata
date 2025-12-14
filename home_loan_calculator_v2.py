#!/usr/bin/env python3
"""
Composite Home Loan Calculator - With Budget Constraints
- Max EMI: ₹3,00,000/month
- Max Annual Bonus Prepayment: ₹5,00,000/year
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

def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate EMI using standard formula"""
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        return principal / tenure_months
    emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
    return emi

def simulate_loan(land_loan, construction_loan, annual_rate, emi, 
                  construction_start_month=25,
                  monthly_prepay=0, yearly_prepay=0, yearly_prepay_month=12):
    """
    Simulate loan with phased disbursement
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
    current_year_emi_paid = 0
    
    while balance > 0.01 and month < 360:  # Max 30 years safety
        month += 1
        year = (month - 1) // 12 + 1
        month_in_year = (month - 1) % 12 + 1
        
        # Add construction loan at start of year 3
        if month == construction_start_month:
            balance += construction_loan
        
        # Calculate interest for this month
        interest = balance * monthly_rate
        principal_component = emi - interest
        
        if principal_component <= 0:
            principal_component = 0
        
        # Handle last payment
        if principal_component > balance:
            principal_component = balance
            actual_emi = principal_component + interest
        else:
            actual_emi = emi
        
        balance -= principal_component
        total_interest += interest
        total_principal_paid += principal_component
        current_year_interest += interest
        current_year_principal += principal_component
        current_year_emi_paid += actual_emi
        
        # Apply prepayments
        prepay_this_month = monthly_prepay
        if month_in_year == yearly_prepay_month and yearly_prepay > 0:
            prepay_this_month += yearly_prepay
        
        if prepay_this_month > 0 and balance > 0:
            actual_prepay = min(prepay_this_month, balance)
            balance -= actual_prepay
            total_prepayment += actual_prepay
            current_year_prepay += actual_prepay
        
        # Year end summary
        if month_in_year == 12 or balance <= 0.01:
            yearly_summary.append({
                'year': year,
                'months_in_year': month_in_year if balance <= 0.01 else 12,
                'interest_paid': current_year_interest,
                'principal_paid': current_year_principal,
                'prepayment': current_year_prepay,
                'total_paid': current_year_emi_paid + current_year_prepay,
                'closing_balance': max(0, balance)
            })
            current_year_interest = 0
            current_year_principal = 0
            current_year_prepay = 0
            current_year_emi_paid = 0
        
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

def analyze_with_constraints(land_loan, construction_loan, annual_rate, 
                              max_emi, max_yearly_bonus, target_years=7):
    """Analyze loan with user's budget constraints"""
    
    total_loan = land_loan + construction_loan
    target_months = target_years * 12
    
    print("=" * 85)
    print("COMPOSITE HOME LOAN ANALYSIS - WITH YOUR BUDGET CONSTRAINTS")
    print("=" * 85)
    
    print(f"\n📋 LOAN STRUCTURE:")
    print(f"   • Land Loan (Year 1-2):       {format_inr(land_loan)}")
    print(f"   • Construction Loan (Year 3): {format_inr(construction_loan)}")
    print(f"   • Total Loan Amount:          {format_inr(total_loan)}")
    print(f"   • Interest Rate:              {annual_rate}% P.A.")
    
    print(f"\n💰 YOUR BUDGET CONSTRAINTS:")
    print(f"   • Maximum EMI:                {format_inr(max_emi)}/month")
    print(f"   • Maximum Annual Bonus:       {format_inr(max_yearly_bonus)}/year")
    print(f"   • Target Closure:             {target_years} years")
    
    # Calculate what EMI would be needed for 7-year closure without prepayment
    # Using binary search
    low_emi = 200000
    high_emi = 500000
    for _ in range(50):
        mid_emi = (low_emi + high_emi) / 2
        result = simulate_loan(land_loan, construction_loan, annual_rate, mid_emi)
        if result['total_months'] > target_months:
            low_emi = mid_emi
        else:
            high_emi = mid_emi
    emi_needed_for_7yr = high_emi
    
    print(f"\n📊 REALITY CHECK:")
    print(f"   • EMI needed for 7-year closure (no prepay): {format_inr(emi_needed_for_7yr)}")
    print(f"   • Your max EMI: {format_inr(max_emi)}")
    print(f"   • Gap: {format_inr(emi_needed_for_7yr - max_emi)}")
    
    if emi_needed_for_7yr <= max_emi:
        print(f"   ✅ Good news! Your max EMI is sufficient for 7-year closure!")
    else:
        print(f"   ⚠️  Your max EMI alone won't achieve 7-year closure. Let's see how prepayments help!")
    
    # Strategy 1: Max EMI only (no prepayment)
    print("\n" + "=" * 85)
    print("STRATEGY 1: MAX EMI ONLY (₹3,00,000/month, No Prepayment)")
    print("=" * 85)
    
    result1 = simulate_loan(land_loan, construction_loan, annual_rate, max_emi)
    
    print(f"\n   Monthly EMI: {format_inr(max_emi)}")
    print(f"   Loan Closure: {result1['total_months']} months ({result1['total_months']/12:.1f} years)")
    print(f"   Total Interest: {format_inr(result1['total_interest'])}")
    print(f"   Total Paid: {format_inr(result1['total_paid'])}")
    
    # Strategy 2: Max EMI + Max Annual Bonus
    print("\n" + "=" * 85)
    print("STRATEGY 2: MAX EMI + MAX ANNUAL BONUS (₹3L/month + ₹5L/year)")
    print("=" * 85)
    
    result2 = simulate_loan(land_loan, construction_loan, annual_rate, max_emi, 
                            yearly_prepay=max_yearly_bonus)
    
    print(f"\n   Monthly EMI: {format_inr(max_emi)}")
    print(f"   Annual Bonus Prepayment: {format_inr(max_yearly_bonus)}")
    print(f"   Loan Closure: {result2['total_months']} months ({result2['total_months']/12:.1f} years)")
    print(f"   Total Interest: {format_inr(result2['total_interest'])}")
    print(f"   Total Prepayment: {format_inr(result2['total_prepayment'])}")
    print(f"   Total Paid: {format_inr(result2['total_paid'])}")
    
    print(f"\n   📅 YEAR-WISE BREAKDOWN:")
    print(f"   {'Year':<6} {'EMI Paid':<14} {'Interest':<14} {'Principal':<14} {'Prepay':<12} {'Balance':<16}")
    print(f"   {'-'*6} {'-'*14} {'-'*14} {'-'*14} {'-'*12} {'-'*16}")
    for y in result2['yearly_summary']:
        emi_for_year = max_emi * y['months_in_year']
        print(f"   {y['year']:<6} {format_inr(emi_for_year):<14} {format_inr(y['interest_paid']):<14} {format_inr(y['principal_paid']):<14} {format_inr(y['prepayment']):<12} {format_inr(y['closing_balance']):<16}")
    
    # Strategy 3: Find optimal EMI + monthly prepay combination within budget
    print("\n" + "=" * 85)
    print("STRATEGY 3: OPTIMAL EMI + MONTHLY SAVINGS + ANNUAL BONUS")
    print("=" * 85)
    
    # Try different EMI levels and see what additional monthly saving is needed
    best_strategy = None
    strategies = []
    
    for emi in [250000, 275000, 300000]:
        # Find monthly prepay needed to hit 7 years (with annual bonus)
        low_mp = 0
        high_mp = 200000
        
        for _ in range(50):
            mid_mp = (low_mp + high_mp) / 2
            result = simulate_loan(land_loan, construction_loan, annual_rate, emi,
                                  monthly_prepay=mid_mp, yearly_prepay=max_yearly_bonus)
            if result['total_months'] > target_months:
                low_mp = mid_mp
            else:
                high_mp = mid_mp
        
        monthly_prepay_needed = high_mp
        result = simulate_loan(land_loan, construction_loan, annual_rate, emi,
                              monthly_prepay=monthly_prepay_needed, yearly_prepay=max_yearly_bonus)
        
        total_monthly = emi + monthly_prepay_needed
        
        strategies.append({
            'emi': emi,
            'monthly_prepay': monthly_prepay_needed,
            'total_monthly': total_monthly,
            'yearly_bonus': max_yearly_bonus,
            'months': result['total_months'],
            'total_interest': result['total_interest'],
            'result': result
        })
    
    print(f"\n   Options to close in ~7 years (with ₹5L annual bonus):\n")
    print(f"   {'EMI':<14} {'Monthly Prepay':<16} {'Total/Month':<14} {'Closure':<12} {'Interest':<14}")
    print(f"   {'-'*14} {'-'*16} {'-'*14} {'-'*12} {'-'*14}")
    
    for s in strategies:
        closure = f"{s['months']} months"
        print(f"   {format_inr(s['emi']):<14} {format_inr(s['monthly_prepay']):<16} {format_inr(s['total_monthly']):<14} {closure:<12} {format_inr(s['total_interest']):<14}")
    
    # Strategy 4: What if you can't do monthly prepayment - only annual bonus
    print("\n" + "=" * 85)
    print("STRATEGY 4: DIFFERENT EMI LEVELS + ONLY ANNUAL BONUS (No Monthly Prepay)")
    print("=" * 85)
    
    print(f"\n   Comparison at different EMI levels (with ₹5L annual bonus only):\n")
    print(f"   {'EMI':<14} {'Closure Time':<16} {'Total Interest':<16} {'Interest Saved':<16}")
    print(f"   {'-'*14} {'-'*16} {'-'*16} {'-'*16}")
    
    baseline = simulate_loan(land_loan, construction_loan, annual_rate, 297277)  # Original 10-yr EMI
    
    for emi in [250000, 275000, 300000]:
        result = simulate_loan(land_loan, construction_loan, annual_rate, emi,
                              yearly_prepay=max_yearly_bonus)
        years = result['total_months'] / 12
        closure = f"{result['total_months']} mo ({years:.1f} yr)"
        saved = baseline['total_interest'] - result['total_interest']
        print(f"   {format_inr(emi):<14} {closure:<16} {format_inr(result['total_interest']):<16} {format_inr(saved):<16}")
    
    # Best achievable with constraints
    print("\n" + "=" * 85)
    print("🎯 BEST STRATEGY WITH YOUR CONSTRAINTS")
    print("=" * 85)
    
    # With max EMI and max bonus, what's the fastest closure?
    result_best = simulate_loan(land_loan, construction_loan, annual_rate, max_emi,
                                yearly_prepay=max_yearly_bonus)
    
    # What additional monthly prepay needed for exactly 7 years?
    low_mp = 0
    high_mp = 100000
    for _ in range(50):
        mid_mp = (low_mp + high_mp) / 2
        result = simulate_loan(land_loan, construction_loan, annual_rate, max_emi,
                              monthly_prepay=mid_mp, yearly_prepay=max_yearly_bonus)
        if result['total_months'] > target_months:
            low_mp = mid_mp
        else:
            high_mp = mid_mp
    
    additional_monthly_for_7yr = high_mp
    result_7yr = simulate_loan(land_loan, construction_loan, annual_rate, max_emi,
                               monthly_prepay=additional_monthly_for_7yr, 
                               yearly_prepay=max_yearly_bonus)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │  📌 YOUR OPTIMAL STRATEGY                                                       │
    ├─────────────────────────────────────────────────────────────────────────────────┤
    │                                                                                 │
    │  Monthly EMI:              {format_inr(max_emi):<14}                                   │
    │  Annual Bonus Prepayment:  {format_inr(max_yearly_bonus):<14} (every year in December)           │
    │                                                                                 │
    │  ⏱️  Loan Closes in:        {result_best['total_months']} months ({result_best['total_months']/12:.1f} years)                           │
    │  💵 Total Interest:        {format_inr(result_best['total_interest']):<14}                                   │
    │  💰 Total Prepayment:      {format_inr(result_best['total_prepayment']):<14}                                   │
    │                                                                                 │
    └─────────────────────────────────────────────────────────────────────────────────┘
    """)
    
    if result_best['total_months'] > target_months:
        print(f"""
    ⚠️  TO ACHIEVE EXACTLY 7 YEARS:
    
    You need an additional monthly prepayment of {format_inr(additional_monthly_for_7yr)}
    
    Total monthly outflow would be: {format_inr(max_emi)} + {format_inr(additional_monthly_for_7yr)} = {format_inr(max_emi + additional_monthly_for_7yr)}
        """)
    
    # Detailed yearly breakdown for best strategy
    print("\n" + "=" * 85)
    print("📅 DETAILED YEAR-BY-YEAR PAYMENT SCHEDULE")
    print("=" * 85)
    print(f"\n   (EMI: {format_inr(max_emi)}/month + Annual Bonus: {format_inr(max_yearly_bonus)})\n")
    
    print(f"   {'Year':<6} {'Monthly EMI':<14} {'Yearly EMI':<14} {'Bonus Prepay':<14} {'Interest':<14} {'Closing Bal':<16}")
    print(f"   {'-'*6} {'-'*14} {'-'*14} {'-'*14} {'-'*14} {'-'*16}")
    
    total_emi_paid = 0
    total_bonus_paid = 0
    
    for y in result_best['yearly_summary']:
        months = y['months_in_year']
        yearly_emi = max_emi * months
        total_emi_paid += yearly_emi
        total_bonus_paid += y['prepayment']
        print(f"   {y['year']:<6} {format_inr(max_emi):<14} {format_inr(yearly_emi):<14} {format_inr(y['prepayment']):<14} {format_inr(y['interest_paid']):<14} {format_inr(y['closing_balance']):<16}")
    
    print(f"   {'-'*6} {'-'*14} {'-'*14} {'-'*14} {'-'*14} {'-'*16}")
    print(f"   {'TOTAL':<6} {'':<14} {format_inr(total_emi_paid):<14} {format_inr(total_bonus_paid):<14} {format_inr(result_best['total_interest']):<14}")
    
    # Compare with original scenario
    print("\n" + "=" * 85)
    print("📊 COMPARISON: YOUR STRATEGY vs ORIGINAL 10-YEAR PLAN")
    print("=" * 85)
    
    original_emi = calculate_emi(total_loan, annual_rate, 120)
    result_original = simulate_loan(land_loan, construction_loan, annual_rate, original_emi)
    
    print(f"""
    ┌────────────────────────────────────────────────────────────────────────┐
    │                    ORIGINAL 10-YR     YOUR STRATEGY      SAVINGS       │
    ├────────────────────────────────────────────────────────────────────────┤
    │ Monthly EMI        {format_inr(original_emi):<14}    {format_inr(max_emi):<14}    -            │
    │ Annual Prepay      ₹0                 {format_inr(max_yearly_bonus):<14}    -            │
    │ Loan Tenure        {result_original['total_months']} months          {result_best['total_months']} months           {result_original['total_months'] - result_best['total_months']} months     │
    │ Total Interest     {format_inr(result_original['total_interest']):<14}    {format_inr(result_best['total_interest']):<14}    {format_inr(result_original['total_interest'] - result_best['total_interest']):<12} │
    │ Total Paid         {format_inr(result_original['total_paid']):<14}    {format_inr(result_best['total_paid']):<14}    {format_inr(result_original['total_paid'] - result_best['total_paid']):<12} │
    └────────────────────────────────────────────────────────────────────────┘
    """)
    
    # Final Recommendations
    print("\n" + "=" * 85)
    print("💡 FINAL RECOMMENDATIONS")
    print("=" * 85)
    
    print(f"""
    1. 🎯 PRIMARY STRATEGY:
       • Pay EMI of {format_inr(max_emi)} every month
       • Make {format_inr(max_yearly_bonus)} prepayment every year (use your bonus)
       • Loan closes in {result_best['total_months']/12:.1f} years
       • You save {format_inr(result_original['total_interest'] - result_best['total_interest'])} in interest!

    2. 💰 IF YOU CAN SAVE A LITTLE MORE MONTHLY:
       • Add {format_inr(additional_monthly_for_7yr)} monthly prepayment
       • This brings closure to exactly 7 years
       • Total monthly outflow: {format_inr(max_emi + additional_monthly_for_7yr)}

    3. 📈 SMART TIPS:
       • Make prepayments early in the year (January instead of December)
         This saves even more interest!
       • Any windfall (gifts, tax refunds, increments) → Put towards loan
       • Consider increasing prepayment when you get salary hikes

    4. 🏦 TAX BENEFITS (Don't forget to claim!):
       • Section 24(b): Up to ₹2,00,000 on interest
       • Section 80C: Up to ₹1,50,000 on principal
       • This effectively reduces your cost further!

    5. ⚠️  IMPORTANT:
       • Check with HDFC if there's any prepayment penalty
       • Most banks allow unlimited prepayment for floating rate loans
       • Keep 3-6 months EMI as emergency fund before aggressive prepayment
    """)

# Main execution
if __name__ == "__main__":
    # Loan parameters
    LAND_LOAN = 15000000          # ₹1.5 Crore
    CONSTRUCTION_LOAN = 10000000  # ₹1 Crore
    ANNUAL_RATE = 7.54            # 7.54% P.A.
    
    # User's constraints
    MAX_EMI = 300000              # ₹3 Lakh/month
    MAX_YEARLY_BONUS = 500000     # ₹5 Lakh/year
    TARGET_YEARS = 7
    
    analyze_with_constraints(LAND_LOAN, CONSTRUCTION_LOAN, ANNUAL_RATE,
                            MAX_EMI, MAX_YEARLY_BONUS, TARGET_YEARS)
