#!/usr/bin/env python3
"""
Simple bioRxiv RAG Database Builder

This script takes a directory of XML files and builds a complete RAG database
with semantic embeddings. Just point it at your XML directory and run!

Usage:
    python build_rag_database.py /path/to/xml/files
    python build_rag_database.py /path/to/xml/files --recursive
    python build_rag_database.py /path/to/xml/files --max-files 50
    python build_rag_database.py /path/to/xml/files --output ./my_database
"""

import os
import sys
import argparse
import glob
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.vector_database import BioRxivVectorDB
from src.search_interface import BioRxivSearchInterface
from src.rag_system import BioRxivRAG

def find_xml_files(directory: str, recursive: bool = False) -> list:
    """
    Find all XML files in a directory.
    
    Args:
        directory: Path to directory containing XML files
        recursive: Whether to search subdirectories
        
    Returns:
        List of XML file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if recursive:
        xml_files = list(directory.rglob("*.xml"))
    else:
        xml_files = list(directory.glob("*.xml"))
    
    return [str(f) for f in xml_files]

def build_database(xml_directory: str, 
                  output_db: str = "./biorxiv_rag_db",
                  max_files: int = None,
                  recursive: bool = False,
                  batch_size: int = 25) -> BioRxivVectorDB:
    """
    Build a complete RAG database from XML files.
    
    Args:
        xml_directory: Directory containing XML files
        output_db: Output database directory
        max_files: Maximum number of files to process (None for all)
        recursive: Search subdirectories for XML files
        batch_size: Number of files to process in each batch
        
    Returns:
        Populated BioRxivVectorDB instance
    """
    
    print("🚀 bioRxiv RAG Database Builder")
    print("=" * 60)
    
    # Find XML files
    print(f"📂 Scanning directory: {xml_directory}")
    xml_files = find_xml_files(xml_directory, recursive)
    
    if not xml_files:
        print("❌ No XML files found!")
        return None
    
    print(f"📄 Found {len(xml_files)} XML files")
    
    # Limit files if specified
    if max_files and max_files < len(xml_files):
        xml_files = xml_files[:max_files]
        print(f"📊 Processing first {max_files} files")
    
    # Initialize database
    print(f"🗄️  Initializing database: {output_db}")
    db = BioRxivVectorDB(output_db)
    
    # Process files in batches
    total_processed = 0
    total_chunks = 0
    
    print(f"\n📦 Processing {len(xml_files)} files in batches of {batch_size}...")
    
    for i in range(0, len(xml_files), batch_size):
        batch_files = xml_files[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(xml_files) - 1) // batch_size + 1
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch_files)} files)")
        print("-" * 40)
        
        batch_chunks = 0
        for xml_file in batch_files:
            try:
                added = db.add_xml_file(xml_file, check_categories=True)
                if added > 0:
                    batch_chunks += added
                    total_processed += 1
                    print(f"✅ {os.path.basename(xml_file)}: {added} chunks")
                else:
                    print(f"⏭️  {os.path.basename(xml_file)}: filtered out")
            except Exception as e:
                print(f"❌ {os.path.basename(xml_file)}: {e}")
        
        total_chunks += batch_chunks
        print(f"📊 Batch {batch_num} complete: {batch_chunks} chunks added")
    
    # Final summary
    print(f"\n🎉 Database Build Complete!")
    print("=" * 60)
    print(f"📁 XML files found: {len(xml_files)}")
    print(f"✅ Articles processed: {total_processed}")
    print(f"📊 Total chunks: {total_chunks}")
    print(f"🗄️  Database location: {output_db}")
    
    # Show database stats
    stats = db.get_stats()
    print(f"\n📈 Database Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Unique subjects: {len(stats['unique_subjects'])}")
    print(f"   Available subjects: {', '.join(stats['unique_subjects'][:5])}...")
    
    return db

def test_database(db: BioRxivVectorDB):
    """Test the built database with sample queries."""
    print(f"\n🧪 Testing Database...")
    print("-" * 40)
    
    # Initialize search interface
    search = BioRxivSearchInterface(db.db_path)
    
    # Test queries
    test_queries = [
        "CRISPR gene editing",
        "protein structure",
        "bacterial resistance",
        "machine learning"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        results = search.search(query, n_results=2, show_content=False)
        if results:
            print(f"   ✅ Found {len(results)} results")
            for i, result in enumerate(results[:1], 1):
                print(f"   {i}. {result['metadata']['title'][:50]}...")
        else:
            print(f"   ❌ No results found")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a bioRxiv RAG database from XML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_rag_database.py ./subset_xml
  python build_rag_database.py ./xml --recursive --max-files 100
  python build_rag_database.py ./data --output ./my_rag_db --batch-size 10
        """
    )
    
    parser.add_argument(
        "xml_directory",
        help="Directory containing XML files"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./biorxiv_rag_db",
        help="Output database directory (default: ./biorxiv_rag_db)"
    )
    
    parser.add_argument(
        "--max-files", "-m",
        type=int,
        default=None,
        help="Maximum number of files to process (default: all)"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Search subdirectories for XML files"
    )
    
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=25,
        help="Number of files to process per batch (default: 25)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the database after building"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive Q&A after building"
    )
    
    args = parser.parse_args()
    
    try:
        # Build database
        db = build_database(
            xml_directory=args.xml_directory,
            output_db=args.output,
            max_files=args.max_files,
            recursive=args.recursive,
            batch_size=args.batch_size
        )
        
        if db is None:
            sys.exit(1)
        
        # Test database if requested
        if args.test:
            test_database(db)
        
        # Start interactive mode if requested
        if args.interactive:
            print(f"\n🤖 Starting Interactive Q&A...")
            rag = BioRxivRAG(db.db_path)
            rag.interactive_qa()
        
        print(f"\n✨ Ready to use! Try:")
        print(f"   python -c \"from src.rag_system import BioRxivRAG; rag = BioRxivRAG('{args.output}'); rag.interactive_qa()\"")
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
