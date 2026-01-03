#!/usr/bin/env python3

from lxml import etree
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_rag import chunk_article, should_keep_article
from config import KEEP_CATEGORIES

def test_filtering():
    # Load the XML file
    xml_file = "/home/ubuntu/xml/April_2019/0a1e58f5-6c09-1014-838d-8b9451ae9aba.xml"
    
    try:
        # Parse the XML
        with open(xml_file, 'r', encoding='utf-8') as f:
            tree = etree.parse(f)
        root = tree.getroot()
        
        print("✅ XML file loaded successfully")
        print(f"Root element: {root.tag}")
        
        # Test the filtering function
        print("\n🔍 Testing article filtering...")
        should_keep, subjects = should_keep_article(root)
        
        print(f"Article subjects: {subjects}")
        print(f"Keep categories: {list(KEEP_CATEGORIES)}")
        print(f"Should keep article: {should_keep}")
        
        # Test with filtering enabled
        print("\n🧪 Testing chunk_article with filtering enabled...")
        result = chunk_article(root, check_categories=True)
        
        if result is None:
            print("❌ Article was filtered out")
        else:
            print(f"✅ Article passed filter")
            print(f"Generated {result['metadata']['total_chunks']} chunks")
            print(f"Title: {result['metadata']['title']}")
            print(f"DOI: {result['metadata']['doi']}")
            print(f"Subjects: {result['metadata']['subjects']}")
            
            # Show first chunk with metadata
            if result['chunks']:
                chunk = result['chunks'][0]
                print(f"\nFirst chunk metadata:")
                for key, value in chunk['metadata'].items():
                    print(f"  {key}: {value}")
        
        # Test with filtering disabled
        print("\n🧪 Testing chunk_article with filtering disabled...")
        result_no_filter = chunk_article(root, check_categories=False)
        if result_no_filter:
            print(f"✅ Without filtering: {result_no_filter['metadata']['total_chunks']} chunks")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_filtering()
