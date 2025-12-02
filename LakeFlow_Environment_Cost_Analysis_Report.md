# LakeFlow System Tables Dashboard - Environment Cost Analysis Report

**Report Date:** December 2, 2025  
**Analysis Period:** June 2025 - November 2025 (6 months)  
**Dashboard:** LakeFlow System Tables Dashboard  

---

## Executive Summary

This report provides a comprehensive analysis and comparison of Databricks usage costs across three environments in the East US region:

| Environment | Workspace | Color | Total Cost (6 months) | Avg Monthly Cost |
|-------------|-----------|-------|----------------------|------------------|
| **Development** | photon-idp-dev-eus-db | 🔵 Blue | ~$302 | ~$60 |
| **QA** | photon-idp-qa-eus-db | 🟡 Yellow | ~$32.99K | ~$5.5K |
| **Production** | photon-idp-prod-eus-db | 🟢 Green | ~$54.66K | ~$9.1K |

**Key Finding:** Production costs are approximately **181x higher** than Dev and **1.7x higher** than QA.

---

## Detailed Monthly Breakdown

### Development Environment (photon-idp-dev-eus-db) 🔵

| Month | Cost (USD) | MoM Change |
|-------|------------|------------|
| Jun 2025 | $61.52 | - |
| Jul 2025 | $79.96 | +30.0% |
| Aug 2025 | $78.61 | -1.7% |
| Sep 2025 | $61.46 | -21.8% |
| Oct 2025 | $20.72 | -66.3% |

**Observations:**
- Very low cost environment (under $100/month)
- Peak usage in July 2025 at $79.96
- Significant drop in October (66% reduction) - possible reduced development activity
- Total 6-month cost: **~$302.27**
- Average monthly cost: **~$60.45**

---

### QA Environment (photon-idp-qa-eus-db) 🟡

| Month | Cost (USD) | MoM Change |
|-------|------------|------------|
| Jun 2025 | $5,780 | - |
| Jul 2025 | $8,770 | +51.7% |
| Aug 2025 | $9,820 | +12.0% |
| Sep 2025 | $5,510 | -43.9% |
| Oct 2025 | $1,090 | -80.2% |
| Nov 2025 | $1,020 | -6.4% |

**Observations:**
- Moderate cost environment ($1K-$10K/month range)
- Peak usage in August 2025 at $9.82K
- Dramatic cost reduction from August to November (89.6% decrease)
- Suggests major testing phase completed after August
- Total 6-month cost: **~$32,990**
- Average monthly cost: **~$5,498**

---

### Production Environment (photon-idp-prod-eus-db) 🟢

| Month | Cost (USD) | MoM Change |
|-------|------------|------------|
| Jun 2025 | $9,640 | - |
| Jul 2025 | $13,090 | +35.8% |
| Aug 2025 | $13,250 | +1.2% |
| Sep 2025 | $11,410 | -13.9% |
| Oct 2025 | $4,290 | -62.4% |
| Nov 2025 | $2,980 | -30.5% |

**Observations:**
- Highest cost environment ($3K-$13K/month range)
- Peak usage in August 2025 at $13.25K
- Consistent decline from September onwards
- October and November show significant reduction (~77% from peak)
- Total 6-month cost: **~$54,660**
- Average monthly cost: **~$9,110**

---

## Comparative Analysis

### Cost Distribution by Environment

```
Production:  ████████████████████████████████████████  62.2% ($54.66K)
QA:          ██████████████████████████               37.6% ($32.99K)
Dev:         █                                         0.3% ($0.30K)
             ─────────────────────────────────────────
             Total: ~$87.95K over 6 months
```

### Monthly Trend Comparison

