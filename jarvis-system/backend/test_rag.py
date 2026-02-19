import sys
import os

# Add parent dir to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.knowledge.rag_engine import EngineeringRAGEngine

def test_rag():
    print("Testing RAG Engine...")
    rag = EngineeringRAGEngine()
    
    # 1. Ingest
    print("\n1. Ingesting Document...")
    # Convert our text file to a "mock" PDF ingestion (or just read text)
    # Since our RAG engine expects PDFs (fitz), let's just make a dummy PDF or modify RAG to handle txt.
    # Actually, let's just use the `text` file path but make the RAG engine robust enough to read .txt for testing.
    
    # For now, let's just manually ingest text into the collection for testing without the PDF requirement
    rag.collection.add(
        documents=["Newton's Second Law: F=ma. Acceleration is directly proportional to Force."],
        metadatas=[{"source": "test_doc", "page": 1, "subject": "applied_physics"}],
        ids=["test_1"]
    )
    print("✅ Ingested test chunk.")

    # 2. Retrieve
    query = "What is Newton's Second Law?"
    print(f"\n2. Retrieving for: '{query}'")
    context = rag.retrieve_context(query)
    
    print("\n--- RETRIEVED CONTEXT ---")
    print(context)
    print("-------------------------")
    
    if "F=ma" in context:
        print("\n✅ TEST PASSED: Setup is working.")
    else:
        print("\n❌ TEST FAILED: Retrieval missed key info.")

if __name__ == "__main__":
    test_rag()
