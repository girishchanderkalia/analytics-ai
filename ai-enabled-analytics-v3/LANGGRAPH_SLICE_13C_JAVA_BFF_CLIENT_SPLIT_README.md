# Slice 13C: Java BFF downstream client split

This slice creates two explicit downstream boundaries:

- `RuntimeServiceClient` for chat, resume, and conversation retrieval.
- `AnalyticsFoundationClient` for deterministic trends, distribution, workspace,
  registration, connection-info, and wafer operations.

The deterministic path calls the separately deployable Analytics Foundation API
directly. The agent path calls the central Runtime Service. MCP tools independently
call the same Analytics Foundation API.

## Apply

Extract from the repository root. The target `app-ui/opo-monitoring` directory was
empty in the new architecture, so this slice provides a complete Spring Boot BFF
skeleton rather than adapting unverified current Java files.

## Test

```bash
cd app-ui/opo-monitoring
mvn test
```

## Configuration

```text
RUNTIME_SERVICE_BASE_URL
ANALYTICS_FOUNDATION_BASE_URL
```

The DTO shapes should be checked against the committed Slice 13A OpenAPI contract
before production integration. No credentials or internal LangGraph identifiers
are included in these application DTOs.
