# 🕹️ GUÍA RÁPIDA

esta guía te muestra cómo usar las funciones principales de la herramienta de dictado

### FLUJO DE DICTADO (VOZ → TEXTO)

este es el flujo principal para capturar tu voz y convertirla en texto

1.  **activa el atajo de teclado** para iniciar la grabación
2.  **habla claramente** en tu micrófono
3.  **vuelve a pulsar el atajo** para detener la grabación
4.  el texto transcrito **se copiará automáticamente** a tu portapapeles

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
flowchart TD
    subgraph VOZ A TEXTO
        A["🎤 ATAJO 1<br/>_inicia grabación_"] --> B{"transcribe con WHISPER"}
        B --> C["📋 COPIADO<br/>_texto en portapapeles_"]
    end

    style A fill:#8EBBFF,stroke:#333,stroke-width:2px
    style B fill:#FFD68E,stroke:#333,stroke-width:2px
    style C fill:#A9E5BB,stroke:#333,stroke-width:2px
```

### FLUJO DE REFINADO (TEXTO → TEXTO MEJORADO)

si la transcripción necesita correcciones o un formato específico puedes usar el flujo de refinado

1.  **copia el texto** que deseas mejorar a tu portapapeles
2.  **activa el segundo atajo de teclado**
3.  el texto será procesado por el LLM de GOOGLE GEMINI
4.  el texto mejorado **reemplazará el contenido** de tu portapapeles

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
flowchart TD
    subgraph TEXTO A TEXTO MEJORADO
        A["📋 COPIAS TEXTO"] --> B["🧠 ATAJO 2<br/>_inicia refinado_"]
        B --> C{"procesa con LLM<br/>_GOOGLE GEMINI_"}
        C --> D["📋 REEMPLAZA<br/>_texto mejorado en portapapeles_"]
    end

    style A fill:#F2C2E0,stroke:#333,stroke-width:2px
    style B fill:#8EBBFF,stroke:#333,stroke-width:2px
    style C fill:#FFD68E,stroke:#333,stroke-width:2px
    style D fill:#A9E5BB,stroke:#333,stroke-width:2px
```
