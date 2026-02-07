import logging
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
try:
    import wikipedia
except ImportError:
    wikipedia = None

logger = logging.getLogger("KnowledgeQA")

class KnowledgeQA:
    def __init__(self):
        pass

    async def answer(self, intent) -> str:
        query = intent.entities.get("query")
        if not query:
            return "I need a query to answer."

        logger.info(f"Answering knowledge query: {query}")
        
        # 1. Try DuckDuckGo
        if DDGS:
            try:
                # Synchronous lib, wrap in logic if needed, but for prototype keep simple
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=1))
                    if results:
                        return f"According to web search: {results[0]['body']}"
            except Exception as e:
                logger.error(f"DDG error: {e}")

        # 2. Try Wikipedia as fallback
        if wikipedia:
            try:
                summary = wikipedia.summary(query, sentences=2)
                return summary
            except Exception as e:
                logger.error(f"Wikipedia error: {e}")

        return "I couldn't find an answer to that."