```
Month     │ Dev      │ QA       │ Prod     │ Total
──────────┼──────────┼──────────┼──────────┼──────────
Jun 2025  │ $62      │ $5,780   │ $9,640   │ $15,482
Jul 2025  │ $80      │ $8,770   │ $13,090  │ $21,940
Aug 2025  │ $79      │ $9,820   │ $13,250  │ $23,149
Sep 2025  │ $61      │ $5,510   │ $11,410  │ $16,981
Oct 2025  │ $21      │ $1,090   │ $4,290   │ $5,401
Nov 2025  │ N/A      │ $1,020   │ $2,980   │ $4,000
```

### Cost Ratios

| Comparison | Ratio |
|------------|-------|
| Prod : Dev | 181:1 |
| QA : Dev | 109:1 |
| Prod : QA | 1.66:1 |

---

## Key Insights & Trends

### 1. 📈 Summer Peak (July-August 2025)
All three environments show peak usage during July-August 2025:
- **Dev:** $79.96 (Jul peak)
- **QA:** $9.82K (Aug peak)
- **Prod:** $13.25K (Aug peak)

This suggests a major release or feature deployment cycle during this period.

### 2. 📉 Significant Q4 Decline
All environments show dramatic cost reductions in October-November:
- **Dev:** -66% in October
- **QA:** -80% in October, additional -6% in November
- **Prod:** -62% in October, additional -31% in November

**Possible reasons:**
- Project milestone completion
- Reduced workload/fewer data pipelines
- Cost optimization initiatives
- Seasonal business slowdown

### 3. 💰 Environment Cost Hierarchy
The expected hierarchy is maintained:
```
Production > QA > Development
```
This aligns with best practices where production handles the most workload.

### 4. ⚠️ Anomaly Detection
- **Dev environment October drop** is notably steep (-66%), suggesting either:
  - Intentional scale-down
  - Reduced development activity
  - Possible infrastructure changes

---

## Recommendations

### 1. Cost Optimization Opportunities

| Priority | Recommendation | Potential Savings |
|----------|---------------|-------------------|
| High | Review QA cluster sizing - costs are 66% of Production | ~$10K/6 months |
| Medium | Implement auto-shutdown for Dev clusters during off-hours | ~$50/month |
| Low | Analyze if recent Q4 cost reduction is sustainable | - |

### 2. Capacity Planning
- Production shows capacity for ~$13K/month at peak
- Plan for potential scale-up if business needs increase
- Consider Reserved Capacity for predictable production workloads

### 3. Monitoring Recommendations
- Set up cost alerts at 80% of monthly budget thresholds
- Implement tagging strategy for better cost attribution
- Review cluster utilization metrics in Operational Observability tab

---

## Cost Projection (Next 3 Months)

Based on recent trends (Oct-Nov average):

| Environment | Projected Monthly Cost | Q1 2026 Estimate |
|-------------|----------------------|------------------|
| Dev | ~$20 | ~$60 |
| QA | ~$1,000 | ~$3,000 |
| Production | ~$3,000 | ~$9,000 |
| **Total** | **~$4,020** | **~$12,060** |

*Note: Projections assume current usage patterns continue. Actual costs may vary based on business activity.*

---

## Summary Statistics

| Metric | Dev | QA | Prod |
|--------|-----|-----|------|
| **Total Cost** | $302 | $32,990 | $54,660 |
| **Average Monthly** | $60 | $5,498 | $9,110 |
| **Peak Month** | Jul ($80) | Aug ($9.82K) | Aug ($13.25K) |
| **Lowest Month** | Oct ($21) | Nov ($1.02K) | Nov ($2.98K) |
| **Volatility** | High (74%) | Very High (89%) | High (77%) |
| **Trend** | Declining | Declining | Declining |

---

## Appendix: Data Source

- **Dashboard:** LakeFlow System Tables Dashboard
- **Date Range:** 6 months ago to Today (June 2025 - November 2025)
- **View:** Monthly aggregation by Workspace
- **Cluster Type:** All Cluster Types
- **Run as:** All Users

---

*Report generated on December 2, 2025*
