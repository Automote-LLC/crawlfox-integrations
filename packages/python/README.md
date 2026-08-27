# crawlfox-py

```bash
pip install crawlfox-py
```

```python
from crawlfox import CrawlFox

client = CrawlFox(api_key="cfx_...")
page = client.scrape("https://example.com", formats=["markdown"])
print(page["data"]["markdown"])
```

See the [CrawlFox docs](https://docs.crawlfox.io) for integration guides.
