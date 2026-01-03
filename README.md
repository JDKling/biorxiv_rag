# bioRxiv RAG System

A Retrieval-Augmented Generation (RAG) system for processing bioRxiv academic articles in XML format. This system filters articles by scientific categories and chunks them into semantically meaningful sections for use with Large Language Models.

## Features

- **Topic Filtering**: Only processes articles in specified scientific categories
- **Intelligent Chunking**: Breaks articles into semantic sections (abstract, introduction, methods, etc.)
- **Metadata Extraction**: Preserves article titles, DOIs, authors, and subject categories
- **Clean Text Processing**: Extracts clean text from XML while preserving structure
- **Configurable Categories**: Easy-to-modify category filtering via config file

## Project Structure

```
├── build_rag.py          # Main RAG functionality
├── config.py             # Configuration (topic categories)
├── tests/                # Test directory
│   ├── __init__.py       # Python package marker
│   ├── run_tests.py      # Test runner script
│   ├── test_chunking.py  # Chunking functionality tests
│   └── test_filtering.py # Filtering functionality tests
├── rag-env/              # Virtual environment
├── xml/                  # bioRxiv XML files directory
└── README.md             # This file
```

## Setup Instructions

### 1. Creating the Environment

The system uses `uv` for Python environment management. Follow these steps:

```bash
# Navigate to project directory
cd /home/ubuntu

# Create virtual environment
uv venv rag-env

# Activate the environment
source rag-env/bin/activate

# Install required dependencies
uv pip install lxml
```

**Alternative with pip (if uv is not available):**
```bash
python3 -m venv rag-env
source rag-env/bin/activate
pip install lxml
```

### 2. Running the Test Script

To verify everything is working correctly, run the test suite:

```bash
# Activate environment (if not already active)
source rag-env/bin/activate

# Run all tests
python tests/run_tests.py

# Or run individual tests
python tests/test_chunking.py
python tests/test_filtering.py
```

**Expected output:**
- ✅ All tests should pass
- The system should process the sample XML file
- Filtering should work based on the "Bioinformatics" category

### 3. Running the Actual Script

#### Basic Usage

```python
from lxml import etree
from build_rag import chunk_article

# Load and parse XML file
with open('xml/April_2019/0a1e58f5-6c09-1014-838d-8b9451ae9aba.xml', 'r') as f:
    tree = etree.parse(f)
    root = tree.getroot()

# Process article with filtering
result = chunk_article(root, check_categories=True)

if result:
    print(f"Title: {result['metadata']['title']}")
    print(f"Chunks: {result['metadata']['total_chunks']}")
    print(f"Subjects: {result['metadata']['subjects']}")
else:
    print("Article filtered out (not in target categories)")
```

#### Batch Processing Example

```python
import os
from lxml import etree
from build_rag import chunk_article

def process_xml_directory(xml_dir):
    """Process all XML files in a directory."""
    all_chunks = []
    processed_count = 0
    filtered_count = 0
    
    for filename in os.listdir(xml_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(xml_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = etree.parse(f)
                    root = tree.getroot()
                
                result = chunk_article(root, check_categories=True)
                
                if result:
                    all_chunks.extend(result['chunks'])
                    processed_count += 1
                    print(f"✅ Processed: {result['metadata']['title']}")
                else:
                    filtered_count += 1
                    print(f"⏭️  Filtered: {filename}")
                    
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
    
    print(f"\nSummary:")
    print(f"Processed: {processed_count} articles")
    print(f"Filtered: {filtered_count} articles")
    print(f"Total chunks: {len(all_chunks)}")
    
    return all_chunks

# Usage
chunks = process_xml_directory('xml/April_2019/')
```

## Configuration

### Modifying Topic Categories

Edit `config.py` to change which scientific categories to include:

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

### Function Parameters

- `chunk_article(article, check_categories=True)`:
  - `article`: lxml element representing the parsed XML
  - `check_categories`: If `True`, filters articles by categories; if `False`, processes all articles

## Output Format

Each processed article returns a dictionary with:

```python
{
    "chunks": [
        {
            "content": "Article title\n\nAbstract text...",
            "type": "abstract",
            "metadata": {
                "title": "Article Title",
                "doi": "10.1101/123456",
                "subjects": ["Bioinformatics", "Genomics"]
            }
        },
        {
            "content": "Section title\n\nSection content...",
            "type": "section",
            "section_id": "s1",
            "metadata": {
                "title": "Article Title",
                "doi": "10.1101/123456",
                "subjects": ["Bioinformatics", "Genomics"],
                "section_title": "Introduction"
            }
        }
    ],
    "metadata": {
        "title": "Article Title",
        "doi": "10.1101/123456",
        "subjects": ["Bioinformatics", "Genomics"],
        "total_chunks": 25
    }
}
```

## Dependencies

- **lxml**: XML parsing and processing
- **Python 3.7+**: Core language support

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure the virtual environment is activated
   ```bash
   source rag-env/bin/activate
   ```

2. **XML Parsing Error**: Ensure XML files are valid JATS format
   
3. **No Articles Processed**: Check if article subjects match categories in `config.py`

4. **Path Issues**: Run scripts from the project root directory

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed: `uv pip list`
2. Verify XML file format matches expected JATS structure
3. Run tests to ensure basic functionality: `python tests/run_tests.py`

## Next Steps

This RAG system provides the foundation for:
- Vector embedding generation
- Integration with vector databases (Chroma, Pinecone, etc.)
- Query interfaces for retrieval
- Integration with LLMs for question answering

## License

This project is designed for academic and research purposes.
