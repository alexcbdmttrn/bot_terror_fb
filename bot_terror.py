from datetime import datetime
import json
import os
import random
import re
import sys
import time
import requests
import moviepy.editor as mp
from cloudinary.uploader import upload
import cloudinary

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL_TERROR = os.getenv("MAKE_WEBHOOK_URL_TERROR")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

# Cloudinary
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

ESTADO_FILE = "estado_terror.json"

# ================================================================
# CONFIGURAR CLOUDINARY
# ================================================================
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
# 🎨 PALETAS MODERNAS 2026
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

# ================================================================
# 📷 ESTILOS VISUALES MODERNOS 2026
# ================================================================
ESTILOS_VISUALES = [
    "Modern 2026 cinematic photograph, bright contemporary lighting, well-lit scene, sharp focus, current era",
    "Contemporary thriller photography 2026, soft modern ambient diffusion, bright highlights, present day",
    "Modern documentary realistic photo 2026, natural crisp skin texture, current fashion and architecture",
    "8k resolution modern cinematic frame, ultra clear facial details, bright exposure, contemporary era",
    "Modern fashion photography style 2026, dramatic but well-lit, clean skin, current trends",
    "Modern noir style 2026, high contrast but well-exposed, contemporary urban atmosphere",
]
ESTILO_VISUAL_ACTUAL = random.choice(ESTILOS_VISUALES)

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
# CARGAR TEMAS
# ================================================================
def cargar_temas():
    try:
        with open("temas_2000.json", "r", encoding="utf-8") as f:
            temas = json.load(f)
            if isinstance(temas, list) and len(temas) > 0:
                return temas
            else:
                raise ValueError("El archivo no contiene una lista válida")
    except Exception as e:
        print(f"⚠️ Error cargando temas: {e}")
        print("❌ No se pudo cargar el archivo de temas. Abortando.")
        sys.exit(1)

# ================================================================
# 🗂️ ESTADO
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "historia_a" in data or "historia_b" in data:
                print("🔄 Detectado estado viejo. Migrando a nuevo formato...")
                publicados = data.get("publicados", [])
                return {"publicados": publicados, "ultimo_tema": ""}
            if "publicados" not in data:
                data["publicados"] = []
            if "ultimo_tema" not in data:
                data["ultimo_tema"] = ""
            return data
    except Exception:
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
        print("🔄 Todos los temas publicados. Reiniciando historial...")
        estado["publicados"] = []
        disponibles = [t for t in temas if t != ultimo_tema]
    
    if not disponibles:
        disponibles = temas
    
    return random.choice(disponibles)

