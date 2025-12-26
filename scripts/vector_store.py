#!/usr/bin/env python3
"""
Vector Store - Semantic Search Engine using ChromaDB.
"""
import chromadb
import os
import sys
from chromadb.utils import embedding_functions

# Use a persistent storage path
DB_PATH = ".council/vector_store"

class VectorStore:
    def __init__(self):
        # Ensure directory exists
        os.makedirs(DB_PATH, exist_ok=True)
        
        # Initialize Client
        self.client = chromadb.PersistentClient(path=DB_PATH)
        
        # Use default embedding function (all-MiniLM-L6-v2)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="council_lessons",
            embedding_function=self.ef
        )

    def add_lesson(self, lesson_id: str, text: str, metadata: dict):
        """Add a lesson to the vector store."""
        try:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[str(lesson_id)]
            )
            return True
        except Exception as e:
            print(f"❌ Vector Store Error (Add): {e}", file=sys.stderr)
            return False

    def search(self, query: str, n_results: int = 3):
        """Search for similar lessons."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"❌ Vector Store Error (Search): {e}", file=sys.stderr)
            return None

def main():
    # Simple CLI for testing
    import argparse
    parser = argparse.ArgumentParser(description="Vector Store CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Add
    add_parser = subparsers.add_parser("add", help="Add document")
    add_parser.add_argument("--id", required=True, help="Document ID")
    add_parser.add_argument("--text", required=True, help="Document Text")
    add_parser.add_argument("--tags", help="Tags (comma separated)")
    
    # Search
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Query text")
    
    args = parser.parse_args()
    
    vs = VectorStore()
    
    if args.command == "add":
        meta = {"tags": args.tags} if args.tags else {}
        if vs.add_lesson(args.id, args.text, meta):
            print(f"✅ Added document {args.id}")
        else:
            sys.exit(1)
            
    elif args.command == "search":
        results = vs.search(args.query)
        if results and results['documents']:
            print(f"🔍 Found {len(results['documents'][0])} results:")
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                dist = results['distances'][0][i] if 'distances' in results else "N/A"
                print(f"--- Result {i+1} (Dist: {dist}) ---")
                print(f"📄 {doc}")
                print(f"🏷️ {meta}")
        else:
            print("ℹ️ No results found.")

if __name__ == "__main__":
    main()
