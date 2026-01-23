---
title: Glossary
description: Domain and technical terms definitions for Voice2Machine.
status: stable
last_update: 2026-01-23
language: US English
---

# Glossary

This glossary defines technical and domain terms used in Voice2Machine.

## General Terms

### Local-First

Design philosophy where data (audio, text) is processed and stored exclusively on the user's device, without relying on the cloud.

### Daemon

Background process (written in Python) that manages recording, transcription, and communication with the frontend.

### REST API

Communication mechanism between the Daemon (Python) and clients (scripts, frontends). We use FastAPI with standard HTTP endpoints and WebSocket for real-time events.

## Technical Components

### Whisper

Speech recognition model (ASR) developed by OpenAI. Voice2Machine uses `faster-whisper`, an optimized implementation with CTranslate2.

### Workflows

Specialized coordination components that manage the complete lifecycle of a specific task (e.g., `RecordingWorkflow`, `LLMWorkflow`). They replace the old monolithic "Orchestrator" for better traceability and maintainability.

### Features

Self-contained modules that group domain logic and its infrastructure adapters (audio, llm, transcription). They represent the system's core capabilities.

### BackendProvider

Frontend component (React Context) that manages connection with the Daemon and distributes state to the UI.

### TelemetryContext

Sub-context in React optimized for high-frequency updates (GPU metrics, audio levels) to avoid unnecessary re-renders of the main UI.

### Modular Architecture

Evolution of Hexagonal Architecture that organizes code around business modules (Features) and execution flows (Workflows), minimizing coupling and maximizing clarity.
