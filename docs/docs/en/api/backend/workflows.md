---
title: Workflows (Orchestration)
description: Documentation of the business workflows that coordinate system features.
ai_context: "Workflows, Orchestration, Recording, LLM"
depends_on: []
status: stable
---

# Workflows (Orchestration)

Workflows are components in charge of coordinating the different system functionalities to complete complex business tasks.

---

## RecordingWorkflow

Manages the entire recording process, from initial capture to final transcription.

::: v2m.orchestration.recording_workflow.RecordingWorkflow
options:
show_source: true

---

## LLMWorkflow

Coordinates text processing using language providers (LLM), including refinement and translation.

::: v2m.orchestration.llm_workflow.LLMWorkflow
options:
show_source: true
