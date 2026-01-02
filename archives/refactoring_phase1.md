# Informe de Refactorización: Fase 1 - Robustez del Sistema

## Introducción

Este documento detalla los cambios arquitectónicos implementados en la primera fase de refactorización del proyecto `whisper-dictation`. El objetivo principal ha sido elevar la **robustez** y la **estabilidad** del sistema, migrando de un enfoque basado en scripts (scripting) a una arquitectura de ingeniería de software profesional.

A continuación, explicamos los cambios técnicos utilizando analogías sencillas sin sacrificar el rigor académico.

## 1. Gestión de Configuración: De la Incertidumbre a la Validación Estricta

### El Cambio
Hemos reemplazado el archivo de configuración estático `config.toml` y su cargador manual por **Pydantic Settings**.

### ¿Por qué? (Explicación Académica)
Anteriormente, el sistema cargaba la configuración como un simple diccionario. Si un valor numérico (ej. `beam_size`) se definía erróneamente como texto, el error solo saltaba en **tiempo de ejecución** (cuando el programa ya estaba trabajando), lo que podía causar caídas inesperadas (crashes).

Al usar **Pydantic**, implementamos **Validación de Tipos en Tiempo de Carga**. El sistema define un "esquema" estricto de qué espera recibir.

### Analogía Sencilla
*   **Antes (config.toml):** Era como ir al aeropuerto y darte cuenta de que olvidaste el pasaporte justo en la puerta de embarque. El error ocurre cuando ya es tarde.
*   **Ahora (Pydantic):** Es como tener una lista de verificación (checklist) obligatoria antes de salir de casa. Si falta el pasaporte, no puedes ni siquiera arrancar el coche. Esto garantiza que, si el programa inicia, tiene todo lo necesario para funcionar correctamente.

## 2. Grabación de Audio: Del Disco Duro a la Memoria RAM

### El Cambio
Hemos eliminado la dependencia de herramientas externas del sistema operativo (`parecord`, `subprocess`) y archivos temporales en disco. Ahora utilizamos **`sounddevice`** y **`numpy`** para capturar audio directamente en la memoria del programa.

### ¿Por qué? (Explicación Académica)
El método anterior generaba una alta **Latencia de E/S (Entrada/Salida)**. Para grabar 5 segundos de audio:
1.  Se iniciaba un proceso externo (costoso para la CPU).
2.  Se escribía el audio en el disco duro (`/tmp/audio.wav`).
3.  Python leía ese archivo del disco para procesarlo.
4.  Se borraba el archivo.

Este ciclo de "Escribir -> Leer -> Borrar" es ineficiente y desgasta innecesariamente el almacenamiento (SSD).

El nuevo método utiliza **Buffers en Memoria**. El audio fluye directamente del micrófono a una estructura de datos en la memoria RAM (un array de NumPy), lista para ser procesada por la IA.

### Analogía Sencilla
*   **Antes (Subprocess + Archivos):** Imagina que para decirle algo a tu compañero, escribes una nota en un papel, la metes en un sobre, la dejas en un buzón, y tu compañero tiene que ir al buzón, abrir el sobre y leerla.
*   **Ahora (Sounddevice + RAM):** Es como hablarle directamente al oído. El mensaje llega de inmediato, sin intermediarios físicos (papel/disco) que ralenticen la comunicación.

## Conclusión

Estos cambios sientan las bases para la siguiente fase: convertir la aplicación en un **Demonio (Servicio Persistente)**. Al tener una configuración validada y un manejo de audio nativo y veloz, podemos construir un sistema que responda en milisegundos, alcanzando el "Estado del Arte" (SOTA) en experiencia de usuario.
