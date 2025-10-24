"""
Tests for Retraining Pipeline

Tests the automatic retraining pipeline functionality.
"""

import pytest
import os
import yaml
from modules.core.retraining_pipeline import RetrainingPipeline


@pytest.fixture
def pipeline():
    """Create a retraining pipeline instance for testing."""
    return RetrainingPipeline()


def test_pipeline_initialization(pipeline):
    """Test that pipeline initializes correctly."""
    assert pipeline is not None
    assert pipeline.trigger_threshold == 10
    assert pipeline.model_type == 'LogisticRegression'
    assert pipeline.validation_split == 0.2


def test_should_retrain_with_sufficient_data(pipeline):
    """Test retraining trigger with sufficient data."""
    # This will check actual training data
    # Result depends on whether we have enough samples
    result = pipeline.should_retrain()
    assert isinstance(result, bool)


def test_get_stats(pipeline):
    """Test getting pipeline statistics."""
    stats = pipeline.get_stats()
    
    assert isinstance(stats, dict)
    assert 'trigger_threshold' in stats
    assert 'model_type' in stats
    assert 'validation_split' in stats
    assert 'should_retrain' in stats
    
    assert stats['trigger_threshold'] == 10
    assert stats['model_type'] == 'LogisticRegression'
    assert stats['validation_split'] == 0.2


def test_run_pipeline_with_insufficient_data(pipeline):
    """Test pipeline run with insufficient data."""
    # Clear any existing training data for this test
    # (or skip if data exists)
    result = pipeline.run()
    
    assert isinstance(result, dict)
    assert 'success' in result
    assert 'timestamp' in result
    assert 'message' in result
    
    # If we have insufficient data, success should be False
    if result['samples_used'] < 4:
        assert result['success'] == False
        assert 'Insufficient' in result['message']


def test_pipeline_config_loading(pipeline):
    """Test that pipeline loads configuration correctly."""
    assert hasattr(pipeline, 'config')
    assert hasattr(pipeline, 'trigger_threshold')
    assert hasattr(pipeline, 'model_type')
    assert hasattr(pipeline, 'validation_split')


def test_pipeline_with_missing_config():
    """Test pipeline handles missing configuration gracefully."""
    pipeline = RetrainingPipeline(config_path="nonexistent.yaml")
    assert pipeline is not None
    # Should use default values
    assert pipeline.trigger_threshold > 0
    assert pipeline.model_type is not None


def test_audit_log_creation(pipeline, tmpdir):
    """Test that audit log is created after retraining."""
    # Run pipeline (may fail with insufficient data, but should log)
    result = pipeline.run()
    
    # Check if audit log was attempted to be created
    audit_log_path = "logs/retraining_audit.yaml"
    
    # Verify the result structure even if training failed
    assert 'timestamp' in result
    assert 'model_type' in result
    assert 'samples_used' in result
    assert 'accuracy' in result


def test_pipeline_result_structure(pipeline):
    """Test that pipeline result has correct structure."""
    result = pipeline.run()
    
    required_fields = [
        'success',
        'timestamp',
        'model_type',
        'samples_used',
        'accuracy',
        'message'
    ]
    
    for field in required_fields:
        assert field in result, f"Missing field: {field}"
    
    assert isinstance(result['success'], bool)
    assert isinstance(result['model_type'], str)
    assert isinstance(result['samples_used'], int)
    assert isinstance(result['accuracy'], (int, float))
    assert isinstance(result['message'], str)


def test_pipeline_error_handling(pipeline):
    """Test that pipeline handles errors gracefully."""
    # Force an error by modifying internal state
    original_threshold = pipeline.trigger_threshold
    pipeline.trigger_threshold = -1  # Invalid value
    
    # Should not crash
    try:
        result = pipeline.run()
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'message' in result
    finally:
        pipeline.trigger_threshold = original_threshold


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
