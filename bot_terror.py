from datetime import datetime
import json
import os
import random
import re
import sys
import time
import requests
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from cloudinary.uploader import upload
import cloudinary
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

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

if all([CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET]):
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=CLOUD_API_KEY,
        api_secret=CLOUD_API_SECRET
    )
    CLOUDINARY_DISPONIBLE = True
else:
    CLOUDINARY_DISPONIBLE = False
    print("⚠️ Cloudinary no configurado. No se podrán subir videos.")

# ================================================================
# 🎨 PALETAS Y ESTILOS
# ================================================================
PALETAS_COLOR = [
    "Cold cyan blue LED fog, navy blue modern shadows, crisp white moonlight",
    "Emerald green twilight, modern city haze, muted sage ambient lighting",
    "Deep violet LED haze, electric purple ambient light, dark magenta shadows",
    "Slate gray modern tones, freezing ice blue highlight, dim overcast ambient",
    "Dark teal and deep blue, modern oceanic midnight, cold misty atmosphere",
    "Stark black and white high contrast, silver moonlight, modern pitch shadows",
    "Desaturated cold film look, moody cinematic lighting, 8k hyperrealistic",
    "Neon purple and electric pink, deep violet shadows, cyberpunk modern lights",
    "Electric yellow and charcoal black, stark contrast, dusty atmospheric haze",
    "Deep crimson red, pitch black shadow, intense orange emergency LED lights",
    "Blood red and burnt orange, modern charcoal shadows, hellish glow",
    "Modern warm amber and dark mahogany, golden LED lighting, deep brown shadows",
    "Fiery sunset orange, deep purple shadows, modern red highlights",
    "Toxic lime green and pitch black, eerie chemical modern glow, radioactive haze",
    "Clean modern daylight, neutral gray ambient, crisp shadows",
    "Modern LED streetlight glow, cool white highlights, urban night atmosphere",
]
PALETA_COLOR_ACTUAL = random.choice(PALETAS_COLOR)

ESTILOS_VISUALES = [
    "Modern 2026 cinematic photograph, bright contemporary lighting, well-lit scene, sharp focus, current era",
    "Contemporary thriller photography 2026, soft modern ambient diffusion, bright highlights, present day",
    "Modern documentary realistic photo 2026, natural crisp skin texture, current fashion and architecture",
    "8k resolution modern cinematic frame, ultra clear facial details, bright exposure, contemporary era",
    "Modern fashion photography style 2026, dramatic but well-lit, clean skin, current trends",
    "Modern noir style 2026, high contrast but well-exposed, contemporary urban atmosphere",
]
ESTILO_VISUAL_ACTUAL = random.choice(ESTILOS_VISUALES)

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
# 🖼️ GENERAR PLACEHOLDER LOCAL
# ================================================================
def generar_placeholder_local(texto="Terror", size=(1080, 1920)):
    try:
        img = Image.new("RGB", size, (20, 20, 20))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), texto, font=font)
        x = (size[0] - (bbox[2]-bbox[0])) // 2
        y = (size[1] - (bbox[3]-bbox[1])) // 2
        draw.text((x, y), texto, fill="red", font=font)
        path = f"placeholder_{random.randint(1000, 9999)}.jpg"
        img.save(path)
        return path
    except Exception as e:
        print(f"⚠️ Error generando placeholder: {e}")
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

