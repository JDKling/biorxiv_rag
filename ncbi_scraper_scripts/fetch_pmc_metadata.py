#!/usr/bin/env python3
"""
Script to download PMC Open Access metadata file (file_list.csv)
This contains metadata for all open access papers in PMC.
"""

import requests
import os
import sys
import gzip
from pathlib import Path

def download_pmc_metadata(output_dir="data"):
    """
    Download the PMC file_list.csv containing metadata for all OA papers
    """
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # PMC file list URL - contains metadata for all open access papers
    url = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_file_list.csv"
    
    output_file = os.path.join(output_dir, "pmc_oa_file_list.csv")
    
    print(f"Downloading PMC Open Access metadata from: {url}")
    print(f"Output file: {output_file}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Write to file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded PMC metadata to {output_file}")
        
        # Check file size
        file_size = os.path.getsize(output_file)
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        return output_file
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

def get_file_info(filepath):
    """
    Get basic information about the downloaded metadata file
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    print(f"\nAnalyzing file: {filepath}")
    
    # Count lines (excluding header)
    with open(filepath, 'r') as f:
        line_count = sum(1 for line in f) - 1  # Subtract header
    
    print(f"Total open access articles: {line_count:,}")
    
    # Show first few lines
    print("\nFirst few lines:")
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if i < 5:  # Show header + 4 data lines
                print(f"  {line.strip()}")

if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    
    metadata_file = download_pmc_metadata(output_dir)
    get_file_info(metadata_file)
