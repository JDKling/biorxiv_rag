# bioRxiv RAG System - Simplified Usage Guide

## 🎉 System Overview

Your bioRxiv RAG (Retrieval-Augmented Generation) system is now **fully functional** and **super simple to use**! Just point it at a directory of XML files and it builds everything automatically.

## 🚀 **Quick Start (One Command!)**

### **Basic Usage**
```bash
cd /home/ubuntu/biorxiv_rag

# Build database from subset_xml directory
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml

# Build from any XML directory
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py /path/to/xml/files

# Search recursively in subdirectories
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./xml --recursive

# Process only first 50 files
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --max-files 50

# Custom output location
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --output ./my_database

# Build and test automatically
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --test

# Build and start interactive Q&A
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --interactive
```

### **All Options**
```bash
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py --help
```

## 📁 **New File Structure**

```
biorxiv_rag/
├── build_rag_database.py    # 🎯 MAIN SCRIPT - Run this!
├── src/                     # All core modules
│   ├── __init__.py
│   ├── build_rag.py         # XML processing & chunking
│   ├── embeddings.py        # SciBERT embedding generation
│   ├── vector_database.py   # ChromaDB integration
│   ├── search_interface.py  # Search functionality
│   ├── rag_system.py       # Complete RAG pipeline
│   └── config.py           # Configuration (categories)
├── biorxiv_rag_db/         # Default database location
├── subset_xml/             # Sample XML files (500)
├── xml/                    # Full XML collection
└── requirements.txt        # Dependencies
```

## ✅ **What the Main Script Does**

The `build_rag_database.py` script automatically:

1. **🔍 Finds XML files** in your directory (with optional recursive search)
2. **📄 Parses bioRxiv articles** and filters by scientific categories

3. **🧠 Generates SciBERT embeddings** for semantic understanding
4. **🗄️ Stores everything** in a ChromaDB vector database
5. **🧪 Tests the database** (optional) with sample queries
6. **🤖 Starts Q&A interface** (optional) for immediate use

## 🎯 **Common Use Cases**

### **1. Quick Test (10 files)**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --max-files 10 --test
```

### **2. Build Full Database (All subset_xml files)**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml
```

### **3. Process Large Collection (All xml files)**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./xml --recursive --max-files 100
```

### **4. Build and Use Immediately**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --interactive
```

## 🔍 **Using the Built Database**

After building, you can use your database in several ways:

### **Interactive Q&A**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python -c "
from src.rag_system import BioRxivRAG
rag = BioRxivRAG('./biorxiv_rag_db')
rag.interactive_qa()
"
```

### **Interactive Search**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python -c "
from src.search_interface import BioRxivSearchInterface
search = BioRxivSearchInterface('./biorxiv_rag_db')
search.interactive_search()
"
```

### **Programmatic Usage**
```python
from src.rag_system import BioRxivRAG
from src.search_interface import BioRxivSearchInterface

# Initialize RAG system
rag = BioRxivRAG('./biorxiv_rag_db')

# Ask questions
result = rag.answer_question("How does CRISPR work?")
print(result['answer'])

# Search for specific topics
search = BioRxivSearchInterface('./biorxiv_rag_db')
results = search.search("protein folding", n_results=5)
```

## 📊 **Expected Performance**

### **Processing Speed**
- **10 files**: ~2-3 minutes
- **50 files**: ~10-15 minutes  
- **500 files**: ~1-2 hours

### **Success Rates**
- **Input**: XML files in bioRxiv JATS format
- **Filtered**: Only articles matching scientific categories in `src/config.py`
- **Typical Success**: 10-30% of files match categories
- **Output**: 10-50 chunks per successful article

### **Database Size**
- **100 chunks**: ~50MB
- **1,000 chunks**: ~200MB
- **10,000 chunks**: ~1GB

## 🛠️ **Configuration**

### **Modify Categories**
Edit `src/config.py` to change which scientific categories to include:

```python
KEEP_CATEGORIES = {
    "Biochemistry",
    "Bioengineering", 
    "Bioinformatics",
    "Biophysics",
    "Ecology",
    "Evolutionary biology",
    "Genetics",
    "Genomics",
    "Microbiology",
    "Molecular biology",
    "Plant biology",
    "Synthetic biology"
}
```

### **Environment Setup**
Always use the conda environment:
```bash
# Check environment
/home/ubuntu/miniconda3/envs/biorxiv/bin/python --version

# Should show: Python 3.11.14
```

## 🧪 **Testing & Validation**

### **Quick Test**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --max-files 5 --test --interactive
```

### **Check Database Stats**
```bash
cd /home/ubuntu/biorxiv_rag
/home/ubuntu/miniconda3/envs/biorxiv/bin/python -c "
from src.vector_database import BioRxivVectorDB
db = BioRxivVectorDB('./biorxiv_rag_db')
stats = db.get_stats()
print(f'Total chunks: {stats[\"total_chunks\"]}')
print(f'Subjects: {stats[\"unique_subjects\"]}')
"
```

## 🔍 **Example Queries**

Try these questions with your built database:

- **Gene Editing**: "How does CRISPR-Cas9 work for gene knockout?"
- **Protein Science**: "What determines protein folding and structure?"
- **Microbiology**: "What are bacterial resistance mechanisms?"
- **Bioengineering**: "Applications of hydrogels in tissue engineering"
- **Bioinformatics**: "Computational methods for protein analysis"

## 🚨 **Troubleshooting**

### **No XML Files Found**
```bash
# Check directory exists and has XML files
ls -la /path/to/xml/directory/*.xml
```

### **No Articles Match Categories**
- Check `src/config.py` categories
- Try processing more files with `--max-files 100`
- Use `--recursive` to search subdirectories

### **Memory Issues**
```bash
# Process in smaller batches
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py ./subset_xml --batch-size 10
```

### **Environment Issues**
```bash
# Always use full Python path
/home/ubuntu/miniconda3/envs/biorxiv/bin/python build_rag_database.py
```

## 🎉 **That's It!**

Your bioRxiv RAG system is now **incredibly simple to use**:

1. **Point the script at XML files**: `python build_rag_database.py /path/to/xml`
2. **Wait for processing**: Automatic embedding generation and database creation
3. **Start asking questions**: Interactive Q&A with scientific literature

The system handles all the complexity behind the scenes - XML parsing, embedding generation, vector storage, and semantic search - while giving you a simple command-line interface.

## 🔗 **Next Steps**

- **LLM Integration**: Add OpenAI/Claude API keys for better answers
- **Web Interface**: Build Streamlit dashboard
- **API**: Create REST API for integration
- **Specialized Models**: Fine-tune on your specific domain

**Happy researching! 🧬🤖**