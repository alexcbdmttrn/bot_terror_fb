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
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from cloudinary.uploader import upload
import cloudinary
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import io

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
# 🖼️ GENERAR PLACEHOLDER LOCAL Y SUBIR A CLOUDINARY
# ================================================================
def generar_y_subir_placeholder(texto="Imagen no disponible", size=(1080, 1350)):
    try:
        img = Image.new("RGB", size, (20, 20, 20))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), texto, font=font)
        x = (size[0] - (bbox[2]-bbox[0])) // 2
        y = (size[1] - (bbox[3]-bbox[1])) // 2
        draw.text((x, y), texto, fill="red", font=font)
        path = f"placeholder_{random.randint(1000, 9999)}.jpg"
        img.save(path)
        print(f"🖼️ Placeholder local generado: {path}")
        
        if CLOUDINARY_DISPONIBLE:
            print("📤 Subiendo placeholder a Cloudinary...")
            result = upload(
                path,
                resource_type="image",
                public_id=f"placeholder_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                overwrite=True
            )
            url = result.get('secure_url')
            print(f"✅ Placeholder subido: {url}")
            os.remove(path)
            return url
        else:
            print("⚠️ Cloudinary no disponible, placeholder local no se subirá")
            return None
    except Exception as e:
        print(f"⚠️ Error generando/subiendo placeholder: {e}")
        return None

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
# 🧹 LIMPIAR TEXTO PARA TTS
# ================================================================
def limpiar_caracteres_para_tts(texto):
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
- Identifica el AÑO o ÉPOCA en que sucede la historia. Si no se menciona, infiere uno lógico basado en el contexto (ej. si hay smartphones, es 2015+).
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
# 🎭 DETECTOR DE ENTIDAD
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
# 🎨 GENERAR PROMPT DE IMAGEN
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
    
    prompt = f"""Eres un DIRECTOR DE FOTOGRAFÍA DE CINE.
Crea un PROMPT DE IMAGEN EN INGLÉS para una imagen VERTICAL (4:5) que sea la escena MÁS REPRESENTATIVA de esta historia.

HISTORIA:
\"\"\"
{limpiar_texto_para_imagen(historia)[:400]}
\"\"\"
TEMA: {tema}
PERSONAJE HUMANO: {sujeto_humano}
ÉPOCA EXACTA: {epoca_mod}

🎬 ESTILO VISUAL:
- Cinematic film still, dramatic volumetric lighting, atmospheric fog
- High contrast chiaroscuro: deep black shadows + ONE dominant accent glow
- Moonlight beams, god rays, anamorphic lens feel, shallow depth of field

📐 COMPOSICIÓN Y LÓGICA NARRATIVA:
- PLANO: wide o medium-wide shot, vertical 4:5
- EL ENTORNO ES EL PROTAGONISTA: arquitectura, callejones, bosques, carreteras, objetos de la época.
- HUMANO: {sujeto_humano} — de espaldas o a distancia, ocupando MÁXIMO 20% del encuadre.
- EXACTAMENTE UNA figura humana. La imagen debe reflejar la lógica del relato y la época específica.

🚫 PROHIBIDO: gore, sangre, heridas, caras en primer plano, texto, watermarks, multitudes, personas duplicadas, clones, gemelos, dobles caras, dos cabezas.

Devuelve SOLO el prompt en inglés, directo, sin explicaciones.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 350,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        prompt_imagen += ", vertical 4:5 cinematic poster style, volumetric fog, high contrast, one accent glow color, sharp focus, no text, no watermark"
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return f"Vertical 4:5 cinematic film still, dark atmospheric scene with volumetric fog, wide shot, no text"

# ================================================================
# 🛡️ FILTRAR PROMPT PARA AGNES
# ================================================================
def filtrar_prompt_para_agnes(prompt):
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
    prompt_limpio = prompt
    for palabra in palabras_prohibidas:
        prompt_limpio = re.sub(rf'\b{palabra}\b', '', prompt_limpio, flags=re.IGNORECASE)
    prompt_limpio = re.sub(r'\s+', ' ', prompt_limpio).strip()
    
    if len(prompt_limpio.split()) < 15:
        prompt_limpio = "Cinematic landscape photograph, atmospheric moonlight, mysterious urban scene at night, cinematic mood, wide shot, vertical composition, no people, no text, no violence"
    
    if not prompt_limpio.lower().startswith("cinematic"):
        prompt_limpio = "Cinematic atmospheric photograph, " + prompt_limpio
    
    print(f"🛡️ Prompt filtrado para Agnes ({len(prompt_limpio)} caracteres)")
    return prompt_limpio

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

# ================================================================
# 🖼️ GENERAR IMAGEN CON AGNES
# ================================================================
def generar_imagen_agnes(prompt, width=1080, height=1350, intentos=5, espera_segundos=15):
    prompt_limpio = filtrar_prompt_para_agnes(prompt[:800])
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
    for intento in range(1, intentos + 1):
        print(f"🎨 Intento {intento}/{intentos} generando imagen...")
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
                    print("⚠️ Violación de política de contenido.")
                    break
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
        if intento < intentos:
            print(f"⏳ Esperando {espera_segundos}s...")
            time.sleep(espera_segundos)
    print("⚠️ Agnes falló. Generando placeholder y subiendo a Cloudinary...")
    texto_placeholder = "Imagen no disponible"
    if width == 1080 and height == 1920:
        texto_placeholder = "Reel"
    elif width == 1080 and height == 1350:
        texto_placeholder = "Post"
    placeholder_url = generar_y_subir_placeholder(texto_placeholder, (width, height))
    if placeholder_url:
        return placeholder_url
    else:
        fallback_url = f"https://via.placeholder.com/{width}x{height}/1a1a1a/ff0000?text={texto_placeholder}"
        print(f"⚠️ Usando URL fallback: {fallback_url}")
        return fallback_url

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
# 🎥 ZOOM LENTO (Ken Burns Effect) – CORREGIDO con .transform() y duración previa
# ================================================================
def aplicar_zoom_lento(clip, zoom_final=1.10):
    """
    Aplica un zoom in suave del 10% durante la duración del clip.
    Requiere que clip.duration ya tenga un valor (no None).
    """
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
    
    # En moviepy 2.x se usa .transform() en lugar de .fl()
    return clip.transform(efecto)

# ================================================================
# 🎬 CREAR VIDEO Y SUBIR A CLOUDINARY (CON ZOOM LENTO CORREGIDO)
# ================================================================
def crear_y_subir_video(texto, imagen_url):
    if not CLOUDINARY_DISPONIBLE:
        print("❌ Cloudinary no configurado.")
        return None

    print("🎬 Creando video Reel con narración y zoom lento...")
    
    img_path = None
    if imagen_url and imagen_url.startswith("http"):
        img_data = descargar_imagen_con_retry(imagen_url)
        if img_data:
            img_path = "temp_background.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data)
            print("✅ Imagen descargada")
        else:
            print("⚠️ No se pudo descargar la imagen, usando placeholder")
    else:
        if imagen_url and os.path.exists(imagen_url):
            img_path = imagen_url
        else:
            img_path = generar_y_subir_placeholder("Reel", (1080, 1920))
            if not img_path:
                print("❌ No se pudo generar placeholder. Abortando.")
                return None
            img_data = descargar_imagen_con_retry(img_path)
            if img_data:
                img_path = "temp_background.jpg"
                with open(img_path, "wb") as f:
                    f.write(img_data)
            else:
                print("❌ No se pudo descargar placeholder")
                return None
    
    if not img_path or not os.path.exists(img_path):
        print("❌ No existe archivo de imagen")
        return None

    print("🔊 Generando narración con edge-tts...")
    audio_path = generar_audio_edge_tts(texto, "reel")
    if not audio_path:
        print("❌ No se pudo generar audio.")
        return None
    
    try:
        clip = ImageClip(img_path).resized((1080, 1920))
    except Exception as e:
        print(f"❌ Error procesando imagen: {e}")
        return None
    
    try:
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration
        print(f"🎵 Duración del audio: {duracion:.1f}s")
    except Exception as e:
        print(f"❌ Error cargando audio: {e}")
        return None
    
    # 🔥 FIX 1: Asignar la duración ANTES de aplicar el zoom
    clip = clip.with_duration(duracion)
    
    # 🔥 Ahora aplicar zoom (clip ya tiene duración definida)
    print("🎥 Aplicando zoom lento (Ken Burns)...")
    clip = aplicar_zoom_lento(clip, zoom_final=1.10)
    
    # Texto superpuesto (opcional, con fallback)
    lineas = []
    palabras = texto.split()
    linea_actual = ""
    for palabra in palabras:
        if len(linea_actual) + len(palabra) + 1 <= 35:
            linea_actual += (palabra + " ")
        else:
            lineas.append(linea_actual.strip())
            linea_actual = palabra + " "
    if linea_actual:
        lineas.append(linea_actual.strip())
    
    txt_clip = None
    for fuente in ['Arial', 'DejaVu-Sans']:
        try:
            txt_clip = TextClip(
                text="\n".join(lineas),
                font_size=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font=fuente,
                method='caption',
                size=(1000, 1800),
                text_align='center',
            )
            txt_clip = txt_clip.with_duration(duracion).with_position('center')
            print(f"✅ Texto superpuesto con {fuente}")
            break
        except Exception as e:
            print(f"⚠️ Fuente {fuente} no disponible: {e}")
    
    if txt_clip:
        final = CompositeVideoClip([clip, txt_clip])
    else:
        print("⚠️ No se puso texto, solo audio")
        final = clip
    
    final = final.with_audio(audio_clip)
    
    output_path = "reel.mp4"
    try:
        final.write_videofile(output_path, fps=24, codec='libx264', logger=None)
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
        for f in [output_path, "temp_background.jpg", audio_path]:
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
    print("👻 Iniciando Bot de Terror (edge-tts + Zoom Lento + Cloudinary + Make)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno (DEEPSEEK, MAKE, AGNES).")
        sys.exit(1)

    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")

    estado = cargar_estado()
    tema = obtener_tema_no_repetido(temas, estado)
    print(f"📖 Tema seleccionado: {tema}")

    print("📝 Generando historia...")
    historia_base = generar_historia_completa(tema)
    if not historia_base:
        print("❌ Falló la generación de la historia.")
        sys.exit(1)

    print(f"✅ Historia generada ({len(historia_base.split())} palabras)")

    print("🧑 Detectando personaje y época...")
    personaje = detectar_personaje_y_epoca(historia_base)

    # Extraer título de la historia (línea que empieza con "🌙")
    titulo_historia = "Relato de terror"
    for linea in historia_base.split('\n'):
        if linea.strip().startswith('🌙'):
            titulo_historia = linea.strip().replace('🌙', '').strip()
            break

    # --- Imagen para post (4:5) ---
    print("🎨 Generando prompt para post...")
    prompt_post = generar_prompt_imagen(historia_base, tema, personaje)
    image_url = generar_imagen_agnes(prompt_post, width=1080, height=1350, intentos=5)
    if not image_url:
        print("❌ No se pudo obtener imagen para post. Abortando.")
        sys.exit(1)
    print(f"📷 URL post: {image_url[:60]}...")

    # --- Imagen para Reel (9:16) ---
    print("🎨 Generando prompt para Reel...")
    prompt_reel = prompt_post.replace("4:5", "9:16")
    image_reel_url = generar_imagen_agnes(prompt_reel, width=1080, height=1920, intentos=3)
    if not image_reel_url:
        print("❌ No se pudo obtener imagen para Reel. Se usará placeholder genérico.")
        image_reel_url = generar_y_subir_placeholder("Reel", (1080, 1920))
        if not image_reel_url:
            image_reel_url = "https://via.placeholder.com/1080x1920/1a1a1a/ff0000?text=Reel"
    print(f"📷 URL Reel: {image_reel_url[:60]}...")

    texto_final = agregar_cta_final(historia_base)
    print("✅ CTA y hashtags agregados")

    print("📝 Generando resumen para Reel...")
    resumen_reel = generar_resumen_reel(historia_base)
    print(f"✅ Resumen: {len(resumen_reel.split())} palabras")

    # --- Crear video y subir a Cloudinary ---
    reel_video_url = None
    if CLOUDINARY_DISPONIBLE:
        reel_video_url = crear_y_subir_video(resumen_reel, image_reel_url)
        if not reel_video_url:
            print("⚠️ Falló la creación/subida del video.")
    else:
        print("⏭️ Cloudinary no configurado, omitiendo Reel.")

    # --- Preparar descripción del Reel (solo título + hashtags + disclaimer IA) ---
    hashtags_texto = "#LeyendasMexicanas #Terror #Misterio #Paranormal #Mexico"
    descripcion_reel = f"🌙 {titulo_historia}\n\n{hashtags_texto}\n\n_Imágenes y voz generados con IA._"

    # --- Enviar a Make ---
    payload = {
        "post_message": texto_final,
        "post_image": image_url,
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
            if tema not in estado.get("publicados", []):
                estado["publicados"].append(tema)
            estado["ultimo_tema"] = tema
            guardar_estado(estado)
            print(f"✅ Relato publicado: {tema}")
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
