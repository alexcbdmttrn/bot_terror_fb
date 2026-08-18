from datetime import datetime
import json
import os
import random
import re
import sys
import time
import requests
import asyncio
import edge_tts
import numpy as np
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from cloudinary.uploader import upload
import cloudinary
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import io
import glob
import atexit

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL_TERROR = os.getenv("MAKE_WEBHOOK_URL_TERROR")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

ESTADO_FILE = "estado_terror.json"

# Configurar Cloudinary
CLOUDINARY_DISPONIBLE = False
if all([CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET]):
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=CLOUD_API_KEY,
        api_secret=CLOUD_API_SECRET
    )
    CLOUDINARY_DISPONIBLE = True
    print("✅ Cloudinary configurado correctamente")
else:
    print("⚠️ Cloudinary no configurado. No se podrán subir placeholders ni videos.")

# ================================================================
# 🎤 VOCES NEURALES EDGE-TTS
# ================================================================
VOCES_DISPONIBLES = [
    {"voz": "es-MX-JorgeNeural", "velocidad": "+10%", "tono": "-2Hz"},
    {"voz": "es-MX-DaliaNeural", "velocidad": "+10%", "tono": "+0Hz"},
    {"voz": "es-ES-AlvaroNeural", "velocidad": "+10%", "tono": "-3Hz"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+10%", "tono": "+1Hz"},
    {"voz": "es-CO-GonzaloNeural", "velocidad": "+10%", "tono": "-1Hz"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+10%", "tono": "-1Hz"},
    {"voz": "es-AR-ElenaNeural", "velocidad": "+10%", "tono": "+2Hz"},
    {"voz": "es-AR-DiegoNeural", "velocidad": "+10%", "tono": "-2Hz"},
    {"voz": "es-US-AlonsoNeural", "velocidad": "+10%", "tono": "-1Hz"},
    {"voz": "es-US-PalomaNeural", "velocidad": "+10%", "tono": "-1Hz"},
    {"voz": "es-PE-CamilaNeural", "velocidad": "+10%", "tono": "+0Hz"},
    {"voz": "es-PE-AlexNeural", "velocidad": "+10%", "tono": "-1Hz"},
    {"voz": "es-CL-LorenzoNeural", "velocidad": "+10%", "tono": "-2Hz"},
    {"voz": "es-CL-CatalinaNeural", "velocidad": "+10%", "tono": "+1Hz"},
]
CONFIG_VOZ_ACTUAL = random.choice(VOCES_DISPONIBLES)

# ================================================================
# 🎵 MÚSICA DE FONDO (desde archivos locales)
# ================================================================
def descargar_musica_fondo():
    mp3_files = glob.glob("*.mp3") + glob.glob("**/*.mp3", recursive=True)
    mp3_files = [f for f in mp3_files if not f.startswith("narracion_") and not f.startswith("audio_")]
    if mp3_files:
        fondo_path = random.choice(mp3_files)
        print(f"🎵 Música seleccionada al azar: {fondo_path}")
        return fondo_path
    else:
        print("⚠️ No se encontraron archivos .mp3 en el repositorio. Se usará solo narración.")
        return None

# ================================================================
# 🖼️ GENERAR IMAGEN DE RESPALDO
# ================================================================
def generar_imagen_respaldo(width=1080, height=1350):
    try:
        img = Image.new("RGB", (width, height), (15, 15, 30))
        path = f"respaldo_{random.randint(1000,9999)}.jpg"
        img.save(path)
        if CLOUDINARY_DISPONIBLE:
            result = upload(path, resource_type="image", public_id=f"respaldo_{datetime.now().strftime('%Y%m%d_%H%M%S')}", overwrite=True)
            url = result.get('secure_url')
            os.remove(path)
            return url
        else:
            return f"https://via.placeholder.com/{width}x{height}/1a1a1a/303060"
    except:
        return f"https://via.placeholder.com/{width}x{height}/1a1a1a/303060"

# ================================================================
# FUNCIONES AUXILIARES
# ================================================================
def cargar_temas():
    try:
        with open("temas_2000.json", "r", encoding="utf-8") as f:
            temas = json.load(f)
            if isinstance(temas, list) and len(temas) > 0:
                return temas
            raise ValueError("El archivo no contiene una lista válida")
    except Exception as e:
        print(f"⚠️ Error cargando temas: {e}")
        sys.exit(1)

def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "publicados" not in data:
                data["publicados"] = []
            if "ultimo_tema" not in data:
                data["ultimo_tema"] = ""
            return data
    except:
        return {"publicados": [], "ultimo_tema": ""}

def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    print(f"✅ Estado guardado correctamente en {ESTADO_FILE}")

def obtener_tema_no_repetido(temas, estado):
    publicados = set(estado.get("publicados", []))
    ultimo_tema = estado.get("ultimo_tema", "")
    disponibles = [t for t in temas if t not in publicados and t != ultimo_tema]
    if not disponibles:
        disponibles = [t for t in temas if t != ultimo_tema]
    if not disponibles:
        disponibles = temas
    return random.choice(disponibles)

def limpiar_texto_para_imagen(texto):
    texto = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF\U000024C2-\U0001F251]', '', texto)
    texto = re.sub(r'#\w+', '', texto)
    texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
    return texto.strip()

# ================================================================
# 🧹 LIMPIAR TEXTO PARA TTS (conversión de números)
# ================================================================
def convertir_numero_a_palabras(numero):
    unidades = ['cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
    decenas = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
    especiales = {11: 'once', 12: 'doce', 13: 'trece', 14: 'catorce', 15: 'quince', 16: 'dieciséis', 17: 'diecisiete', 18: 'dieciocho', 19: 'diecinueve'}
    try:
        num = int(numero)
        if 0 <= num <= 9:
            return unidades[num]
        elif 10 <= num <= 19:
            return especiales.get(num, decenas[num//10] + ' y ' + unidades[num%10])
        elif 20 <= num <= 99:
            if num % 10 == 0:
                return decenas[num//10]
            else:
                return decenas[num//10] + ' y ' + unidades[num%10]
        else:
            return str(num)
    except:
        return str(num)

def limpiar_caracteres_para_tts(texto):
    texto = re.sub(r'\b(\d{1,2})\b', lambda m: convertir_numero_a_palabras(m.group(1)), texto)
    texto = re.sub(r'[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\-\'\"]', ' ', texto)
    texto = re.sub(r'[\U0001F600-\U0001F64F]', '', texto)
    texto = re.sub(r'[\U0001F300-\U0001F5FF]', '', texto)
    texto = re.sub(r'[\U0001F680-\U0001F6FF]', '', texto)
    texto = re.sub(r'[\U0001F900-\U0001F9FF]', '', texto)
    texto = re.sub(r'[\U00002700-\U000027BF]', '', texto)
    texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def limpiar_texto_para_audio(texto):
    texto = re.sub(r"imagen_prompt.*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"prompt.*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r'[\{\}\[\]]', ' ', texto)
    texto = texto.replace('"', "'")
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def descargar_imagen_con_retry(url, intentos=3, timeout=30):
    for i in range(intentos):
        try:
            r = requests.get(url, timeout=timeout, verify=False)
            if r.status_code == 200:
                return r.content
        except Exception as e:
            print(f"   ⚠️ Error descargando imagen (intento {i+1}): {e}")
            time.sleep(2)
    return None

# ================================================================
# 💀 CTA FINAL
# ================================================================
CTAS_FINALES = [
    "\n\n💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇",
    "\n\n👻 ¿Conoces una leyenda similar? Compártela en los comentarios. 👇",
    "\n\n🌙 ¿Qué harías tú en esta situación? Te leemos en comentarios. 👇",
    "\n\n👁️ ¿Crees que estas historias son reales? Déjanos tu opinión. 👇",
    "\n\n🔮 ¿Has vivido algo sobrenatural? Cuéntanos tu experiencia. 👇",
    "\n\n😱 ¿Te atreverías a visitar este lugar? Cuéntanos. 👇",
    "\n\n🌑 ¿Conoces más historias así? Compártelas en comentarios. 👇",
    "\n\n💬 Tu historia puede ser la siguiente. Cuéntanos. 👇",
]

# ================================================================
# 🧑 DETECTAR PERSONAJE Y ÉPOCA
# ================================================================
def detectar_personaje_y_epoca(texto_historia):
    prompt = f"""Analiza el siguiente relato en primera persona y extrae las características físicas del protagonista y la época/año en que ocurre.

REGLAS:
- Si el texto menciona explícitamente el género (hombre/mujer), úsalo. Si no, infiere por el contexto.
- Si menciona edad o época, calcula la edad actual aproximada.
- Si menciona oficio o vestimenta, inclúyelo.
- Identifica el AÑO o ÉPOCA en que sucede la historia. Si no se menciona, infiere uno lógico basado en el contexto.
- Devuelve SOLO un JSON válido con estos campos:
  - "genero": "hombre" o "mujer"
  - "edad_aprox": número
  - "ocupacion": breve descripción
  - "descripcion_breve": 1 línea en inglés describiendo al personaje
  - "anio": número de 4 dígitos (ej. 1985, 2004, 2023)

REGLA CRÍTICA: Si no hay información suficiente, devuelve valores por defecto:
- genero: "hombre"
- edad_aprox: 35
- ocupacion: "persona común"
- descripcion_breve: "a 35-year-old Mexican person, contemporary clothing"
- anio: 2015

RELATO:
\"\"\"
{texto_historia[:1500]}
\"\"\"

Devuelve SOLO el JSON, sin explicaciones, sin markdown.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 300,
        "response_format": {"type": "json_object"}
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        respuesta = r.json()["choices"][0]["message"]["content"].strip()
        respuesta = re.sub(r"```json\s*", "", respuesta)
        respuesta = re.sub(r"```\s*", "", respuesta)
        data = json.loads(respuesta, strict=False)
        print(f"🧑 Personaje detectado: {data.get('genero', '?')}, {data.get('edad_aprox', '?')} años | 🗓️ Época: {data.get('anio', '?')}")
        return data
    except Exception as e:
        print(f"⚠️ Error detectando personaje: {e}. Usando valores por defecto.")
        return {
            "genero": "hombre",
            "edad_aprox": 35,
            "ocupacion": "persona común",
            "descripcion_breve": "a 35-year-old Mexican person, contemporary clothing",
            "anio": 2015
        }

# ================================================================
# 🎭 DETECTOR DE ENTIDAD (para variar visuales)
# ================================================================
def detectar_tipo_entidad(tema):
    t = tema.lower()
    if any(w in t for w in ["vampiro", "vampira", "chupasangre", "chupacabras"]):
        return "vampiro"
    if any(w in t for w in ["lobo", "nahual", "licántropo", "hombre lobo", "bestia"]):
        return "lobo"
    if any(w in t for w in ["monstruo", "criatura", "engendro", "demonio", "diablo"]):
        return "monstruo"
    if any(w in t for w in ["bruja", "hechicera", "nahuala", "aquelarre"]):
        return "bruja"
    if any(w in t for w in ["fantasma", "espíritu", "aparición", "sombra", "llorona", "ánima", "espectro"]):
        return "fantasma"
    return "misterio"

DIRECTRICES_ENTIDAD = {
    "vampiro": "an elegant tall vampire figure in dark Victorian clothing, pale skin, faintly glowing crimson eyes, standing among shadows at distance",
    "lobo": "a massive black wolf silhouette with glowing amber eyes emerging from dense fog at distance",
    "monstruo": "a towering dark creature silhouette with faint glowing eyes hidden between shadows at distance",
    "bruja": "a hunched witch silhouette in black robes with faint green glowing eyes at distance",
    "fantasma": "a translucent ghostly figure in white-gray with soft spectral glow at distance",
    "misterio": "a faint dark silhouette far in the background, barely visible between shadows",
}

# ================================================================
# 🎨 GENERAR PROMPT DE IMAGEN CON DEEPSEEK (VERSIÓN MUY NEUTRAL)
# ================================================================
def generar_prompt_imagen(historia, tema, personaje):
    tipo = detectar_tipo_entidad(tema)
    entidad = DIRECTRICES_ENTIDAD[tipo]
    
    genero = personaje.get("genero", "hombre")
    edad = personaje.get("edad_aprox", 35)
    anio = personaje.get("anio", 2015)
    
    if anio >= 2015:
        epoca_mod = "present day contemporary era (2020s), modern vehicles, modern architecture, smartphones, LED lighting"
    elif anio >= 2000:
        epoca_mod = f"early 2000s era (year {anio}), 2000s cars, CRT TVs, flip phones, no smartphones"
    elif anio >= 1990:
        epoca_mod = f"1990s era (year {anio}), 90s cars, analog tech, 90s fashion, no modern devices"
    elif anio >= 1980:
        epoca_mod = f"1980s era (year {anio}), 80s cars, vintage clothing, older buildings, analog technology"
    else:
        epoca_mod = f"past era (year {anio}), classic cars, period clothing, aged architecture, no modern devices"

    if genero == "mujer":
        sujeto_humano = f"a {edad}-year-old Mexican woman"
    else:
        sujeto_humano = f"a {edad}-year-old Mexican man"

    prompt_deepseek = f"""Eres un EXPERTO EN FOTOGRAFÍA CINEMATOGRÁFICA. Tu tarea es generar un prompt de imagen en INGLÉS para una foto VERTICAL (4:5) de una escena que represente la siguiente historia, pero de forma SUTIL y ATMOSFÉRICA.

HISTORIA:
\"\"\"
{limpiar_texto_para_imagen(historia)[:400]}
\"\"\"

REGLAS ABSOLUTAMENTE ESTRICTAS:
1. La imagen debe parecer una fotografía REALISTA, no una ilustración.
2. Enfócate en el ENTORNO: arquitectura, calles, paisajes, objetos. La historia sucede en un lugar; muestra ese lugar.
3. Si el personaje aparece, debe ser muy pequeño (menos del 20% del encuadre), de espaldas o a lo lejos. 
4. ESTILO: fotografía nocturna, luces tenues, niebla ligera, colores fríos (azulados, grises, o cálidos si es atardecer).
5. PROHIBIDO mencionar: ghost, terror, horror, paranormal, supernatural, haunted, creepy, scary, evil, demon, devil, death, blood, gore, wound, kill, murder, etc. En su lugar, usa palabras como: atmosphere, moody, dim light, foggy, mysterious (pero sin miedo).
6. La imagen debe ser apta para todo público, sin elementos violentos ni aterradores.
7. Época exacta: {epoca_mod}. Muestra vehículos, edificios y vestimenta de esa época.

Ejemplo de prompt BUENO:
"A cinematic vertical 4:5 photograph of a quiet street in a small Mexican town at night, with a vintage car parked under a streetlamp, soft fog, and a person walking away in the distance. Dark blue and amber tones, realistic photography."

Ejemplo de prompt MALO:
"A ghost appears in the dark, terrifying shadows, horror movie style."

Devuelve SOLO el prompt en inglés, sin explicaciones, directo y concreto.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_deepseek}],
        "temperature": 0.6,
        "max_tokens": 350,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        # Limpiar posibles etiquetas de markdown
        prompt_imagen = re.sub(r'["\']', '', prompt_imagen)
        prompt_imagen = prompt_imagen.strip()
        if not prompt_imagen.endswith('.'):
            prompt_imagen += '.'
        # Añadir sufijo seguro
        prompt_imagen += " vertical 4:5, realistic photography, no horror, no violence, no ghosts, no blood, no text."
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return "Vertical 4:5 cinematic photograph of an empty street at night with fog and lamplight, realistic style, no horror, no ghosts, no text."

# ================================================================
# 🛡️ FILTRAR Y REESCRIBIR PROMPT PARA AGNES (MUY AGRESIVO)
# ================================================================
def reescribir_prompt_seguro(prompt):
    """Reemplaza palabras 'peligrosas' por sinónimos inofensivos."""
    reemplazos = {
        r'\bghost\b': 'silhouette',
        r'\bphantom\b': 'figure',
        r'\bspecter\b': 'shadow',
        r'\bapparition\b': 'form',
        r'\bhorror\b': 'atmosphere',
        r'\bterror\b': 'mystery',
        r'\bhaunted\b': 'old',
        r'\bspooky\b': 'moody',
        r'\bcreepy\b': 'dimly lit',
        r'\bscary\b': 'dark',
        r'\bevil\b': 'unsettling',
        r'\bdemon\b': 'shadow',
        r'\bdevil\b': 'figure',
        r'\bdeath\b': 'stillness',
        r'\bkill\b': 'silence',
        r'\bmurder\b': 'incident',
        r'\bblood\b': 'darkness',
        r'\bgore\b': 'red tones',
        r'\bwound\b': 'mark',
        r'\binjury\b': 'scar',
        r'\bparanormal\b': 'mysterious',
        r'\bsupernatural\b': 'unexplained',
        r'\bfear\b': 'tension',
        r'\bpanic\b': 'intensity',
        r'\bscream\b': 'echo',
        r'\bshriek\b': 'sound',
        r'\bhowl\b': 'wind',
        r'\battack\b': 'silence',
        r'\bassault\b': 'incident',
        r'\bvicious\b': 'intense',
        r'\bmenacing\b': 'dark',
        r'\bthreatening\b': 'ominous',
    }
    prompt_limpio = prompt
    for patron, sustituto in reemplazos.items():
        prompt_limpio = re.sub(patron, sustituto, prompt_limpio, flags=re.IGNORECASE)
    # Eliminar múltiples espacios
    prompt_limpio = re.sub(r'\s+', ' ', prompt_limpio).strip()
    # Asegurar que no contenga palabras prohibidas residuales
    palabras_prohibidas = [
        "gore", "blood", "bleeding", "wound", "injury", "mutilated", "disfigured",
        "corpse", "dead", "death", "dying", "kill", "murder", "assassination",
        "suicide", "self-harm", "torture", "violent", "brutality", "massacre",
        "slaughter", "decapitation", "hanging", "suffocation", "drowning",
        "burned", "burnt", "scar", "deformed", "demonic", "satanic", "occult",
        "ritual", "sacrifice", "cult", "possessed", "exorcism", "evil", "devil",
        "hell", "damnation", "apocalypse", "dystopian", "post-apocalyptic",
        "wasteland", "decay", "rotten", "mold", "fungus", "infected", "plague",
        "virus", "zombie", "undead", "ghoul", "skeleton", "skull", "bone",
        "grave", "tomb", "crypt", "cemetery", "morgue", "autopsy", "cadaver",
        "bloodstained", "crimson", "red liquid", "dark mist", "shadow figure",
        "ghost", "phantom", "apparition", "specter", "horror", "terror",
        "frightening", "scary", "creepy", "sinister", "menacing", "threatening",
        "gloom", "grim", "dread", "fear", "panic", "scream", "shriek", "howl",
        "attack", "assault", "stabbing", "strangle", "choke", "cut", "slash",
        "dead body", "murdered", "vicious", "haunted", "spooky",
        "paranormal", "supernatural", "eerie", "uncanny", "macabre", "ghastly"
    ]
    for palabra in palabras_prohibidas:
        prompt_limpio = re.sub(rf'\b{palabra}\b', '', prompt_limpio, flags=re.IGNORECASE)
    prompt_limpio = re.sub(r'\s+', ' ', prompt_limpio).strip()
    if len(prompt_limpio.split()) < 8:
        # Si quedó muy corto, usar uno genérico
        return "Vertical 4:5 cinematic photograph of a quiet urban street at night with fog and streetlights, realistic style, no text."
    return prompt_limpio

def filtrar_prompt_para_agnes(prompt):
    """Aplica el reemplazo de sinónimos y elimina palabras prohibidas."""
    return reescribir_prompt_seguro(prompt)

# ================================================================
# 📖 GENERAR HISTORIA COMPLETA
# ================================================================
def generar_historia_completa(tema):
    prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR un testimonio COMPLETO y AUTOCONCLUSIVO sobre:
"{tema}"

🚨 REGLAS ESTRICTAS:
- Ambientación: Mención EXACTA del lugar en México.
- Narración en PRIMERA PERSONA, como si la persona te lo estuviera contando a ti.
- El narrador debe tener un PERFIL ÚNICO Y DIVERSO en cada historia. Varía el género, la edad (entre 20 y 70 años) y el oficio. NO repitas el mismo perfil en historias consecutivas.
- Extensión: ENTRE 300 y 340 palabras.
- ESTRUCTURA OBLIGATORIA en PÁRRAFOS (cada párrafo separado por una línea en blanco):
  1. GANCHO inicial impactante (1-2 frases)
  2. CONTEXTO: quién es el narrador, dónde y cuándo ocurrió
  3. DESARROLLO: los hechos sobrenaturales paso a paso, con detalles sensoriales (2-3 párrafos)
  4. CLÍMAX: el momento más intenso (1 párrafo)
  5. DESENLACE: cómo terminó todo y qué le quedó al narrador (1 párrafo)
- Tono NATURAL Y COLOQUIAL, como alguien contando su experiencia real.
- Detalles específicos: nombres de lugares reales, años concretos, oficios reales.

Formato EXACTO de salida:
🌙 **[Título descriptivo del suceso]**

[Primer párrafo]

[Segundo párrafo]

[... y así sucesivamente, separados por línea en blanco]

(NO agregues hashtags ni llamadas a comentar, yo los agregaré después)
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 1200,
    }
    for intento in range(3):
        try:
            print(f"📝 Intento {intento+1}/3 generando historia...")
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            resultado = r.json()["choices"][0]["message"]["content"].strip()
            if "[Error" in resultado or len(resultado) < 200:
                raise ValueError("Respuesta muy corta o con error")
            lineas = resultado.split('\n')
            texto_narrativo = '\n'.join(linea for linea in lineas if linea.strip() and not linea.strip().startswith('🌙'))
            palabras = len(texto_narrativo.split())
            print(f"   📊 Palabras generadas: {palabras}")
            if palabras < 250:
                print(f"   ⚠️ Muy corto ({palabras} palabras). Reintentando...")
                raise ValueError("Historia demasiado corta")
            return resultado
        except Exception as e:
            print(f"❌ Intento {intento+1} falló: {e}")
            if intento < 2:
                time.sleep(5)
    print("❌ No se pudo generar la historia después de 3 intentos.")
    return None

# ================================================================
# 💀 AGREGAR CTA + HASHTAGS + LEYENDA IA
# ================================================================
def agregar_cta_final(texto):
    texto = re.sub(r'#\w+', '', texto)
    patrones = [
        r"💀.*?comentarios.*?",
        r"👇.*?comentarios.*?",
        r"👻.*?comentarios.*?",
        r"🌙.*?comentarios.*?",
        r"👁️.*?comentarios.*?",
        r"🔮.*?experiencia.*?",
    ]
    for patron in patrones:
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE | re.DOTALL)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    cta = random.choice(CTAS_FINALES)
    hashtags = "\n\n#LeyendasMexicanas #Terror #Misterio #Paranormal #Mexico"
    leyenda_ia = "\n\n_Imágenes generadas con IA_"
    return texto.strip() + cta + hashtags + leyenda_ia

# ================================================================
# 📝 GENERAR RESUMEN PARA REEL
# ================================================================
def generar_resumen_reel(historia_completa):
    prompt = f"""Resume el siguiente relato de terror en un texto CORTO y ATMOSFÉRICO de EXACTAMENTE 100 palabras, ideal para un Reel de Facebook.

REGLAS:
- Mantén el suspenso y el tono de terror.
- Incluye el lugar y el nombre del narrador si aparece.
- Debe ser un resumen que enganche al espectador a querer leer el post completo.
- Extensión: 100 palabras exactas (aproximadamente).

RELATO COMPLETO:
\"\"\"
{historia_completa}
\"\"\"

Devuelve SOLO el resumen, sin títulos, sin hashtags, sin llamados a la acción.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        resumen = r.json()["choices"][0]["message"]["content"].strip()
        palabras = resumen.split()
        if len(palabras) > 110:
            resumen = " ".join(palabras[:100]) + "..."
        return resumen
    except Exception as e:
        print(f"❌ Error generando resumen: {e}")
        palabras = historia_completa.split()
        return " ".join(palabras[:100]) + "..."

def dividir_resumen_en_segmentos(resumen, num_segmentos=3):
    oraciones = re.split(r'(?<=[.!?])\s+', resumen)
    if len(oraciones) >= num_segmentos:
        segmentos = []
        oraciones_por_seg = len(oraciones) // num_segmentos
        for i in range(num_segmentos):
            inicio = i * oraciones_por_seg
            fin = (i + 1) * oraciones_por_seg if i < num_segmentos - 1 else len(oraciones)
            segmentos.append(" ".join(oraciones[inicio:fin]))
        return segmentos
    else:
        palabras = resumen.split()
        if len(palabras) < num_segmentos * 5:
            return [resumen]
        segmentos = []
        palabras_por_seg = len(palabras) // num_segmentos
        for i in range(num_segmentos):
            inicio = i * palabras_por_seg
            fin = (i + 1) * palabras_por_seg if i < num_segmentos - 1 else len(palabras)
            segmentos.append(" ".join(palabras[inicio:fin]))
        return segmentos

# ================================================================
# 🖼️ GENERAR IMAGEN CON AGNES (CON REINTENTOS Y REWRITE)
# ================================================================
def generar_imagen_agnes(prompt, width=1080, height=1350, intentos=6, espera_segundos=15):
    prompt_original = prompt
    for intento in range(1, intentos + 1):
        print(f"🎨 Intento {intento}/{intentos} generando imagen...")
        # En el primer intento, usar prompt original; si falla, ir reescribiendo
        if intento > 1:
            prompt = reescribir_prompt_seguro(prompt_original)
        if intento > 3:
            # Si sigue fallando, usar uno genérico y muy neutral
            prompt = "Vertical 4:5 cinematic photograph of a quiet urban street at night with fog and streetlights, realistic photography, no violence, no ghosts, no text."

        prompt_limpio = prompt[:800]
        url = "https://apihub.agnes-ai.com/v1/images/generations"
        headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
        negative = (
            "close-up face, portrait, headshot, person filling frame, "
            "deformed face, disfigured, mutated, bad anatomy, extra limbs, "
            "extra fingers, asymmetrical eyes, malformed features, uncanny valley, "
            "gaunt, emaciated, ugly, grotesque, gore, blood, "
            "dilapidated, decrepit, run-down, crumbling, cracked walls, peeling paint, "
            "moldy, musty, dusty, cobwebs, "
            "sepia tone, monochrome, black and white, film grain, "
            "duplicate people, cloned faces, multiple subjects, "
            "dual face, split face, two faces, double face, mirror face, two heads, "
            "cloned face, duplicate person, twin, twins, doppelganger, siamese, conjoined, "
            "low quality, blurry, oversharpened, over-saturated, "
            "text, letters, words, captions, subtitles, titles, watermarks, logos"
        )
        payload = {
            "model": "agnes-image-2.1-flash",
            "prompt": prompt_limpio,
            "negative_prompt": negative,
            "width": width,
            "height": height,
            "num_images": 1,
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]
                print(f"✅ Imagen generada (intento {intento})")
                return image_url
            else:
                error_msg = response.text[:200]
                print(f"❌ Error en Agnes: {response.status_code} - {error_msg}")
                if "content_policy_violation" in error_msg:
                    print(f"⚠️ Violación de política (intento {intento}). Reescribiendo prompt...")
                    time.sleep(espera_segundos)
                    continue
                else:
                    time.sleep(espera_segundos)
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            time.sleep(espera_segundos)
    print("⚠️ Agnes falló tras todos los intentos. Se usará imagen de respaldo.")
    return None

# ================================================================
# 🎤 GENERAR AUDIO CON EDGE-TTS
# ================================================================
def generar_audio_edge_tts(texto, index):
    global CONFIG_VOZ_ACTUAL
    
    texto_limpio = limpiar_caracteres_para_tts(texto)
    texto_limpio = limpiar_texto_para_audio(texto_limpio)
    
    if len(texto_limpio) < 30:
        print(f"⚠️ Texto corto ({len(texto_limpio)} caracteres). Rellenando...")
        texto_limpio = "Esa noche el silencio era tan denso que podía cortarse con un cuchillo. El miedo lo envolvía todo."
    
    filename = f"narracion_{index}.mp3"
    
    voz = CONFIG_VOZ_ACTUAL["voz"]
    rate = CONFIG_VOZ_ACTUAL["velocidad"]
    pitch = CONFIG_VOZ_ACTUAL["tono"]
    
    print(f"🎤 Generando narración con voz neural: {voz} (velocidad {rate})")
    
    for intento in range(3):
        try:
            async def _generar():
                communicate = edge_tts.Communicate(
                    text=texto_limpio,
                    voice=voz,
                    rate=rate,
                    pitch=pitch
                )
                await communicate.save(filename)
            
            asyncio.run(_generar())
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"✅ Audio generado con {voz}")
                return filename
        except Exception as e:
            print(f"❌ Falló intento {intento+1} con {voz}: {e}")
            if intento < 2:
                time.sleep(2 * (intento + 1))
    
    print("🔄 Probando otras voces neurales como fallback...")
    for voz_config in VOCES_DISPONIBLES:
        if voz_config["voz"] == voz:
            continue
        voz_fb = voz_config["voz"]
        rate_fb = voz_config["velocidad"]
        pitch_fb = voz_config["tono"]
        try:
            async def _generar_fb():
                communicate = edge_tts.Communicate(
                    text=texto_limpio,
                    voice=voz_fb,
                    rate=rate_fb,
                    pitch=pitch_fb
                )
                await communicate.save(filename)
            asyncio.run(_generar_fb())
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"✅ Fallback exitoso con {voz_fb}")
                CONFIG_VOZ_ACTUAL = voz_config
                return filename
        except Exception as e:
            print(f"❌ Fallback con {voz_fb} falló: {e}")
    
    print("⚠️ Todas las voces neurales fallaron. Usando gTTS como respaldo...")
    try:
        tts = gTTS(text=texto_limpio, lang='es', slow=True)
        tts.save(filename)
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"✅ Audio generado con gTTS (fallback)")
            return filename
    except Exception as e:
        print(f"❌ gTTS también falló: {e}")
    
    return None

# ================================================================
# 🎥 ZOOM LENTO
# ================================================================
def aplicar_zoom_lento(clip, zoom_final=1.10):
    dur = clip.duration
    if dur is None or dur <= 0:
        return clip
    
    def efecto(get_frame, t):
        frame = get_frame(t)
        factor = 1.0 + (zoom_final - 1.0) * (t / dur)
        h, w = frame.shape[:2]
        new_h, new_w = int(h * factor), int(w * factor)
        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        img = img.crop((left, top, left + w, top + h))
        return np.array(img)
    
    return clip.transform(efecto)

# ================================================================
# 🎬 CREAR SUBTÍTULO POR SEGMENTO
# ================================================================
def crear_subtitulo_por_segmento(texto, duracion, video_size=(1080, 1920)):
    lineas = []
    palabras = texto.split()
    linea = ""
    for p in palabras:
        if len(linea) + len(p) + 1 <= 35:
            linea += p + " "
        else:
            lineas.append(linea.strip())
            linea = p + " "
    if linea:
        lineas.append(linea.strip())
    texto_final = "\n".join(lineas)

    for fuente in ['Arial', 'DejaVu-Sans', 'sans-serif', None]:
        try:
            txt_clip = TextClip(
                text=texto_final,
                font=fuente,
                font_size=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video_size[0] * 0.9, video_size[1] * 0.8),
                text_align='center',
            )
            txt_clip = txt_clip.with_duration(duracion).with_position(('center', 'center'))
            return txt_clip
        except:
            continue

    # Fallback PIL
    try:
        img_width = video_size[0]
        img = Image.new("RGBA", (img_width, int(video_size[1] * 0.7)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/arial/arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, 40)
                    break
                except:
                    continue
        if font is None:
            font = ImageFont.load_default()
        
        y_offset = 50
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (img_width - text_width) // 2
            for dx, dy in [(-2,-2), (-2,0), (-2,2), (0,-2), (0,2), (2,-2), (2,0), (2,2)]:
                draw.text((x+dx, y_offset+dy), linea, fill='black', font=font)
            draw.text((x, y_offset), linea, fill='white', font=font)
            y_offset += text_height + 10
        
        img_path = f"subtitulo_seg_{random.randint(1000,9999)}.png"
        img.save(img_path)
        sub_clip = ImageClip(img_path).with_duration(duracion).with_position(('center', 'center'))
        atexit.register(lambda p=img_path: os.remove(p) if os.path.exists(p) else None)
        return sub_clip
    except:
        return None

# ================================================================
# 🎬 CREAR VIDEO CON MÚLTIPLES ESCENAS, MÚSICA Y SUBTÍTULOS
# ================================================================
def crear_y_subir_video(texto, imagen_url, historia_completa, tema, personaje, num_escenas=3):
    if not CLOUDINARY_DISPONIBLE:
        print("❌ Cloudinary no configurado.")
        return None

    print("🎬 Creando video Reel con múltiples escenas, música y subtítulos por segmento...")
    
    if len(texto.split()) < 20:
        segmentos_texto = [texto]
        num_escenas = 1
    else:
        segmentos_texto = dividir_resumen_en_segmentos(texto, num_escenas)
    
    print(f"📝 Generando {len(segmentos_texto)} imágenes y subtítulos para el Reel...")
    
    urls_imagenes = []
    for i, seg in enumerate(segmentos_texto):
        prompt_seg = f"Escena de la historia: {seg}\n\n{historia_completa[:300]}"
        img_prompt = generar_prompt_imagen(prompt_seg, tema, personaje)
        img_url = generar_imagen_agnes(img_prompt, width=1080, height=1920, intentos=4, espera_segundos=10)
        if img_url:
            urls_imagenes.append(img_url)
            print(f"✅ Imagen {i+1}/{len(segmentos_texto)} generada")
        else:
            if imagen_url:
                urls_imagenes.append(imagen_url)
                print(f"⚠️ Imagen {i+1} falló, usando imagen de respaldo del Reel")
            else:
                respaldo = generar_imagen_respaldo(1080, 1920)
                urls_imagenes.append(respaldo)
                print(f"⚠️ Imagen {i+1} falló, usando imagen de respaldo genérica")
    
    while len(urls_imagenes) < 3:
        urls_imagenes.append(imagen_url if imagen_url else generar_imagen_respaldo(1080, 1920))
    
    if len(urls_imagenes) > 5:
        urls_imagenes = urls_imagenes[:5]
    
    print("🔊 Generando narración con edge-tts...")
    audio_path = generar_audio_edge_tts(texto, "reel")
    if not audio_path:
        print("❌ No se pudo generar audio.")
        return None
    
    try:
        audio_clip = AudioFileClip(audio_path)
        duracion_total = audio_clip.duration
        print(f"🎵 Duración del audio: {duracion_total:.1f}s")
    except Exception as e:
        print(f"❌ Error cargando audio: {e}")
        return None
    
    fondo_path = descargar_musica_fondo()
    fondo_audio = None
    if fondo_path and os.path.exists(fondo_path):
        try:
            fondo_audio = AudioFileClip(fondo_path)
            if fondo_audio.duration < duracion_total:
                veces = int(duracion_total / fondo_audio.duration) + 1
                from moviepy import concatenate_audioclips
                fondo_audio = concatenate_audioclips([fondo_audio] * veces)
            fondo_audio = fondo_audio.subclipped(0, duracion_total).with_volume_scaled(0.08)
            print("🎵 Música de fondo cargada desde archivo local")
        except Exception as e:
            print(f"⚠️ Error con música de fondo: {e}")
            fondo_audio = None
    
    clips = []
    duracion_por_segmento = duracion_total / len(urls_imagenes)
    
    for i, url_img in enumerate(urls_imagenes):
        print(f"🖼️ Procesando escena {i+1}/{len(urls_imagenes)}...")
        img_data = descargar_imagen_con_retry(url_img)
        if img_data:
            img_path = f"temp_scene_{i}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data)
        else:
            respaldo = generar_imagen_respaldo(1080, 1920)
            if respaldo:
                img_data = descargar_imagen_con_retry(respaldo)
                if img_data:
                    img_path = f"temp_scene_{i}.jpg"
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                else:
                    continue
            else:
                continue
        
        try:
            clip = ImageClip(img_path).resized((1080, 1920))
            clip = clip.with_duration(duracion_por_segmento)
            clip = aplicar_zoom_lento(clip, zoom_final=1.10)
            clips.append(clip)
        except Exception as e:
            print(f"⚠️ Error procesando escena {i+1}: {e}")
            continue
    
    if not clips:
        print("❌ No se pudieron crear clips. Usando imagen única de respaldo.")
        respaldo_url = generar_imagen_respaldo(1080, 1920)
        if respaldo_url:
            img_data = descargar_imagen_con_retry(respaldo_url)
            if img_data:
                img_path = "temp_fallback.jpg"
                with open(img_path, "wb") as f:
                    f.write(img_data)
                clip = ImageClip(img_path).resized((1080, 1920))
                clip = clip.with_duration(duracion_total)
                clip = aplicar_zoom_lento(clip, zoom_final=1.10)
                clips = [clip]
                segmentos_texto = [texto]
                duracion_por_segmento = duracion_total
            else:
                print("❌ No se pudo generar ni siquiera la imagen de respaldo.")
                return None
    
    video_final = concatenate_videoclips(clips, method="compose")
    video_final = video_final.with_duration(duracion_total)
    
    # Subtítulos por segmento
    subtitulos_clips = []
    if len(segmentos_texto) != len(clips):
        while len(segmentos_texto) < len(clips):
            segmentos_texto.append(segmentos_texto[-1])
        segmentos_texto = segmentos_texto[:len(clips)]
    
    for i, seg_texto in enumerate(segmentos_texto):
        if i >= len(clips):
            break
        duracion_seg = clips[i].duration
        sub_clip = crear_subtitulo_por_segmento(seg_texto, duracion_seg, (1080, 1920))
        if sub_clip:
            start_time = sum(c.duration for c in clips[:i])
            sub_clip = sub_clip.with_start(start_time)
            subtitulos_clips.append(sub_clip)
    
    if subtitulos_clips:
        video_final = CompositeVideoClip([video_final] + subtitulos_clips)
    
    if fondo_audio:
        audio_final = CompositeAudioClip([audio_clip, fondo_audio])
    else:
        audio_final = audio_clip
    
    video_final = video_final.with_audio(audio_final)
    
    output_path = "reel.mp4"
    try:
        video_final.write_videofile(output_path, fps=24, codec='libx264', logger=None)
        print(f"✅ Video guardado en {output_path}")
    except Exception as e:
        print(f"❌ Error exportando: {e}")
        return None
    
    print("📤 Subiendo a Cloudinary...")
    try:
        result = upload(
            output_path,
            resource_type="video",
            public_id=f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            overwrite=True
        )
        video_url = result.get('secure_url')
        print(f"✅ Video subido: {video_url}")
        return video_url
    except Exception as e:
        print(f"❌ Error subiendo a Cloudinary: {e}")
        return None
    finally:
        for f in [output_path, audio_path, fondo_path] + [f"temp_scene_{i}.jpg" for i in range(len(clips))]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass

# ================================================================
# MAIN
# ================================================================
def main():
    print(f"🎤 Voz inicial: {CONFIG_VOZ_ACTUAL['voz']} ({CONFIG_VOZ_ACTUAL['velocidad']})")
    print("👻 Iniciando Bot de Terror (POST y REEL con relatos DIFERENTES)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno (DEEPSEEK, MAKE, AGNES).")
        sys.exit(1)

    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")

    estado = cargar_estado()
    
    # --- POST ---
    tema_post = obtener_tema_no_repetido(temas, estado)
    print(f"📖 Tema POST seleccionado: {tema_post}")

    print("📝 Generando historia para POST...")
    historia_post = generar_historia_completa(tema_post)
    if not historia_post:
        print("❌ Falló la generación de la historia del POST.")
        sys.exit(1)

    print(f"✅ Historia POST generada ({len(historia_post.split())} palabras)")
    personaje_post = detectar_personaje_y_epoca(historia_post)

    titulo_post = "Relato de terror"
    for linea in historia_post.split('\n'):
        if linea.strip().startswith('🌙'):
            titulo_post = linea.strip().replace('🌙', '').strip()
            break

    print("🎨 Generando imagen para POST (4:5)...")
    prompt_post = generar_prompt_imagen(historia_post, tema_post, personaje_post)
    image_post_url = generar_imagen_agnes(prompt_post, width=1080, height=1350, intentos=6)
    if not image_post_url:
        print("⚠️ Agnes falló para el post. Usando imagen de respaldo...")
        image_post_url = generar_imagen_respaldo(1080, 1350)

    texto_final_post = agregar_cta_final(historia_post)
    print("✅ POST listo: Historia + Imagen + CTA")

    # --- REEL ---
    estado_temporal = {
        "publicados": estado.get("publicados", []) + [tema_post],
        "ultimo_tema": tema_post
    }
    tema_reel = obtener_tema_no_repetido(temas, estado_temporal)
    print(f"🎬 Tema REEL seleccionado (diferente al post): {tema_reel}")

    print("📝 Generando historia para REEL...")
    historia_reel = generar_historia_completa(tema_reel)
    if not historia_reel:
        print("❌ Falló la generación de la historia del REEL.")
        sys.exit(1)
        
    print(f"✅ Historia REEL generada ({len(historia_reel.split())} palabras)")
    personaje_reel = detectar_personaje_y_epoca(historia_reel)
    
    titulo_reel = "Relato de terror"
    for linea in historia_reel.split('\n'):
        if linea.strip().startswith('🌙'):
            titulo_reel = linea.strip().replace('🌙', '').strip()
            break

    print("📝 Generando resumen para Reel...")
    resumen_reel = generar_resumen_reel(historia_reel)
    print(f"✅ Resumen Reel: {len(resumen_reel.split())} palabras")

    print("🎨 Generando imagen de respaldo para Reel (9:16)...")
    prompt_reel = generar_prompt_imagen(historia_reel, tema_reel, personaje_reel).replace("4:5", "9:16")
    image_reel_url = generar_imagen_agnes(prompt_reel, width=1080, height=1920, intentos=4)
    if not image_reel_url:
        print("⚠️ No se pudo generar imagen de respaldo para el Reel. Se usará una genérica.")
        image_reel_url = generar_imagen_respaldo(1080, 1920)

    reel_video_url = None
    if CLOUDINARY_DISPONIBLE:
        reel_video_url = crear_y_subir_video(
            texto=resumen_reel,
            imagen_url=image_reel_url,
            historia_completa=historia_reel,
            tema=tema_reel,
            personaje=personaje_reel,
            num_escenas=3
        )
        if not reel_video_url:
            print("⚠️ Falló la creación/subida del video.")
    else:
        print("⏭️ Cloudinary no configurado, omitiendo Reel.")

    hashtags_texto = "#LeyendasMexicanas #Terror #Misterio #Paranormal #Mexico"
    descripcion_reel = f"🌙 {titulo_reel}\n\n{hashtags_texto}\n\n_Imágenes y voz generados con IA._"

    payload = {
        "post_message": texto_final_post,
        "post_image": image_post_url,
        "comment_text": "😱 El relato completo ya está en el post principal. ¡No te lo pierdas!",
        "reel_video_url": reel_video_url,
        "reel_text": descripcion_reel,
        "timestamp": datetime.now().isoformat(),
    }

    print("📤 Enviando a Make...")
    try:
        r = requests.post(MAKE_WEBHOOK_URL_TERROR, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado a Make correctamente")
            if tema_post not in estado.get("publicados", []):
                estado["publicados"].append(tema_post)
            if tema_reel not in estado.get("publicados", []):
                estado["publicados"].append(tema_reel)
            estado["ultimo_tema"] = tema_reel
            guardar_estado(estado)
            print(f"✅ Relatos publicados: POST ({tema_post}) | REEL ({tema_reel})")
        else:
            print(f"❌ Make respondió: {r.status_code}")
            print(f"   Respuesta: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Error enviando a Make: {e}")

    print("🎉 Proceso completado")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
