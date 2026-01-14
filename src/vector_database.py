#!/usr/bin/env python3
"""
ChromaDB Vector Database for bioRxiv RAG System.
Handles storage, retrieval, and semantic search of scientific articles.
"""

import chromadb
from chromadb.config import Settings
import json
import uuid
import os
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from .build_rag import process_xml_directory_with_embeddings, chunk_article
from .embeddings import get_embedder
from lxml import etree

class BioRxivVectorDB:
    """
    Vector database for bioRxiv articles using ChromaDB.
    Handles embedding storage, semantic search, and metadata filtering.
    """
    
    def __init__(self, db_path: str = "./biorxiv_chroma_db"):
        """
        Initialize the vector database.
        
        Args:
            db_path: Path to store the ChromaDB database
        """
        self.db_path = db_path
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="biorxiv_articles",
            metadata={
                "description": "bioRxiv scientific articles with SciBERT embeddings",
                "embedding_model": "allenai/scibert_scivocab_uncased",
                "embedding_dimension": "768",
                "created_at": datetime.now().isoformat()
            }
        )
        
        print(f"📚 Vector database initialized at: {db_path}")
        print(f"📊 Current collection size: {self.collection.count()} chunks")
    
    def add_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100) -> int:
        """
        Add chunks with embeddings to the database.
        
        Args:
            chunks: List of chunk dictionaries with embeddings
            batch_size: Number of chunks to process in each batch
            
        Returns:
            Number of chunks successfully added
        """
        if not chunks:
            print("⚠️  No chunks to add")
            return 0
        
        print(f"📥 Adding {len(chunks)} chunks to vector database...")
        
        # Process in batches to avoid memory issues
        added_count = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for chunk in batch:
                # Generate unique ID
                chunk_id = str(uuid.uuid4())
                ids.append(chunk_id)
                
                # Extract embedding
                if 'embedding' not in chunk:
                    print(f"⚠️  Chunk missing embedding, skipping...")
                    continue
                    
                embeddings.append(chunk['embedding'])
                
                # Document content
                documents.append(chunk['content'])
                
                # Metadata (ChromaDB requires string values)
                metadata = {
                    'type': chunk['type'],
                    'title': chunk['metadata']['title'][:500],  # Truncate long titles
                    'doi': chunk['metadata']['doi'],
                    'subjects': json.dumps(chunk['metadata']['subjects']),
                    'embedding_model': chunk.get('embedding_model', ''),
                    'embedding_dimension': str(chunk.get('embedding_dimension', 768)),
                    'content_length': str(len(chunk['content'])),
                    'added_at': datetime.now().isoformat()
                }
                
                # Add section info if available
                if 'section_id' in chunk:
                    metadata['section_id'] = chunk['section_id']
                if 'section_title' in chunk['metadata']:
                    metadata['section_title'] = chunk['metadata']['section_title'][:200]
                    
                metadatas.append(metadata)
            
            # Add batch to collection
            if embeddings:  # Only add if we have valid embeddings
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                added_count += len(embeddings)
                print(f"✅ Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(embeddings)} chunks)")
        
        print(f"🎉 Successfully added {added_count} chunks to vector database")
        return added_count
    
    def search(self, query: str, n_results: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar chunks using text query.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with similarity scores
        """
        print(f"🔍 Searching for: '{query}'")
        
        # Generate embedding for query
        embedder = get_embedder()
        query_embedding = embedder.embed_text(query)
        
        # Prepare where clause for filtering
        where_clause = filter_dict if filter_dict else None
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        if results['ids'][0]:  # Check if we have results
            for i in range(len(results['ids'][0])):
                # Convert distance to similarity (ChromaDB uses cosine distance)
                similarity = 1 - results['distances'][0][i]
                
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': similarity,
                    'distance': results['distances'][0][i]
                }
                formatted_results.append(result)
        
        print(f"📊 Found {len(formatted_results)} results")
        return formatted_results
    
    def search_by_embedding(self, embedding: np.ndarray, n_results: int = 5, 
                           filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search using a pre-computed embedding.
        
        Args:
            embedding: Query embedding vector
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with similarity scores
        """
        where_clause = filter_dict if filter_dict else None
        
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'metadatas', 'distances']
        )
        
        formatted_results = []
        if results['ids'][0]:
            for i in range(len(results['ids'][0])):
                similarity = 1 - results['distances'][0][i]
                
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': similarity,
                    'distance': results['distances'][0][i]
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def filter_search(self, query: str, subject_filter: Optional[str] = None, 
                     article_type: Optional[str] = None, n_results: int = 5) -> List[Dict]:
        """
        Search with common filters for scientific articles.
        
        Args:
            query: Search query text
            subject_filter: Filter by subject (e.g., "Bioinformatics")
            article_type: Filter by type ("abstract" or "section")
            n_results: Number of results to return
            
        Returns:
            List of filtered search results
        """
        where_clause = {}
        
        if article_type:
            where_clause['type'] = article_type
            
        if subject_filter:
            # Note: ChromaDB filtering with JSON strings requires exact match
            # For more flexible subject filtering, we'd need post-processing
            print(f"🏷️  Filtering by subject: {subject_filter}")
        
        results = self.search(query, n_results, where_clause if where_clause else None)
        
        # Post-process for subject filtering (since subjects are stored as JSON)
        if subject_filter:
            filtered_results = []
            for result in results:
                try:
                    subjects = json.loads(result['metadata']['subjects'])
                    if subject_filter in subjects:
                        filtered_results.append(result)
                except (json.JSONDecodeError, KeyError):
                    continue
            results = filtered_results
        
        return results
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        count = self.collection.count()
        
        # Get sample of metadata to analyze
        if count > 0:
            sample = self.collection.get(limit=min(100, count), include=['metadatas'])
            
            # Analyze subjects
            all_subjects = []
            article_types = {}
            
            for metadata in sample['metadatas']:
                try:
                    subjects = json.loads(metadata['subjects'])
                    all_subjects.extend(subjects)
                except:
                    pass
                
                article_type = metadata.get('type', 'unknown')
                article_types[article_type] = article_types.get(article_type, 0) + 1
            
            # Count unique subjects
            unique_subjects = list(set(all_subjects))
            
        else:
            unique_subjects = []
            article_types = {}
        
        return {
            'total_chunks': count,
            'collection_name': self.collection.name,
            'collection_metadata': self.collection.metadata,
            'database_path': self.db_path,
            'unique_subjects': unique_subjects[:10],  # Show top 10
            'article_types': article_types
        }
    
    def add_xml_file(self, xml_path: str, check_categories: bool = True) -> int:
        """
        Add a single XML file to the database.
        
        Args:
            xml_path: Path to XML file
            check_categories: Whether to filter by categories
            
        Returns:
            Number of chunks added
        """
        print(f"📄 Processing XML file: {os.path.basename(xml_path)}")
        
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                tree = etree.parse(f)
            root = tree.getroot()
            
            # Process article with embeddings
            result = chunk_article(root, check_categories=check_categories, include_embeddings=True)
            
            if result:
                chunks = result['chunks']
                added = self.add_chunks(chunks)
                print(f"✅ Added {added} chunks from {result['metadata']['title'][:60]}...")
                return added
            else:
                print(f"⏭️  Article filtered out")
                return 0
                
        except Exception as e:
            print(f"❌ Error processing {xml_path}: {e}")
            return 0
    
    def populate_from_directory(self, xml_dir: str, max_files: Optional[int] = None, 
                               check_categories: bool = True) -> Dict:
        """
        Populate database from a directory of XML files.
        
        Args:
            xml_dir: Directory containing XML files
            max_files: Maximum number of files to process (None for all)
            check_categories: Whether to filter by categories
            
        Returns:
            Summary statistics
        """
        print(f"🗂️  Populating database from: {xml_dir}")
        
        xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
        if max_files:
            xml_files = xml_files[:max_files]
        
        total_added = 0
        processed_count = 0
        filtered_count = 0
        error_count = 0
        
        for xml_file in xml_files:
            xml_path = os.path.join(xml_dir, xml_file)
            added = self.add_xml_file(xml_path, check_categories)
            
            if added > 0:
                total_added += added
                processed_count += 1
            elif added == 0:
                filtered_count += 1
            else:
                error_count += 1
        
        summary = {
            'total_files_processed': len(xml_files),
            'successful_articles': processed_count,
            'filtered_articles': filtered_count,
            'error_articles': error_count,
            'total_chunks_added': total_added
        }
        
        print(f"\n📊 Population Summary:")
        print(f"   Files processed: {len(xml_files)}")
        print(f"   Successful articles: {processed_count}")
        print(f"   Filtered articles: {filtered_count}")
        print(f"   Total chunks added: {total_added}")
        
        return summary

