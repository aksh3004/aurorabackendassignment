## Commits
- Commit 1: Initial commit with in-memory search
- Commit 2: Redis cache implementation for faster responses


## API endpoints
- `GET /search?q=<query>&page=<page>&limit=<limit>` Search the messages


## Current implementation

- We chose FastAPI for its high performance and async-first.
- We are caching for reduced latency and quicker lookups.
- We have an external API that will go into Redis cache and then do an in-memory search.

- First request could be around 400-500ms due to cache miss or cold caches.
- Subsequent requests are closer to 50ms.

## Design Notes

### Alternative approaches

I considered several alternatives to the solution I eventually provided.

```
Request -> API -> Filter results -> Response
```
The simplest way to get the freshest results was to query the API directly. The drawback was that each request would add about 100ms of latency, since there was no caching. We could not meet the <100ms SLA.

```
API -> Elasticsearch indexing -> Search -> Response
```
I thought it was overkill for this scope. With Elasticseach, we get optimized search capabilities, but the complexity of this was not justified.

```
API -> In-Memory Dict -> Search -> Response
```
This was where I was going ahead during my first commit. It was simple and fast but we lost the data on restart each time. Difficult to scale and not distributed. So, we evolved with the use of Redis in the next commit.

```
API -> Redis Cache -> Search -> Response
```
Using Redis Cache, we get fast responses. It is easy to scale horizontally and provides good performance without increasing complexity.

### Reduce latency to 30ms
```
Query caching
```
We could cache popular query results separately that could improve performance for such repeated queries.

```
Indexed search
```
We could build an inverted index on cache load that massively improves lookup time from O(n) to O(1).


## Deployment using Cloud Run (Google Cloud)
gcloud run deploy aurora-backend \
    --source . \
    --platform managed \
    --region europe-west1 \
    --memory 512Mi \
    --set-env-vars="REDIS_URL=redis://localhost:6379"


## Testing
curl "http://localhost:8000/search?q=test&page=1&page_size=10"