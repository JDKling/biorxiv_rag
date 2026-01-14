# Best Practices for Retrieving Open Access Papers from NCBI/PMC

## Overview
This guide provides best practices for retrieving and processing **open-access scientific papers** from PubMed Central (PMC) via the National Center for Biotechnology Information (NCBI). It focuses on **legally reusable** content and methods for filtering before download to save storage and processing time.

The approach is designed for researchers building machine learning pipelines, literature review tools, or structured knowledge bases.

---

## Why Use PMC Open Access Data?
- **Legally reusable**: All articles in the Open Access Subset are licensed under terms (e.g., CC BY, CC0) that permit text and data mining.
- **Well-structured**: Articles are available in JATS XML format, suitable for automated parsing.
- **Comprehensive**: Covers a wide range of biomedical literature, including microbiology.

---

## Sources of Open Access Content
1. **PMC Open Access Subset** via FTP
   - Bulk archives containing full-text XML and PDFs.
2. **Europe PMC API**
   - Allows targeted search and filtering before download.
3. **PMC Metadata Files**
   - `file_list.csv` includes PMCID, DOI, journal title, and file paths for all OA articles.

---

## Best Practices

### 1. Work Only With Licensed Open Access Material
- Always verify licenses before use.
- Filter for open-access subsets to avoid legal issues.

### 2. Filter Before Download
- Use **Europe PMC API** for keyword, species, or journal-specific searches.
- Use **PMC metadata CSV** for offline filtering by journal, title keywords, or license type.

### 3. Optimize Storage and Bandwidth
- Download only relevant XML files instead of full bulk archives when possible.
- Store large corpora on a fast external SSD to avoid filling local disk space.

### 4. Keep Data Structured
- Organize files into logical folders (e.g., by journal or topic).
- Maintain a metadata table with PMCID, title, journal, license, and download path.

### 5. Preserve Source Metadata
- Keep PMCID or DOI associated with every file for traceability.
- Store license type and retrieval date in your records.

### 6. Automate but Validate
- Automate retrieval and parsing steps to handle large datasets.
- Periodically validate downloads to ensure completeness and avoid corrupted files.

---

## Recommended Pipeline Steps

1. **Identify Scope**
   - Define whether you need all biomedical papers, microbiology-specific articles, or papers on particular species.
   - Compile a keyword list or journal list to target.

2. **Fetch Metadata**
   - Download PMC’s `file_list.csv` OR query the Europe PMC API to retrieve article metadata.
   - Include PMCID, DOI, journal name, license type, and file path in your dataset.

3. **Filter Records**
   - Apply filters to select only:
     - Open Access licensed content
     - Relevant journals or keywords
     - Articles with full-text available in XML

4. **Download Full Text**
   - For bulk: download `.tar.gz` archives from the PMC FTP server containing relevant files.
   - For targeted retrieval: download only filtered XMLs via direct URLs.

5. **Extract and Store**
   - Unpack archives or parse API responses to retrieve XML files.
   - Store articles in a consistent folder structure (e.g., `/data/journal_name/pmcid.xml`).

6. **Parse XML**
   - Extract relevant sections such as title, abstract, and body text from JATS XML.
   - Remove boilerplate text (e.g., references, figure captions) if not needed.

7. **Index and Use**
   - Store cleaned text and metadata in a database (e.g., SQLite, PostgreSQL, or a document store).
   - Use this indexed data for machine learning, search, or knowledge extraction tasks.

---

## Notes and Considerations
- **Licensing**: Even within the OA subset, some licenses have attribution or share-alike requirements.
- **Performance**: XML parsing is CPU-intensive; parallelize where possible.
- **Reproducibility**: Keep a record of queries, filters, and metadata files used.
- **Updates**: PMC is updated daily; refresh your dataset periodically if ongoing work depends on it.

---

---

## Nextflow Pipeline Usage

This directory includes a complete Nextflow pipeline to automate the retrieval of open access papers from NCBI/PMC.

### Quick Start

1. **List available journals** (to see what's available):
   ```bash
   ./run_pipeline.sh --list-journals-only
   ```

2. **Get metadata for specific journals**:
   ```bash
   ./run_pipeline.sh --journals-file example_journals.txt
   ```

3. **Download full-text articles** (limited sample for testing):
   ```bash
   ./run_pipeline.sh --journals "Nature,Science" --download-fulltext --max-articles 10
   ```

### Pipeline Files

- `ncbi_scraper.nf` - Main Nextflow pipeline
- `nextflow.config` - Configuration file
- `fetch_pmc_metadata.py` - Downloads PMC metadata
- `filter_by_journals.py` - Filters metadata by journal list
- `download_articles.py` - Downloads full-text articles
- `run_pipeline.sh` - Convenience script to run pipeline
- `example_journals.txt` - Example journal list

### Pipeline Parameters

- `--journals "J1,J2,J3"` - Comma-separated journal names
- `--journal_file FILE` - File containing journal names (one per line)
- `--output_dir DIR` - Output directory (default: results)
- `--download_fulltext` - Download full-text articles (default: metadata only)
- `--max_articles N` - Limit to N articles (for testing)
- `--list_journals_only` - Only list available journals

### Output Structure

```
results/
├── metadata/
│   ├── pmc_oa_file_list.csv      # All PMC metadata
│   └── journal_counts.csv        # Available journals (if --list-journals-only)
├── filtered/
│   ├── filtered_pmc_metadata.csv # Filtered by target journals
│   └── filter_stats.txt          # Filtering statistics
├── articles/                     # Downloaded full-text (if enabled)
│   ├── Nature/
│   ├── Science/
│   └── ...
└── reports/                      # Nextflow execution reports
    ├── timeline.html
    ├── report.html
    └── trace.txt
```

### Requirements

- Nextflow (>= 21.04.0)
- Python 3 with packages: requests, pandas
- Internet connection for downloading

### Docker Usage

Build and run with Docker:
```bash
docker build -t ncbi-scraper .
docker run -v $(pwd)/results:/app/results ncbi-scraper \
    nextflow run ncbi_scraper.nf --journals "Nature,Science"
```

---

## References
- [NCBI PMC Open Access Subset](https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/)
- [Europe PMC REST API](https://europepmc.org/RestfulWebService)
- [PMC FTP Server](https://ftp.ncbi.nlm.nih.gov/pub/pmc/)
- [Nextflow Documentation](https://www.nextflow.io/docs/latest/)
