#!/usr/bin/env python3

from lxml import etree
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_rag import chunk_article

def test_chunk_article():
    # Load the XML file
    xml_file = "/home/ubuntu/xml/April_2019/0a1e58f5-6c09-1014-838d-8b9451ae9aba.xml"
    
    try:
        # Parse the XML
        with open(xml_file, 'r', encoding='utf-8') as f:
            tree = etree.parse(f)
        root = tree.getroot()
        
        print("✅ XML file loaded successfully")
        print(f"Root element: {root.tag}")
        
        # Test the chunk_article function
        print("\n🧪 Testing chunk_article function...")
        result = chunk_article(root)
        
        if result is None:
            print("❌ Article was filtered out")
            return
            
        chunks = result['chunks']
        metadata = result['metadata']
        
        print(f"✅ Generated {len(chunks)} chunks")
        print(f"Title: {metadata['title']}")
        print(f"DOI: {metadata['doi']}")
        print(f"Subjects: {metadata['subjects']}")
        
        # Display first few chunks
        for i, chunk in enumerate(chunks[:3]):  # Show only first 3 chunks
            print(f"\n--- Chunk {i+1} ---")
            print(f"Type: {chunk['type']}")
            if 'section_id' in chunk:
                print(f"Section ID: {chunk['section_id']}")
            print(f"Content length: {len(chunk['content'])} characters")
            print("Content preview:")
            print(chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'])
            print("-" * 50)
            
        if len(chunks) > 3:
            print(f"... and {len(chunks) - 3} more chunks")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chunk_article()
