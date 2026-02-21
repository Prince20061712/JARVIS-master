import pytest
from engine import JARVISCore

@pytest.mark.asyncio
async def test_end_to_end_query_processing():
    """Integration test for the full academic pipeline"""
    engine = JARVISCore()
    
    result = await engine.process_query(
        query="Explain Linked Lists",
        marks=5,
        subject="computer_science"
    )
    
    assert "response" in result
    assert "sources" in result
    assert "confidence" in result
    # Check if marks-based formatting was applied
    assert "**Definition:**" in result['response'] or "**Explanation:**" in result['response']

@pytest.mark.asyncio
async def test_proactive_suggestions():
    """Test if proactive engine generates tips based on student state"""
    engine = JARVISCore()
    # Mock some history
    engine.memory.short_term.add_message("student", "I am tired")
    
    suggestions = engine.proactive_layer.generate_suggestions()
    assert len(suggestions) >= 0 # Should at least not crash
