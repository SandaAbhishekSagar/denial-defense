# Denial Defense

An open-source healthcare AI research project that helps patients draft insurance appeal letters using a multi-agent system.

> **Note**: The CA DMHC IMR dataset (81MB CSV) is not included in this repository due to GitHub file size limits. 
> Download it from: https://data.chhs.ca.gov/dataset/independent-medical-review-imr-determinations-trend
> Place it in: `data/raw/imr/independent-medical-review-imr-determinations-trend.csv`

## Overview

Denial Defense is a non-commercial research project (MIT License) that aims to empower patients facing health insurance denials by providing AI-assisted appeal letter drafting. The system analyzes denial letters, medical policies, and successful appeal examples to help craft effective appeals.

## Project Structure

```
denial-defense/
├── data/                           # All datasets (raw and processed)
│   ├── raw/                       # Raw, unprocessed data
│   │   ├── imr/                  # CA DMHC IMR dataset (42,750 cases)
│   │   ├── sample_appeals/       # State-published appeal letter examples
│   │   ├── denial_letters/       # Denial letter examples
│   │   ├── insurer_policies/     # Medical policies by insurer
│   │   ├── propublica_articles/  # ProPublica reporting
│   │   ├── kff_bill_of_month/    # KFF Health News stories
│   │   └── state_appeal_resources/ # State-specific appeal guides
│   ├── processed/                 # Cleaned and structured data
│   └── demo/                      # Demo cases for testing
│       ├── case_01_bariatric/
│       ├── case_02_cromolyn/
│       └── case_03_oon_emergency/
├── scripts/                        # Data collection and processing scripts
│   ├── collect_supplemental_data.py
│   ├── collect.ps1
│   └── collect.sh
├── agents/                         # Multi-agent system components
├── web/                           # Web interface
│   └── templates/
├── eval/                          # Evaluation scripts and results
├── prompts/                       # LLM prompts and templates
├── logs/                          # Collection and processing logs
├── requirements.txt               # Python dependencies
├── DATA_COLLECTION.md             # Data collection documentation
└── README.md                      # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Data Directories

```bash
python scripts/collect_supplemental_data.py --setup-only
```

This creates the complete directory hierarchy without running any scrapers.

### 3. Collect Supplemental Data

#### Option A: Run all phases

```bash
python scripts/collect_supplemental_data.py --all
```

#### Option B: Use shell scripts

**PowerShell (Windows):**
```powershell
.\scripts\collect.ps1
```

**Bash (Linux/Mac):**
```bash
bash scripts/collect.sh
```

#### Option C: Run individual phases

```bash
# State appeal resources (fastest, most reliable)
python scripts/collect_supplemental_data.py --skip-setup --only state_resources

# ProPublica articles
python scripts/collect_supplemental_data.py --skip-setup --only propublica

# KFF Bill of the Month
python scripts/collect_supplemental_data.py --skip-setup --only kff

# Insurer policies (may require manual steps)
python scripts/collect_supplemental_data.py --skip-setup --only insurer_policies
```

See [DATA_COLLECTION.md](DATA_COLLECTION.md) for comprehensive documentation on data collection.

## Data Sources

### Primary Dataset

**California DMHC Independent Medical Review (IMR) Determinations**
- 42,750 cases of independent medical review decisions
- Covers denials across all major insurers and medical categories
- Source: https://data.chhs.ca.gov/dataset/independent-medical-review-imr-determinations-trend
- License: Public domain

### Supplemental Data

1. **Sample Appeal Letters** - State insurance departments (WA, NC, NY, TX, MA)
2. **Insurer Medical Policies** - Publicly published policies from major insurers
3. **ProPublica "Uncovered" Series** - Investigative journalism on insurance denials
4. **KFF Bill of the Month** - Consumer stories about medical bills and denials
5. **State Appeal Resources** - Consumer guides and templates

All data sources are publicly available, and collection respects robots.txt, rate limits, and data privacy.

## Data Collection Principles

1. **Public sources only** - We only collect publicly published content
2. **Robots.txt compliance** - All scraping respects robots.txt directives
3. **Rate limiting** - 1 request per 2 seconds per domain minimum
4. **Privacy protection** - PHI screening to exclude protected health information
5. **Attribution** - All sources documented with URLs and timestamps
6. **License compliance** - We respect Creative Commons and other license terms

## Project Goals

### Phase 1: Data Collection ✅
- [x] Set up project hierarchy
- [x] Collect CA DMHC IMR dataset
- [x] Collect state appeal letter samples
- [x] Implement supplemental data scrapers
- [ ] Reach collection targets (30+ policies, 15+ articles, 20+ stories)

### Phase 2: Data Processing
- [ ] Clean and structure IMR dataset
- [ ] Extract denial patterns and themes
- [ ] Categorize by procedure, insurer, and outcome
- [ ] Build searchable index

### Phase 3: Multi-Agent System
- [ ] Appeal analyzer agent
- [ ] Policy researcher agent
- [ ] Letter drafter agent
- [ ] Evidence compiler agent
- [ ] Coordinator agent

### Phase 4: Evaluation
- [ ] Test on demo cases
- [ ] Evaluate appeal quality
- [ ] Measure success factors

### Phase 5: Web Interface
- [ ] Upload denial letter
- [ ] Select insurer and procedure
- [ ] Generate appeal draft
- [ ] Export to Word/PDF

## Technology Stack

- **Language**: Python 3.8+
- **Web Scraping**: requests, BeautifulSoup, Playwright
- **Data Processing**: pandas, numpy
- **NLP/AI**: (TBD - likely OpenAI/Anthropic API)
- **Web Framework**: (TBD - likely Flask or FastAPI)

## Contributing

This is an open-source research project. Contributions are welcome!

Areas where help is needed:
- Manual collection of insurer medical policies
- Data cleaning and structuring
- Multi-agent system architecture
- Evaluation framework
- Web interface development

## Legal and Ethical Considerations

### Privacy
- No PHI (Protected Health Information) is collected or stored
- All data comes from public sources or is anonymized
- Users must remove identifying information before uploading denial letters

### Disclaimer
- This tool provides informational assistance only
- Not a substitute for legal or medical advice
- Users should review and customize all generated content
- Success not guaranteed - appeals are evaluated on individual merit

### License
MIT License - See LICENSE file for details

Individual data sources may have their own licenses:
- ProPublica: CC BY-NC-ND 3.0
- KFF Health News: CC BY-NC-ND 4.0
- Government sources: Public domain
- Insurer policies: Publicly published (fair use for research)

## Contact

**Project Lead**: Abhishek Sagar
- Email: sabhisheksagar200@gmail.com

This is a hackathon/research project. For questions about data collection, contributions, or collaboration, please reach out.

## Acknowledgments

- **California Department of Managed Health Care** - For publishing the IMR dataset
- **ProPublica** - For investigative reporting on insurance denials
- **KFF Health News** - For consumer stories highlighting insurance issues
- **State Insurance Departments** - For publishing consumer appeal resources
- **Open source community** - For tools and frameworks that make this possible

---

**Note**: This project is in active development. Data collection is functional, but the multi-agent system and web interface are still in planning/development.
