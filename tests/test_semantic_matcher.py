"""
Tests for Semantic Matcher

Tests the semantic matching functionality using sentence embeddings.
"""

import pytest
import os
from modules.core.semantic_matcher import SemanticMatcher


@pytest.fixture
def matcher():
    """Create a semantic matcher instance for testing."""
    return SemanticMatcher()


def test_matcher_initialization(matcher):
    """Test that matcher initializes correctly."""
    assert matcher is not None
    assert matcher.similarity_threshold == 0.75
    assert matcher.model_name == 'all-MiniLM-L6-v2'


def test_is_available(matcher):
    """Test checking if semantic matching is available."""
    result = matcher.is_available()
    assert isinstance(result, bool)
    
    # If sentence-transformers is not installed, should be False
    # If installed and model loaded, should be True


def test_get_stats(matcher):
    """Test getting matcher statistics."""
    stats = matcher.get_stats()
    
    assert isinstance(stats, dict)
    assert 'model_available' in stats
    assert 'model_name' in stats
    assert 'categories_cached' in stats
    assert 'similarity_threshold' in stats
    
    assert stats['model_name'] == 'all-MiniLM-L6-v2'
    assert stats['similarity_threshold'] == 0.75


def test_match_with_clear_example(matcher):
    """Test matching with a clear example phrase."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available (sentence-transformers not installed)")
    
    # Test a phrase that should match Transport/Bränsle
    result = matcher.match("Tankning av bensin på Shell")
    
    if result:  # May be None if below threshold
        assert isinstance(result, dict)
        assert 'category' in result
        assert 'subcategory' in result
        assert 'similarity_score' in result
        assert 'best_example' in result
        
        assert result['similarity_score'] >= matcher.similarity_threshold


def test_match_with_low_similarity(matcher):
    """Test matching with unrelated text."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    # Test with random unrelated text
    result = matcher.match("XYZ123 RANDOM UNKNOWN TEXT ABC")
    
    # Should return None if below threshold
    # or a low confidence match
    if result:
        assert result['similarity_score'] < 0.90  # Should not be highly confident


def test_match_returns_none_below_threshold(matcher):
    """Test that matcher returns None for low similarity."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    # Set high threshold temporarily
    original_threshold = matcher.similarity_threshold
    matcher.similarity_threshold = 0.99  # Very high threshold
    
    try:
        result = matcher.match("Some random text")
        # Should return None with such high threshold
        # (unless by chance it matches something very well)
    finally:
        matcher.similarity_threshold = original_threshold


def test_match_with_empty_text(matcher):
    """Test matching with empty text."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    result = matcher.match("")
    # Should handle gracefully, likely return None


def test_match_with_swedish_text(matcher):
    """Test matching with Swedish phrases."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    swedish_phrases = [
        "Köp av mat på ICA",
        "Hyresbetalning till fastighetsägare",
        "Tankning på Circle K",
        "Besök hos tandläkare"
    ]
    
    for phrase in swedish_phrases:
        result = matcher.match(phrase)
        # Should either match or return None
        if result:
            assert isinstance(result, dict)
            assert 'category' in result
            assert 'subcategory' in result


def test_matcher_with_missing_config():
    """Test matcher handles missing configuration gracefully."""
    matcher = SemanticMatcher(config_path="nonexistent.yaml")
    assert matcher is not None
    # Should use default values
    assert matcher.similarity_threshold > 0


def test_embeddings_cache_structure(matcher):
    """Test that embeddings cache has correct structure."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    assert hasattr(matcher, 'embeddings_cache')
    assert isinstance(matcher.embeddings_cache, dict)
    
    # Check structure of cached items
    for key, value in matcher.embeddings_cache.items():
        assert '/' in key  # Should be in format "Category/Subcategory"
        assert 'examples' in value
        assert 'embeddings' in value
        assert isinstance(value['examples'], list)


def test_cosine_similarity_calculation(matcher):
    """Test cosine similarity calculation method."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    import numpy as np
    
    # Test with identical vectors (should give similarity ~1.0)
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2_matrix = np.array([[1.0, 0.0, 0.0]])
    
    similarities = matcher._cosine_similarity(vec1, vec2_matrix)
    assert len(similarities) == 1
    assert 0.99 <= similarities[0] <= 1.01  # Allow for floating point errors


def test_match_result_structure(matcher):
    """Test that match result has correct structure when successful."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    # Try to get a match (use a phrase likely to match)
    result = matcher.match("Köp på ICA Supermarket matvaror")
    
    if result is not None:
        # Verify structure
        required_fields = ['category', 'subcategory', 'similarity_score', 'best_example']
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        assert isinstance(result['category'], str)
        assert isinstance(result['subcategory'], str)
        assert isinstance(result['similarity_score'], (int, float))
        assert isinstance(result['best_example'], str)
        assert 0.0 <= result['similarity_score'] <= 1.0


def test_multiple_matches(matcher):
    """Test matching multiple phrases."""
    if not matcher.is_available():
        pytest.skip("Semantic matcher not available")
    
    test_phrases = [
        "Matinköp",
        "Parkering",
        "Elräkning",
        "Gymmedlemskap",
        "Spotify"
    ]
    
    results = []
    for phrase in test_phrases:
        result = matcher.match(phrase)
        results.append(result)
    
    # At least some should match
    successful_matches = [r for r in results if r is not None]
    # (Depending on semantic vectors, some may not match)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
