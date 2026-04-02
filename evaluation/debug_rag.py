#!/usr/bin/env python
"""Quick diagnostic to check RAG retrieval"""

import sys
sys.path.insert(0, '..')

import json
from pathlib import Path

print("="*80)
print("RAG RETRIEVAL DIAGNOSTIC")
print("="*80)

# Load one Q&A dataset
print("\n1. CHECKING Q&A DATASETS")
print("-"*80)

try:
    with open('datasets/healthcare_qa_reference.json') as f:
        qa = json.load(f)
        q1 = qa[0]
        print(f"✅ Healthcare Q&A loaded")
        question = q1.get('query') or q1.get('question')
        print(f"   Query: {question}")
        print(f"   Gold keywords: {q1['gold_keywords']}")
except Exception as e:
    print(f"❌ Error loading Q&A: {e}")
    sys.exit(1)

# Initialize RAG and try retrieval
print("\n2. INITIALIZING RAG SYSTEM")
print("-"*80)

try:
    from rag.pipeline import init, retriever
    from rag.db import init_db
    
    print("   Initializing database...")
    init_db()
    print("   Initializing retriever...")
    init()
    print("✅ RAG system initialized")
    
except Exception as e:
    print(f"❌ Error initializing RAG: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test retrieval
print("\n3. TESTING RETRIEVAL")
print("-"*80)

try:
    result = retriever.query(question, top_k=5)
    print(f"✅ Retriever returned {len(result) if result else 0} chunks")
    
    if not result:
        print("   ⚠️  WARNING: Empty result!")
    else:
        print(f"\n   Retrieved chunks content:")
        for i, item in enumerate(result[:2]):
            if isinstance(item, tuple):
                text, score = item
            else:
                text = item
                score = "N/A"
            
            # Check if this looks like legal content
            preview = str(text)[:400].replace('\n', ' ')
            print(f"\n   Chunk {i+1} (score={score}):")
            print(f"   {preview}...")
            
            # Check for keyword matches
            keywords_found = [kw for kw in q1['gold_keywords'] if kw.lower() in str(text).lower()]
            if keywords_found:
                print(f"   ✅ KEYWORDS FOUND: {keywords_found}")
            else:
                print(f"   ❌ No keywords found. Expected: {q1['gold_keywords'][:2]}")
                
except Exception as e:
    print(f"❌ Error during retrieval: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
