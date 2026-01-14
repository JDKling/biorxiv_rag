from lxml import etree
from .config import KEEP_CATEGORIES
from .embeddings import add_embeddings_to_chunks, get_embedder
from typing import Optional

def _extract_text(element, xpath):
    elements = element.xpath(xpath)
    if elements:
        # Use etree.tostring to get all text content including nested elements
        text = etree.tostring(elements[0], method='text', encoding='unicode').strip()
        return text
    return ""

def _extract_elements(element, xpath):
    return element.xpath(xpath)

def _extract_all_text(element, xpath):
    elements = element.xpath(xpath)
    texts = []
    for el in elements:
        text = etree.tostring(el, method='text', encoding='unicode').strip()
        if text:
            texts.append(text)
    return "\n\n".join(texts)

def should_keep_article(article):
    """
    Check if article should be kept based on subject categories.
    Returns True if any subject matches KEEP_CATEGORIES, False otherwise.
    """
    # Extract all subject elements
    subjects = _extract_elements(article, ".//subj-group/subject")
    
    # Get text content from each subject
    article_subjects = []
    for subject in subjects:
        subject_text = etree.tostring(subject, method='text', encoding='unicode').strip()
        if subject_text:
            article_subjects.append(subject_text)
    
    # Check if any subject is in our keep categories
    for subject in article_subjects:
        if subject in KEEP_CATEGORIES:
            return True, article_subjects
    
    return False, article_subjects

def chunk_article(article, check_categories=True, include_embeddings=False):
    """
    Chunk an article into sections for RAG.
    
    Args:
        article: lxml element representing the article
        check_categories: If True, only process articles in KEEP_CATEGORIES
        include_embeddings: If True, generate SciBERT embeddings for each chunk
    
    Returns:
        dict with 'chunks' and 'metadata', or None if article should be filtered out
    """
    # Check if we should keep this article based on categories
    if check_categories:
        should_keep, subjects = should_keep_article(article)
        if not should_keep:
            return None
    else:
        _, subjects = should_keep_article(article)
    
    chunks = []
    
    # Extract metadata
    title = _extract_text(article, ".//article-title")
    doi = _extract_text(article, ".//article-id[@pub-id-type='doi']")
    
    # Title + Abstract as one chunk
    abstract = _extract_all_text(article, ".//abstract//p")
    chunks.append({
        "content": f"{title}\n\n{abstract}", 
        "type": "abstract",
        "metadata": {
            "title": title,
            "doi": doi,
            "subjects": subjects
        }
    })

    # Each main section as separate chunks
    for section in _extract_elements(article, ".//body//sec[@id]"):
        section_title = _extract_text(section, ".//title")
        section_content = _extract_all_text(section, ".//p")  # Use _extract_all_text to get all paragraphs
        chunks.append({
            "content": f"{section_title}\n\n{section_content}", 
            "type": "section",
            "section_id": section.get("id"),
            "metadata": {
                "title": title,
                "doi": doi,
                "subjects": subjects,
                "section_title": section_title
            }
        })
    
    # Add embeddings if requested
    if include_embeddings:
        embedder = get_embedder()
        chunks = add_embeddings_to_chunks(chunks, embedder)
    
    return {
        "chunks": chunks,
        "metadata": {
            "title": title,
            "doi": doi,
            "subjects": subjects,
            "total_chunks": len(chunks),
            "has_embeddings": include_embeddings
        }
    }

def process_xml_directory_with_embeddings(xml_dir, include_embeddings=True, check_categories=True):
    """
    Process all XML files in a directory and generate embeddings.
    
    Args:
        xml_dir: Directory containing XML files
        include_embeddings: Whether to generate embeddings
        check_categories: Whether to filter by categories
        
    Returns:
        List of all chunks with embeddings and metadata
    """
    import os
    
    all_chunks = []
    processed_count = 0
    filtered_count = 0
    error_count = 0
    
    print(f"Processing XML files in: {xml_dir}")
    print(f"Include embeddings: {include_embeddings}")
    print(f"Filter categories: {check_categories}")
    print("=" * 60)
    
    for filename in os.listdir(xml_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(xml_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = etree.parse(f)
                    root = tree.getroot()
                
                result = chunk_article(root, 
                                     check_categories=check_categories, 
                                     include_embeddings=include_embeddings)
                
                if result:
                    all_chunks.extend(result['chunks'])
                    processed_count += 1
                    print(f"✅ Processed: {result['metadata']['title'][:60]}...")
                    print(f"   Chunks: {result['metadata']['total_chunks']}, "
                          f"Embeddings: {result['metadata']['has_embeddings']}")
                else:
                    filtered_count += 1
                    print(f"⏭️  Filtered: {filename}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing {filename}: {e}")
    
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Successfully processed: {processed_count} articles")
    print(f"Filtered out: {filtered_count} articles")
    print(f"Errors: {error_count} articles")
    print(f"Total chunks generated: {len(all_chunks)}")
    
    if include_embeddings and all_chunks:
        embedding_dim = all_chunks[0].get('embedding_dimension', 'Unknown')
        print(f"Embedding dimension: {embedding_dim}")
        print(f"Embedding model: {all_chunks[0].get('embedding_model', 'Unknown')}")
    
    return all_chunks

