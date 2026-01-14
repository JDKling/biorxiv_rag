#!/usr/bin/env python3
"""
Complete RAG (Retrieval-Augmented Generation) System for bioRxiv.
Combines semantic search with LLM generation for question answering.
"""

import json
from typing import List, Dict, Any, Optional
from .search_interface import BioRxivSearchInterface
from .vector_database import BioRxivVectorDB

class BioRxivRAG:
    """
    Complete RAG system for bioRxiv scientific literature.
    Combines vector search with language model generation.
    """
    
    def __init__(self, db_path: str = "./biorxiv_chroma_db"):
        """Initialize the RAG system."""
        print("🤖 Initializing bioRxiv RAG System...")
        self.search_interface = BioRxivSearchInterface(db_path)
        self.db = self.search_interface.db
        
        print("✅ RAG system ready!")
    
    def retrieve_context(self, query: str, n_results: int = 5, min_similarity: float = 0.0) -> List[Dict]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User question/query
            n_results: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of relevant chunks with metadata
        """
        print(f"🔍 Retrieving context for: '{query}'")
        
        # Get search results
        results = self.search_interface.search(query, n_results, show_content=False)
        
        # Filter by similarity threshold
        filtered_results = [r for r in results if r['similarity'] >= min_similarity]
        
        print(f"📊 Retrieved {len(filtered_results)} relevant chunks")
        return filtered_results
    
    def format_context(self, results: List[Dict]) -> str:
        """
        Format search results into context for LLM.
        
        Args:
            results: Search results from retrieve_context
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            # Parse subjects
            try:
                subjects = json.loads(result['metadata']['subjects'])
                subjects_str = ', '.join(subjects[:3])
            except:
                subjects_str = result['metadata']['subjects']
            
            # Format each chunk
            chunk_context = f"""
[Source {i}]
Title: {result['metadata']['title']}
Type: {result['metadata']['type']}
Subjects: {subjects_str}
Content: {result['content']}
"""
            context_parts.append(chunk_context.strip())
        
        return "\n\n".join(context_parts)
    
    def generate_answer_prompt(self, query: str, context: str) -> str:
        """
        Generate a prompt for LLM with query and context.
        
        Args:
            query: User question
            context: Retrieved context
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are a scientific research assistant specializing in bioRxiv preprints. Answer the user's question based on the provided scientific literature context. Be accurate, cite specific findings, and acknowledge limitations.

QUESTION: {query}

SCIENTIFIC CONTEXT:
{context}

INSTRUCTIONS:
1. Answer based primarily on the provided context
2. Cite specific papers/sources when making claims
3. If the context doesn't fully answer the question, say so
4. Use scientific terminology appropriately
5. Highlight key findings and methodologies
6. If multiple papers provide different perspectives, mention both

ANSWER:"""
        
        return prompt
    
    def answer_question(self, query: str, n_results: int = 5, use_llm: bool = False) -> Dict[str, Any]:
        """
        Answer a question using RAG approach.
        
        Args:
            query: User question
            n_results: Number of chunks to retrieve
            use_llm: Whether to use LLM for generation (requires API)
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        print(f"\n🎯 Question: {query}")
        print("=" * 60)
        
        # Step 1: Retrieve relevant context
        results = self.retrieve_context(query, n_results)
        
        if not results:
            return {
                'query': query,
                'answer': "I couldn't find relevant information in the bioRxiv database for this question.",
                'sources': [],
                'context_used': "",
                'method': 'no_context'
            }
        
        # Step 2: Format context
        context = self.format_context(results)
        
        # Step 3: Generate answer
        if use_llm:
            # This would integrate with OpenAI, Anthropic, or local LLM
            prompt = self.generate_answer_prompt(query, context)
            answer = self._call_llm(prompt)  # Placeholder for LLM integration
            method = 'llm_generated'
        else:
            # Provide structured summary without LLM
            answer = self._generate_summary_answer(query, results)
            method = 'summary_based'
        
        # Step 4: Prepare sources
        sources = []
        for result in results:
            source = {
                'title': result['metadata']['title'],
                'type': result['metadata']['type'],
                'similarity': result['similarity'],
                'content_preview': result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
            }
            
            if 'section_title' in result['metadata']:
                source['section'] = result['metadata']['section_title']
            
            try:
                source['subjects'] = json.loads(result['metadata']['subjects'])
            except:
                source['subjects'] = [result['metadata']['subjects']]
            
            sources.append(source)
        
        return {
            'query': query,
            'answer': answer,
            'sources': sources,
            'context_used': context,
            'method': method,
            'num_sources': len(sources)
        }
    
    def _generate_summary_answer(self, query: str, results: List[Dict]) -> str:
        """
        Generate a summary-based answer without LLM.
        
        Args:
            query: User question
            results: Search results
            
        Returns:
            Summary answer
        """
        if not results:
            return "No relevant information found."
        
        # Analyze results
        papers = {}
        for result in results:
            title = result['metadata']['title']
            if title not in papers:
                papers[title] = {
                    'title': title,
                    'chunks': [],
                    'subjects': result['metadata'].get('subjects', ''),
                    'type_counts': {}
                }
            
            papers[title]['chunks'].append(result)
            chunk_type = result['metadata']['type']
            papers[title]['type_counts'][chunk_type] = papers[title]['type_counts'].get(chunk_type, 0) + 1
        
        # Generate summary
        answer_parts = []
        answer_parts.append(f"Based on {len(results)} relevant sections from {len(papers)} scientific papers:")
        
        for i, (title, paper_info) in enumerate(papers.items(), 1):
            try:
                subjects = json.loads(paper_info['subjects'])
                subjects_str = ', '.join(subjects[:3])
            except:
                subjects_str = paper_info['subjects']
            
            answer_parts.append(f"\n{i}. **{title}**")
            answer_parts.append(f"   - Research area: {subjects_str}")
            answer_parts.append(f"   - Relevant sections: {len(paper_info['chunks'])}")
            
            # Show key content from abstract if available
            abstract_chunks = [c for c in paper_info['chunks'] if c['metadata']['type'] == 'abstract']
            if abstract_chunks:
                content_preview = abstract_chunks[0]['content'][:300] + "..."
                answer_parts.append(f"   - Key findings: {content_preview}")
        
        answer_parts.append(f"\n**Summary**: The retrieved papers cover aspects related to '{query}' across {len(set(r['metadata'].get('subjects', '') for r in results))} different research areas. For detailed information, please refer to the specific sections above.")
        
        return "\n".join(answer_parts)
    
    def _call_llm(self, prompt: str) -> str:
        """
        Placeholder for LLM integration.
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            Generated response
        """
        # This is where you would integrate with:
        # - OpenAI API (GPT-4, GPT-3.5)
        # - Anthropic API (Claude)
        # - Local models (Ollama, etc.)
        
        return f"""[LLM Integration Placeholder]

