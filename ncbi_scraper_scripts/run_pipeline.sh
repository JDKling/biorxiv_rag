#!/bin/bash

# Example script to run the NCBI/PMC scraper pipeline

# Set script to exit on any error
set -e

echo "NCBI/PMC Open Access Scraper Pipeline"
echo "====================================="

# Check if Nextflow is installed
if ! command -v nextflow &> /dev/null; then
    echo "Error: Nextflow is not installed or not in PATH"
    echo "Please install Nextflow: https://www.nextflow.io/docs/latest/getstarted.html"
    exit 1
fi

# Default parameters
JOURNALS_FILE="example_journals.txt"
OUTPUT_DIR="results"
DOWNLOAD_FULLTEXT=false
MAX_ARTICLES=""
LIST_JOURNALS_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --journals-file)
            JOURNALS_FILE="$2"
            shift 2
            ;;
        --journals)
            JOURNALS_LIST="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --download-fulltext)
            DOWNLOAD_FULLTEXT=true
            shift
            ;;
        --max-articles)
            MAX_ARTICLES="--max_articles $2"
            shift 2
            ;;
        --list-journals-only)
            LIST_JOURNALS_ONLY=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --journals-file FILE     File containing journal names (default: example_journals.txt)"
            echo "  --journals \"J1,J2,J3\"    Comma-separated list of journal names"
            echo "  --output-dir DIR         Output directory (default: results)"
            echo "  --download-fulltext      Download full-text articles (default: metadata only)"
            echo "  --max-articles N         Limit to N articles (for testing)"
            echo "  --list-journals-only     Only list available journals and exit"
            echo "  --help                   Show this help message"
            echo ""
            echo "Examples:"
            echo "  # List available journals"
            echo "  $0 --list-journals-only"
            echo ""
            echo "  # Get metadata for specific journals"
            echo "  $0 --journals-file my_journals.txt"
            echo ""
            echo "  # Download full-text for Nature and Science (limited to 100 articles)"
            echo "  $0 --journals \"Nature,Science\" --download-fulltext --max-articles 100"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build Nextflow command
NF_CMD="nextflow run ncbi_scraper.nf"
NF_CMD="$NF_CMD --output_dir $OUTPUT_DIR"

if [ "$LIST_JOURNALS_ONLY" = true ]; then
    NF_CMD="$NF_CMD --list_journals_only true"
elif [ -n "$JOURNALS_LIST" ]; then
    NF_CMD="$NF_CMD --journals '$JOURNALS_LIST'"
elif [ -f "$JOURNALS_FILE" ]; then
    NF_CMD="$NF_CMD --journal_file $JOURNALS_FILE"
else
    echo "Error: Must specify either --journals-file or --journals"
    echo "Use --help for usage information"
    exit 1
fi

if [ "$DOWNLOAD_FULLTEXT" = true ]; then
    NF_CMD="$NF_CMD --download_fulltext true"
fi

if [ -n "$MAX_ARTICLES" ]; then
    NF_CMD="$NF_CMD $MAX_ARTICLES"
fi

# Show command and confirm
echo "Running command:"
echo "$NF_CMD"
echo ""

if [ "$LIST_JOURNALS_ONLY" = false ]; then
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run the pipeline
echo "Starting pipeline..."
eval $NF_CMD

echo ""
echo "Pipeline completed!"
echo "Results available in: $OUTPUT_DIR"

if [ "$LIST_JOURNALS_ONLY" = true ]; then
    echo "Available journals listed in: $OUTPUT_DIR/metadata/journal_counts.csv"
else
    echo "Filtered metadata available in: $OUTPUT_DIR/filtered/"
    if [ "$DOWNLOAD_FULLTEXT" = true ]; then
        echo "Downloaded articles available in: $OUTPUT_DIR/articles/"
    fi
fi
