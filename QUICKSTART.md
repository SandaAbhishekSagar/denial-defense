# Quick Reference - Denial Defense Data Collection

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (optional, for JS-heavy sites)
playwright install
```

## Common Commands

### Setup Only
```bash
# Create directory structure without scraping
python scripts/collect_supplemental_data.py --setup-only
```

### Run Everything
```bash
# Setup + all scrapers + validation
python scripts/collect_supplemental_data.py --all
```

### Individual Scrapers
```bash
# State appeal resources (recommended first - fast and reliable)
python scripts/collect_supplemental_data.py --skip-setup --only state_resources

# ProPublica articles
python scripts/collect_supplemental_data.py --skip-setup --only propublica

# KFF Bill of the Month stories
python scripts/collect_supplemental_data.py --skip-setup --only kff

# Insurer medical policies (may need manual steps)
python scripts/collect_supplemental_data.py --skip-setup --only insurer_policies
```

### Shell Scripts

**PowerShell (Windows):**
```powershell
# Run everything with venv management
.\scripts\collect.ps1
```

**Bash (Linux/Mac):**
```bash
# Run everything with venv management
bash scripts/collect.sh
```

## Check Results

### View logs
```bash
# Full log
cat logs/collection.log

# Last 50 lines
tail -n 50 logs/collection.log

# Summary report
cat logs/collection_summary.md
```

### Count files
```bash
# Count by category (PowerShell)
Get-ChildItem -Path "data\raw" -Recurse -File | Group-Object Directory | Select-Object Name, Count

# Count by category (Bash)
find data/raw -type f | grep -v '.gitkeep' | wc -l
```

### Verify downloads
```bash
# Check Washington state files (PowerShell)
Get-ChildItem -Path "data\raw\state_appeal_resources\washington" -File

# Check Washington state files (Bash)
ls -lh data/raw/state_appeal_resources/washington/
```

## Troubleshooting

### Unicode errors on Windows
```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/collect_supplemental_data.py --all
```

### Rate limiting (429 errors)
Edit `scripts/collect_supplemental_data.py`:
```python
RATE_LIMIT_SECONDS = 3.0  # Increase from 2.0 to 3.0
```

### Missing dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Playwright not installed
```bash
pip install playwright
playwright install chromium
```

## File Structure Reference

```
data/raw/
├── imr/                           # 4 files - CA DMHC IMR dataset
├── sample_appeals/                # 3 files - Sample letters from states
├── denial_letters/
│   ├── propublica/               # Denial letters from reporting
│   └── reddit/                   # Manually collected
├── insurer_policies/             # Medical policies by insurer
│   ├── anthem/
│   ├── aetna/
│   ├── cigna/
│   ├── uhc/
│   ├── oscar/
│   └── bcbs_fep/
├── propublica_articles/          # "Uncovered" series articles
├── kff_bill_of_month/            # "Bill of the Month" stories
└── state_appeal_resources/       # Appeal guides by state
    ├── washington/
    ├── north_carolina/
    ├── new_york/
    ├── texas/
    └── massachusetts/
```

## Target Goals

- [ ] 30+ insurer policy PDFs
- [ ] 15+ ProPublica articles
- [ ] 20+ KFF Bill of the Month stories
- [x] No PHI detected
- [x] Clean directory structure

## Quick Validation

```bash
# Run validation without scraping
python scripts/collect_supplemental_data.py --skip-setup

# Check summary
cat logs/collection_summary.md
```

## Notes

- Script is idempotent - safe to run multiple times
- Existing files are never overwritten
- Rate limiting: 1 request per 2 seconds per domain
- Respects robots.txt automatically
- All operations logged to `logs/collection.log`

## Getting Help

```bash
# Show all options
python scripts/collect_supplemental_data.py --help

# Check documentation
cat DATA_COLLECTION.md
cat README.md
```