# ================================================================
# 🧹 LIMPIAR TEXTO PARA IMAGEN
# ================================================================
def limpiar_texto_para_imagen(texto):
    texto = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF\U000024C2-\U0001F251]', '', texto)
    texto = re.sub(r'#\w+', '', texto)
    texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
    return texto.strip()

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
# 🎨 GENERAR PROMPT DE IMAGEN (ESTILO CINE DE TERROR)
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
    
    prompt = f"""Eres un DIRECTOR DE FOTOGRAFÍA DE CINE DE TERROR de nivel mundial, experto en concept art cinematográfico atmosférico.
Crea un PROMPT DE IMAGEN EN INGLÉS para una imagen VERTICAL (4:5) que sea la escena MÁS REPRESENTATIVA de esta historia.

HISTORIA:
\"\"\"
{limpiar_texto_para_imagen(historia)[:400]}
\"\"\"
TEMA: {tema}
ENTIDAD DEL RELATO: {tipo}
PERSONAJE HUMANO: {sujeto_humano}

🎬 ESTILO VISUAL OBLIGATORIO (horror cinematográfico de alto impacto):
- Cinematic horror film still, dramatic volumetric lighting, thick atmospheric fog
- High contrast chiaroscuro: deep black shadows + ONE dominant accent glow (crimson red, electric cyan, amber or toxic green)
- Subtle neon/electric glow on supernatural elements (glowing eyes, spectral aura, eerie light sources, neon signs if urban)
- Moonlight beams, god rays, anamorphic lens feel, shallow depth of field
- Saturated but elegant cinematic color grading, modern horror movie poster style

📐 COMPOSICIÓN OBLIGATORIA:
- PLANO: wide o medium-wide shot, vertical 4:5, composición de póster cinematográfico
- EL ENTORNO ES EL PROTAGONISTA: arquitectura colonial, callejones con faroles, bosques con niebla, cementerios, interiores con velas, carreteras solitarias, metro, drenajes
- ENTIDAD VISUAL DEL RELATO: {entidad} — SIEMPRE a distancia o entre sombras, integrada en la atmósfera, NUNCA en primer plano extremo
- HUMANO: {sujeto_humano} — de espaldas o a distancia, ocupando MÁXIMO 20-25% del encuadre
- EXACTAMENTE UNA figura humana y UNA entidad

🚫 PROHIBIDO:
- gore, sangre explícita, heridas, mutilaciones
- caras deformes o monstruosas en primer plano extremo
- texto, letras, watermarks, logos
- multitudes, personas duplicadas, clones, gemelos

Devuelve SOLO el prompt en inglés, directo, sin explicaciones.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 350,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        prompt_imagen += ", vertical 4:5 cinematic horror poster style, volumetric fog, high contrast, one accent glow color, sharp focus, no text, no watermark"
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return f"Vertical 4:5 cinematic horror film still, dark atmospheric scene with volumetric fog and one accent glow, {entidad}, wide shot, no text"

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
        "corpse", "dead body", "murdered", "vicious"
    ]
    
    prompt_limpio = prompt
    for palabra in palabras_prohibidas:
        prompt_limpio = re.sub(rf'\b{palabra}\b', '', prompt_limpio, flags=re.IGNORECASE)
    
    prompt_limpio = re.sub(r'\s+', ' ', prompt_limpio).strip()
    
    if len(prompt_limpio.split()) < 10:
        prompt_limpio = "Cinematic landscape photograph, atmospheric moonlight, mysterious urban scene at night, no violence, no horror, cinematic mood"
    
    print(f"🛡️ Prompt filtrado para Agnes (caracteres: {len(prompt_limpio)})")
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
- El narrador debe tener un PERFIL ÚNICO Y DIVERSO en cada historia. Varía el género, la edad (entre 20 y 70 años) y el oficio (ejemplos: profesor, taxista, enfermera, albañil, ama de casa, comerciante, policía, etc.). NO repitas el mismo perfil en historias consecutivas.
- Extensión: ENTRE 300 y 340 palabras.
- ESTRUCTURA OBLIGATORIA en PÁRRAFOS (cada párrafo separado por una línea en blanco):
  1. GANCHO inicial impactante (1-2 frases)
  2. CONTEXTO: quién es el narrador, dónde y cuándo ocurrió
  3. DESARROLLO: los hechos sobrenaturales paso a paso, con detalles sensoriales (2-3 párrafos)
  4. CLÍMAX: el momento más intenso (1 párrafo)
  5. DESENLACE: cómo terminó todo y qué le quedó al narrador (1 párrafo)
- TERMINA la última oración completamente.
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
            print(f"📝 Intento {intento+1}/3 generando historia completa...")
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
# 🖼️ GENERAR IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt, width=1080, height=1350, intentos=5, espera_segundos=15):
    prompt_limpio = prompt[:800]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    
    negative = (
        "close-up face, portrait, headshot, person filling frame, "
        "deformed face, disfigured, mutated, bad anatomy, extra limbs, "
        "extra fingers, asymmetrical eyes, malformed features, uncanny valley, "
        "gaunt, emaciated, ugly, grotesque, gore, blood, "
        "rusty, rusted, oxidized, weathered, aged, vintage, retro, antique, old-fashioned, "
        "dilapidated, decrepit, run-down, crumbling, cracked walls, peeling paint, "
        "deteriorated, abandoned ruins, moldy, musty, dusty, cobwebs, "
        "classic car, old car, vintage car, retro car, horse carriage, "
        "1950s, 1960s, 1970s, 1980s, 1990s, ancient, medieval, historical, "
        "sepia tone, monochrome, black and white, film grain, "
        "duplicate people, cloned faces, multiple subjects, "
        "low quality, blurry, oversharpened, over-saturated"
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
        print(f"🎨 Intento {intento}/{intentos} generando imagen vertical...")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]
                print(f"✅ Imagen generada (1080x{height}) en el intento {intento}")
                return image_url
            else:
                error_msg = response.text[:200]
                print(f"❌ Error en Agnes AI: {response.status_code} - {error_msg}")
                if "content_policy_violation" in error_msg:
                    print("⚠️ Violación de política de contenido. No se reintentará con este prompt.")
                    break
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

        if intento < intentos:
            print(f"⏳ Esperando {espera_segundos}s antes de reintentar...")
            time.sleep(espera_segundos)

    print(f"❌ No se pudo generar la imagen después de {intentos} intentos.")
    return None

# ================================================================
# 🎬 CREAR VIDEO Y SUBIR A CLOUDINARY
# ================================================================
def crear_y_subir_video(texto, imagen_url):
    """
    Crea un video de 6 segundos y lo sube a Cloudinary.
    Retorna la URL pública del video.
    """
    if not CLOUDINARY_DISPONIBLE:
        print("❌ Cloudinary no configurado. No se puede subir el video.")
        return None

    print("🎬 Creando video Reel...")
    
    # 1. Descargar imagen
    img_response = requests.get(imagen_url)
    if img_response.status_code != 200:
        print("❌ Error descargando imagen para el video")
        return None
    
    with open("temp_background.jpg", "wb") as f:
        f.write(img_response.content)
    
    # 2. Crear clip de imagen (resize a 1080x1920)
    try:
        clip = mp.ImageClip("temp_background.jpg").resize(newsize=(1080, 1920))
    except Exception as e:
        print(f"❌ Error procesando imagen: {e}")
        return None
    
    # 3. Añadir texto superpuesto
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
    
    txt_clip = mp.TextClip(
        "\n".join(lineas),
        fontsize=40,
        color='white',
        stroke_color='black',
        stroke_width=2,
        font='Arial',
        method='caption',
        size=(1000, 1800),
        align='center'
    )
    txt_clip = txt_clip.set_duration(6).set_position('center')
    
    # 4. Combinar
    clip = clip.set_duration(6)
    final = mp.CompositeVideoClip([clip, txt_clip])
    
    # 5. Exportar
    output_path = "reel.mp4"
    final.write_videofile(output_path, fps=24, codec='libx264', audio=False, verbose=False, logger=None)
    print(f"✅ Video guardado en {output_path}")
    
    # 6. Subir a Cloudinary
    print("📤 Subiendo video a Cloudinary...")
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
        # Limpiar archivos temporales
        try:
            os.remove(output_path)
            os.remove("temp_background.jpg")
        except:
            pass

# ================================================================
# MAIN
# ================================================================
def main():
    print("👻 Iniciando Bot de Terror (genera video → Cloudinary → Make)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Validar variables de entorno
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno (DEEPSEEK, MAKE, AGNES).")
        sys.exit(1)

    if not CLOUDINARY_DISPONIBLE:
        print("⚠️ Cloudinary no configurado. No se podrá subir el video del Reel.")
        print("   El Reel se omitirá.")

    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")

    estado = cargar_estado()

    tema = obtener_tema_no_repetido(temas, estado)
    print(f"📖 Tema seleccionado: {tema}")

    print("📝 Generando historia completa con DeepSeek...")
    historia_base = generar_historia_completa(tema)

    if not historia_base:
        print("❌ Falló la generación de la historia. Abortando sin guardar estado.")
        sys.exit(1)

    print(f"✅ Historia completa generada ({len(historia_base.split())} palabras aprox)")

    # Detectar personaje
    print("🧑 Detectando personaje del relato...")
    personaje = detectar_personaje(historia_base)

    # Generar prompt de imagen para post (4:5)
    print("🎨 Generando prompt de imagen para post...")
    prompt_imagen_post = generar_prompt_imagen(historia_base, tema, personaje)
    prompt_imagen_post_filtrado = filtrar_prompt_para_agnes(prompt_imagen_post)
    image_url = generar_imagen_agnes(prompt_imagen_post_filtrado, width=1080, height=1350, intentos=5)
    if image_url is None:
        image_url = "https://via.placeholder.com/1080x1350/1a1a1a/ff0000?text=Terror"

    # Generar imagen para Reel (9:16)
    print("🎨 Generando prompt de imagen para Reel (9:16)...")
    prompt_imagen_reel = prompt_imagen_post.replace("4:5", "9:16").replace("vertical 4:5", "vertical 9:16")
    prompt_imagen_reel_filtrado = filtrar_prompt_para_agnes(prompt_imagen_reel)
    image_reel_url = generar_imagen_agnes(prompt_imagen_reel_filtrado, width=1080, height=1920, intentos=3)
    if image_reel_url is None:
        image_reel_url = "https://via.placeholder.com/1080x1920/1a1a1a/ff0000?text=Reel"

    # Agregar CTA, hashtags y leyenda IA
    texto_final = agregar_cta_final(historia_base)
    print("✅ CTA, hashtags y leyenda de IA agregados")

    # Generar resumen para Reel
    print("📝 Generando resumen para Reel (100 palabras)...")
    resumen_reel = generar_resumen_reel(historia_base)
    print(f"✅ Resumen: {len(resumen_reel.split())} palabras")

    # ---------- GENERAR VIDEO Y SUBIR A CLOUDINARY ----------
    reel_video_url = None
    if CLOUDINARY_DISPONIBLE:
        reel_video_url = crear_y_subir_video(resumen_reel, image_reel_url)
        if reel_video_url is None:
            print("⚠️ Falló la creación/subida del video. El Reel se omitirá.")
    else:
        print("⏭️ Omisión de video (Cloudinary no configurado)")

    # ---------- Enviar TODO a Make ----------
    payload = {
        "post_message": texto_final,
        "post_image": image_url,
        "comment_text": "😱 El relato completo ya está en el post principal. ¡No te lo pierdas!",
        "reel_video_url": reel_video_url,  # URL del video en Cloudinary (o None)
        "reel_text": resumen_reel,         # Texto para el Reel (por si acaso)
        "timestamp": datetime.now().isoformat(),
    }

    print("📤 Enviando a Make...")
    try:
        r = requests.post(MAKE_WEBHOOK_URL_TERROR, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado a Make.com correctamente")
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
