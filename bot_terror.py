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
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

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
# ️ GENERAR IMAGEN DE RESPALDO (con variación)
# ================================================================
def generar_imagen_respaldo(width=1080, height=1350):
    try:
        color_fondo = (random.randint(10, 40), random.randint(10, 40), random.randint(10, 40))
        img = Image.new("RGB", (width, height), color_fondo)
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
# 📷 BUSCAR IMAGEN EN PEXELS (CORREGIDO - Sin caché)
# ================================================================
def generar_imagen_pexels(query, width=1080, height=1350, orientacion="vertical", page=None):
    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY no configurada. Usando imagen de respaldo.")
        return generar_imagen_respaldo(width, height)

    if orientacion == "vertical" and width < height:
        orientation_param = "portrait"
    elif orientacion == "horizontal" and width > height:
        orientation_param = "landscape"
    else:
        orientation_param = "square"

    # Si no se especifica página, usar una basada en tiempo para evitar caché
    if page is None:
        page = (int(time.time()) % 10) + 1

    # Añadir variación aleatoria a la consulta
    variantes = ["angle", "view", "perspective", "mood", "atmosphere", "lighting", "scene", "shot"]
    variacion = random.choice(variantes)
    query_variada = f"{query} {variacion}"

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query_variada,
        "per_page": 15,  # Más opciones para elegir
        "orientation": orientation_param,
        "size": "large",
        "page": page
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                fotos = data["photos"]
                # Elegir aleatoriamente de las primeras 5 para variedad
                fotos_disponibles = fotos[:min(5, len(fotos))]
                foto = random.choice(fotos_disponibles)
                src = foto.get("src")
                if src:
                    image_url = src.get("large2x") or src.get("large") or src.get("original")
                    print(f" Imagen de Pexels: {image_url[:80]}...")
                    return image_url
                else:
                    print("⚠️ Pexels no devolvió URL de imagen.")
                    return generar_imagen_respaldo(width, height)
            else:
                print(f"⚠️ Pexels no encontró imágenes para: '{query_variada}'")
                return generar_imagen_respaldo(width, height)
        else:
            print(f"❌ Error en Pexels API: {response.status_code} - {response.text[:100]}")
            return generar_imagen_respaldo(width, height)
    except requests.exceptions.Timeout:
        print(" Timeout en Pexels. Usando imagen de respaldo.")
        return generar_imagen_respaldo(width, height)
    except Exception as e:
        print(f"❌ Excepción en Pexels: {e}")
        return generar_imagen_respaldo(width, height)

# ================================================================
# 🔍 EXTRAER PALABRAS CLAVE PARA PEXELS
# ================================================================
def extraer_palabras_clave_pexels(segmento_texto, tema, personaje, indice_segmento=0):
    texto_limpio = limpiar_texto_para_imagen(segmento_texto)
    lugar = "Mexico"
    match = re.search(r'en\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*[A-ZÁÉÍÓÚÑ]?[a-záéíóúñ]*)', segmento_texto)
    if match:
        lugar = match.group(1).strip()
    
    hora = "night"
    if re.search(r'\b(3|2|1|4|5)\s*AM\b', segmento_texto, re.IGNORECASE):
        hora = "early morning"
    elif re.search(r'\b(atardecer|crepúsculo)\b', segmento_texto, re.IGNORECASE):
        hora = "sunset"
    elif re.search(r'\b(amanecer|madrugada)\b', segmento_texto, re.IGNORECASE):
        hora = "sunrise"
    elif re.search(r'\b(noche|medianoche)\b', segmento_texto, re.IGNORECASE):
        hora = "night"
    
    objetos = []
    if "auto" in texto_limpio.lower() or "camión" in texto_limpio.lower():
        objetos.append("car")
    if "calle" in texto_limpio.lower() or "avenida" in texto_limpio.lower():
        objetos.append("street")
    if "bosque" in texto_limpio.lower() or "árbol" in texto_limpio.lower():
        objetos.append("forest")
    if "río" in texto_limpio.lower() or "agua" in texto_limpio.lower() or "lago" in texto_limpio.lower():
        objetos.append("river")
    if "puente" in texto_limpio.lower():
        objetos.append("bridge")
    if "casa" in texto_limpio.lower() or "edificio" in texto_limpio.lower():
        objetos.append("building")
    if "iglesia" in texto_limpio.lower():
        objetos.append("church")
    if "cementerio" in texto_limpio.lower() or "panteón" in texto_limpio.lower():
        objetos.append("cemetery")
    
    query_parts = []
    if lugar:
        query_parts.append(lugar)
    if hora:
        query_parts.append(hora)
    if objetos:
        query_parts.extend(objetos[:2])
    if not objetos:
        query_parts.append("mexican")
        query_parts.append("landscape")
    
    # Añadir variación por índice para que cada segmento tenga consulta diferente
    variantes = ["angle", "view", "perspective", "mood", "atmosphere", "lighting", "scene"]
    variacion = variantes[indice_segmento % len(variantes)]
    query_parts.append(variacion)
    
    query = " ".join(query_parts[:5])
    print(f"🔍 Consulta Pexels: '{query}'")
    return query

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