def limpiar_texto_para_audio(texto):
    texto = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF\U000024C2-\U0001F251]', '', texto)
    texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto)
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
# 🧑 DETECTAR PERSONAJE
# ================================================================
def detectar_personaje(texto_historia):
    prompt = f"""Analiza el siguiente relato en primera persona y extrae las características físicas del protagonista.

REGLAS:
- Si el texto menciona explícitamente el género (hombre/mujer), úsalo. Si no, infiere por el contexto.
- Si menciona edad o época, calcula la edad actual aproximada.
- Si menciona oficio o vestimenta, inclúyelo.
- Devuelve SOLO un JSON válido con estos campos:
  - "genero": "hombre" o "mujer"
  - "edad_aprox": número
  - "ocupacion": breve descripción
  - "descripcion_breve": 1 línea en inglés describiendo al personaje

REGLA CRÍTICA: Si no hay información suficiente, devuelve valores por defecto:
- genero: "hombre"
- edad_aprox: 35
- ocupacion: "persona común"
- descripcion_breve: "a 35-year-old Mexican person, contemporary clothing"

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
        print(f"🧑 Personaje detectado: {data.get('genero', '?')}, {data.get('edad_aprox', '?')} años, {data.get('ocupacion', '?')}")
        return data
    except Exception as e:
        print(f"⚠️ Error detectando personaje: {e}. Usando valores por defecto.")
        return {
            "genero": "hombre",
            "edad_aprox": 35,
            "ocupacion": "persona común",
            "descripcion_breve": "a 35-year-old Mexican person, contemporary clothing"
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
# 🎨 GENERAR PROMPT DE IMAGEN (NEUTRALIZADO)
# ================================================================
def generar_prompt_imagen(historia, tema, personaje):
    tipo = detectar_tipo_entidad(tema)
    entidad = DIRECTRICES_ENTIDAD[tipo]
    genero = personaje.get("genero", "hombre")
    edad = personaje.get("edad_aprox", 35)
    if genero == "mujer":
        sujeto_humano = f"a {edad}-year-old Mexican woman"
    else:
        sujeto_humano = f"a {edad}-year-old Mexican man"

    prompt = f"""Crea un PROMPT DE IMAGEN EN INGLÉS para una fotografía vertical (4:5) que represente esta escena:

Historia: {limpiar_texto_para_imagen(historia)[:400]}

Ubicación: {tema}

Reglas de composición:
- Estilo: fotografía cinematográfica, iluminación dramática, niebla atmosférica
- Plano: gran angular o plano medio, vertical
- El protagonista es el entorno: arquitectura, callejones, bosques, carreteras
- Persona: {sujeto_humano} (de espaldas o a distancia, ocupando máximo el 20% del encuadre)
- Prohibido: gore, sangre, violencia, caras en primer plano, texto, marcas de agua
- Colores: tonos fríos, alto contraste, un acento de color brillante (rojo, cian, ámbar o verde tóxico)

Devuelve SOLO el prompt en inglés, sin introducciones."""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 300,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        # Añadir restricciones adicionales para evitar bloqueos
        prompt_imagen += ", vertical 4:5, cinematic, no violence, no gore, no blood, no text, no watermark, wide shot, environment as main subject"
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt: {e}")
        return None

# ================================================================
# 🛡️ FILTRAR PROMPT PARA AGNES (MUY AGRESIVO)
# ================================================================
def filtrar_prompt_para_agnes(prompt):
    if not prompt:
        return "Cinematic atmospheric photograph, wide shot of a mysterious urban scene at night, volumetric fog, moonlight, high contrast, no people, no text, vertical 4:5"
    # Eliminar palabras problemáticas
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
        "corpse", "dead body", "murdered", "vicious", "haunted", "spooky",
        "paranormal", "supernatural", "eerie", "uncanny", "macabre", "ghastly",
        "disturbing", "unsettling", "creep", "lurking", "ominous"
    ]
    prompt_limpio = prompt
    for palabra in palabras_prohibidas:
        prompt_limpio = re.sub(rf'\b{palabra}\b', '', prompt_limpio, flags=re.IGNORECASE)
    prompt_limpio = re.sub(r'\s+', ' ', prompt_limpio).strip()
    if len(prompt_limpio.split()) < 10:
        prompt_limpio = "Cinematic atmospheric photograph, wide shot of an urban scene at night, volumetric fog, moonlight, high contrast, vertical 4:5, no people, no text"
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
  3. DESARROLLO: los hechos paso a paso (2-3 párrafos)
  4. CLÍMAX: el momento más intenso (1 párrafo)
  5. DESENLACE: cómo terminó todo (1 párrafo)
- Tono NATURAL Y COLOQUIAL.
- Detalles específicos: nombres de lugares reales, años concretos, oficios reales.

Formato EXACTO de salida:
🌙 **[Título descriptivo del suceso]**

[Primer párrafo]

[Segundo párrafo]

[...]

(NO agregues hashtags ni llamadas a comentar)
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
                raise ValueError("Respuesta corta o con error")
            lineas = resultado.split('\n')
            texto_narrativo = '\n'.join(linea for linea in lineas if linea.strip() and not linea.strip().startswith('🌙'))
            palabras = len(texto_narrativo.split())
            print(f"   📊 Palabras generadas: {palabras}")
            if palabras < 250:
                print(f"   ⚠️ Muy corto ({palabras}). Reintentando...")
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
    prompt = f"""Resume el siguiente relato en un texto CORTO y ATMOSFÉRICO de EXACTAMENTE 100 palabras, ideal para un Reel.

