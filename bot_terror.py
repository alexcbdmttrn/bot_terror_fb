from datetime import datetime
import json
import os
import random
import re
import sys
import time
import pytz
import requests

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL_TERROR = os.getenv("MAKE_WEBHOOK_URL_TERROR")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

ESTADO_FILE = "estado_terror.json"

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
# 💀 CTA FINAL ÚNICO (sin "Parte 2 mañana")
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
# CARGAR TEMAS DESDE JSON
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
# 🗂️ ESTADO SIMPLIFICADO
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
    lineas = [linea for linea in texto.split('\n') if linea.strip()]
    return '\n'.join(lineas).strip()

# ================================================================
# 🧑 DETECTAR PERSONAJE DEL RELATO
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
# 🎨 GENERAR PROMPT DE IMAGEN MODERNO
# ================================================================
def generar_prompt_imagen_moderno(historia, tema, personaje):
    genero = personaje.get("genero", "hombre")
    edad = personaje.get("edad_aprox", 35)
    descripcion_breve = personaje.get("descripcion_breve", "a 35-year-old Mexican person, contemporary clothing")
    
    if genero == "mujer":
        sujeto = f"a {edad}-year-old Mexican woman"
    else:
        sujeto = f"a {edad}-year-old Mexican man"
    
    prompt = f"""Genera un PROMPT DE IMAGEN EN INGLÉS para una fotografía cinematográfica vertical (aspect ratio 4:5).

Escena del relato: {limpiar_texto_para_imagen(historia)[:400]}

TEMA: {tema}

PERSONAJE DEL RELATO:
{descripcion_breve}

REGLAS DE COMPOSICIÓN CINEMATOGRÁFICA:
- PLANO: Wide angle o Medium shot. NUNCA primeros planos de caras.
- SUJETO PRINCIPAL: {sujeto} (DEBE coincidir con el género y edad del relato). Ocupa máximo 20-25% del encuadre.
- ENTORNO: Arquitectura o paisaje relacionado con "{tema}". CONTEMPORÁNEO 2026.
- ESTILO: {ESTILO_VISUAL_ACTUAL}
- PALETA DE COLOR: {PALETA_COLOR_ACTUAL}
- RESTRICCIONES: CERO caras en primer plano, CERO expresiones exageradas, CERO personas duplicadas, CERO texto, CERO gore.

PROHIBIDO usar palabras como: abandoned, decaying, rusty, rusted, vintage, antique, sepia, weathered, dilapidated, 1950s, 1970s, 1980s.

Formato de salida: SOLO el prompt en inglés, directo y sin introducciones.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 400,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        prompt_imagen += f", vertical composition 4:5, cinematic atmosphere, sharp focus, establishing shot, no faces close up, single person ({sujeto}) in distance, no duplicate people, no text, modern 2026 era, no vintage, no rusty, no decayed"
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return f"Vertical 4:5 cinematic photo, {sujeto} walking alone at distance in modern Mexican street at night, atmospheric fog, LED streetlamp lighting, mysterious mood, wide shot, no text, modern 2026 era, no vintage, no rusty"

# ================================================================
# 📖 GENERAR HISTORIA COMPLETA (SIN HASHTAGS en el prompt)
# ================================================================
def generar_historia_completa(tema):
    prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR un testimonio COMPLETO y AUTOCONCLUSIVO sobre:
"{tema}"

🚨 REGLAS ESTRICTAS:
- Ambientación: Mención EXACTA del lugar en México.
- Narración en PRIMERA PERSONA, como si la persona te lo estuviera contando a ti.
- Extensión: ENTRE 380 y 420 palabras. NI MÁS NI MENOS.
- ESTRUCTURA OBLIGATORIA:
  1. GANCHO inicial impactante (1-2 frases)
  2. CONTEXTO: quién es el narrador, dónde y cuándo ocurrió
  3. DESARROLLO: los hechos sobrenaturales paso a paso, con detalles sensoriales
  4. CLÍMAX: el momento más intenso del encuentro paranormal
  5. DESENLACE: cómo terminó todo y qué le quedó al narrador
- TERMINA la última oración completamente.
- El narrador debe tener género y edad identificables.
- Tono NATURAL Y COLOQUIAL, como alguien contando su experiencia real.
- Detalles específicos: nombres de lugares reales, años concretos, oficios reales.

Formato EXACTO de salida:
🌙 **[Título descriptivo del suceso]**

[Texto completo del testimonio, 380-420 palabras]

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
            texto_narrativo = '\n'.join(linea for linea in lineas if linea.strip() and not linea.strip().startswith('#') and not linea.strip().startswith('🌙'))
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
# 💀 AGREGAR CTA FINAL + HASHTAGS SIEMPRE AL FINAL
# ================================================================
def agregar_cta_final(texto):
    # 1. Quitar hashtags existentes (los re-agregaremos al final)
    texto = re.sub(r'#\w+', '', texto)
    
    # 2. Limpiar cualquier CTA previo
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
    
    # 3. Limpiar líneas vacías excesivas
    texto = "\n".join(linea for linea in texto.split("\n") if linea.strip())
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    
    # 4. Agregar CTA aleatorio
    cta = random.choice(CTAS_FINALES)
    
    # 5. 🆕 Agregar hashtags SIEMPRE al final (después del CTA)
    hashtags = "\n\n#LeyendasMexicanas #Terror #Misterio #Paranormal #Mexico"
    
    return texto.strip() + cta + hashtags

# ================================================================
# 🖼️ GENERAR IMAGEN CON AGNES AI (negative prompt moderno)
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
        print(f"🎨 Intento {intento}/{intentos} generando imagen vertical moderna...")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]
                print(f"✅ Imagen generada (1080x{height}) en el intento {intento}")
                return image_url
            else:
                print(f"❌ Error en Agnes AI: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

        if intento < intentos:
            print(f"⏳ Esperando {espera_segundos}s antes de reintentar...")
            time.sleep(espera_segundos)

    print(f"❌ No se pudo generar la imagen después de {intentos} intentos.")
    return None

# ================================================================
# 📤 ENVIAR A MAKE.COM
# ================================================================
def enviar_a_make(message, image_url):
    payload = {
        "message": message,
        "image_url": image_url,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        r = requests.post(MAKE_WEBHOOK_URL_TERROR, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado a Make.com")
            return True
        else:
            print(f"❌ Make respondió: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

# ================================================================
# MAIN
# ================================================================
def main():
    print("👻 Iniciando Bot de Terror (1 relato completo, 3x diarios)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        sys.exit(1)

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

    print(f"✅ Historia completa generada ({len(historia_base.split())} palabras)")

    # 🆕 Agregar CTA + hashtags SIEMPRE al final
    texto_final = agregar_cta_final(historia_base)
    print("✅ CTA final y hashtags agregados")

    print("🧑 Detectando personaje del relato...")
    personaje = detectar_personaje(historia_base)

    print("🎨 Generando prompt de imagen moderno...")
    prompt_imagen = generar_prompt_imagen_moderno(historia_base, tema, personaje)
    print(f"📝 Prompt de imagen: {prompt_imagen[:200]}...")

    image_url = generar_imagen_agnes(prompt_imagen, width=1080, height=1350, intentos=5, espera_segundos=15)

    if image_url is None:
        print("⚠️ Falló imagen tras todos los reintentos, usando placeholder")
        image_url = "https://via.placeholder.com/1080x1350/1a1a1a/ff0000?text=Terror"

    enviado = enviar_a_make(texto_final, image_url)

    if enviado:
        if tema not in estado.get("publicados", []):
            estado["publicados"].append(tema)
        estado["ultimo_tema"] = tema
        print(f"✅ Relato publicado: {tema}")
    else:
        print(f"⚠️ Relato NO publicado (error de Make). Tema no registrado.")

    guardar_estado(estado)
    print("🎉 Proceso completado")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
