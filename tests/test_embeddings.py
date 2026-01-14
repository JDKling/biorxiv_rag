#!/usr/bin/env python3
"""
Test script for SciBERT embeddings integration.
"""

import sys
import os
from lxml import etree
from build_rag import chunk_article, process_xml_directory_with_embeddings
from embeddings import SciBERTEmbedder, get_embedder
import numpy as np

def test_single_article_with_embeddings():
    """Test embedding generation for a single article."""
    print("=" * 60)
    print("Testing Single Article with SciBERT Embeddings")
    print("=" * 60)
    
    # Use a sample XML file
    xml_file = "/home/ubuntu/biorxiv_rag/subset_xml/00abb580-6e3f-1014-931e-89cd96e1699b.xml"
    
    try:
        # Parse the XML
        with open(xml_file, 'r', encoding='utf-8') as f:
            tree = etree.parse(f)
        root = tree.getroot()
        
        print("✅ XML file loaded successfully")
        
        # Test without embeddings first
        print("\n🧪 Testing without embeddings...")
        result_no_embed = chunk_article(root, check_categories=True, include_embeddings=False)
        
        if result_no_embed:
            print(f"✅ Generated {len(result_no_embed['chunks'])} chunks without embeddings")
            print(f"Title: {result_no_embed['metadata']['title']}")
            print(f"DOI: {result_no_embed['metadata']['doi']}")
            print(f"Subjects: {result_no_embed['metadata']['subjects']}")
        else:
            print("❌ Article was filtered out")
            return
        
        # Test with embeddings
        print("\n🧪 Testing with SciBERT embeddings...")
        result_with_embed = chunk_article(root, check_categories=True, include_embeddings=True)
        
        if result_with_embed:
            chunks = result_with_embed['chunks']
            print(f"✅ Generated {len(chunks)} chunks with embeddings")
            
            # Check first chunk
            first_chunk = chunks[0]
            if 'embedding' in first_chunk:
                embedding = np.array(first_chunk['embedding'])
                print(f"✅ Embedding generated successfully")
                print(f"   Embedding dimension: {len(embedding)}")
                print(f"   Embedding model: {first_chunk.get('embedding_model', 'Unknown')}")
                print(f"   Embedding range: [{embedding.min():.3f}, {embedding.max():.3f}]")
                print(f"   Embedding norm: {np.linalg.norm(embedding):.3f}")
                
                # Show content preview
                print(f"\n📄 First chunk content preview:")
                content = first_chunk['content']
                print(f"   Type: {first_chunk['type']}")
                print(f"   Content length: {len(content)} characters")
                print(f"   Preview: {content[:200]}...")
                
            else:
                print("❌ No embedding found in chunk")
        else:
            print("❌ Article was filtered out")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_embedding_similarity():
    """Test similarity calculation between embeddings."""
    print("\n" + "=" * 60)
    print("Testing Embedding Similarity")
    print("=" * 60)
    
    try:
        embedder = get_embedder()
        
        # Test texts with different levels of similarity
        texts = [
            "CRISPR-Cas9 gene editing in bacterial systems",
            "Gene knockout using CRISPR technology",  # Similar to first
            "Protein structure prediction using machine learning",  # Different topic
            "Machine learning algorithms for protein folding"  # Similar to third
        ]
        
        print("Generating embeddings for test texts...")
        embeddings = embedder.embed_texts(texts)
        
        print(f"✅ Generated embeddings with dimension: {embeddings.shape[1]}")
        
        # Calculate similarities
        print("\n🔍 Similarity matrix:")
        print("Texts:")
        for i, text in enumerate(texts):
            print(f"  {i+1}. {text}")
        
        print("\nSimilarity scores:")
        for i in range(len(texts)):
            for j in range(i+1, len(texts)):
                similarity = embedder.similarity(embeddings[i], embeddings[j])
                print(f"  Text {i+1} ↔ Text {j+1}: {similarity:.3f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_batch_processing():
    """Test batch processing with embeddings on a few files."""
    print("\n" + "=" * 60)
    print("Testing Batch Processing (First 3 Files)")
    print("=" * 60)
    
    try:
        # Get first 3 XML files from subset
        xml_dir = "/home/ubuntu/biorxiv_rag/subset_xml"
        xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')][:3]
        
        print(f"Processing {len(xml_files)} files with embeddings...")
        
        total_chunks = 0
        for xml_file in xml_files:
            filepath = os.path.join(xml_dir, xml_file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = etree.parse(f)
                root = tree.getroot()
                
                result = chunk_article(root, check_categories=True, include_embeddings=True)
                
                if result:
                    chunks = result['chunks']
                    total_chunks += len(chunks)
                    print(f"✅ {xml_file}: {len(chunks)} chunks")
                    
                    # Verify embeddings
                    if chunks and 'embedding' in chunks[0]:
                        embedding_dim = len(chunks[0]['embedding'])
                        print(f"   Embedding dimension: {embedding_dim}")
                    else:
                        print("   ❌ No embeddings found")
                else:
                    print(f"⏭️  {xml_file}: Filtered out")
                    
            except Exception as e:
                print(f"❌ Error processing {xml_file}: {e}")
        
        print(f"\n✅ Total chunks processed: {total_chunks}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all embedding tests."""
    print("🧪 SciBERT Embedding Integration Tests")
    print("=" * 60)
    
    # Test 1: Single article
    test_single_article_with_embeddings()
    
    # Test 2: Similarity calculation
    test_embedding_similarity()
    
    # Test 3: Batch processing
    test_batch_processing()
    
    print("\n" + "=" * 60)
    print("🎉 All embedding tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
