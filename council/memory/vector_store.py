#!/usr/bin/env python3
"""
Vector Store - Semantic Search Engine (Architecture Agnostic).
Automatically falls back to JSON storage if ChromaDB is missing.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

# Constants
DB_PATH = ".council/vector_store"

class VectorStore:
    def __init__(self, use_fallback: bool = False):
        self.use_fallback = use_fallback
        self.chroma_client = None
        self.collection = None
        
        # Ensure base directory exists
        os.makedirs(DB_PATH, exist_ok=True)
        
        # Try importing ChromaDB
        if not use_fallback:
            try:
                import chromadb
                from chromadb.utils import embedding_functions
                
                self.chroma_client = chromadb.PersistentClient(path=DB_PATH)
                self.ef = embedding_functions.DefaultEmbeddingFunction()
                self.collection = self.chroma_client.get_or_create_collection(
                    name="council_lessons", embedding_function=self.ef
                )
                print("✅ VectorStore: using ChromaDB", file=sys.stderr)
            except ImportError:
                print("⚠️  VectorStore: ChromaDB not found. Using JSON fallback.", file=sys.stderr)
                self.use_fallback = True

        if self.use_fallback:
            self.json_path = os.path.join(DB_PATH, "fallback.json")
            self._load_fallback()

    def _load_fallback(self):
        """Load simple JSON store for fallback."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"documents": [], "metadatas": [], "ids": []}
        else:
            self.data = {"documents": [], "metadatas": [], "ids": []}

    def _save_fallback(self):
        """Save simple JSON store."""
        with open(self.json_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_lesson(self, lesson_id: str, text: str, metadata: dict) -> bool:
        """Add a document to the store."""
        try:
            if not self.use_fallback:
                self.collection.add(
                    documents=[text], metadatas=[metadata], ids=[str(lesson_id)]
                )
            else:
                # Simple append for fallback
                # Check duplication by ID
                if lesson_id in self.data["ids"]:
                    idx = self.data["ids"].index(lesson_id)
                    self.data["documents"][idx] = text
                    self.data["metadatas"][idx] = metadata
                else:
                    self.data["ids"].append(str(lesson_id))
                    self.data["documents"].append(text)
                    self.data["metadatas"].append(metadata)
                self._save_fallback()
            return True
        except Exception as e:
            print(f"❌ Vector Store Error (Add): {e}", file=sys.stderr)
            return False

    def search(self, query: str, n_results: int = 3) -> Optional[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            if not self.use_fallback:
                return self.collection.query(query_texts=[query], n_results=n_results)
            else:
                # Naive Keyword Search for fallback
                results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
                query_lower = query.lower()
                
                # Simple score: count query word overlap
                scored_docs = []
                for i, doc in enumerate(self.data["documents"]):
                    score = 0
                    doc_lower = doc.lower()
                    if query_lower in doc_lower:
                        score += 2
                    for word in query_lower.split():
                        if word in doc_lower:
                            score += 1
                    
                    if score > 0:
                        scored_docs.append((score, i))
                
                # Sort by score desc
                scored_docs.sort(key=lambda x: x[0], reverse=True)
                top_k = scored_docs[:n_results]
                
                for score, idx in top_k:
                    results["ids"][0].append(self.data["ids"][idx])
                    results["documents"][0].append(self.data["documents"][idx])
                    results["metadatas"][0].append(self.data["metadatas"][idx])
                    results["distances"][0].append(10.0 - score) # Mock distance
                    
                return results

        except Exception as e:
            print(f"❌ Vector Store Error (Search): {e}", file=sys.stderr)
            return None

def main():
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    add_p = subparsers.add_parser("add")
    add_p.add_argument("--id", required=True)
    add_p.add_argument("--text", required=True)
    add_p.add_argument("--tags")

    search_p = subparsers.add_parser("search")
    search_p.add_argument("query")

    args = parser.parse_args()
    vs = VectorStore()

    if args.command == "add":
        meta = {"tags": args.tags} if args.tags else {}
        vs.add_lesson(args.id, args.text, meta)
        print(f"Added {args.id}")
    elif args.command == "search":
        res = vs.search(args.query)
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
