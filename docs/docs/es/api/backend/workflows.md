# Workflows (Orquestación)

Los Workflows son los componentes encargados de coordinar las diferentes funcionalidades del sistema para completar tareas complejas de negocio.

---

## RecordingWorkflow

Gestiona el proceso completo de grabación, desde la captura inicial hasta la transcripción final.

::: v2m.orchestration.recording_workflow.RecordingWorkflow
    options:
      show_source: true

---

## LLMWorkflow

Coordina el procesamiento de texto mediante proveedores de lenguaje (LLM), incluyendo refinamiento y traducción.

::: v2m.orchestration.llm_workflow.LLMWorkflow
    options:
      show_source: true
