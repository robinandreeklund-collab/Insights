"""
Semantic Matcher for Insights

Uses SentenceTransformer embeddings to find semantic similarity
between transaction descriptions and category examples.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class SemanticMatcher:
    """
    Semantic matcher using sentence embeddings for transaction categorization.
    Uses cosine similarity to match transaction descriptions to category examples.
    """
    
    def __init__(self, config_path: str = "yaml/semantic_matcher.yaml"):
        """Initialize semantic matcher."""
        self.config_path = config_path
        self.config = self._load_config()
        self.vectors_data = self._load_vectors()
        self.model = None
        self.embeddings_cache = {}
        
        # Get configuration
        self.similarity_threshold = self.config.get('similarity_threshold', 0.75)
        self.model_name = self.config.get('model', 'all-MiniLM-L6-v2')
        
        # Initialize model lazily
        self._initialize_model()
        
        logger.info(f"Semantic Matcher initialized with threshold {self.similarity_threshold}")
    
    def _load_config(self) -> Dict:
        """Load semantic matcher configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('semantic_matcher', {})
        except Exception as e:
            logger.warning(f"Could not load semantic matcher config: {e}")
            return {}
    
    def _load_vectors(self) -> Dict:
        """Load semantic vector examples."""
        vectors_path = "yaml/semantic_vectors.yaml"
        try:
            with open(vectors_path, 'r', encoding='utf-8') as f:
                vectors = yaml.safe_load(f)
            return vectors.get('semantic_vectors', {})
        except Exception as e:
            logger.error(f"Error loading semantic vectors: {e}")
            return {}
    
    def _initialize_model(self):
        """Initialize SentenceTransformer model if available."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Try to initialize model with explicit device mapping
            try:
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.model = SentenceTransformer(self.model_name, device=device)
            except Exception as e:
                # Fallback to default initialization
                logger.warning(f"Device-specific init failed, using default: {e}")
                try:
                    self.model = SentenceTransformer(self.model_name)
                except Exception as e2:
                    # Final fallback: use a simpler model
                    logger.warning(f"Failed to load {self.model_name}, trying paraphrase-MiniLM-L3-v2: {e2}")
                    self.model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
            
            logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
            
            # Pre-compute embeddings for all examples
            self._compute_example_embeddings()
        except ImportError:
            logger.warning("sentence-transformers not installed. Semantic matching disabled.")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer: {e}")
            logger.info("Semantic matching will be disabled. System will use AI and rules only.")
            self.model = None
    
    def _compute_example_embeddings(self):
        """Pre-compute embeddings for all category examples."""
        if not self.model:
            return
        
        try:
            logger.info("Computing embeddings for category examples...")
            for category, subcategories in self.vectors_data.items():
                if not isinstance(subcategories, dict):
                    continue
                
                for subcategory, examples in subcategories.items():
                    if not isinstance(examples, list):
                        continue
                    
                    key = f"{category}/{subcategory}"
                    try:
                        embeddings = self.model.encode(examples, convert_to_tensor=False, show_progress_bar=False)
                        self.embeddings_cache[key] = {
                            'examples': examples,
                            'embeddings': embeddings
                        }
                    except Exception as e:
                        logger.error(f"Failed to compute embeddings for {key}: {e}")
            
            logger.info(f"Computed embeddings for {len(self.embeddings_cache)} categories")
        except Exception as e:
            logger.error(f"Error during embedding computation: {e}")
            # Clear cache and disable model if embedding computation fails
            self.embeddings_cache = {}
            self.model = None
            logger.warning("Semantic matching disabled due to embedding computation failure")
    
    def match(self, text: str) -> Optional[Dict]:
        """
        Find best semantic match for given text.
        
        Args:
            text: Transaction description to match
        
        Returns:
            Dict with category, subcategory, and similarity_score, or None
        """
        if not self.model or not self.embeddings_cache:
            logger.debug("Semantic matching not available")
            return None
        
        try:
            # Compute embedding for input text
            text_embedding = self.model.encode([text], convert_to_tensor=False)[0]
            
            # Find best match across all categories
            best_match = None
            best_score = 0.0
            
            for key, cache_data in self.embeddings_cache.items():
                # Compute cosine similarity with all examples
                similarities = self._cosine_similarity(text_embedding, cache_data['embeddings'])
                max_similarity = float(np.max(similarities))
                
                if max_similarity > best_score:
                    best_score = max_similarity
                    parts = key.split('/')
                    best_match = {
                        'category': parts[0],
                        'subcategory': parts[1] if len(parts) > 1 else 'Övrigt',
                        'similarity_score': max_similarity,
                        'best_example': cache_data['examples'][int(np.argmax(similarities))]
                    }
            
            # Only return if above threshold
            if best_match and best_score >= self.similarity_threshold:
                logger.debug(f"Semantic match: {text[:50]}... -> {best_match['category']}/{best_match['subcategory']} ({best_score:.2f})")
                return best_match
            
            return None
        except Exception as e:
            logger.error(f"Semantic matching error: {e}")
            return None
    
    def _cosine_similarity(self, vec1, vec2_matrix):
        """Compute cosine similarity between a vector and matrix of vectors."""
        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norms = vec2_matrix / (np.linalg.norm(vec2_matrix, axis=1, keepdims=True) + 1e-10)
        
        # Compute dot product
        similarities = np.dot(vec2_norms, vec1_norm)
        return similarities
    
    def is_available(self) -> bool:
        """Check if semantic matching is available."""
        return self.model is not None and len(self.embeddings_cache) > 0
    
    def get_stats(self) -> Dict:
        """Get statistics about semantic matcher."""
        return {
            'model_available': self.model is not None,
            'model_name': self.model_name,
            'categories_cached': len(self.embeddings_cache),
            'similarity_threshold': self.similarity_threshold
        }
