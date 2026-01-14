#!/usr/bin/env python3
"""
Script to download full-text XML articles from PMC based on filtered metadata.
Downloads articles respectfully with rate limiting.
"""

import pandas as pd
import requests
import os
import sys
import time
import argparse
from pathlib import Path
from urllib.parse import urljoin
import re

class PMCDownloader:
    def __init__(self, output_dir="articles", delay=1.0, max_retries=3):
        """
        Initialize PMC downloader
        
        Args:
            output_dir: Directory to save articles
            delay: Delay between downloads (seconds)
            max_retries: Maximum retry attempts for failed downloads
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NCBI-Scraper/1.0 (Research; mailto:your-email@domain.com)'
        })
        
    def get_article_url(self, file_path, pmcid=None):
        """
        Construct download URL for PMC article
        
        Args:
            file_path: File path from PMC metadata (e.g., 'oa_package/xx/xx/PMC123456.tar.gz')
            pmcid: PMC ID (e.g., 'PMC123456')
        
        Returns:
            Direct URL to XML file or tar.gz package
        """
        base_url = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/"
        
        if file_path:
            # Use the file path from metadata
            return urljoin(base_url, file_path)
        elif pmcid:
            # Construct path based on PMC ID
            # PMC articles are organized in subdirectories based on ID
            pmc_num = pmcid.replace('PMC', '')
            # Create nested directory structure (e.g., PMC123456 -> 12/34/PMC123456)
            if len(pmc_num) >= 4:
                subdir1 = pmc_num[-2:]
                subdir2 = pmc_num[-4:-2]
                return f"{base_url}oa_package/{subdir2}/{subdir1}/{pmcid}.tar.gz"
        
        return None
    
    def sanitize_filename(self, filename):
        """
        Sanitize filename for safe filesystem storage
        """
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip()
        return filename[:255]  # Limit length
    
    def download_article(self, pmcid, file_path, journal=None, title=None):
        """
        Download a single article
        
        Args:
            pmcid: PMC ID
            file_path: File path from metadata
            journal: Journal name (for organization)
            title: Article title
            
        Returns:
            (success, output_path, error_message)
        """
        url = self.get_article_url(file_path, pmcid)
        if not url:
            return False, None, "Could not construct download URL"
        
        # Create subdirectory by journal if provided
        if journal:
            journal_dir = self.output_dir / self.sanitize_filename(journal)
            journal_dir.mkdir(exist_ok=True)
            output_dir = journal_dir
        else:
            output_dir = self.output_dir
        
        # Determine output filename
        if file_path and file_path.endswith('.tar.gz'):
            filename = f"{pmcid}.tar.gz"
        else:
            filename = f"{pmcid}.xml"
        
        output_path = output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            return True, str(output_path), "Already exists"
        
        # Download with retries
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Write file
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return True, str(output_path), None
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    return False, None, str(e)
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False, None, "Max retries exceeded"
    
    def download_from_metadata(self, metadata_file, log_file=None):
        """
        Download articles based on filtered metadata file
        
        Args:
            metadata_file: Path to CSV file with PMC metadata
            log_file: Path to log file (optional)
        """
        # Load metadata
        try:
            df = pd.read_csv(metadata_file)
            print(f"Loaded metadata for {len(df)} articles")
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return
        
        # Identify columns
        pmcid_col = None
        filepath_col = None
        journal_col = None
        title_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'pmcid' in col_lower or 'pmc' in col_lower or 'accession id' in col_lower:
                pmcid_col = col
            elif 'file' in col_lower and ('path' in col_lower or col == 'File'):
                filepath_col = col
            elif 'journal' in col_lower:
                journal_col = col
            elif 'title' in col_lower:
                title_col = col
        
        if not pmcid_col:
            print("Error: Could not find PMC ID column in metadata")
            return
        
        print(f"Using columns - PMC ID: {pmcid_col}, File Path: {filepath_col}")
        print(f"Journal: {journal_col}, Title: {title_col}")
        
        # Download articles
        success_count = 0
        error_count = 0
        skip_count = 0
        
        log_entries = []
        
        for idx, row in df.iterrows():
            pmcid = row[pmcid_col]
            file_path = row[filepath_col] if filepath_col else None
            journal = row[journal_col] if journal_col else None
            title = row[title_col] if title_col else None
            
            print(f"Downloading {idx+1}/{len(df)}: {pmcid}")
            
            success, output_path, error = self.download_article(
                pmcid, file_path, journal, title
            )
            
            if success:
                if error == "Already exists":
                    skip_count += 1
                    print(f"  Skipped (already exists): {output_path}")
                else:
                    success_count += 1
                    print(f"  Downloaded: {output_path}")
            else:
                error_count += 1
                print(f"  Error: {error}")
            
            # Log entry
            log_entries.append({
                'pmcid': pmcid,
                'success': success,
                'output_path': output_path,
                'error': error,
                'journal': journal
            })
            
            # Rate limiting
            if idx < len(df) - 1:  # Don't delay after last download
                time.sleep(self.delay)
        
        # Summary
        print(f"\nDownload Summary:")
        print(f"  Successful: {success_count}")
        print(f"  Skipped (existing): {skip_count}")
        print(f"  Errors: {error_count}")
        print(f"  Total: {len(df)}")
        
        # Write log file
        if log_file:
            log_df = pd.DataFrame(log_entries)
            log_df.to_csv(log_file.replace('.txt', '.csv'), index=False)
            
            with open(log_file, 'a') as f:
                f.write(f"\nDownload Summary:\n")
                f.write(f"  Successful: {success_count}\n")
                f.write(f"  Skipped (existing): {skip_count}\n")
                f.write(f"  Errors: {error_count}\n")
                f.write(f"  Total: {len(df)}\n")

def main():
    parser = argparse.ArgumentParser(description='Download PMC articles from metadata')
    parser.add_argument('--metadata', required=True, help='Path to filtered metadata CSV')
    parser.add_argument('--output', default='articles', help='Output directory for articles')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between downloads (seconds)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    parser.add_argument('--log', help='Log file path')
    
    args = parser.parse_args()
    
    downloader = PMCDownloader(
        output_dir=args.output,
        delay=args.delay,
        max_retries=args.max_retries
    )
    
    downloader.download_from_metadata(args.metadata, args.log)

if __name__ == "__main__":
    main()
