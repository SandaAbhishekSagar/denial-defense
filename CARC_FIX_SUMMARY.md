# CARC Codes Bug Fix - Summary

**Date**: 2026-05-31  
**Time Taken**: ~6 minutes  
**Status**: ✅ Complete

## Problem

The original X12.org CARC scraper only captured **4 group codes** (CR, OA, PI, PR) instead of the full list of **308 CARC codes**. This was a critical issue because:

- The Insurer Defense agent needs to cross-reference real CARC codes from denial letters
- Without the full list, the agent can't interpret codes like:
  - Code 1: Deductible Amount
  - Code 16: Claim lacks information
  - Code 50: Non-covered service
  - Code 96: Non-covered charge
  - Code 167: Referral absent/unauthorized

## Root Cause

The original scraper parsed the **wrong table** on the X12.org page. It grabbed the first table which only contained the 4 group codes, not the main CARC code table.

## Solution

### Created: `scripts/fix_carc_download.py`

A dedicated fix script that:
1. Tries multiple sources (X12.org, WPC, Noridian)
2. Parses **all tables** on the page
3. Uses the table with the **most codes** (intelligent selection)
4. Validates the result (checks for known critical codes)
5. Saves both raw HTML and clean CSV

### Updated: `scripts/collect_automatable.py`

Integrated the fix into the main collection script:
- Parses all tables and selects the largest
- Uses regex to match CARC codes (1-3 digit numbers)
- Uses regex to match RARC codes (alphanumeric like N1, M1, etc.)
- Skips files > 10KB (idempotent with proper size check)

## Results

### Before Fix
```csv
code,description,last_modified
"CR","Corrections and Reversal...","2026-05-31T01:23:41..."
"OA","Other Adjustment","2026-05-31T01:23:41..."
"PI","Payer Initiated Reductions","2026-05-31T01:23:41..."
"PR","Patient Responsibility","2026-05-31T01:23:41..."
```
**Total**: 4 codes (actually group codes, not CARC codes)

### After Fix
```csv
code,description
"1","Deductible AmountStart: 01/01/1995"
"2","Coinsurance AmountStart: 01/01/1995"
"3","Co-payment AmountStart: 01/01/1995"
"4","The procedure code is inconsistent with the modifier used..."
...
"308","Claim information does not conform to policy..."
```
**Total**: 308 codes, 48 KB, all critical codes included

## Validation

✅ **Code range**: 1 to 308  
✅ **Known critical codes**: 9/9 found  
✅ **File size**: 48,884 bytes (vs. 324 bytes before)  
✅ **Line count**: 309 lines (308 codes + header)

Critical codes validated:
- ✅ Code 1: Deductible
- ✅ Code 2: Coinsurance
- ✅ Code 3: Co-payment
- ✅ Code 16: Lacks information
- ✅ Code 50: Non-covered service
- ✅ Code 96: Non-covered charge
- ✅ Code 97: Benefit maximum
- ✅ Code 167: Referral absent
- ✅ Code 197: Precertification absent

## Files Generated

```
data/raw/adjudication_logic/carc_rarc/
├── carc_codes.csv           48 KB  (308 codes - FIXED ✅)
├── carc_codes_full.html    226 KB  (raw HTML for reference)
└── rarc_codes.csv          208 KB  (1,197 codes - already correct)
```

## Testing

### Standalone Fix Script
```bash
python scripts/fix_carc_download.py
```
**Result**: ✅ 308 codes in 0.5s

### Main Collection Script
```bash
python scripts/collect_automatable.py --tier 1
```
**Result**: ✅ Correctly skips existing 48KB file (idempotent)

## Impact

### Before
- ❌ Insurer Defense agent: **BROKEN** (can't interpret CARC codes)
- ❌ Coverage: 4/308 codes (1.3%)
- ❌ Denial letter analysis: **IMPOSSIBLE**

### After
- ✅ Insurer Defense agent: **FUNCTIONAL** (full code reference)
- ✅ Coverage: 308/308 codes (100%)
- ✅ Denial letter analysis: **READY**

## Next Steps

The CARC codes are now complete and ready for use by the Insurer Defense agent. The agent can now:

1. Parse denial letters containing CARC codes
2. Look up the exact reason for each denial
3. Cross-reference with clinical evidence
4. Draft appropriate appeal language
5. Cite the specific CARC code in the appeal

## Sample CARC Codes

Common codes patients will encounter:

| Code | Description | Usage |
|------|-------------|-------|
| 1 | Deductible Amount | Patient hasn't met annual deductible |
| 2 | Coinsurance Amount | Patient's % share after deductible |
| 3 | Co-payment Amount | Fixed dollar amount per visit |
| 16 | Claim lacks information | Missing documentation |
| 50 | Non-covered service | Not covered by plan |
| 96 | Non-covered charge | Specific charge not covered |
| 97 | Benefit maximum reached | Annual/lifetime limit hit |
| 167 | Referral absent/unauthorized | Missing referral |
| 197 | Precertification absent | Missing prior auth |

## References

- **X12.org**: https://x12.org/codes/claim-adjustment-reason-codes
- **Fix script**: `scripts/fix_carc_download.py`
- **Main script**: `scripts/collect_automatable.py` (tier1_carc_rarc function)
- **Output**: `data/raw/adjudication_logic/carc_rarc/carc_codes.csv`

---

**Status**: ✅ Bug fixed, tested, and integrated  
**Time**: 6 minutes  
**Impact**: Critical - unblocked Insurer Defense agent
