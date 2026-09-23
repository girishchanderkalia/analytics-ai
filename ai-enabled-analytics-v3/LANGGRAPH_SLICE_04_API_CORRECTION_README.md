# Slice 04: bulk registration API correction

Replaces the incomplete draft/import API with trusted-application endpoints:

- POST /v1/applications/{application_id}/agents:bulk-register
- GET /v1/applications/{application_id}/agents

No draft management, ZIP upload, repository scanning, or end-user registration.
