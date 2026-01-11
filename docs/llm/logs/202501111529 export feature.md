---
target:
 - apps/backend
 - apps/frontend
---
<new feature>
`Export` section

lo que busco es que haya una seccion de `Export` en la cual yo le meta como input por ejemplo un video mp4
el flujo seria asi:
input -> recibe el video `mp4` -> convierte el video audio `WAV` -> utiliza el modelo de transcripcion local para convertir el audio en texto -> genera un archivo de texto con la transcripcion -> da la opcion de descargar el archivo de texto

esta feature debe funcionar con:
- videos mp4
- audios wav
- audios mp3
- audios m4a
etc
</new feature>

<technical details>
- Preferably use `Rust` in whatever is strictly beneficial.
- Keep in mind and optimize the software considering that it is aimed at people who use `Linux`.
</technical details>

<quality vectors>
- Ensure you have used the state of the art as of 2026.
- Ensure you have used best practices as of 2026.
- Mentally, counterargue and look at what you did with a very skeptical and critical eye.
- Then, once identified, apply the improvements.
- It doesn't have to reek of “coded vibe", It has to look like it was made by a skilled human.
- Use all necessary tools, such as Google Search or web browsing, to fetch content from the web.
</quality vectors>



<performance phylosophy>
Performance is design, and every millisecond counts.

Every update must reduce load time. This is quite complex given the amount of software configurations and code.

We will test many different solutions to speed up the software.

Launching the software should be instantaneous, regardless of the size of the app. This is absolutely necessary for the flow to run smoothly.

Our software has always focused on performance.

There is still more time we can cut. Believe me, every bit of slowness, wherever it occurs, I will not rest until we have completely eliminated it.
</performance phylosophy>