def descargar_imagen_con_retry(url, intentos=2, timeout=15):
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
    "\n\n ¿Conoces una leyenda similar? Compártela en los comentarios. 👇",
    "\n\n🌙 ¿Qué harías tú en esta situación? Te leemos en comentarios. 👇",
    "\n\n👁️ ¿Crees que estas historias son reales? Déjanos tu opinión. ",
    "\n\n🔮 ¿Has vivido algo sobrenatural? Cuéntanos tu experiencia. 👇",
    "\n\n😱 ¿Te atreverías a visitar este lugar? Cuéntanos. 👇",
    "\n\n ¿Conoces más historias así? Compártelas en comentarios. 👇",
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
        r = requests.post(url, headers=headers, json=payload, timeout=25)
        r.raise_for_status()
        respuesta = r.json()["choices"][0]["message"]["content"].strip()
        respuesta = re.sub(r"```json\s*", "", respuesta)
        respuesta = re.sub(r"```\s*", "", respuesta)
        data = json.loads(respuesta, strict=False)
        print(f"🧑 Personaje detectado: {data.get('genero', '?')}, {data.get('edad_aprox', '?')} años | 🗓️ Época: {data.get('anio', '?')}")
        return data
    except Exception as e:
        print(f"️ Error detectando personaje: {e}. Usando valores por defecto.")
        return {
            "genero": "hombre",
            "edad_aprox": 35,
            "ocupacion": "persona común",
            "descripcion_breve": "a 35-year-old Mexican person, contemporary clothing",
            "anio": 2015
        }

# ================================================================
# 📖 GENERAR HISTORIA COMPLETA
# ================================================================
def generar_historia_completa(tema):
    prompt = f"""Eres un MAESTRO DE LA NARRATIVA DE TERROR y un EXPERTO EN REDES SOCIALES.

Tu tarea es crear una historia de terror CORTA y AUTOCONCLUSIVA basada en el tema: "{tema}", pero con un GANCHO IMPOSIBLE DE IGNORAR.

🚨 REGLAS ESTRICTAS:
- Ambientación: EXACTA y realista (México).
- Narración en PRIMERA PERSONA, tono coloquial.
- El narrador debe tener un PERFIL ÚNICO (género, edad, oficio).
- Extensión: 300-340 palabras.
- ESTRUCTURA: 1. Gancho en el título 2. Contexto 3. Desarrollo 4. Clímax 5. Desenlace

🎯 REGLAS DE ORO PARA EL ÉXITO EN REDES:
1. TÍTULO: NO uses un título descriptivo ("El fantasma de..."). Usa un GANCHO que genere CURIOSIDAD o PREGUNTA.
   - "Lo que vi en [LUGAR] a las [HORA] me hizo [REACCIÓN]"
   - "Intenté [ACCIÓN] en [LUGAR] y esto pasó"
   - "[NÚMERO] años después, todavía no puedo olvidar lo que pasó en [LUGAR]"
   - "La noche que [ACCIÓN] en [LUGAR] cambió mi vida"

2. RESTRICCIÓN (El "Hook" del Reel): La historia DEBE contener al menos una RESTRICCIÓN que el narrador enfrente.

3. GANCHO PARA EL POST: Crea una frase (máx 60 caracteres) que sea una PREGUNTA directa al espectador.

Formato EXACTO de salida:
🌙 **[Título de Curiosidad]**

[Primer párrafo]

[Segundo párrafo]

[... y así sucesivamente, separados por línea en blanco]

GANCHO_POST: [Frase de pregunta para Facebook]
RESTRICCION: [Descripción clara de la restricción]

(NO agregues hashtags ni llamadas a comentar)
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 1300,
    }
    for intento in range(3):
        try:
            print(f"📝 Intento {intento+1}/3 generando historia...")
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            resultado = r.json()["choices"][0]["message"]["content"].strip()
            if "[Error" in resultado or len(resultado) < 200:
                raise ValueError("Respuesta muy corta o con error")
            if "GANCHO_POST:" not in resultado or "RESTRICCION:" not in resultado:
                print("   ⚠️ No contiene los marcadores necesarios. Reintentando...")
                raise ValueError("Faltan marcadores")
            lineas = resultado.split('\n')
            texto_narrativo = '\n'.join(linea for linea in lineas if not linea.startswith('GANCHO_POST:') and not linea.startswith('RESTRICCION:') and linea.strip())
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
    texto = re.sub(r'GANCHO_POST:.*', '', texto)
    texto = re.sub(r'RESTRICCION:.*', '', texto)
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
    leyenda_ia = "\n\n_Imágenes de Pexels y voz generada con IA_"
    return texto.strip() + cta + hashtags + leyenda_ia

# ================================================================
# 📝 GENERAR RESUMEN PARA REEL
# ================================================================
def generar_resumen_reel(historia_completa, restriccion):
    lugar = "México"
    lineas = historia_completa.split('\n')
    for linea in lineas:
        if "en" in linea and len(linea.split()) > 3:
            match = re.search(r'en\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*[A-ZÁÉÍÓÚÑ]?[a-záéíóúñ]*)', linea)
            if match:
                lugar = match.group(1).strip()
                break
    
    prompt = f"""Resume el siguiente relato de terror en un texto CORTO y ATMOSFÉRICO (máximo 100 palabras) para un Reel de Facebook, enmarcándolo como un EXPERIMENTO o DESAFÍO.

