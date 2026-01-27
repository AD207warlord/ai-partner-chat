"""
Vector database utilities for AI Partner skill.

This module provides functions to query the vector database programmatically.
Supports hybrid search: vector similarity + BM25 keyword matching.
"""

import os
import re
import math
from collections import Counter

# Use offline mode to avoid HuggingFace API rate limits (429 errors)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import chromadb
from sentence_transformers import SentenceTransformer


def tokenize_chinese(text: str) -> List[str]:
    """
    Simple Chinese tokenizer: split by punctuation and whitespace,
    then split Chinese characters individually, keep English words together.
    """
    # Remove punctuation and split
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    tokens = []
    for word in text.split():
        if re.match(r'^[\u4e00-\u9fff]+$', word):
            # Chinese: split into characters
            tokens.extend(list(word))
        else:
            # English/numbers: keep as word
            tokens.append(word.lower())
    return tokens


def compute_bm25_score(query_tokens: List[str], doc_tokens: List[str],
                       avg_doc_len: float, k1: float = 1.5, b: float = 0.75) -> float:
    """
    Compute BM25 score for a single document.
    Simplified version without IDF (since we're scoring within a small result set).
    """
    doc_len = len(doc_tokens)
    doc_freq = Counter(doc_tokens)

    score = 0.0
    for token in query_tokens:
        if token in doc_freq:
            freq = doc_freq[token]
            # BM25 term frequency component
            numerator = freq * (k1 + 1)
            denominator = freq + k1 * (1 - b + b * (doc_len / avg_doc_len))
            score += numerator / denominator

    return score


class NoteRetriever:
    """Handle vector database operations for note retrieval."""

    def __init__(self, db_path: str = "./vector_db"):
        """
        Initialize the retriever with a database path.

        Args:
            db_path: Path to ChromaDB database
        """
        self.db_path = db_path
        self.model = None
        self.client = None
        self.collection = None

    def _ensure_initialized(self):
        """Lazy initialization of model and database connection."""
        if self.model is None:
            self.model = SentenceTransformer('BAAI/bge-m3')

        if self.client is None:
            try:
                self.client = chromadb.PersistentClient(path=self.db_path)
                self.collection = self.client.get_collection("notes")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to connect to database at {self.db_path}. "
                    f"Please run init_vector_db.py first. Error: {e}"
                )

    def query(self, query: str, top_k: int = 5, hybrid: bool = True,
              vector_weight: float = 0.7) -> List[Dict[str, str]]:
        """
        Query the vector database for similar notes.

        Args:
            query: Query text
            top_k: Number of results to return
            hybrid: Whether to use hybrid search (vector + BM25)
            vector_weight: Weight for vector score (1 - vector_weight = BM25 weight)

        Returns:
            List of dicts with 'content', 'path', 'filename' keys
        """
        self._ensure_initialized()

        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()

        # Query collection - get more results for re-ranking if hybrid
        fetch_k = top_k * 3 if hybrid else top_k
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            include=['documents', 'metadatas', 'distances']
        )

        # Format results
        candidates = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                # ChromaDB returns distance, convert to similarity (1 - distance for cosine)
                distance = results['distances'][0][i] if results.get('distances') else 0
                vector_score = 1 - distance  # Convert distance to similarity

                candidates.append({
                    'content': results['documents'][0][i],
                    'filepath': metadata.get('filepath', ''),
                    'filename': metadata.get('filename', ''),
                    'date': metadata.get('date', ''),
                    'chunk_id': metadata.get('chunk_id', ''),
                    'chunk_type': metadata.get('chunk_type', ''),
                    'vector_score': vector_score,
                })

        if not candidates:
            return []

        if not hybrid:
            return candidates[:top_k]

        # Hybrid search: re-rank with BM25
        query_tokens = tokenize_chinese(query)

        # Tokenize all documents and compute avg length
        doc_tokens_list = [tokenize_chinese(c['content']) for c in candidates]
        avg_doc_len = sum(len(t) for t in doc_tokens_list) / len(doc_tokens_list)

        # Compute BM25 scores
        bm25_scores = [
            compute_bm25_score(query_tokens, doc_tokens, avg_doc_len)
            for doc_tokens in doc_tokens_list
        ]

        # Normalize BM25 scores to [0, 1]
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        bm25_scores_norm = [s / max_bm25 for s in bm25_scores]

        # Compute hybrid scores
        bm25_weight = 1 - vector_weight
        for i, candidate in enumerate(candidates):
            candidate['bm25_score'] = bm25_scores_norm[i]
            candidate['hybrid_score'] = (
                vector_weight * candidate['vector_score'] +
                bm25_weight * candidate['bm25_score']
            )

        # Sort by hybrid score
        candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)

        return candidates[:top_k]


def get_relevant_notes(query: str, db_path: str = "./vector_db", top_k: int = 5,
                       hybrid: bool = True, vector_weight: float = 0.7) -> List[Dict[str, str]]:
    """
    Convenience function to retrieve relevant notes with hybrid search.

    Args:
        query: Query text
        db_path: Path to vector database
        top_k: Number of results to return
        hybrid: Whether to use hybrid search (vector + BM25). Default True.
        vector_weight: Weight for vector score (0.7 = 70% vector, 30% BM25)

    Returns:
        List of dicts with 'content', 'path', 'filename' keys
        If hybrid=True, also includes 'vector_score', 'bm25_score', 'hybrid_score'
    """
    retriever = NoteRetriever(db_path)
    return retriever.query(query, top_k, hybrid=hybrid, vector_weight=vector_weight)
