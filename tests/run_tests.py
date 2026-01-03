#!/usr/bin/env python3
"""
Test runner for RAG system tests.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Run all available tests."""
    print("=" * 60)
    print("Running RAG System Tests")
    print("=" * 60)
    
    # Import and run chunking test
    try:
        from test_chunking import test_chunk_article
        print("\n📄 Running chunking tests...")
        test_chunk_article()
        print("✅ Chunking tests passed")
    except Exception as e:
        print(f"❌ Chunking tests failed: {e}")
    
    # Import and run filtering test
    try:
        from test_filtering import test_filtering
        print("\n🔍 Running filtering tests...")
        test_filtering()
        print("✅ Filtering tests passed")
    except Exception as e:
        print(f"❌ Filtering tests failed: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
