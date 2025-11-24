"""Search Agent - Performs multi-round web searches."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.search import MultiSearch


class SearchAgent(BaseAgent):
    """
    Performs web searches across multiple engines and collects results.
    """
    
    def __init__(self, llm_client=None):
        super().__init__("SearchAgent", llm_client)
        self.search_engine = MultiSearch()
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute web searches based on queries or topics.
        
        Args:
            input_data: {
                "queries": List[str] - Search queries
                "max_results_per_query": int (optional) - Results per query
            }
            
        Returns:
            {
                "search_results": List[Dict] - All search results,
                "total_results": int,
                "queries_executed": List[str]
            }
        """
        self.validate_input(input_data, ["queries"])
        
        queries = input_data["queries"]
        max_results = input_data.get("max_results_per_query", 10)
        
        self.log_progress(f"Executing {len(queries)} searches")
        
        all_results = []
        executed_queries = []
        
        for query in queries:
            self.log_progress(f"Searching: {query}")
            
            try:
                results = await self.search_engine.search(query, max_results)
                
                # Convert to dict format
                for result in results:
                    all_results.append(result.to_dict())
                    
                executed_queries.append(query)
                self.log_progress(f"Found {len(results)} results for: {query}")
                
            except Exception as e:
                self.logger.error(f"Search failed for '{query}': {e}")
                continue
                
        # Deduplicate by URL
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            url = result.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
                
        self.log_progress(f"Total unique results: {len(unique_results)}")
        
        return {
            "search_results": unique_results,
            "total_results": len(unique_results),
            "queries_executed": executed_queries
        }
