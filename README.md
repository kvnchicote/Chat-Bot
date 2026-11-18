# Chatbot RAG PDF → Telegram | Proyecto PyCharm

## ¿Qué hace?
Lee **un PDF a la vez**, lo fragmenta con **LangChain**, lo transforma en vectores con **Sentence Transformers**, guarda los vectores en **ChromaDB local**, recupera fragmentos según la pregunta y usa **Gemini** solamente para seleccionar una **cita textual verificable**. En Telegram entrega esa cita con página, o dice que no encuentra respuesta explícita.

> Importante: ningún sistema RAG garantiza interpretación perfecta. La verificación evita que se emitan frases que no estén en el fragmento fuente, pero una cita auténtica podría ser irrelevante. Probá tanto preguntas positivas como negativas.

## PASO 1. Abrir en PyCharm (Windows)
1. Instalá **Python 3.11 de 64 bits** si aún no lo tenés (recomendado; Python 3.12 también puede funcionar).
2. Extraé el ZIP en una carpeta, por ejemplo `C:\Proyectos\Chatbot_RAG_PyCharm`.
3. En PyCharm: **File → Open**, elegí la carpeta `Chatbot_RAG_PyCharm`.
4. En **Settings → Project → Python Interpreter**, creá un **Virtualenv** nuevo basado en Python 3.11. PyCharm puede hacerlo automáticamente.
5. Abrí **Terminal** dentro de PyCharm. Verificá que al principio aparezca `(.venv)`.
6. Ejecutá `python -m pip install --upgrade pip` y luego `python -m pip install -r requirements.txt`.
   **La primera vez puede tardar y descargar el modelo de embeddings**. No requiere GPU.

## PASO 2. Credenciales
1. Hablá con `@BotFather` en Telegram y creá un bot con `/newbot`. Copiá el **token**.
2. Obtené tu **API key de Gemini** en https://aistudio.google.com/apikey (puede tener cuotas y costos según tu cuenta).
3. Duplicá `.env.example` y renombrá la copia a `.env`.
4. Pegá las dos claves en `.env` después de `=`. **Nunca compartas tu `.env`**.
5. Podés dejar `GEMINI_MODEL=gemini-2.5-flash`; si tu cuenta no tiene acceso, cambiá por un modelo de texto disponible en AI Studio.

## PASO 3. Indexar tu PDF
El ZIP incluye `documentos/ejemplo_educacion_financiera.pdf`. En la terminal de PyCharm:

```powershell
python main.py indexar documentos/ejemplo_educacion_financiera.pdf
```

Para usar tu propio archivo: copialo en `documentos/`, luego `python main.py indexar documentos/mi_archivo.pdf`.
**Importante:** cada nueva indexación **reemplaza** el PDF anterior; no mezcla documentos.

## PASO 4. Probar antes de Telegram
```powershell
python main.py preguntar "¿Qué es un plazo fijo?"
python main.py preguntar "¿Qué es una criptomoneda?"
```
La segunda debe contestar que no encuentra esa información si estás usando el PDF de ejemplo. La primera debería citar la definición, siempre que el modelo la seleccione correctamente.

## PASO 5. Ejecutar Telegram
```powershell
python main.py bot
```
Dejá esa terminal abierta y escribile `/start` a tu bot en Telegram. Para ver la fuente usá `/fuente`. Para detenerlo: `Ctrl+C`.

## Configuración en PyCharm con Run Configurations
Run → Edit Configurations → `+` → Python → Script path: seleccioná `main.py` → Working directory: la carpeta del proyecto. Program arguments: `indexar documentos/ejemplo_educacion_financiera.pdf` (para indexar) o `bot` (para iniciar). Podés guardar dos configuraciones independientes.

## Pruebas automatizadas
Instalá pytest con `python -m pip install pytest` y corré:
```powershell
python -m pytest -q
```
No precisan credenciales ni consultan Telegram ni Gemini. Validan la selección y rechazo de citas con respuestas simuladas.

## Cómo funciona RAG en este proyecto
PDF → `pypdf` (extracción por página) → `RecursiveCharacterTextSplitter` (chunks) → `SentenceTransformer` (embeddings) → `ChromaDB` (persistencia) → recuperación semántica (coseno) → Gemini (selector de cita) → verificador literal → Telegram.

### Seguridad y límites
- **No es navegación web ni búsqueda externa**; únicamente Gemini recibe la pregunta y los fragmentos recuperados del PDF. El servicio de Gemini es externo y los textos enviados se procesan según sus términos y políticas. No cargues documentos confidenciales sin autorización.
- PDFs escaneados sin capa de texto necesitan OCR y no están soportados directamente.
- El filtro semántico `MIN_SIMILARITY` puede rechazar respuestas válidas si queda muy alto o traer fragmentos poco relevantes si queda bajo.
- Las citas son literales (pueden contener saltos de línea), por lo que la respuesta es menos conversacional que una IA generativa libre, pero tiene mayor control documental.
- El bot funciona mientras PyCharm/la computadora estén encendidos y el proceso siga en ejecución.
- Si indexás otro PDF con el bot abierto, detené y reiniciá `python main.py bot` para evitar consultas durante el cambio de colección.
- No ejecutes dos instancias del mismo bot simultáneamente: Telegram solo admite un consumidor polling por token.

## Estructura
- `main.py`: interfaz de línea de comandos.
- `ragbot/pdf_index.py`: lectura PDF, segmentación y base vectorial.
- `ragbot/qa.py`: Gemini, criterio estricto y validación literal.
- `ragbot/telegram_app.py`: comandos `/start`, `/fuente`, mensajes.
- `ragbot/config.py`: configuración.
- `ragbot/text_utils.py`: comparación de citas.
- `documentos/`: PDF de ejemplo.
- `tests/`: pruebas sin conexión.
- `.env.example`: plantilla de claves.
- `.gitignore`: protege secretos y cache.

## Solución de errores comunes
- `ModuleNotFoundError`: asegurate de seleccionar el intérprete `.venv` y ejecutar `python -m pip install -r requirements.txt`.
- `Falta configurar ...`: revisá `.env` en la raíz, no `.env.txt`.
- `429 / quota exceeded`: verificá límites o facturación de Gemini; no es un error del PDF.
- `model not found`: cambiá `GEMINI_MODEL` por uno que tu clave pueda usar.
- `PDF no tiene texto extraíble`: archivo escaneado sin OCR.
- `Conflict: terminated by other getUpdates request`: cerrá instancias anteriores del bot.
- Si la descarga del modelo se bloquea, verificá conexión a Hugging Face o política del antivirus.
