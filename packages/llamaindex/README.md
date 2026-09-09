# crawlfox-llamaindex

LlamaIndex reader that loads pages through CrawlFox scrape.

```bash
pip install crawlfox-llamaindex crawlfox-py llama-index-core
```

```python
from crawlfox_llamaindex import CrawlFoxWebReader

reader = CrawlFoxWebReader(mode="scrape")
documents = reader.load_data(url="https://example.com")
print(documents[0].text)
```

Set `CRAWLFOX_API_KEY`.

Docs: https://docs.crawlfox.io
