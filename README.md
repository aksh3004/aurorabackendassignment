We have a working state of the code where we are not running into any issues.

We chose FastAPI for its high performance and async-first.
We are caching for reduced latency and quicker lookups.
We have an external API that will go into Redis cache and then do an in-memory search.
Cache TTL is set at 60 mins for now.