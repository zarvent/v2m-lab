# PROMPTS

### ¿qué es esta carpeta?
esta carpeta centraliza todos los `prompts` o plantillas de texto que se utilizan para interactuar con modelos de lenguaje generativo (llm), como `google gemini`.

### ¿para qué sirve?
su objetivo es desacoplar los prompts del código fuente de la aplicación. esto permite que los prompts puedan ser editados, mejorados y gestionados por personas no desarrolladoras sin necesidad de modificar la lógica del programa.

### ¿qué puedo encontrar aquí?
*   `archivos de texto (.txt)`: cada archivo contiene una plantilla de prompt para un caso de uso específico. los prompts pueden incluir placeholders (e.g., `{texto_a_corregir}`) que la aplicación reemplaza dinámicamente.

### uso y ejemplos
la aplicación carga estos archivos de texto y los utiliza como plantillas para generar el prompt final que se envía al llm.

*   **ejemplo de archivo (`correct_text.txt`):**
    ```
    por favor, corrige la gramática y el estilo del siguiente texto, que es una transcripción de voz. mantén el significado original pero mejora la claridad y fluidez. el texto es:
    "{texto_a_corregir}"
    ```

*   **uso en el código (conceptual):**
    ```python
    # la aplicación leería el contenido del archivo
    prompt_template = read_file("prompts/correct_text.txt")

    # y luego reemplazaría el placeholder con el texto real
    final_prompt = prompt_template.format(texto_a_corregir="hola, q tal... este es mi texto.")

    # este prompt final se envía al llm
    ```

### cómo contribuir
1.  **crea un nuevo archivo**: añade un nuevo archivo `.txt` con un nombre descriptivo (e.g., `summarize_text.txt`).
2.  **escribe el prompt**: redacta el prompt utilizando un lenguaje claro y placeholders si es necesario.
3.  **integra en la aplicación**: asegúrate de que el nuevo prompt sea cargado y utilizado por el servicio correspondiente en la capa de `application`.

### faqs o preguntas frecuentes
*   **¿por qué no poner los prompts directamente en el código?**
    *   separarlos facilita la experimentación y el ajuste fino de los prompts (`prompt engineering`) sin tener que volver a desplegar la aplicación.
*   **¿qué formato deben tener los placeholders?**
    *   utiliza llaves `{}` para definir placeholders, de modo que sean compatibles con el método `.format()` de las cadenas de `python`.

### referencias y recursos
*   [guía de diseño de prompts (google ai)](https://ai.google.dev/docs/prompt_guides): buenas prácticas para escribir prompts efectivos.