To integrate with an LLM, you would:

1. **OpenAI Integration**:
   ```python
   import openai
   response = openai.ChatCompletion.create(
       model="gpt-4",
       messages=[{"role": "user", "content": prompt}]
   )
   return response.choices[0].message.content
   ```

2. **Anthropic Claude**:
   ```python
   import anthropic
   client = anthropic.Anthropic(api_key="your-key")
   response = client.messages.create(
       model="claude-3-sonnet-20240229",
       messages=[{"role": "user", "content": prompt}]
   )
   return response.content[0].text
   ```

3. **Local LLM (Ollama)**:
   ```python
   import requests
   response = requests.post('http://localhost:11434/api/generate',
       json={'model': 'llama2', 'prompt': prompt})
   return response.json()['response']
   ```

For now, using summary-based answers from retrieved context.
"""
    
    def interactive_qa(self):
        """Start interactive Q&A session."""
        print(f"\n🤖 bioRxiv RAG Q&A System")
        print("=" * 50)
        print("Ask questions about scientific research!")
        print("Commands:")
        print("  • Enter your question")
        print("  • 'stats' - Show database statistics")
        print("  • 'search <query>' - Just search without Q&A")
        print("  • 'quit' - Exit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input(f"\n❓ Your question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'stats':
                    self.search_interface.explore_database()
                elif user_input.lower().startswith('search '):
                    query = user_input[7:].strip()
                    if query:
                        self.search_interface.search(query, n_results=3)
                elif user_input:
                    # Answer the question
                    result = self.answer_question(user_input, n_results=5)
                    
                    print(f"\n🤖 **Answer:**")
                    print(result['answer'])
                    
                    print(f"\n📚 **Sources ({result['num_sources']} papers):**")
                    for i, source in enumerate(result['sources'], 1):
                        print(f"{i}. {source['title']}")
                        print(f"   Type: {source['type']}, Similarity: {source['similarity']:.3f}")
                        if 'section' in source:
                            print(f"   Section: {source['section']}")
                        print(f"   Preview: {source['content_preview']}")
                        print()
                
            except KeyboardInterrupt:
                print(f"\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def demo_rag_system():
    """Demonstrate the complete RAG system."""
    print("🧪 bioRxiv RAG System Demo")
    print("=" * 60)
    
    # Initialize RAG system
    rag = BioRxivRAG()
    
    # Demo questions
    demo_questions = [
        "How does CRISPR work in gene editing?",
        "What are the mechanisms of bacterial resistance?",
        "How do proteins fold and what determines their structure?",
        "What are the applications of hydrogels in bioengineering?"
    ]
    
    print(f"\n🎯 Running demo Q&A...")
    
    for question in demo_questions:
        result = rag.answer_question(question, n_results=3)
        
        print(f"\n❓ **Question:** {question}")
        print(f"🤖 **Answer:**")
        print(result['answer'])
        print(f"\n📊 **Sources:** {result['num_sources']} papers")
        
        input(f"\nPress Enter to continue...")
    
    print(f"\n🎉 Demo completed!")
    
    # Ask if user wants interactive mode
    response = input(f"\nStart interactive Q&A? (y/n): ").lower().strip()
    if response == 'y':
        rag.interactive_qa()

if __name__ == "__main__":
    demo_rag_system()