def create_and_populate_db(xml_dir: str = "/home/ubuntu/biorxiv_rag/subset_xml", 
                          max_files: int = 10) -> BioRxivVectorDB:
    """
    Convenience function to create and populate the database.
    
    Args:
        xml_dir: Directory containing XML files
        max_files: Maximum number of files to process
        
    Returns:
        Initialized and populated database
    """
    print("🚀 Creating and Populating bioRxiv Vector Database")
    print("=" * 60)
    
    # Initialize database
    db = BioRxivVectorDB()
    
    # Check if already populated
    current_count = db.collection.count()
    if current_count > 0:
        print(f"📚 Database already contains {current_count} chunks")
        response = input("Do you want to add more articles? (y/n): ").lower().strip()
        if response != 'y':
            return db
    
    # Populate database
    summary = db.populate_from_directory(xml_dir, max_files=max_files)
    
    # Show final stats
    stats = db.get_stats()
    print(f"\n🎉 Database ready!")
    print(f"📊 Total chunks: {stats['total_chunks']}")
    print(f"🏷️  Subjects: {', '.join(stats['unique_subjects'][:5])}...")
    print(f"📁 Database path: {stats['database_path']}")
    
    return db

if __name__ == "__main__":
    # Example usage
    db = create_and_populate_db()
    
    # Test search
    print("\n🔍 Testing search functionality...")
    results = db.search("CRISPR gene editing bacteria", n_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Similarity: {result['similarity']:.3f}")
        print(f"   Title: {result['metadata']['title']}")
        print(f"   Type: {result['metadata']['type']}")
        print(f"   Content: {result['content'][:150]}...")
