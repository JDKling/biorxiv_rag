#!/usr/bin/env python3
"""
Script to filter PMC metadata by a list of target journals.
Outputs filtered metadata and statistics.
"""

import pandas as pd
import sys
import argparse
from pathlib import Path

def load_journal_list(journal_file):
    """
    Load journal names from a file (one per line) or from command line arguments
    """
    if journal_file and Path(journal_file).exists() and Path(journal_file).stat().st_size > 0:
        with open(journal_file, 'r') as f:
            journals = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(journals)} journals from {journal_file}")
        return journals
    return []

def filter_metadata_by_journals(metadata_file, target_journals, output_file=None, case_sensitive=False):
    """
    Filter PMC metadata by target journals
    
    Args:
        metadata_file: Path to PMC metadata CSV file
        target_journals: List of journal names to filter by
        output_file: Output file path (optional)
        case_sensitive: Whether to use case-sensitive matching
    """
    
    print(f"Loading metadata from: {metadata_file}")
    
    # Read the metadata file
    try:
        df = pd.read_csv(metadata_file)
        print(f"Total articles in metadata: {len(df):,}")
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        sys.exit(1)
    
    # Show column names
    print(f"Columns available: {list(df.columns)}")
    
    # Check if 'Journal Title' column exists (common name in PMC metadata)
    journal_col = None
    possible_journal_cols = ['Journal Title', 'journal', 'Journal', 'journal_title']
    
    for col in possible_journal_cols:
        if col in df.columns:
            journal_col = col
            break
    
    # If no dedicated journal column, extract from Article Citation
    if not journal_col and 'Article Citation' in df.columns:
        print("No dedicated journal column found. Extracting journal from Article Citation...")
        # Extract journal name from citation (format: "Journal Name. YYYY MMM DD; Volume(Issue):Pages")
        df['Journal'] = df['Article Citation'].str.extract(r'^([^.]+)\.', expand=False)
        journal_col = 'Journal'
        print(f"Extracted {df['Journal'].notna().sum()} journal names from citations")
    
    if not journal_col:
        print("Warning: Could not find or extract journal information. Available columns:")
        for col in df.columns:
            print(f"  - {col}")
        print("Please check the metadata file format.")
        sys.exit(1)
    
    print(f"Using journal column: '{journal_col}'")
    
    # Convert to lowercase for case-insensitive matching if needed
    if not case_sensitive:
        df[journal_col + '_lower'] = df[journal_col].str.lower()
        target_journals_lower = [j.lower() for j in target_journals]
        filter_col = journal_col + '_lower'
        filter_values = target_journals_lower
    else:
        filter_col = journal_col
        filter_values = target_journals
    
    # Filter by journals
    filtered_df = df[df[filter_col].isin(filter_values)]
    
    print(f"\nFiltering results:")
    print(f"Articles matching target journals: {len(filtered_df):,}")
    print(f"Percentage of total: {len(filtered_df)/len(df)*100:.2f}%")
    
    # Show journal breakdown
    if len(filtered_df) > 0:
        print(f"\nJournal breakdown:")
        journal_counts = filtered_df[journal_col].value_counts()
        for journal, count in journal_counts.head(20).items():
            print(f"  {journal}: {count:,} articles")
        
        if len(journal_counts) > 20:
            print(f"  ... and {len(journal_counts) - 20} more journals")
    
    # Save filtered results
    if output_file:
        # Remove the temporary lowercase column if created
        if not case_sensitive and journal_col + '_lower' in filtered_df.columns:
            filtered_df = filtered_df.drop(columns=[journal_col + '_lower'])
        
        filtered_df.to_csv(output_file, index=False)
        print(f"\nFiltered metadata saved to: {output_file}")
    
    return filtered_df

def get_unique_journals(metadata_file, output_file=None, top_n=100):
    """
    Extract unique journal names from metadata file for reference
    """
    print(f"Extracting unique journals from: {metadata_file}")
    
    try:
        df = pd.read_csv(metadata_file)
        
        # Find journal column
        journal_col = None
        possible_journal_cols = ['Journal Title', 'journal', 'Journal', 'journal_title']
        
        for col in possible_journal_cols:
            if col in df.columns:
                journal_col = col
                break
        
        # If no dedicated journal column, extract from Article Citation
        if not journal_col and 'Article Citation' in df.columns:
            print("No dedicated journal column found. Extracting journal from Article Citation...")
            # Extract journal name from citation
            df['Journal'] = df['Article Citation'].str.extract(r'^([^.]+)\.', expand=False)
            journal_col = 'Journal'
        
        if not journal_col:
            print("Could not find or extract journal column")
            return
        
        # Get journal counts
        journal_counts = df[journal_col].value_counts()
        
        print(f"Total unique journals: {len(journal_counts)}")
        print(f"\nTop {top_n} journals by article count:")
        
        for i, (journal, count) in enumerate(journal_counts.head(top_n).items(), 1):
            print(f"{i:3d}. {journal}: {count:,} articles")
        
        if output_file:
            journal_counts.to_csv(output_file, header=['count'])
            print(f"\nAll journal counts saved to: {output_file}")
            
    except Exception as e:
        print(f"Error processing file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Filter PMC metadata by journals')
    parser.add_argument('metadata_file', help='Path to PMC metadata CSV file')
    parser.add_argument('--journals', nargs='+', help='List of journal names to filter by')
    parser.add_argument('--journal-file', help='File containing journal names (one per line)')
    parser.add_argument('--output', help='Output file for filtered metadata')
    parser.add_argument('--case-sensitive', action='store_true', help='Use case-sensitive matching')
    parser.add_argument('--list-journals', action='store_true', help='List unique journals in metadata')
    parser.add_argument('--top-journals', type=int, default=100, help='Number of top journals to show (default: 100)')
    
    args = parser.parse_args()
    
    if args.list_journals:
        output_file = args.output or "journal_counts.csv"
        get_unique_journals(args.metadata_file, output_file, args.top_journals)
        return
    
    # Get target journals
    target_journals = []
    
    if args.journal_file:
        target_journals.extend(load_journal_list(args.journal_file))
    
    if args.journals:
        target_journals.extend(args.journals)
    
    if not target_journals:
        print("Error: No target journals specified. Use --journals or --journal-file")
        sys.exit(1)
    
    print(f"Target journals: {target_journals}")
    
    # Filter metadata
    output_file = args.output or "filtered_pmc_metadata.csv"
    filter_metadata_by_journals(
        args.metadata_file, 
        target_journals, 
        output_file, 
        args.case_sensitive
    )

if __name__ == "__main__":
    main()
