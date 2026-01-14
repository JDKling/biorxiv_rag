#!/usr/bin/env python3
"""
Interactive Search Interface for bioRxiv RAG System.
Provides command-line interface for semantic search and exploration.
"""

import json
from typing import List, Dict, Any, Optional
from .vector_database import BioRxivVectorDB
from .embeddings import get_embedder

class BioRxivSearchInterface:
    """Interactive search interface for the bioRxiv vector database."""
    
    def __init__(self, db_path: str = "./biorxiv_chroma_db"):
        """Initialize the search interface."""
        print("🔍 Initializing bioRxiv Search Interface...")
        self.db = BioRxivVectorDB(db_path)
        self.embedder = get_embedder()
        
        # Get database stats
        stats = self.db.get_stats()
        print(f"📚 Database loaded: {stats['total_chunks']} chunks")
        print(f"🏷️  Available subjects: {', '.join(stats['unique_subjects'][:5])}...")
        print("✅ Search interface ready!")
    
    def search(self, query: str, n_results: int = 5, show_content: bool = True) -> List[Dict]:
        """
        Perform semantic search with improved similarity calculation.
        
        Args:
            query: Search query
            n_results: Number of results to return
            show_content: Whether to display content in results
            
        Returns:
            List of search results
        """
        print(f"\n🔍 Searching for: '{query}'")
        print("-" * 60)
        
        # Get query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Search using ChromaDB
        results = self.db.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Process and format results
        formatted_results = []
        if results['ids'][0]:
            for i in range(len(results['ids'][0])):
                # Calculate proper similarity (ChromaDB returns squared euclidean distance)
                distance = results['distances'][0][i]
                # Convert to cosine similarity approximation
                similarity = max(0, 1 - (distance / 2))  # Normalize distance to similarity
                
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': similarity,
                    'distance': distance
                }
                formatted_results.append(result)
        
        # Display results
        if formatted_results:
            for i, result in enumerate(formatted_results, 1):
                print(f"\n{i}. Similarity: {result['similarity']:.3f}")
                print(f"   📄 Title: {result['metadata']['title']}")
                print(f"   🏷️  Type: {result['metadata']['type']}")
                
                # Parse subjects
                try:
                    subjects = json.loads(result['metadata']['subjects'])
                    print(f"   🔬 Subjects: {', '.join(subjects[:3])}")
                except:
                    print(f"   🔬 Subjects: {result['metadata']['subjects']}")
                
                if 'section_title' in result['metadata']:
                    print(f"   📑 Section: {result['metadata']['section_title']}")
                
                if show_content:
                    content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    print(f"   📝 Content: {content_preview}")
        else:
            print("❌ No results found")
        
        return formatted_results
    
    def search_by_subject(self, query: str, subject: str, n_results: int = 5) -> List[Dict]:
        """Search within a specific subject area."""
        print(f"\n🔍 Searching in '{subject}' for: '{query}'")
        
        # Get all results first, then filter by subject
        all_results = self.search(query, n_results=20, show_content=False)
        
        # Filter by subject
        filtered_results = []
        for result in all_results:
            try:
                subjects = json.loads(result['metadata']['subjects'])
                if subject in subjects:
                    filtered_results.append(result)
            except:
                continue
        
        # Display filtered results
        filtered_results = filtered_results[:n_results]
        if filtered_results:
            print(f"\n📊 Found {len(filtered_results)} results in '{subject}':")
            for i, result in enumerate(filtered_results, 1):
                print(f"\n{i}. Similarity: {result['similarity']:.3f}")
                print(f"   📄 Title: {result['metadata']['title']}")
                print(f"   🏷️  Type: {result['metadata']['type']}")
                content_preview = result['content'][:150] + "..." if len(result['content']) > 150 else result['content']
                print(f"   📝 Content: {content_preview}")
        else:
            print(f"❌ No results found in '{subject}'")
        
        return filtered_results
    
    def compare_queries(self, queries: List[str], n_results: int = 3):
        """Compare multiple queries side by side."""
        print(f"\n🔄 Comparing {len(queries)} queries:")
        print("=" * 80)
        
        all_results = {}
        for query in queries:
            results = self.search(query, n_results, show_content=False)
            all_results[query] = results
        
        # Show comparison
        print(f"\n📊 Query Comparison Results:")
        for query, results in all_results.items():
            print(f"\n🎯 '{query}' - {len(results)} results:")
            for i, result in enumerate(results[:2], 1):  # Show top 2 for each
                print(f"   {i}. {result['similarity']:.3f} - {result['metadata']['title'][:50]}...")
    
    def explore_database(self):
        """Explore database contents and statistics."""
        stats = self.db.get_stats()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Unique subjects: {len(stats['unique_subjects'])}")
        print(f"   Article types: {stats['article_types']}")
        print(f"   Database path: {stats['database_path']}")
        
        print(f"\n🏷️  Available subjects:")
        for subject in stats['unique_subjects']:
            print(f"   • {subject}")
    
    def interactive_search(self):
        """Start interactive search session."""
        print(f"\n🚀 Interactive bioRxiv Search")
        print("=" * 50)
        print("Commands:")
        print("  • Enter search query")
        print("  • 'stats' - Show database statistics") 
        print("  • 'subjects' - List available subjects")
        print("  • 'compare' - Compare multiple queries")
        print("  • 'quit' - Exit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n🔍 Search query: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'stats':
                    self.explore_database()
                elif user_input.lower() == 'subjects':
                    stats = self.db.get_stats()
                    print(f"\n🏷️  Available subjects:")
                    for subject in stats['unique_subjects']:
                        print(f"   • {subject}")
                elif user_input.lower() == 'compare':
                    print("Enter queries separated by semicolons (;):")
                    queries_input = input("Queries: ").strip()
                    queries = [q.strip() for q in queries_input.split(';') if q.strip()]
                    if len(queries) >= 2:
                        self.compare_queries(queries)
                    else:
                        print("❌ Please enter at least 2 queries separated by semicolons")
                elif user_input:
                    # Check if it's a subject-specific search
                    if ' in ' in user_input.lower():
                        parts = user_input.lower().split(' in ')
                        if len(parts) == 2:
                            query, subject = parts[0].strip(), parts[1].strip()
                            self.search_by_subject(query, subject.title())
                        else:
                            self.search(user_input)
                    else:
                        self.search(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def demo_search():
    """Demonstrate search capabilities."""
    print("🧪 bioRxiv RAG Search Demo")
    print("=" * 60)
    
    # Initialize search interface
    search = BioRxivSearchInterface()
    
    # Demo queries
    demo_queries = [
        "CRISPR gene editing",
        "protein folding mechanisms", 
        "bacterial cell wall",
        "hydrogel biomaterials",
        "antimicrobial resistance"
    ]
    
    print(f"\n🎯 Running demo searches...")
    
    for query in demo_queries:
        results = search.search(query, n_results=2, show_content=True)
        input(f"\nPress Enter to continue to next query...")
    
    print(f"\n🎉 Demo completed!")
    
    # Ask if user wants interactive mode
    response = input(f"\nStart interactive search? (y/n): ").lower().strip()
    if response == 'y':
        search.interactive_search()

if __name__ == "__main__":
    demo_search()