REGLAS:
- El resumen debe enganchar al espectador haciéndole sentir que está viendo un intento, una prueba o un desafío real.
- Comienza con: "Basado en un testimonio real. Esta noche intentamos [ACCIÓN] en [LUGAR] y esto pasó..."
- Incluye la RESTRICCIÓN: "{restriccion}".
- Extensión: aproximadamente 100 palabras.
- NO incluyas hashtags ni llamadas a la acción.

RELATO COMPLETO:
\"\"\"
{historia_completa}
\"\"\"
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 250,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        resumen = r.json()["choices"][0]["message"]["content"].strip()
        palabras = resumen.split()
        if len(palabras) > 120:
            resumen = " ".join(palabras[:100]) + "..."
        if not any(resumen.lower().startswith(prefix) for prefix in ["basado en", "esta noche", "intenté", "intentamos"]):
            resumen = f"Basado en un testimonio real. {resumen}"
        return resumen
    except Exception as e:
        print(f"❌ Error generando resumen: {e}")
        palabras = historia_completa.split()
        return f"Basado en un testimonio real. {' '.join(palabras[:80])}..."

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
# 🎬 CREAR VIDEO CON MÚLTIPLES ESCENAS (CORREGIDO)
# ================================================================
def crear_y_subir_video(texto, imagen_url, historia_completa, tema, personaje, num_escenas=3):
    if not CLOUDINARY_DISPONIBLE:
        print("❌ Cloudinary no configurado.")
        return None

    print("🎬 Creando video Reel con múltiples escenas, música y subtítulos...")
    
    if len(texto.split()) < 20:
        segmentos_texto = [texto]
        num_escenas = 1
    else:
        segmentos_texto = dividir_resumen_en_segmentos(texto, num_escenas)
    
    print(f"📝 Generando {len(segmentos_texto)} imágenes únicas para el Reel...")
    
    genero = personaje.get("genero", "hombre")
    edad = personaje.get("edad_aprox", 35)
    anio = personaje.get("anio", 2015)
    
    urls_imagenes = []
    for i, seg in enumerate(segmentos_texto):
        print(f"🔍 Generando consulta Pexels para segmento {i+1}/{len(segmentos_texto)}...")
        # Cada segmento usa página diferente basada en tiempo + índice
        page = ((int(time.time()) + i) % 10) + 1
        query = extraer_palabras_clave_pexels(seg, tema, personaje, indice_segmento=i)
        img_url = generar_imagen_pexels(query, width=1080, height=1920, orientacion="vertical", page=page)
        if img_url:
            urls_imagenes.append(img_url)
            print(f"✅ Imagen {i+1}/{len(segmentos_texto)} obtenida de Pexels")
        else:
            if imagen_url:
                urls_imagenes.append(imagen_url)
                print(f"⚠️ Imagen {i+1} falló, usando imagen de respaldo del Reel")
            else:
                respaldo = generar_imagen_respaldo(1080, 1920)
                urls_imagenes.append(respaldo)
                print(f"⚠️ Imagen {i+1} falló, usando imagen de respaldo genérica")
    
    while len(urls_imagenes) < 3:
        page = (int(time.time()) % 10) + 1
        urls_imagenes.append(generar_imagen_pexels("mexican night landscape", width=1080, height=1920, orientacion="vertical", page=page))
    
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
            print(" Música de fondo cargada desde archivo local")
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
            page = (int(time.time()) % 10) + 1
            respaldo = generar_imagen_pexels("mexican night", width=1080, height=1920, orientacion="vertical", page=page)
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
        page = (int(time.time()) % 10) + 1
        respaldo_url = generar_imagen_pexels("mexican night", width=1080, height=1920, orientacion="vertical", page=page)
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
# MAIN (CORREGIDO - Sin imagen de respaldo fija)
# ================================================================
def main():
    print(f"🎤 Voz inicial: {CONFIG_VOZ_ACTUAL['voz']} ({CONFIG_VOZ_ACTUAL['velocidad']})")
    print("👻 Iniciando Bot de Terror (Pexels + Imágenes únicas por reel)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, PEXELS_API_KEY]):
        print("❌ Faltan variables de entorno: DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, PEXELS_API_KEY")
        sys.exit(1)

    temas = cargar_temas()
    print(f" {len(temas)} temas cargados")

    estado = cargar_estado()
    
    # ==========================================
    # 1. GENERAR POST (Relato A)
    # ==========================================
    tema_post = obtener_tema_no_repetido(temas, estado)
    print(f" Tema POST seleccionado: {tema_post}")

    print("📝 Generando historia para POST (con gancho y restricción)...")
    historia_post = generar_historia_completa(tema_post)
    if not historia_post:
        print("❌ Falló la generación de la historia del POST.")
        sys.exit(1)

    print(f"✅ Historia POST generada ({len(historia_post.split())} palabras)")
    
    gancho_post = "¿Qué harías tú si ves esto a las 3 AM?"
    restriccion = "No podía moverme"
    titulo_historia_post = "Relato de terror"
    
    for linea in historia_post.split('\n'):
        if linea.startswith('GANCHO_POST:'):
            gancho_post = linea.replace('GANCHO_POST:', '').strip()
        elif linea.startswith('RESTRICCION:'):
            restriccion = linea.replace('RESTRICCION:', '').strip()
        elif linea.strip().startswith('🌙'):
            titulo_historia_post = linea.strip().replace('', '').strip()
    
    print(f" Gancho POST: {gancho_post}")
    print(f"🔒 Restricción: {restriccion}")

    personaje_post = detectar_personaje_y_epoca(historia_post)

    print("🎨 Buscando imagen para POST (4:5) en Pexels...")
    query_post = extraer_palabras_clave_pexels(historia_post[:500], tema_post, personaje_post, indice_segmento=0)
    page_post = (int(time.time()) % 10) + 1
    image_post_url = generar_imagen_pexels(query_post, width=1080, height=1350, orientacion="vertical", page=page_post)
    if not image_post_url:
        print("⚠️ Pexels falló para el post. Usando imagen de respaldo...")
        image_post_url = generar_imagen_respaldo(1080, 1350)

    texto_post_limpio = agregar_cta_final(historia_post)
    texto_final_post = f"🤔 {gancho_post}\n\n{texto_post_limpio}"
    print("✅ POST listo: Gancho + Historia + Imagen + CTA")

    # ==========================================
    # 2. GENERAR REEL (Relato B - DIFERENTE)
    # ==========================================
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
    
    restriccion_reel = "No podía moverme"
    titulo_historia_reel = "Relato de terror"
    for linea in historia_reel.split('\n'):
        if linea.startswith('RESTRICCION:'):
            restriccion_reel = linea.replace('RESTRICCION:', '').strip()
        elif linea.strip().startswith('🌙'):
            titulo_historia_reel = linea.strip().replace('🌙', '').strip()
    
    personaje_reel = detectar_personaje_y_epoca(historia_reel)

    print("📝 Generando resumen para Reel (formato experimento)...")
    resumen_reel = generar_resumen_reel(historia_reel, restriccion_reel)
    print(f"✅ Resumen Reel: {len(resumen_reel.split())} palabras")

    # CORRECCIÓN: No buscar imagen de respaldo, el video generará sus propias 3 imágenes
    print(" El video generará 3 imágenes únicas desde Pexels automáticamente")
    image_reel_url = None  # <-- IMPORTANTE: Pasar None

    reel_video_url = None
    if CLOUDINARY_DISPONIBLE:
        reel_video_url = crear_y_subir_video(
            texto=resumen_reel,
            imagen_url=None,  # <-- CORREGIDO: Pasar None para que genere imágenes únicas
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
    descripcion_reel = f"🌙 {titulo_historia_reel}\n\n{resumen_reel}\n\n{hashtags_texto}\n\n_Imágenes de Pexels y voz generada con IA._"

    # ==========================================
    # 3. ENVIAR A MAKE
    # ==========================================
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
        r = requests.post(MAKE_WEBHOOK_URL_TERROR, json=payload, timeout=30)
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
        print(f" Error enviando a Make: {e}")

    print("🎉 Proceso completado")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f" Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
