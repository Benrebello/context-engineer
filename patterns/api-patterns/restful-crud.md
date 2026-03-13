# RESTful CRUD Blueprint

## Overview
Provide a baseline API contract for CRUD resources including request/response payload guidance, security hooks, and observability recommendations.

## Endpoints
- `GET /resources` – list items with pagination and optional filters.
- `POST /resources` – create item after validating schema and ownership.
- `GET /resources/{id}` – fetch detail with 404 when resource is not found.
- `PUT /resources/{id}` – replace entity using optimistic locking.
- `PATCH /resources/{id}` – partial update enforcing JSON Patch semantics.
- `DELETE /resources/{id}` – soft delete with audit trail recording.

## Implementation Notes
1. Enforce idempotency keys for POST endpoints to avoid duplicates.
2. Emit structured logs (request_id, user_id, resource_id) for every mutation.
3. Wrap all database calls with circuit breaker policies when service dependencies exist.
4. Provide rate limiting headers (`X-RateLimit-Remaining`) through API Gateway configuration.
5. Add OpenAPI examples to help Context Engineer agents generate tasks automatically.
