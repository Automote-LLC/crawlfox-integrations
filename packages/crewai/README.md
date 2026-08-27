# crawlfox-crewai

CrewAI tools for [CrawlFox](https://crawlfox.io) scrape and search.

```bash
pip install crawlfox-crewai crawlfox-py 'crewai[tools]'
```

```python
from crawlfox_crewai import CrawlFoxScrapeWebsiteTool, CrawlFoxSearchTool

scrape_tool = CrawlFoxScrapeWebsiteTool()
search_tool = CrawlFoxSearchTool()
# Pass tools=[scrape_tool, search_tool] to your CrewAI agent
```

Requires `CRAWLFOX_API_KEY` or `api_key=` on each tool.
