# Narrative provider selection — issue #4

`PITCHVOLT_NARRATIVE_PROVIDER=local` (default) executes deterministic Analyst and Storyteller. Selecting `foundry` wires the optional Microsoft Agent Framework adapter but **does not authorize model inference**: the production configuration always uses `inference_explicitly_approved=False`. Even valid endpoint/model settings cannot activate it; the application publishes an evidence-backed deterministic fallback.

Optional configuration keys: `PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT` and `PITCHVOLT_FOUNDRY_MODEL`. These are not activation or consent mechanisms. Unknown providers and unavailable/disabled Foundry providers fail closed. The fast tactical event stream is independent and unchanged.

Real model usage requires a separately reviewed owner approval, rate and concurrency limits, input and output token limits, retry budgets and aggregate cloud-cost controls. No Azure resources are provisioned or invoked by this change.
