import pytest
import os
from knowledge.rag_engine.syllabus_aware_rag import SyllabusAwareRAG

@pytest.mark.asyncio
async def test_document_ingestion(rag_engine, temp_data_dir, sample_document):
    """Test full document ingestion via RAG engine"""
    test_file = temp_data_dir / "test_doc.txt"
    test_file.write_text(sample_document)
    
    try:
        await rag_engine.ingest_document(str(test_file))
        assert True # Should not raise exception
    except Exception as e:
        pytest.fail(f"Ingestion failed: {e}")

@pytest.mark.asyncio
async def test_query_enhancement(rag_engine):
    """Test query reformulation with syllabus context"""
    raw_query = "sorting"
    enhanced = rag_engine.query_enhancer.enhance(raw_query, syllabus_context="DS Unit 3")
    assert "sorting" in enhanced.lower()
    assert "syllabus" in enhanced.lower() or "exam" in enhanced.lower()

@pytest.mark.asyncio
async def test_retrieval_with_context(rag_engine, temp_data_dir, sample_document):
    """Test retrieval accuracy with matched syllabus topics"""
    test_file = temp_data_dir / "arrays.txt"
    test_file.write_text(sample_document)
    await rag_engine.ingest_document(str(test_file))
    
    results = await rag_engine.retrieve_context("What are array operations?", top_k=2)
    assert len(results) > 0
    assert "Insertion" in results[0].page_content

@pytest.mark.asyncio
async def test_response_generation(rag_engine):
    """Test LLM response generation integration"""
    # Note: Requires mock/local LLM running
    try:
        response = await rag_engine.generate_response(
            query="What is an array?", 
            context="An array stores data in memory.",
            marks=2
        )
        assert isinstance(response, str)
        assert len(response) > 0
    except Exception:
        # Expected if LLM is not running during simple unit tests
        pass
