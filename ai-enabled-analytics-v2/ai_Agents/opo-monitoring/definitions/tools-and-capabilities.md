---
id: opo-investigation-tools
version: "1.0"
kind: tools-and-capabilities
capabilities:
  - id: data_query.read_trends
    operation: read_trends
    permissions: [query:trends:read]
    side_effect: false
    approval_required: false
  - id: data_query.read_wafers
    operation: read_wafers
    permissions: [query:wafers:read]
    side_effect: false
    approval_required: false
  - id: workspace.create
    operation: create_workspace
    permissions: [workspace:create]
    side_effect: true
    approval_required: false
  - id: workspace.add_filters
    operation: add_filters
    permissions: [workspace:write]
    side_effect: true
    approval_required: false
  - id: workspace.register_dataset
    operation: register_dataset
    permissions: [workspace:register]
    side_effect: true
    approval_required: true
approvals:
  default: deny
  required_for: [workspace.register_dataset]
---

# Tools and Capabilities Definition

Capabilities are governed by name, request schema, permissions, approval policy, side-effect flag, owner, and version. Invocation validates the request, checks authorization, records audit events, executes the handler, and records the result.

## OPO Operations

| Operation | Capability | Side effect |
| --- | --- | ---: |
| Read trends | `data_query.read_trends` | No |
| Create workspace | `workspace.create` | Yes |
| Apply filters | `workspace.add_filters` | Yes |
| Register wafer dataset | `workspace.register_dataset` | Yes |
| Read wafer evidence | `data_query.read_wafers` | No |

The agent never accesses databases, HDFS, object storage, or platform APIs directly. Model text cannot bypass permission or approval checks.
