# PROMPTS

### What is this folder?

This folder centralizes all `prompts` or text templates used to interact with generative language models (LLM), such as `Google Gemini`.

### What is it for?

Its goal is to decouple prompts from the application's source code. This allows prompts to be edited, improved, and managed by non-developers without modifying the program's logic.

### What can I find here?

- `text files (.txt)`: Each file contains a prompt template for a specific use case. Prompts can include placeholders (e.g., `{text_to_correct}`) that the application dynamically replaces.

### Usage and examples

The application loads these text files and uses them as templates to generate the final prompt sent to the LLM.

- **File example (`correct_text.txt`):**

  ```
  Please correct the grammar and style of the following text, which is a voice transcription. Keep the original meaning but improve clarity and fluency. The text is:
  "{text_to_correct}"
  ```

- **Code usage (conceptual):**

  ```python
  # the application would read the file content
  prompt_template = read_file("prompts/correct_text.txt")

  # and then replace the placeholder with actual text
  final_prompt = prompt_template.format(text_to_correct="hello, howz it going... this is my text.")

  # this final prompt is sent to the LLM
  ```

### How to contribute

1.  **Create a new file**: Add a new `.txt` file with a descriptive name (e.g., `summarize_text.txt`).
2.  **Write the prompt**: Draft the prompt using clear language and placeholders if needed.
3.  **Integrate in the application**: Make sure the new prompt is loaded and used by the corresponding service in the `application` layer.

### FAQs

- **Why not put prompts directly in the code?**
  - Separating them facilitates experimentation and fine-tuning of prompts (`prompt engineering`) without redeploying the application.
- **What format should placeholders have?**
  - Use curly braces `{}` to define placeholders, so they're compatible with Python's string `.format()` method.

### References and resources

- [Prompt design guide (Google AI)](https://ai.google.dev/docs/prompt_guides): Best practices for writing effective prompts.
