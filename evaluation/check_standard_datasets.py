#!/usr/bin/env python
"""Check RAG content vs standard datasets"""

import sys
sys.path.insert(0, '..')

import json
from pathlib import Path

print("="*80)
print("CHECKING RAG CONTENT AGAINST STANDARD BENCHMARK DATASETS")
print("="*80)

# Test legal domain (since RAG has legal docs)
with open('datasets/legal_standard.json') as f:
    legal = json.load(f)
    q1 = legal[0]
    print(f"\n✅ Testing Legal Domain")
    print(f"   Query: {q1['query'][:70]}...")
    print(f"   Keywords: {q1['gold_keywords']}")

# Initialize RAG
print("\n🔧 Initializing RAG...")
from rag.pipeline import init, retriever
from rag.db import init_db

init_db()
init()
print("   ✅ RAG initialized")

# Test retrieval
result = retriever.query(q1['query'], top_k=3)
print(f"\n   Retrieved {len(result) if result else 0} chunks")

if result:
    for i, (text, score) in enumerate(result[:1]):
        preview = text[:200].replace('\n', ' ')
        print(f"\n   Chunk {i+1} (score={score}):")
        print(f"   {preview}...")
        matching = [kw for kw in q1['gold_keywords'] if kw.lower() in text.lower()]
        if matching:
            print(f"   ✅ KEYWORDS FOUND: {matching}")
        else:
            print(f"   ❌ No keywords match. Expected: {q1['gold_keywords'][:2]}")

print("\n" + "="*80)
print("Summary:")
print("- Your RAG database: LEGAL documents")
print("- Standard datasets: 6 domains (healthcare, technical, financial, legal, textbook, agriculture)")
print("- Legal domain questions: Will have keyword matches ✓")
print("- Other domain questions: Will show 0.0 metrics (different content)")
print("="*80)
