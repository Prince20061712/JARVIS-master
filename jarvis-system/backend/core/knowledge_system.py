#!/usr/bin/env python3
"""
Knowledge System Module
Provides access to global knowledge via Wikipedia and Web Search
"""

import wikipedia
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

class KnowledgeSystem:
    def __init__(self):
        self.wiki_lang = "en"
        wikipedia.set_lang(self.wiki_lang)
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
    
    def get_general_knowledge(self, query):
        """Get general knowledge about a query"""
        # Try Wikipedia first as it's the most reliable source for "knowledge"
        wiki_result = self.search_wikipedia(query)
        if wiki_result:
            return {
                "source": "Wikipedia",
                "content": wiki_result,
                "found": True
            }
        
        # Fallback to web search snippet (simulated/basic)
        # Note: robust web search usually requires an API key (Google/Bing).
        # We will attempt a direct scrape of a search engine or duckduckgo as a fallback,
        # but for reliability without keys, Wikipedia is our primary knowledge base.
        return {
            "source": "None",
            "content": "I couldn't find specific information about that in my knowledge base.",
            "found": False
        }

    def search_wikipedia(self, query, sentences=3):
        """Search Wikipedia for a query"""
        try:
            # First clean the query
            clean_query = self._clean_query(query)
            
            # Search for pages
            search_results = wikipedia.search(clean_query)
            
            if not search_results:
                return None
            
            # Get summary of the first result
            # auto_suggest=False is CRITICAL here because the library sometimes
            # "corrects" valid titles into invalid ones (e.g. "Elon Musk" -> "e on musk")
            try:
                summary = wikipedia.summary(search_results[0], sentences=sentences, auto_suggest=False)
                return summary
            except wikipedia.DisambiguationError as e:
                # If ambiguous, try the first option
                try:
                    summary = wikipedia.summary(e.options[0], sentences=sentences, auto_suggest=False)
                    return f"Referencing {e.options[0]}: {summary}"
                except:
                    return None
            except wikipedia.PageError:
                return None
                
        except Exception as e:
            print(f"Wikipedia error: {e}")
            return None
    
    def _clean_query(self, query):
        """Clean query for better search results"""
        # Remove common question words
        stopwords = ["what", "who", "where", "when", "why", "how", "is", "are", "do", "does", "tell", "me", "about", "give", "knowledge", "world"]
        query_words = query.lower().split()
        clean_words = [w for w in query_words if w not in stopwords]
        return " ".join(clean_words)

if __name__ == "__main__":
    ks = KnowledgeSystem()
    print("Testing Knowledge System...")
    q = "Who is Elon Musk"
    print(f"Query: {q}")
    print(f"Result: {ks.get_general_knowledge(q)}")
