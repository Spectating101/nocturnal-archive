# Problem+JSON Error Catalog

This document catalogs all error types returned by the Nocturnal Archive API using RFC 7807 Problem+JSON format.

## Error Response Format

All 4xx and 5xx responses follow this structure:

```json
{
  "type": "https://api.nocturnal.dev/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Either ticker or cik must be provided",
  "instance": "X-Request-ID: abc123"
}
```

## Error Types

### Authentication & Authorization

#### `unauthorized`
- **Status**: 401
- **Title**: "Unauthorized"
- **Detail**: "API key is required"
- **When**: Missing or invalid API key

#### `forbidden`
- **Status**: 403
- **Title**: "Forbidden"
- **Detail**: "API key is paused or revoked"
- **When**: Valid but inactive API key

#### `rate-limit-exceeded`
- **Status**: 429
- **Title**: "Rate Limit Exceeded"
- **Detail**: "Rate limit exceeded for this API key"
- **When**: Too many requests per time window

### Validation Errors

#### `validation-error`
- **Status**: 422
- **Title**: "Validation Error"
- **Detail**: Specific validation message
- **When**: Invalid request parameters or body

#### `ungrounded-claim`
- **Status**: 422
- **Title**: "Ungrounded Claim"
- **Detail**: "Numeric claim could not be verified against data"
- **When**: Finance synthesis with unverifiable numeric claims

### Resource Errors

#### `not-found`
- **Status**: 404
- **Title**: "Not Found"
- **Detail**: "Resource not found"
- **When**: Requested resource doesn't exist

#### `service-unavailable`
- **Status**: 503
- **Title**: "Service Unavailable"
- **Detail**: "External service temporarily unavailable"
- **When**: Upstream service (EDGAR, LLM) is down

### Job Queue Errors

#### `queue-full`
- **Status**: 429
- **Title**: "Job queue full"
- **Detail**: "The job queue is currently full. Please try again later."
- **When**: Async job queue is at capacity

#### `too-many-inflight`
- **Status**: 429
- **Title**: "Too many requests in progress"
- **Detail**: "You have reached the per-key concurrency limit. Please retry later."
- **When**: Per-key concurrent job limit exceeded

### Server Errors

#### `internal-error`
- **Status**: 500
- **Title**: "Internal Server Error"
- **Detail**: "An unexpected error occurred"
- **When**: Unhandled server errors

## Headers

All error responses include:

- `X-Request-ID`: Unique request identifier for tracing
- `Retry-After`: Seconds to wait before retrying (for 429/503 responses)
- `Content-Type`: `application/problem+json`

## Examples

### Rate Limit Exceeded
```http
HTTP/1.1 429 Too Many Requests
X-Request-ID: req_123
Retry-After: 60
Content-Type: application/problem+json

{
  "type": "https://api.nocturnal.dev/problems/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Rate limit exceeded for this API key",
  "instance": "X-Request-ID: req_123"
}
```

### Ungrounded Finance Claim
```http
HTTP/1.1 422 Unprocessable Entity
X-Request-ID: req_456
Content-Type: application/problem+json

{
  "type": "https://api.nocturnal.dev/problems/ungrounded-claim",
  "title": "Ungrounded Claim",
  "status": 422,
  "detail": "Numeric claim could not be verified against data",
  "instance": "X-Request-ID: req_456",
  "evidence": {
    "claim": "Revenue increased 15% YoY",
    "available_data": ["Q1: +12%", "Q2: +8%"],
    "verification_status": "insufficient_data"
  }
}
```

### Job Queue Full
```http
HTTP/1.1 429 Too Many Requests
X-Request-ID: req_789
Retry-After: 60
Content-Type: application/problem+json

{
  "type": "https://api.nocturnal.dev/problems/queue-full",
  "title": "Job queue full",
  "status": 429,
  "detail": "The job queue is currently full. Please try again later.",
  "instance": "X-Request-ID: req_789"
}
```

