# bioRxiv RAG System

A complete Retrieval-Augmented Generation (RAG) system for bioRxiv scientific literature with SciBERT embeddings and semantic search.

## 🚀 Quick Start

**One command to build your entire RAG database:**

```bash
# Activate environment
cd /home/ubuntu/biorxiv_rag

# Build database from XML files
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml

# Build with options
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --max-files 50 --test --interactive
```

## 📁 Structure

```
biorxiv_rag/
├── build_rag_database.py    # 🎯 MAIN SCRIPT - Run this!
├── src/                     # All core modules
│   ├── build_rag.py         # XML processing & chunking
│   ├── embeddings.py        # SciBERT embedding generation
│   ├── vector_database.py   # ChromaDB integration
│   ├── search_interface.py  # Search functionality
│   ├── rag_system.py       # Complete RAG pipeline
│   └── config.py           # Configuration
├── subset_xml/             # Sample XML files (500)
├── xml/                    # Full XML collection
└── USAGE_GUIDE.md         # Detailed documentation
```

## 🎯 What It Does

1. **Finds XML files** in your directory (recursive search supported)
2. **Parses bioRxiv articles** and filters by scientific categories
3. **Generates SciBERT embeddings** for semantic understanding
4. **Stores in ChromaDB** vector database with rich metadata
5. **Provides search & Q&A** interfaces for scientific literature

## 📊 Features

- **SciBERT Embeddings**: 768D vectors optimized for scientific text
- **Semantic Search**: Find relevant content by meaning, not just keywords
- **Category Filtering**: Focus on specific scientific domains
- **Interactive Q&A**: Ask questions about the literature
- **Batch Processing**: Handle large collections efficiently
- **Persistent Storage**: Database survives restarts

## 🔧 Options

```bash
# See all options
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py --help

# Common usage patterns
python build_rag_database.py ./subset_xml                    # Basic usage
python build_rag_database.py ./xml --recursive               # Search subdirectories  
python build_rag_database.py ./subset_xml --max-files 50     # Limit files
python build_rag_database.py ./subset_xml --test             # Build and test
python build_rag_database.py ./subset_xml --interactive      # Build and start Q&A
python build_rag_database.py ./subset_xml --output ./my_db   # Custom output location
```

## 🧪 Example Queries

After building your database, try asking:

- "How does CRISPR work in gene editing?"
- "What are bacterial resistance mechanisms?"
- "Applications of hydrogels in bioengineering"
- "Protein structure prediction methods"

## 📚 Documentation

See `USAGE_GUIDE.md` for complete documentation, troubleshooting, and advanced usage.

## 🎉 That's It!

Your bioRxiv RAG system is now **incredibly simple**: just point the script at XML files and get a complete semantic search database with Q&A capabilities!

**Happy researching! 🧬🤖**