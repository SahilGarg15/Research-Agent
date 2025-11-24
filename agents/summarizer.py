"""Summarizer Agent - Extracts and summarizes content from web pages."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.scraper import scrape_multiple
import json


class SummarizerAgent(BaseAgent):
    """
    Scrapes web pages and generates concise summaries of the content.
    """
    
    def __init__(self, llm_client, model_name: str = None):
        super().__init__("SummarizerAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape and summarize content from URLs.
        
        Args:
            input_data: {
                "search_results": List[Dict] - Results from SearchAgent,
                "max_urls": int (optional) - Max URLs to process
            }
            
        Returns:
            {
                "summaries": List[Dict] - Summaries with metadata,
                "total_processed": int,
                "failed_urls": List[str]
            }
        """
        self.validate_input(input_data, ["search_results"])
        
        search_results = input_data["search_results"]
        max_urls = input_data.get("max_urls", 20)
        
        # Extract URLs
        urls = [r["url"] for r in search_results[:max_urls]]
        
        self.log_progress(f"Scraping {len(urls)} URLs")
        
        # Scrape all URLs in parallel
        scraped_data = await scrape_multiple(urls, use_playwright=False)
        
        self.log_progress(f"Successfully scraped {len(scraped_data)} pages")
        
        # Generate summaries
        summaries = []
        failed_urls = []
        
        for data in scraped_data:
            try:
                summary = await self._generate_summary(data)
                summaries.append(summary)
            except Exception as e:
                self.logger.error(f"Failed to summarize {data.get('url')}: {e}")
                failed_urls.append(data.get('url'))
                
        self.log_progress(f"Generated {len(summaries)} summaries")
        
        return {
            "summaries": summaries,
            "total_processed": len(summaries),
            "failed_urls": failed_urls
        }
        
    async def _generate_summary(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concise summary of scraped content using LLM.
        
        Args:
            scraped_data: Scraped webpage data
            
        Returns:
            Summary dictionary
        """
        content = scraped_data.get("content", "")
        title = scraped_data.get("title", "")
        url = scraped_data.get("url", "")
        
        # Truncate content if too long
        if len(content) > 8000:
            content = content[:8000] + "..."
            
        system_prompt = """You are an expert at extracting key information from web content.
Create a concise, factual summary focusing on:
- Main facts and claims
- Statistical data
- Key findings
- Important dates and names

Respond in JSON format:
{
    "summary": "2-3 paragraph summary",
    "key_facts": ["fact 1", "fact 2", ...],
    "statistics": ["stat 1", "stat 2", ...],
    "entities": ["entity 1", "entity 2", ...]
}"""

        user_prompt = f"""Title: {title}
URL: {url}

Content:
{content}

Please provide a structured summary of this content."""

        try:
            response = await self._call_llm(system_prompt, user_prompt)
            result = json.loads(response)
            
            # Add metadata
            result["url"] = url
            result["title"] = title
            result["source_content_length"] = len(content)
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "url": url,
                "title": title,
                "summary": content[:500],
                "key_facts": [],
                "statistics": [],
                "entities": [],
                "source_content_length": len(content)
            }
            
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM."""
        if not self.llm_client:
            raise ValueError("LLM client not configured")
            
        response = await self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