REGLAS:
- Mantén el suspenso.
- Incluye lugar y narrador.
- Extensión: 100 palabras.

RELATO:
\"\"\"
{historia_completa}
\"\"\"

Devuelve SOLO el resumen, sin títulos, sin hashtags, sin llamados.
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
# 🖼️ GENERAR IMAGEN CON AGNES AI (CON FALLBACK A PLACEHOLDER)
# ================================================================
def generar_imagen_agnes(prompt, width=1080, height=1350, intentos=5):
    prompt_limpio = prompt[:800] if prompt else "Cinematic atmospheric photograph, wide shot, vertical 4:5, no text"
    prompt_limpio = filtrar_prompt_para_agnes(prompt_limpio)
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    negative = (
        "close-up face, portrait, headshot, person filling frame, "
        "deformed, mutated, bad anatomy, extra limbs, extra fingers, "
        "asymmetrical eyes, malformed features, uncanny valley, "
        "gaunt, emaciated, ugly, grotesque, gore, blood, "
        "rusty, rusted, weathered, aged, vintage, retro, antique, old-fashioned, "
        "dilapidated, decrepit, run-down, crumbling, cracked walls, "
        "sepia, monochrome, black and white, film grain, "
        "duplicate people, multiple subjects, "
        "low quality, blurry, oversharpened, over-saturated, text, watermark"
    )
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt_limpio,
        "negative_prompt": negative,
        "width": width,
        "height": height,
        "num_images": 1,
    }
    for intento in range(1, intentos+1):
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
                print(f"❌ Error Agnes: {response.status_code} - {error_msg}")
                if "content_policy_violation" in error_msg:
                    print("⚠️ Violación de contenido, usando placeholder.")
                    break
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
        if intento < intentos:
            time.sleep(5)
    print("⚠️ No se pudo generar imagen con Agnes. Usando placeholder local.")
    placeholder_path = generar_placeholder_local("Imagen", (width, height))
    if placeholder_path:
        return placeholder_path
    return None

# ================================================================
# 🎤 GENERAR AUDIO CON GTTS
# ================================================================
def generar_audio_gtts(texto, index):
    texto_limpio = limpiar_texto_para_audio(texto)
    if len(texto_limpio) < 30:
        texto_limpio = "Esa noche en la carretera, el silencio era denso."
    filename = f"narracion_{index}.mp3"
    try:
        tts = gTTS(text=texto_limpio, lang='es', slow=False)
        tts.save(filename)
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"🔊 Audio generado con gTTS")
            return filename
    except Exception as e:
        print(f"❌ gTTS falló: {e}")
    return None

