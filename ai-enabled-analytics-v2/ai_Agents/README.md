# Agent Catalog

Each application agent owns one directory under `ai_Agents/`. The OPO agent is defined entirely by reviewed Markdown:

```text
ai_Agents/
└── opo-monitoring/
    └── definitions/
```

Add future agents as sibling directories. `agent_runtime/` contains shared model execution, contract generation, workflow interpretation, routing, approval, capability, and definition-loading infrastructure. Agent directories contain only declarative definitions.
