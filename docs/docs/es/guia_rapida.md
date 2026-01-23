---
title: Guía Rápida
description: Resumen ejecutivo de los flujos de dictado y refinado en Voice2Machine.
ai_context: "Guía Rápida, Dictado, Refinado, UX"
depends_on: []
status: stable
---

# 🕹️ Guía Rápida

!!! abstract "Resumen Ejecutivo"
Voice2Machine tiene dos superpoderes: **Dictado** (Voz → Texto) y **Refinado** (Texto → Mejor Texto).

Esta guía visual te ayuda a entender los flujos de trabajo principales para que seas productivo en minutos.

---

## 1. Flujo de Dictado (Voz → Texto)

_Ideal para: Escribir correos, código o mensajes rápidos sin tocar el teclado._

1.  **Foco**: Haz clic en el campo de texto donde quieres escribir.
2.  **Activa el atajo** (Configurable, por defecto ejecutando `v2m-toggle.sh`). Escucharás un sonido de inicio 🔔.
3.  **Habla** claramente. No te preocupes por ser un robot, habla natural.
4.  **Pulsa el atajo de nuevo** para detener. Escucharás un sonido de fin 🔕.
5.  El texto se **pegará automáticamente** en tu campo activo (o quedará en el portapapeles si la auto-escritura está desactivada).

```mermaid
flowchart LR
    A((🎤 INICIO)) -->|Grabar| B{Whisper Local}
    B -->|Transcribir| C[📋 Portapapeles / Pegado]

    style A fill:#ff6b6b,stroke:#333,stroke-width:2px,color:white
    style B fill:#feca57,stroke:#333,stroke-width:2px
    style C fill:#48dbfb,stroke:#333,stroke-width:2px
```

---

## 2. Flujo de Refinado (Texto → IA → Texto)

_Ideal para: Corregir gramática, traducir o dar formato profesional a un borrador sucio._

1.  **Selecciona y Copia** (`Ctrl + C`) el texto que quieres mejorar.
2.  **Activa el atajo de IA** (ejecutando `v2m-llm.sh`).
3.  Espera unos segundos (la IA está pensando 🧠).
4.  El texto mejorado **reemplazará** el contenido de tu portapapeles.
5.  **Pega** (`Ctrl + V`) el resultado.

```mermaid
flowchart LR
    A[📋 Texto Original] -->|Copiar| B((🧠 ATAJO IA))
    B -->|Procesar| C{Local LLM / Gemini}
    C -->|Mejorar| D[✨ Texto Pulido]

    style A fill:#c8d6e5,stroke:#333,stroke-width:2px
    style B fill:#5f27cd,stroke:#333,stroke-width:2px,color:white
    style C fill:#feca57,stroke:#333,stroke-width:2px
    style D fill:#1dd1a1,stroke:#333,stroke-width:2px
```

---

## 💡 Consejos Pro

!!! tip "Mejora tu Precisión" - **Habla fluido**: Whisper entiende mejor el contexto de frases completas que palabras sueltas. - **Hardware**: Un micrófono con cancelación de ruido mejora drásticamente los resultados. - **Configuración**: Puedes ajustar la "temperatura" del LLM en la configuración para hacerlo más creativo o más literal.

!!! success "Privacidad Garantizada"
El **Dictado** es 100% local (ejecutado en tu GPU). El **Refinado** puede ser local (Ollama) o nube (Gemini), tú tienes el control total en la configuración.
