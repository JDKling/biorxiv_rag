from lxml import etree
from config import KEEP_CATEGORIES

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

def chunk_article(article, check_categories=True):
    """
    Chunk an article into sections for RAG.
    
    Args:
        article: lxml element representing the article
        check_categories: If True, only process articles in KEEP_CATEGORIES
    
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
    
    return {
        "chunks": chunks,
        "metadata": {
            "title": title,
            "doi": doi,
            "subjects": subjects,
            "total_chunks": len(chunks)
        }
    }

