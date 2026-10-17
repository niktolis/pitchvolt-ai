# Foundry specialist client configuration — issue #4

The approved architecture assigns **independent FoundryChatClient instances** to each configured specialist. Analyst targets GPT-5 mini Global Standard and Storyteller targets GPT-4o mini Regional Standard. Editorial is optional, has no approved model assignment, and **must not be scheduled** until a reviewed escalation policy, model and additional budget are approved. The deterministic Orchestrator and Verifier remain model-free.

The adapter accepts `FoundryConfig(model_deployment=..., storyteller_model_deployment=..., editorial_model_deployment=...)`. The historic `model_deployment` parameter remains the Analyst deployment; Storyteller defaults to it for backwards-compatible single-model baselines. When specified, the Editorial deployment creates a separately configured agent/client but adds no execution or billing calls. A single credential object is shared across clients, while the clients and prompts are role-specific. The existing two-call budget remains fixed; this is not authorization for a third inference call.

**Current production mode remains fail-closed**: `narrative_stream._provider_roles` sets `inference_explicitly_approved=False`, so constructing or authenticating a Foundry client is blocked. The tests that construct clients use in-memory SDK doubles, not Azure endpoints. No deployments, inference, quota, subscription settings or credentials are modified.

## Integration still pending

- Model-specific request settings, output/reasoning budgets and tracked per-role usage.
- Approved deployment provisioning, followed by a bounded connectivity and tool-loop test.
- Conditional Editorial invocation and cost/quality justification.
- Measured baseline versus heterogeneous latency, grounding, tokens and cost.
