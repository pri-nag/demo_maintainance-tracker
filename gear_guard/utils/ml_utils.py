# -*- coding: utf-8 -*-
"""
GearGuard ML Utilities
Lightweight machine learning utilities for smart search functionality.
Uses TF-IDF and cosine similarity for finding similar maintenance issues.
"""

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class SimilaritySearch:
    """
    TF-IDF based similarity search for maintenance requests.
    Provides smart search functionality to find similar past issues.
    """
    
    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.documents = []
        self.document_ids = []
    
    def is_available(self):
        """Check if ML libraries are available."""
        return ML_AVAILABLE
    
    def build_index(self, documents, document_ids):
        """
        Build TF-IDF index from documents.
        
        Args:
            documents: List of text documents (descriptions)
            document_ids: List of corresponding record IDs
        """
        if not ML_AVAILABLE:
            return False
        
        if not documents or len(documents) < 2:
            return False
        
        try:
            self.documents = documents
            self.document_ids = document_ids
            
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
            )
            
            self.tfidf_matrix = self.vectorizer.fit_transform(documents)
            return True
        except Exception:
            return False
    
    def find_similar(self, query, top_k=5, threshold=0.1):
        """
        Find similar documents to the query.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of tuples (document_id, similarity_score)
        """
        if not ML_AVAILABLE or self.vectorizer is None:
            return []
        
        if not query or not query.strip():
            return []
        
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top-k indices sorted by similarity
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= threshold:
                    results.append((self.document_ids[idx], score))
            
            return results
        except Exception:
            return []
    
    def clear(self):
        """Clear the index."""
        self.vectorizer = None
        self.tfidf_matrix = None
        self.documents = []
        self.document_ids = []


def preprocess_text(text):
    """
    Preprocess text for similarity search.
    
    Args:
        text: Input text string
        
    Returns:
        Preprocessed text string
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def extract_keywords(text, max_keywords=10):
    """
    Extract keywords from text using TF-IDF.
    
    Args:
        text: Input text string
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of keywords
    """
    if not ML_AVAILABLE or not text:
        return []
    
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=max_keywords,
            ngram_range=(1, 2),
        )
        
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        
        # Get scores for each feature
        scores = tfidf_matrix.toarray()[0]
        
        # Sort by score and return top keywords
        keyword_scores = list(zip(feature_names, scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [kw for kw, score in keyword_scores if score > 0]
    except Exception:
        return []
