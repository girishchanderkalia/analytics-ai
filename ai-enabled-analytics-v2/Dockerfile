# Build context MUST be the repository root (one level above this folder),
# because this service reads AnalyticsFoundation/mock_data and
# ApplicationUI/opo_monitoring_ui/static in place (read-only), matching local
# dev (see PLAN.md's "Non-negotiable constraints"). Build with:
#   cd ai_enabled_analytics   # repo root, NOT ai-enabled-analytics-v2
#   docker build -f ai-enabled-analytics-v2/Dockerfile -t iact/analytics-workflow-runtime:latest .
FROM python:3.12-slim

WORKDIR /app
COPY ai-enabled-analytics-v2/requirements.txt ai-enabled-analytics-v2/requirements.txt
RUN pip install --no-cache-dir -r ai-enabled-analytics-v2/requirements.txt

COPY AnalyticsFoundation/mock_data AnalyticsFoundation/mock_data
COPY ApplicationUI/opo_monitoring_ui/static ApplicationUI/opo_monitoring_ui/static
COPY ai-enabled-analytics-v2 ai-enabled-analytics-v2

ENV PYTHONPATH=/app/ai-enabled-analytics-v2
WORKDIR /app/ai-enabled-analytics-v2

EXPOSE 8100
CMD ["uvicorn", "application_ui.opo_monitoring_service.api:app", "--host", "0.0.0.0", "--port", "8100"]
