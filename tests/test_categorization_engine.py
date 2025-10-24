"""
Tests for Categorization Engine

Tests the advanced categorization engine with AI, semantic matching, and rules.
"""

import pytest
import os
import yaml
from modules.core.categorization_engine import CategorizationEngine


@pytest.fixture
def engine():
    """Create a categorization engine instance for testing."""
    return CategorizationEngine()


def test_engine_initialization(engine):
    """Test that engine initializes correctly."""
    assert engine is not None
    assert engine.confidence_threshold == 0.65
    assert engine.semantic_threshold == 0.75
    assert engine.retrain_trigger == 10


def test_get_categories(engine):
    """Test getting list of categories."""
    categories = engine.get_categories()
    assert isinstance(categories, list)
    assert len(categories) == 12
    assert 'Boende' in categories
    assert 'Transport' in categories
    assert 'Mat' in categories
    assert 'Inkomst' in categories


def test_get_subcategories(engine):
    """Test getting subcategories for a category."""
    # Test Transport subcategories
    subcats = engine.get_subcategories('Transport')
    assert isinstance(subcats, list)
    assert 'Bränsle' in subcats
    assert 'Parkering' in subcats
    assert 'Tåg' in subcats
    
    # Test Mat subcategories
    subcats = engine.get_subcategories('Mat')
    assert 'Livsmedel' in subcats
    assert 'Restaurang' in subcats
    
    # Test non-existent category
    subcats = engine.get_subcategories('NonExistent')
    assert subcats == []


def test_categorize_with_rules(engine):
    """Test categorization using rules."""
    # Test clear rule match
    result = engine.categorize(
        description="Tankning Shell",
        amount=-450.00,
        use_ai=False,
        use_semantic=False
    )
    
    assert result is not None
    assert result['category'] == 'Transport'
    assert result['subcategory'] == 'Bränsle'
    assert result['source'] == 'rule'
    assert result['confidence_score'] == 1.0
    assert result['flagged'] == False


def test_categorize_with_semantic_fallback(engine):
    """Test categorization with semantic matching."""
    # Test semantic similarity
    result = engine.categorize(
        description="Köp av bensin på macken",
        amount=-350.00,
        use_ai=False,
        use_semantic=True
    )
    
    assert result is not None
    # Should match Transport/Bränsle with semantic matching
    # (if sentence-transformers is installed)


def test_categorize_fallback_to_default(engine):
    """Test fallback to default for unknown transactions."""
    result = engine.categorize(
        description="XYZ123 Unknown Transaction ABC",
        amount=-100.00,
        use_ai=False,
        use_semantic=False
    )
    
    assert result is not None
    assert result['category'] == 'Övrigt'
    assert result['subcategory'] == 'Okänd'
    assert result['source'] == 'default'
    assert result['flagged'] == True  # Should be flagged for review


def test_register_manual_override(engine):
    """Test registering manual overrides."""
    initial_count = engine.manual_override_count
    
    # Register override
    engine.register_manual_override(
        transaction_id='test-tx-1',
        category='Mat',
        subcategory='Livsmedel',
        description='ICA Supermarket',
        train_ai=False  # Don't train during test
    )
    
    assert engine.manual_override_count == initial_count + 1


def test_manual_override_triggers_retraining(engine):
    """Test that manual overrides trigger retraining at threshold."""
    # Set low threshold for testing
    engine.retrain_trigger = 3
    engine.manual_override_count = 0
    
    # Add overrides below threshold
    for i in range(2):
        engine.register_manual_override(
            transaction_id=f'test-tx-{i}',
            category='Mat',
            subcategory='Livsmedel',
            description=f'Test transaction {i}',
            train_ai=False
        )
    
    assert engine.manual_override_count == 2
    
    # Add one more to trigger retraining
    engine.register_manual_override(
        transaction_id='test-tx-3',
        category='Mat',
        subcategory='Livsmedel',
        description='Test transaction 3',
        train_ai=False
    )
    
    # After retraining, counter should reset to 0
    assert engine.manual_override_count == 0


def test_get_stats(engine):
    """Test getting engine statistics."""
    stats = engine.get_stats()
    
    assert isinstance(stats, dict)
    assert 'categories' in stats
    assert 'confidence_threshold' in stats
    assert 'semantic_threshold' in stats
    assert 'manual_overrides_count' in stats
    assert 'retrain_trigger' in stats
    assert 'rules_loaded' in stats
    assert 'semantic_vectors_loaded' in stats
    
    assert stats['categories'] == 12
    assert stats['confidence_threshold'] == 0.65
    assert stats['semantic_threshold'] == 0.75
    assert stats['retrain_trigger'] == 10


def test_rule_matching_multiple_keywords(engine):
    """Test rule matching with multiple keyword variations."""
    test_cases = [
        ("ICA Supermarket", "Mat", "Livsmedel"),
        ("Parkering EasyPark", "Transport", "Parkering"),
        ("Hemförsäkring Folksam", "Boende", "Hemförsäkring"),
        ("Spotify Premium", "Nöje", "Streaming"),
        ("Lön från arbetsgivare", "Inkomst", "Lön"),
    ]
    
    for description, expected_category, expected_subcategory in test_cases:
        result = engine.categorize(
            description=description,
            use_ai=False,
            use_semantic=False
        )
        assert result['category'] == expected_category, f"Failed for: {description}"
        assert result['subcategory'] == expected_subcategory, f"Failed for: {description}"


def test_categorize_with_amount_context(engine):
    """Test that amount context is passed to categorization."""
    # Positive amount (income)
    result = engine.categorize(
        description="Utbetalning lön",
        amount=35000.00,
        use_ai=False,
        use_semantic=False
    )
    assert result['category'] == 'Inkomst'
    
    # Negative amount (expense)
    result = engine.categorize(
        description="ICA Maxi",
        amount=-450.00,
        use_ai=False,
        use_semantic=False
    )
    assert result['category'] == 'Mat'


def test_confidence_scores(engine):
    """Test that confidence scores are appropriate."""
    # Rule-based should have 1.0 confidence
    result = engine.categorize(
        description="Shell tankning",
        use_ai=False,
        use_semantic=False
    )
    assert result['confidence_score'] == 1.0
    
    # Default fallback should have 0.0 confidence and be flagged
    result = engine.categorize(
        description="UNKNOWN_XYZ_123",
        use_ai=False,
        use_semantic=False
    )
    assert result['confidence_score'] == 0.0
    assert result['flagged'] == True


def test_engine_with_missing_config():
    """Test engine handles missing configuration gracefully."""
    # This should not crash even if config is missing
    engine = CategorizationEngine(config_path="nonexistent.yaml")
    assert engine is not None
    # Should use default values
    assert engine.confidence_threshold > 0


def test_categorize_case_insensitive(engine):
    """Test that categorization is case-insensitive."""
    test_cases = [
        "SHELL TANKNING",
        "shell tankning",
        "Shell Tankning",
        "sHeLl TaNkNiNg"
    ]
    
    for description in test_cases:
        result = engine.categorize(
            description=description,
            use_ai=False,
            use_semantic=False
        )
        assert result['category'] == 'Transport'
        assert result['subcategory'] == 'Bränsle'


def test_categorize_with_merchant_info(engine):
    """Test categorization with separate merchant field."""
    result = engine.categorize(
        description="Inköp",
        merchant="ICA Supermarket",
        use_ai=False,
        use_semantic=False
    )
    
    # Should match based on merchant name
    assert result['category'] == 'Mat'
    assert result['subcategory'] == 'Livsmedel'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
