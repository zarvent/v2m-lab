# 🕹️ GUÍA RÁPIDA

> **Resumen Ejecutivo**: Voice2Machine tiene dos superpoderes: **Dictado** (Voz → Texto) y **Refinado** (Texto → Mejor Texto).

Esta guía visual te ayuda a entender los flujos de trabajo principales.

---

## 1. Flujo de Dictado (Voz → Texto)

*Ideal para: Escribir correos, código o mensajes rápidos sin tocar el teclado.*

1.  **Activa el atajo** (ej. `Super + V`). Escucharás un sonido de inicio 🔔.
2.  **Habla** claramente.
3.  **Pulsa el atajo de nuevo** para detener. Escucharás un sonido de fin 🔕.
4.  El texto aparecerá mágicamente en tu **portapapeles** (listo para pegar `Ctrl + V`).

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
flowchart LR
    A((🎤 INICIO)) -->|Grabar| B{Whisper Local}
    B -->|Transcribir| C[📋 Portapapeles]

    style A fill:#ff6b6b,stroke:#333,stroke-width:2px,color:white
    style B fill:#feca57,stroke:#333,stroke-width:2px
    style C fill:#48dbfb,stroke:#333,stroke-width:2px
```

---

## 2. Flujo de Refinado (Texto → IA → Texto)

*Ideal para: Corregir gramática, traducir o dar formato profesional a un borrador.*

1.  **Copia algo de texto** (`Ctrl + C`).
2.  **Activa el atajo de IA** (ej. `Super + G`).
3.  Espera unos segundos (la IA está pensando 🧠).
4.  El texto mejorado **reemplaza** lo que tenías en el portapapeles. ¡Pégalo!

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
flowchart LR
    A[📋 Texto Original] -->|Copiar| B((🧠 ATAJO IA))
    B -->|Procesar| C{Gemini / LLM}
    C -->|Mejorar| D[✨ Texto Pulido]

    style A fill:#c8d6e5,stroke:#333,stroke-width:2px
    style B fill:#5f27cd,stroke:#333,stroke-width:2px,color:white
    style C fill:#feca57,stroke:#333,stroke-width:2px
    style D fill:#1dd1a1,stroke:#333,stroke-width:2px
```

---

## 💡 Consejos Pro

- **Habla fluido**: Whisper entiende mejor frases completas que palabras sueltas.
- **Micro**: Un buen micrófono mejora drásticamente la precisión.
- **Privacidad**: Recuerda que el **Dictado** es 100% local. El **Refinado** usa la nube (Google Gemini) solo si tú lo activas.
