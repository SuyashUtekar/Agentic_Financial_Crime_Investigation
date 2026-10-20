# Documentation index

This documentation describes the current MVP implementation. The product plan in the repository root describes the wider roadmap; it is not a statement that every planned capability has been implemented.

| Read this | When you need |
| --- | --- |
| [Case walkthrough](CASE_WALKTHROUGH.md) | A plain-language explanation of what the system investigates and what each result means |
| [Project report](PROJECT_REPORT.md) | A formal report with abstract, problem statement, objectives, methodology, architecture, limitations, and future work |
| [Agentic workflow](AGENTIC_WORKFLOW.md) | The LangGraph nodes, conditional routes, bounded tools, Gemini planning guardrails, and resume behavior |
| [Architecture](ARCHITECTURE.md) | How the frontend, API, analytics, optional LLM, evidence checks, and checkpointing work together |
| [Operations guide](OPERATIONS.md) | Setup, Gemini secrets, uv commands, tests, API routes, and troubleshooting |

## Important boundary

This is a synthetic-data demonstration. It supports an analyst's investigation by organizing evidence and highlighting configured indicators. It does not determine that a person committed financial crime and cannot file a regulatory report, freeze funds, or take action on an account.
