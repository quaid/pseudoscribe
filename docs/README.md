# PseudoScribe Documentation Index

This folder contains high-level documentation for the PseudoScribe Agent backend and VSCode extension.

## Core Documents

- `API_GAP_ANALYSIS.md`  
  Current implementation vs. stubs for major APIs and infrastructure components.

- `STYLE_API.md`  
  Functional spec for the Style API endpoints (analyze, compare, adapt, check).

- `VSC-004-technical-specification.md`  
  Technical specification for the VSCode extension features and architecture.

## Model / Agent Hand-Off

- `MODEL_TRANSFER_GUIDE.md`  
  **Primary hand-off guide for an MCP-enabled coding model.**
  - Summarizes architecture, Kubernetes/Ollama setup, and testing discipline.  
  - Documents which tests are intentionally RED or skipped and why.  
  - Explains prior debugging decisions (especially around hanging tests).  
  - Lists external resources the user must provide to any new model.

When bringing a new LLM or automated agent into this project, start by reading `MODEL_TRANSFER_GUIDE.md`, then follow the links to the other docs as needed.
