# PROMPTS

### ¿Qué es esta carpeta?

Esta carpeta centraliza todos los `prompts` o plantillas de texto que se utilizan para interactuar con modelos de lenguaje generativo (LLM), como `Google Gemini`.

### ¿Para qué sirve?

Su objetivo es desacoplar los prompts del código fuente de la aplicación. Esto permite que los prompts puedan ser editados, mejorados y gestionados por personas no desarrolladoras sin necesidad de modificar la lógica del programa.

### ¿Qué puedo encontrar aquí?

- `archivos de texto (.txt)`: Cada archivo contiene una plantilla de prompt para un caso de uso específico. Los prompts pueden incluir placeholders (ej. `{texto_a_corregir}`) que la aplicación reemplaza dinámicamente.

### Uso y ejemplos

La aplicación carga estos archivos de texto y los utiliza como plantillas para generar el prompt final que se envía al LLM.

- **Ejemplo de archivo (`correct_text.txt`):**

  ```
  Por favor, corrige la gramática y el estilo del siguiente texto, que es una transcripción de voz. Mantén el significado original pero mejora la claridad y fluidez. El texto es:
  "{texto_a_corregir}"
  ```

- **Uso en el código (conceptual):**

  ```python
  # la aplicación leería el contenido del archivo
  prompt_template = read_file("prompts/correct_text.txt")

  # y luego reemplazaría el placeholder con el texto real
  final_prompt = prompt_template.format(texto_a_corregir="hola, q tal... este es mi texto.")

  # este prompt final se envía al LLM
  ```

### Cómo contribuir

1.  **Crea un nuevo archivo**: Añade un nuevo archivo `.txt` con un nombre descriptivo (ej. `summarize_text.txt`).
2.  **Escribe el prompt**: Redacta el prompt utilizando un lenguaje claro y placeholders si es necesario.
3.  **Integra en la aplicación**: Asegúrate de que el nuevo prompt sea cargado y utilizado por el servicio correspondiente en la capa de `application`.

### FAQs o preguntas frecuentes

- **¿Por qué no poner los prompts directamente en el código?**
  - Separarlos facilita la experimentación y el ajuste fino de los prompts (`prompt engineering`) sin tener que volver a desplegar la aplicación.
- **¿Qué formato deben tener los placeholders?**
  - Utiliza llaves `{}` para definir placeholders, de modo que sean compatibles con el método `.format()` de las cadenas de Python.

### Referencias y recursos

- [Guía de diseño de prompts (Google AI)](https://ai.google.dev/docs/prompt_guides): Buenas prácticas para escribir prompts efectivos.