# ================================================================
# 🎬 CREAR VIDEO Y SUBIR A CLOUDINARY (CORREGIDO)
# ================================================================
def crear_y_subir_video(texto, imagen_url):
    if not CLOUDINARY_DISPONIBLE:
        print("❌ Cloudinary no configurado.")
        return None

    print("🎬 Creando video Reel con narración...")

    # 1. Obtener imagen
    img_path = None
    if imagen_url and isinstance(imagen_url, str) and imagen_url.startswith("http"):
        img_data = descargar_imagen_con_retry(imagen_url)
        if img_data:
            img_path = "temp_background.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data)
            print("✅ Imagen descargada")
        else:
            print("⚠️ No se pudo descargar la imagen, usando placeholder")
    elif imagen_url and os.path.exists(imagen_url):
        img_path = imagen_url
    else:
        print("⚠️ No hay imagen válida, generando placeholder")

    if not img_path or not os.path.exists(img_path):
        img_path = generar_placeholder_local("Reel", (1080, 1920))
        if not img_path:
            print("❌ No se pudo generar placeholder. Abortando.")
            return None

    # 2. Generar audio
    print("🔊 Generando narración...")
    audio_path = generar_audio_gtts(texto, "reel")
    if not audio_path:
        print("❌ No se pudo generar audio.")
        return None

    # 3. Crear clip de imagen
    try:
        clip = ImageClip(img_path).resized((1080, 1920))
    except Exception as e:
        print(f"❌ Error procesando imagen: {e}")
        return None

    # 4. Cargar audio
    try:
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration
        print(f"🎵 Duración del audio: {duracion:.1f}s")
    except Exception as e:
        print(f"❌ Error cargando audio: {e}")
        return None

    # 5. Añadir texto superpuesto (sin fuente específica para evitar errores)
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

    try:
        # Usar None para fuente por defecto (evita error de Arial)
        txt_clip = TextClip(
            text="\n".join(lineas),
            font_size=40,
            color='white',
            stroke_color='black',
            stroke_width=2,
            font=None,  # <--- Fuente por defecto, evita error
            method='caption',
            size=(1000, 1800),
            text_align='center',
        )
        txt_clip = txt_clip.with_duration(duracion).with_position('center')
    except Exception as e:
        print(f"⚠️ Error creando texto: {e}")
        txt_clip = None

    # 6. Combinar
    clip = clip.with_duration(duracion)
    if txt_clip:
        final = CompositeVideoClip([clip, txt_clip])
    else:
        final = clip
    final = final.with_audio(audio_clip)

    # 7. Exportar (SIN 'verbose', solo logger=None)
    output_path = "reel.mp4"
    try:
        final.write_videofile(output_path, fps=24, codec='libx264', logger=None)
        print(f"✅ Video guardado en {output_path}")
    except Exception as e:
        print(f"❌ Error exportando: {e}")
        return None

    # 8. Subir a Cloudinary
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
    print("👻 Iniciando Bot de Terror (gTTS → Cloudinary → Make)")
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

    print("🧑 Detectando personaje...")
    personaje = detectar_personaje(historia_base)

    # Imagen para post (4:5)
    print("🎨 Generando prompt para post...")
    prompt_post = generar_prompt_imagen(historia_base, tema, personaje)
    if not prompt_post:
        prompt_post = "Cinematic atmospheric photograph, wide shot of an urban scene, vertical 4:5, no text"
    image_url = generar_imagen_agnes(prompt_post, width=1080, height=1350, intentos=5)
    if not image_url:
        image_url = generar_placeholder_local("Post", (1080, 1350))
        if not image_url:
            image_url = "https://via.placeholder.com/1080x1350/1a1a1a/ff0000?text=Post"

    # Imagen para Reel (9:16)
    print("🎨 Generando prompt para Reel...")
    prompt_reel = prompt_post.replace("4:5", "9:16") if prompt_post else "Cinematic atmospheric photograph, wide shot, vertical 9:16, no text"
    image_reel_url = generar_imagen_agnes(prompt_reel, width=1080, height=1920, intentos=3)
    if not image_reel_url:
        image_reel_url = generar_placeholder_local("Reel", (1080, 1920))
        if not image_reel_url:
            image_reel_url = "https://via.placeholder.com/1080x1920/1a1a1a/ff0000?text=Reel"

    texto_final = agregar_cta_final(historia_base)
    print("✅ CTA y hashtags agregados")

    print("📝 Generando resumen para Reel...")
    resumen_reel = generar_resumen_reel(historia_base)
    print(f"✅ Resumen: {len(resumen_reel.split())} palabras")

    # Crear video
    reel_video_url = None
    if CLOUDINARY_DISPONIBLE:
        reel_video_url = crear_y_subir_video(resumen_reel, image_reel_url)
        if not reel_video_url:
            print("⚠️ Falló la creación/subida del video.")
    else:
        print("⏭️ Cloudinary no configurado, omitiendo Reel.")

    # Enviar a Make
    payload = {
        "post_message": texto_final,
        "post_image": image_url,
        "comment_text": "😱 El relato completo ya está en el post principal. ¡No te lo pierdas!",
        "reel_video_url": reel_video_url,
        "reel_text": resumen_reel,
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
