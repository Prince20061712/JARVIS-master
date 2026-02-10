#!/usr/bin/env python3
"""
Enhanced Knowledge System Module
Provides access to global knowledge, current affairs, and real-time information
"""

import wikipedia
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import json
import datetime
from typing import Dict, List, Optional, Any
import os
from dataclasses import dataclass

@dataclass
class KnowledgeResponse:
    source: str
    content: str
    found: bool
    timestamp: str
    confidence: float
    additional_info: Dict[str, Any]

class EnhancedKnowledgeSystem:
    def __init__(self, use_web_search: bool = True):
        self.wiki_lang = "en"
        wikipedia.set_lang(self.wiki_lang)
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.use_web_search = use_web_search
        self.current_year = datetime.datetime.now().year
        
        # For current affairs - RSS feed sources
        self.news_sources = {
            "reuters": "https://www.reuters.com/subjects/technology/rss.xml",
            "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "al_jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "ap_news": "https://apnews.com/rss",
            "cnn": "http://rss.cnn.com/rss/edition.rss"
        }
        
        # Knowledge domains for better categorization
        self.knowledge_domains = {
            "history": ["history", "historical", "past", "century", "war", "king", "queen", "empire"],
            "science": ["science", "scientific", "physics", "chemistry", "biology", "research", "discovery"],
            "technology": ["tech", "technology", "computer", "software", "ai", "artificial intelligence", "internet"],
            "current_affairs": ["news", "current", "recent", "today", "latest", "2024", "2025", "update"],
            "geography": ["country", "city", "capital", "river", "mountain", "continent", "map"],
            "politics": ["government", "president", "prime minister", "election", "law", "policy"],
            "economics": ["economy", "economic", "market", "stock", "trade", "gdp", "inflation"],
            "sports": ["sports", "football", "cricket", "basketball", "olympics", "tournament"]
        }
    
    def get_comprehensive_knowledge(self, query: str, include_current: bool = True) -> KnowledgeResponse:
        """Get comprehensive knowledge including current affairs"""
        
        # Analyze query type
        query_type = self._analyze_query_type(query)
        
        # For current affairs queries, prioritize news sources
        if include_current and ("current" in query_type or self._is_current_affairs_query(query)):
            current_info = self.get_current_affairs(query)
            if current_info and current_info.found:
                return current_info
        
        # Try multiple sources
        sources_to_try = [
            ("Wikipedia", self._search_wikipedia_enhanced),
            ("Web Search", self._search_web),
            ("Knowledge Base", self._search_predefined_knowledge)
        ]
        
        all_results = []
        for source_name, search_func in sources_to_try:
            try:
                result = search_func(query)
                if result and result.found:
                    all_results.append(result)
                    # If we have high confidence, return immediately
                    if result.confidence > 0.8:
                        return result
            except Exception as e:
                print(f"Error with {source_name}: {e}")
                continue
        
        # Return the best result
        if all_results:
            # Sort by confidence and return the best
            all_results.sort(key=lambda x: x.confidence, reverse=True)
            return all_results[0]
        
        # Fallback to basic web search
        return self._create_fallback_response(query)
    
    def _search_wikipedia_enhanced(self, query: str) -> Optional[KnowledgeResponse]:
        """Enhanced Wikipedia search with better error handling"""
        try:
            # Clean and optimize query
            clean_query = self._optimize_wikipedia_query(query)
            
            # Try to get page directly first
            try:
                page = wikipedia.page(clean_query, auto_suggest=False)
                summary = wikipedia.summary(clean_query, sentences=5, auto_suggest=False)
                
                # Get additional page info
                categories = page.categories[:5] if hasattr(page, 'categories') else []
                url = page.url if hasattr(page, 'url') else ""
                
                return KnowledgeResponse(
                    source="Wikipedia",
                    content=summary,
                    found=True,
                    timestamp=datetime.datetime.now().isoformat(),
                    confidence=0.9,
                    additional_info={
                        "categories": categories,
                        "url": url,
                        "page_title": page.title
                    }
                )
                
            except wikipedia.DisambiguationError as e:
                # Handle disambiguation
                options = e.options[:3]
                option_summaries = []
                for option in options:
                    try:
                        opt_summary = wikipedia.summary(option, sentences=2, auto_suggest=False)
                        option_summaries.append(f"{option}: {opt_summary}")
                    except:
                        continue
                
                if option_summaries:
                    content = f"Multiple topics match your query:\n\n" + "\n\n".join(option_summaries)
                    return KnowledgeResponse(
                        source="Wikipedia",
                        content=content,
                        found=True,
                        timestamp=datetime.datetime.now().isoformat(),
                        confidence=0.7,
                        additional_info={"disambiguation_options": options}
                    )
                    
            except wikipedia.PageError:
                # Try search
                search_results = wikipedia.search(clean_query)
                if search_results:
                    try:
                        summary = wikipedia.summary(search_results[0], sentences=4, auto_suggest=False)
                        return KnowledgeResponse(
                            source="Wikipedia",
                            content=summary,
                            found=True,
                            timestamp=datetime.datetime.now().isoformat(),
                            confidence=0.8,
                            additional_info={"search_results": search_results[:3]}
                        )
                    except:
                        pass
            
            return None
            
        except Exception as e:
            print(f"Wikipedia error: {e}")
            return None
    
    def get_current_affairs(self, query: str = None, limit: int = 5) -> KnowledgeResponse:
        """Get current affairs and recent news"""
        try:
            # Try to fetch from news APIs or RSS feeds
            news_items = self._fetch_news_feeds(limit)
            
            if query:
                # Filter news items based on query
                filtered_items = []
                query_terms = query.lower().split()
                for item in news_items:
                    if any(term in item['title'].lower() or term in item.get('description', '').lower() 
                           for term in query_terms if len(term) > 3):
                        filtered_items.append(item)
                
                if filtered_items:
                    content = self._format_news_items(filtered_items)
                    return KnowledgeResponse(
                        source="Current Affairs",
                        content=content,
                        found=True,
                        timestamp=datetime.datetime.now().isoformat(),
                        confidence=0.85,
                        additional_info={"items": filtered_items}
                    )
            
            # Return general news if no specific query or no matches
            if news_items:
                content = self._format_news_items(news_items[:limit])
                return KnowledgeResponse(
                    source="Current Affairs",
                    content=f"Recent news and current affairs:\n\n{content}",
                    found=True,
                    timestamp=datetime.datetime.now().isoformat(),
                    confidence=0.8,
                    additional_info={"items": news_items[:limit]}
                )
            
        except Exception as e:
            print(f"Error fetching current affairs: {e}")
        
        return KnowledgeResponse(
            source="Current Affairs",
            content="Unable to fetch current affairs at the moment.",
            found=False,
            timestamp=datetime.datetime.now().isoformat(),
            confidence=0.0,
            additional_info={}
        )
    
    def _fetch_news_feeds(self, limit: int = 5) -> List[Dict]:
        """Fetch news from RSS feeds (simplified version)"""
        news_items = []
        
        # Simplified - in production, use RSS parsing libraries or news APIs
        # This is a mock implementation
        mock_news = [
            {
                "title": "Global Summit Addresses Climate Change Initiatives",
                "description": "World leaders gather to discuss new climate policies...",
                "source": "Reuters",
                "date": "2024-01-15",
                "category": "Environment"
            },
            {
                "title": "Breakthrough in Quantum Computing Announced",
                "description": "Researchers achieve quantum supremacy with new processor...",
                "source": "BBC Technology",
                "date": "2024-01-14",
                "category": "Technology"
            },
            {
                "title": "Economic Forum Predicts Global Growth Trends",
                "description": "Annual economic report released with projections for 2024...",
                "source": "AP News",
                "date": "2024-01-13",
                "category": "Economics"
            }
        ]
        
        return mock_news[:limit]
    
    def _search_web(self, query: str) -> Optional[KnowledgeResponse]:
        """Web search using DuckDuckGo or similar"""
        if not self.use_web_search:
            return None
            
        try:
            # DuckDuckGo HTML search (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            response = self.session.get(search_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract first result
                results = soup.find_all('a', class_='result__url')
                if results:
                    # Get snippet from first result
                    result_snippets = soup.find_all('a', class_='result__snippet')
                    if result_snippets:
                        snippet = result_snippets[0].get_text(strip=True)
                        return KnowledgeResponse(
                            source="Web Search",
                            content=snippet[:500],  # Limit length
                            found=True,
                            timestamp=datetime.datetime.now().isoformat(),
                            confidence=0.7,
                            additional_info={"method": "duckduckgo"}
                        )
            
        except Exception as e:
            print(f"Web search error: {e}")
        
        return None
    
    def _search_predefined_knowledge(self, query: str) -> Optional[KnowledgeResponse]:
        """Search predefined knowledge base (can be expanded)"""
        # This can be expanded with a local knowledge database
        knowledge_base = {
            "current president of united states": {
                "content": "As of 2024, the President of the United States is Joe Biden.",
                "confidence": 0.95,
                "category": "politics"
            },
            "largest country by area": {
                "content": "Russia is the largest country by area, covering approximately 17.1 million square kilometers.",
                "confidence": 0.98,
                "category": "geography"
            },
            "artificial intelligence": {
                "content": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn.",
                "confidence": 0.9,
                "category": "technology"
            }
        }
        
        query_lower = query.lower()
        for key, info in knowledge_base.items():
            if key in query_lower:
                return KnowledgeResponse(
                    source="Knowledge Base",
                    content=info["content"],
                    found=True,
                    timestamp=datetime.datetime.now().isoformat(),
                    confidence=info["confidence"],
                    additional_info={"category": info["category"]}
                )
        
        return None
    
    def _analyze_query_type(self, query: str) -> List[str]:
        """Analyze what type of knowledge the query is asking for"""
        query_lower = query.lower()
        detected_types = []
        
        for domain, keywords in self.knowledge_domains.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_types.append(domain)
        
        return detected_types if detected_types else ["general"]
    
    def _is_current_affairs_query(self, query: str) -> bool:
        """Check if query is about current affairs"""
        current_indicators = ["current", "recent", "today", "latest", "new", "now", "2024", "2025"]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in current_indicators)
    
    def _optimize_wikipedia_query(self, query: str) -> str:
        """Optimize query for Wikipedia search"""
        # Remove question words and common verbs
        stopwords = ["what", "who", "where", "when", "why", "how", "is", "are", 
                    "do", "does", "did", "tell", "me", "about", "explain", "describe"]
        
        words = query.lower().split()
        clean_words = [w for w in words if w not in stopwords and len(w) > 2]
        
        if not clean_words:
            return query
        
        return " ".join(clean_words).title()
    
    def _format_news_items(self, items: List[Dict]) -> str:
        """Format news items for display"""
        formatted = []
        for i, item in enumerate(items, 1):
            formatted.append(f"{i}. {item['title']}")
            if 'description' in item:
                formatted.append(f"   {item['description']}")
            if 'source' in item and 'date' in item:
                formatted.append(f"   Source: {item['source']} | Date: {item['date']}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _create_fallback_response(self, query: str) -> KnowledgeResponse:
        """Create a fallback response when no information is found"""
        return KnowledgeResponse(
            source="System",
            content=f"I couldn't find specific information about '{query}'. This could be due to the query being too recent, too specific, or outside my current knowledge scope. Try rephrasing or asking about a more established topic.",
            found=False,
            timestamp=datetime.datetime.now().isoformat(),
            confidence=0.0,
            additional_info={"suggestion": "Try rephrasing your query"}
        )
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        return {
            "current_year": self.current_year,
            "knowledge_domains": list(self.knowledge_domains.keys()),
            "news_sources": list(self.news_sources.keys()),
            "timestamp": datetime.datetime.now().isoformat()
        }


# Example usage with integration into your AI bot
class AIBotWithKnowledge:
    def __init__(self):
        self.knowledge_system = EnhancedKnowledgeSystem()
        self.conversation_history = []
    
    def respond_to_query(self, user_query: str) -> str:
        """Main method to handle user queries with knowledge integration"""
        
        # Store in history
        self.conversation_history.append({
            "user": user_query,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Get knowledge response
        knowledge = self.knowledge_system.get_comprehensive_knowledge(user_query)
        
        # Format response
        if knowledge.found:
            response = f"Based on information from {knowledge.source}:\n\n"
            response += knowledge.content
            response += f"\n\n[Information retrieved: {knowledge.timestamp.split('T')[0]}]"
        else:
            response = knowledge.content
        
        return response
    
    def get_current_affairs_summary(self, category: str = None) -> str:
        """Get a summary of current affairs"""
        query = category if category else "current news"
        result = self.knowledge_system.get_current_affairs(query)
        return result.content


if __name__ == "__main__":
    print("Testing Enhanced Knowledge System...")
    
    # Test the system
    bot = AIBotWithKnowledge()
    
    test_queries = [
        "Who is the current president of the United States?",
        "Tell me about artificial intelligence",
        "What's happening in current news?",
        "Who is Elon Musk?",
        "What is quantum computing?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        response = bot.respond_to_query(query)
        print(f"Response: {response[:300]}...")  # Limit output for demo
    
    # Get system info
    print(f"\n\nSystem Statistics: {bot.knowledge_system.get_statistics()}")