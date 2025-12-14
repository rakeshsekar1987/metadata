#!/usr/bin/env python3
"""
Composite Home Loan Calculator
- Phase 1: Land Loan ₹1.5 Cr (Year 1-2)
- Phase 2: Construction Loan ₹1 Cr added (Year 3 onwards)
- Target: Close loan in 7 years
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

def simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, fixed_emi, 
                                  construction_start_month=25, target_months=84,
                                  monthly_prepay=0, yearly_prepay=0, yearly_prepay_month=12):
    """
    Simulate loan with phased disbursement and fixed EMI
    """
    monthly_rate = annual_rate / 12 / 100
    
    # Track balances
    balance = land_loan
    total_interest = 0
    total_principal_paid = 0
    total_prepayment = 0
    month = 0
    
    schedule = []
    yearly_summary = []
    current_year_interest = 0
    current_year_principal = 0
    current_year_prepay = 0
    
    while balance > 0 and month < 360:  # Max 30 years safety
        month += 1
        year = (month - 1) // 12 + 1
        month_in_year = (month - 1) % 12 + 1
        
        # Add construction loan at start of year 3
        if month == construction_start_month:
            balance += construction_loan
            schedule.append({
                'month': month,
                'event': f'Construction loan of {format_inr(construction_loan)} disbursed',
                'new_balance': balance
            })
        
        # Calculate interest for this month
        interest = balance * monthly_rate
        principal_component = fixed_emi - interest
        
        # If EMI is less than interest, we have a problem
        if principal_component <= 0:
            print(f"WARNING: EMI {format_inr(fixed_emi)} is less than interest {format_inr(interest)} at month {month}")
            principal_component = 0
        
        # Handle last payment
        if principal_component > balance:
            principal_component = balance
            actual_emi = principal_component + interest
        else:
            actual_emi = fixed_emi
        
        balance -= principal_component
        total_interest += interest
        total_principal_paid += principal_component
        current_year_interest += interest
        current_year_principal += principal_component
        
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
        if month_in_year == 12 or balance <= 0:
            yearly_summary.append({
                'year': year,
                'interest_paid': current_year_interest,
                'principal_paid': current_year_principal,
                'prepayment': current_year_prepay,
                'closing_balance': balance
            })
            current_year_interest = 0
            current_year_principal = 0
            current_year_prepay = 0
        
        if balance <= 0:
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

def find_optimal_strategy(land_loan, construction_loan, annual_rate, target_months=84):
    """Find optimal EMI and prepayment strategy to close in target months"""
    
    total_loan = land_loan + construction_loan
    
    print("=" * 80)
    print("COMPOSITE HOME LOAN ANALYSIS")
    print("=" * 80)
    print(f"\n📋 LOAN STRUCTURE:")
    print(f"   • Land Loan (Year 1-2):      {format_inr(land_loan)}")
    print(f"   • Construction Loan (Year 3): {format_inr(construction_loan)}")
    print(f"   • Total Loan Amount:          {format_inr(total_loan)}")
    print(f"   • Interest Rate:              {annual_rate}% P.A.")
    print(f"   • Target Closure:             {target_months} months ({target_months/12:.1f} years)")
    
    # Scenario 1: Original 10-year EMI (as reference)
    print("\n" + "=" * 80)
    print("SCENARIO 1: ORIGINAL 10-YEAR PLAN (Reference)")
    print("=" * 80)
    
    original_emi = calculate_emi(total_loan, annual_rate, 120)
    result_original = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, original_emi)
    
    print(f"\n   Monthly EMI: {format_inr(original_emi)}")
    print(f"   Total Months: {result_original['total_months']}")
    print(f"   Total Interest: {format_inr(result_original['total_interest'])}")
    print(f"   Total Paid: {format_inr(result_original['total_paid'])}")
    
    # Scenario 2: Fixed EMI for 7-year closure (no prepayment)
    print("\n" + "=" * 80)
    print("SCENARIO 2: HIGHER EMI FOR 7-YEAR CLOSURE (No Prepayment)")
    print("=" * 80)
    
    # We need to find EMI that closes the phased loan in 84 months
    # Binary search for optimal EMI
    low_emi = calculate_emi(total_loan, annual_rate, 120)
    high_emi = calculate_emi(total_loan, annual_rate, 60)
    
    for _ in range(50):  # Binary search iterations
        mid_emi = (low_emi + high_emi) / 2
        result = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, mid_emi)
        if result['total_months'] > target_months:
            low_emi = mid_emi
        else:
            high_emi = mid_emi
    
    emi_7year = high_emi
    result_7year = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, emi_7year)
    
    print(f"\n   Monthly EMI Required: {format_inr(emi_7year)}")
    print(f"   EMI Increase from Original: {format_inr(emi_7year - original_emi)} (+{((emi_7year/original_emi)-1)*100:.1f}%)")
    print(f"   Total Months: {result_7year['total_months']}")
    print(f"   Total Interest: {format_inr(result_7year['total_interest'])}")
    print(f"   Interest Saved vs 10-year: {format_inr(result_original['total_interest'] - result_7year['total_interest'])}")
    
    print(f"\n   📅 YEAR-WISE BREAKDOWN:")
    print(f"   {'Year':<6} {'Interest':<15} {'Principal':<15} {'Closing Balance':<18}")
    print(f"   {'-'*6} {'-'*15} {'-'*15} {'-'*18}")
    for y in result_7year['yearly_summary']:
        print(f"   {y['year']:<6} {format_inr(y['interest_paid']):<15} {format_inr(y['principal_paid']):<15} {format_inr(y['closing_balance']):<18}")
    
    # Scenario 3: Keep original EMI + Monthly Prepayment
    print("\n" + "=" * 80)
    print("SCENARIO 3: ORIGINAL EMI + MONTHLY PREPAYMENT")
    print("=" * 80)
    
    # Find monthly prepayment needed
    low_prepay = 0
    high_prepay = 500000
    
    for _ in range(50):
        mid_prepay = (low_prepay + high_prepay) / 2
        result = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, 
                                               original_emi, monthly_prepay=mid_prepay)
        if result['total_months'] > target_months:
            low_prepay = mid_prepay
        else:
            high_prepay = mid_prepay
    
    monthly_prepay_needed = high_prepay
    result_prepay = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, 
                                                  original_emi, monthly_prepay=monthly_prepay_needed)
    
    total_monthly_outflow = original_emi + monthly_prepay_needed
    
    print(f"\n   Monthly EMI: {format_inr(original_emi)}")
    print(f"   Monthly Prepayment: {format_inr(monthly_prepay_needed)}")
    print(f"   Total Monthly Outflow: {format_inr(total_monthly_outflow)}")
    print(f"   Total Months: {result_prepay['total_months']}")
    print(f"   Total Interest: {format_inr(result_prepay['total_interest'])}")
    print(f"   Total Prepayment Made: {format_inr(result_prepay['total_prepayment'])}")
    print(f"   Interest Saved vs 10-year: {format_inr(result_original['total_interest'] - result_prepay['total_interest'])}")
    
    # Scenario 4: Original EMI + Yearly Lump Sum Prepayment
    print("\n" + "=" * 80)
    print("SCENARIO 4: ORIGINAL EMI + YEARLY LUMP SUM PREPAYMENT")
    print("=" * 80)
    
    low_yearly = 0
    high_yearly = 5000000
    
    for _ in range(50):
        mid_yearly = (low_yearly + high_yearly) / 2
        result = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, 
                                               original_emi, yearly_prepay=mid_yearly)
        if result['total_months'] > target_months:
            low_yearly = mid_yearly
        else:
            high_yearly = mid_yearly
    
    yearly_prepay_needed = high_yearly
    result_yearly = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, 
                                                  original_emi, yearly_prepay=yearly_prepay_needed)
    
    print(f"\n   Monthly EMI: {format_inr(original_emi)}")
    print(f"   Yearly Prepayment (every December): {format_inr(yearly_prepay_needed)}")
    print(f"   Total Months: {result_yearly['total_months']}")
    print(f"   Total Interest: {format_inr(result_yearly['total_interest'])}")
    print(f"   Total Prepayment Made: {format_inr(result_yearly['total_prepayment'])}")
    print(f"   Interest Saved vs 10-year: {format_inr(result_original['total_interest'] - result_yearly['total_interest'])}")
    
    # Scenario 5: Hybrid - Moderate EMI increase + Moderate Prepayment
    print("\n" + "=" * 80)
    print("SCENARIO 5: HYBRID - MODERATE EMI + MODERATE PREPAYMENT")
    print("=" * 80)
    
    # Increase EMI by 15% and find prepayment needed
    hybrid_emi = original_emi * 1.15
    
    low_prepay = 0
    high_prepay = 300000
    
    for _ in range(50):
        mid_prepay = (low_prepay + high_prepay) / 2
        result = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, 
                                               hybrid_emi, monthly_prepay=mid_prepay)
        if result['total_months'] > target_months:
            low_prepay = mid_prepay
        else:
            high_prepay = mid_prepay
    
    hybrid_monthly_prepay = high_prepay
    result_hybrid = simulate_loan_with_fixed_emi(land_loan, construction_loan, annual_rate, 
                                                  hybrid_emi, monthly_prepay=hybrid_monthly_prepay)
    
    print(f"\n   Monthly EMI: {format_inr(hybrid_emi)} (+15% from original)")
    print(f"   Monthly Prepayment: {format_inr(hybrid_monthly_prepay)}")
    print(f"   Total Monthly Outflow: {format_inr(hybrid_emi + hybrid_monthly_prepay)}")
    print(f"   Total Months: {result_hybrid['total_months']}")
    print(f"   Total Interest: {format_inr(result_hybrid['total_interest'])}")
    print(f"   Interest Saved vs 10-year: {format_inr(result_original['total_interest'] - result_hybrid['total_interest'])}")
    
    # Phase-wise EMI Analysis
    print("\n" + "=" * 80)
    print("PHASE-WISE EMI ANALYSIS (Using 7-Year Strategy)")
    print("=" * 80)
    
    # EMI for just land loan portion (first 2 years)
    # This is tricky because loan tenure changes
    land_only_emi = calculate_emi(land_loan, annual_rate, target_months)
    
    print(f"\n   📍 PHASE 1 (Year 1-2): Land Loan Only")
    print(f"      Principal: {format_inr(land_loan)}")
    print(f"      If separate 7-yr EMI: {format_inr(land_only_emi)}")
    
    # After 24 months, remaining balance
    monthly_rate = annual_rate / 12 / 100
    balance_after_2yr = land_loan
    interest_yr1_2 = 0
    for m in range(24):
        interest = balance_after_2yr * monthly_rate
        principal = emi_7year - interest
        balance_after_2yr -= principal
        interest_yr1_2 += interest
    
    print(f"      With combined EMI ({format_inr(emi_7year)}), balance after 2 years: {format_inr(balance_after_2yr)}")
    
    print(f"\n   📍 PHASE 2 (Year 3-7): After Construction Loan Added")
    print(f"      Balance from Land Loan: {format_inr(balance_after_2yr)}")
    print(f"      + Construction Loan: {format_inr(construction_loan)}")
    print(f"      = New Principal: {format_inr(balance_after_2yr + construction_loan)}")
    print(f"      Remaining Tenure: 60 months (5 years)")
    print(f"      Continue same EMI: {format_inr(emi_7year)}")
    
    # RECOMMENDATIONS
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS")
    print("=" * 80)
    
    print(f"""
    BEST STRATEGIES TO CLOSE LOAN IN 7 YEARS:
    
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ OPTION A: HIGHER FIXED EMI (Simplest)                                       │
    │ • Set EMI at {format_inr(emi_7year):<12} from Day 1                                  │
    │ • No need to track prepayments                                              │
    │ • Total Interest: {format_inr(result_7year['total_interest']):<12}                                        │
    │ • Interest Saved: {format_inr(result_original['total_interest'] - result_7year['total_interest']):<12}                                        │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ OPTION B: ORIGINAL EMI + MONTHLY PREPAYMENT (Flexible)                      │
    │ • EMI: {format_inr(original_emi):<12}                                                │
    │ • Monthly Prepayment: {format_inr(monthly_prepay_needed):<12}                                  │
    │ • Total Monthly: {format_inr(total_monthly_outflow):<12}                                       │
    │ • More flexibility - can skip prepayment in tight months                    │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ OPTION C: ORIGINAL EMI + YEARLY LUMP SUM (If you get annual bonus)          │
    │ • EMI: {format_inr(original_emi):<12}                                                │
    │ • Yearly Prepayment: {format_inr(yearly_prepay_needed):<12}                                   │
    │ • Good if you receive annual bonus/incentives                               │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ OPTION D: HYBRID (Balanced Approach) ⭐ RECOMMENDED                          │
    │ • EMI: {format_inr(hybrid_emi):<12} (+15%)                                           │
    │ • Monthly Prepayment: {format_inr(hybrid_monthly_prepay):<12}                                  │
    │ • Total Monthly: {format_inr(hybrid_emi + hybrid_monthly_prepay):<12}                                       │
    │ • Balance between commitment and flexibility                                │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    💡 KEY INSIGHTS:
    
    1. INTEREST SAVINGS: Closing in 7 years instead of 10 saves you approximately
       {format_inr(result_original['total_interest'] - result_7year['total_interest'])} in interest!
    
    2. PHASED DISBURSEMENT ADVANTAGE: Since ₹1 Cr is disbursed only in Year 3,
       you pay less interest in Years 1-2 (interest only on ₹1.5 Cr).
    
    3. PREPAYMENT TIMING: Making prepayments in the first 3-4 years has the 
       maximum impact on interest savings.
    
    4. TAX BENEFIT: Remember you can claim up to ₹2 Lakh deduction on home loan 
       interest under Section 24(b) and ₹1.5 Lakh on principal under Section 80C.
    """)
    
    return {
        'original_emi': original_emi,
        'emi_7year': emi_7year,
        'monthly_prepay_needed': monthly_prepay_needed,
        'yearly_prepay_needed': yearly_prepay_needed,
        'interest_saved': result_original['total_interest'] - result_7year['total_interest']
    }

# Main execution
if __name__ == "__main__":
    # Loan parameters
    LAND_LOAN = 15000000      # ₹1.5 Crore
    CONSTRUCTION_LOAN = 10000000  # ₹1 Crore
    ANNUAL_RATE = 7.54        # 7.54% P.A.
    TARGET_MONTHS = 84        # 7 years
    
    results = find_optimal_strategy(LAND_LOAN, CONSTRUCTION_LOAN, ANNUAL_RATE, TARGET_MONTHS)
