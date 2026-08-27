# crawlfox-llamaindex

LlamaIndex web reader for [CrawlFox](https://crawlfox.io).

```bash
pip install crawlfox-llamaindex crawlfox-py llama-index-core
```

```python
from crawlfox_llamaindex import CrawlFoxWebReader

reader = CrawlFoxWebReader(mode="scrape")
documents = reader.load_data(url="https://example.com")
print(documents[0].text)
```
