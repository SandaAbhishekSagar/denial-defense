# Raw Data Directory

This directory contains raw, unprocessed data collected from various public sources for the Denial Defense project.

## Directory Structure

### `imr/`
California Department of Managed Health Care (DMHC) Independent Medical Review (IMR) determinations dataset.
- Source: https://data.chhs.ca.gov/dataset/independent-medical-review-imr-determinations-trend
- License: Public domain
- Format: CSV
- Records: 42,750 cases

### `sample_appeals/`
Sample appeal letters published by state insurance departments for consumer education.
- Sources: Washington, North Carolina, New York, Texas, Massachusetts insurance departments
- License: Public domain (government works)
- Format: DOC/DOCX

### `denial_letters/`
Denial letters from various sources (anonymized if containing PHI).
- `propublica/`: From ProPublica investigative reporting
- `reddit/`: Manually collected from Reddit (r/HealthInsurance, r/Insurance) with user permission

### `insurer_policies/`
Publicly published medical policies from major insurers.
- Format: PDF
- Covers 10 key procedures frequently subject to denials
- Sources: Anthem, Aetna, Cigna, UHC, Oscar, BCBS FEP

### `propublica_articles/`
Articles from ProPublica's "Uncovered" series on health insurance denials.
- Source: https://www.propublica.org/series/uncovered-the-power-of-health-insurance
- License: Creative Commons BY-NC-ND 3.0
- Format: Markdown with frontmatter

### `kff_bill_of_month/`
Stories from KFF Health News "Bill of the Month" series.
- Source: https://kffhealthnews.org/news/series/bill-of-the-month/
- License: Creative Commons BY-NC-ND 4.0
- Format: Markdown with structured frontmatter

### `state_appeal_resources/`
Consumer appeal guides and sample letters by state.
- License: Public domain (government works)
- Format: Mixed (PDF, DOC, HTML)

## Data Collection Principles

1. **Public sources only**: We only collect data that is published publicly for consumer information
2. **Robots.txt compliance**: All scraping respects robots.txt
3. **Rate limiting**: 1 request per 2 seconds per domain
4. **Anonymization**: Any PHI encountered is flagged and excluded
5. **Attribution**: All sources are documented with URLs and timestamps
6. **License compliance**: We respect all license terms (Creative Commons, public domain, etc.)

## License

The Denial Defense project is open source under the MIT License. Individual data sources may have their own licenses (documented above). All data is used for non-commercial research purposes only.
