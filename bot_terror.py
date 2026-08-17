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
# PALETAS Y ESTILOS (se usan en el prompt de imagen)
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

def limpiar_texto_para_imagen(texto):
    texto = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF\U000024C2-\U0001F251]', '', texto)
    texto = re.sub(r'#\w+', '', texto)
    texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
    return texto.strip()

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
    "vampiro": "a tall elegant figure in dark clothing, pale skin, subtle crimson glow in eyes, standing at distance among shadows",
    "lobo": "a massive dark silhouette of a wolf-like creature with faint amber eyes emerging from fog at distance",
    "monstruo": "a large dark shape with faint glowing eyes hidden in shadows at distance",
    "bruja": "a hunched silhouette in dark robes with a subtle greenish glow at distance",
    "fantasma": "a translucent pale figure with soft white glow at distance",
    "misterio": "a faint silhouette barely visible in the background",
}

def generar_prompt_imagen(historia, tema, personaje):
    tipo = detectar_tipo_entidad(tema)
    entidad = DIRECTRICES_ENTIDAD[tipo]
    
    genero = personaje.get("genero", "hombre")
    edad = personaje.get("edad_aprox", 35)
    if genero == "mujer":
        sujeto_humano = f"a {edad}-year-old Mexican woman"
    else:
        sujeto_humano = f"a {edad}-year-old Mexican man"
    
    # Prompt modificado para evitar palabras prohibidas por el filtro de contenido
    prompt = f"""Eres un DIRECTOR DE FOTOGRAFÍA CINEMATOGRÁFICA. Crea un PROMPT DE IMAGEN EN INGLÉS para una imagen VERTICAL (4:5) que represente la escena más icónica de la siguiente historia.

HISTORIA:
\"\"\"
{limpiar_texto_para_imagen(historia)[:400]}
\"\"\"
TEMA: {tema}
ENTIDAD: {tipo}
PERSONAJE HUMANO: {sujeto_humano}

🎬 ESTILO VISUAL:
- Cinematic still from a mystery thriller film, dramatic atmospheric lighting, volumetric fog
- High contrast with deep shadows and one dominant color accent (cool cyan, warm amber, or muted green)
- Subtle glow on supernatural elements
- Moonlight or ambient city light, anamorphic lens feel, shallow depth of field
- Rich cinematic color grading, modern movie poster composition

📐 COMPOSICIÓN:
- Wide or medium-wide shot, vertical 4:5
- Entorno arquitectónico o natural: callejones, plazas, bosques, carreteras, interiores históricos
- ENTIDAD: {entidad} — siempre a distancia o entre sombras, integrada en la atmósfera, NUNCA en primer plano
- HUMANO: {sujeto_humano} — de espaldas o a distancia, ocupando máximo 20-25% del encuadre
- Exactamente una figura humana y una entidad

🚫 PROHIBIDO: gore, sangre, heridas, mutilaciones, caras deformes, texto, logotipos, multitudes, personas duplicadas.

Devuelve SOLO el prompt en inglés, sin explicaciones adicionales.
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
        # Añadir filtro de palabras prohibidas para Agnes
        palabras_prohibidas = ["horror", "terrifying", "scary", "blood", "gore", "violent", "murder", "killing", "corpse", "dead", "zombie", "ghostly", "spectral", "eerie", "creepy", "menacing", "sinister", "evil", "demonic"]
        for palabra in palabras_prohibidas:
            prompt_imagen = re.sub(r'\b' + palabra + r'\b', '', prompt_imagen, flags=re.IGNORECASE)
        prompt_imagen += ", vertical 4:5, cinematic mood, atmospheric, no violence, no blood"
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return f"Vertical 4:5 cinematic scene, mysterious atmosphere, {entidad} in the distance, atmospheric lighting, no violence"

def generar_historia_completa(tema):
    prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR un testimonio COMPLETO y AUTOCONCLUSIVO sobre:
"{tema}"

🚨 REGLAS ESTRICTAS:
- Ambientación: Mención EXACTA del lugar en México.
- Narración en PRIMERA PERSONA, como si la persona te lo estuviera contando a ti.
- El narrador debe tener un PERFIL ÚNICO Y DIVERSO (edad, género, oficio).
- Extensión: EXACTAMENTE 300-340 palabras. DEBES contar las palabras y asegurarte de que esté en ese rango.
- ESTRUCTURA en PÁRRAFOS separados por línea en blanco:
  1. Gancho inicial
  2. Contexto: quién, dónde, cuándo
  3. Desarrollo de los hechos (2-3 párrafos)
  4. Clímax
  5. Desenlace
- Tono natural y coloquial.
- Detalles específicos: nombres reales, años, oficios.
- TERMINA la última oración completamente.

Formato:
🌙 **[Título]**

[Párrafo 1]

[Párrafo 2]

[...]

(NO incluyas hashtags ni llamadas a comentar)
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
            
            # Contar palabras (solo parte narrativa, sin título)
            lineas = resultado.split('\n')
            texto_narrativo = '\n'.join(linea for linea in lineas if linea.strip() and not linea.strip().startswith('🌙'))
            palabras = len(texto_narrativo.split())
            print(f"   📊 Palabras generadas: {palabras}")
            
            # Si excede las 340, truncar o reintentar. En lugar de truncar, reintentamos.
            if palabras > 380:
                print(f"   ⚠️ Demasiado largo ({palabras} palabras). Reintentando...")
                raise ValueError("Historia demasiado larga")
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

def agregar_cta_final(texto):
    # Quitar hashtags existentes y CTAs previos
    texto = re.sub(r'#\w+', '', texto)
    patrones = [r"💀.*?comentarios.*?", r"👇.*?comentarios.*?", r"👻.*?comentarios.*?", r"🌙.*?comentarios.*?", r"👁️.*?comentarios.*?", r"🔮.*?experiencia.*?"]
    for patron in patrones:
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE | re.DOTALL)
    
    # Mantener párrafos: solo reducir líneas vacías excesivas
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    
    cta = random.choice(CTAS_FINALES)
    hashtags = "\n\n#LeyendasMexicanas #Terror #Misterio #Paranormal #Mexico"
    leyenda_ia = "\n\n_Imágenes generadas con IA_"
    
    return texto.strip() + cta + hashtags + leyenda_ia

def generar_imagen_agnes(prompt, width=1080, height=1350, intentos=5, espera_segundos=15):
    prompt_limpio = prompt[:800]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    
    # Negative prompt más restrictivo para evitar contenido prohibido
    negative = (
        "gore, blood, violence, murder, dead body, corpse, mutilation, "
        "close-up face, portrait, headshot, person filling frame, "
        "deformed face, disfigured, bad anatomy, extra limbs, "
        "duplicate people, multiple subjects, text, watermark, "
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
                print(f"✅ Imagen generada en el intento {intento}")
                return image_url
            else:
                print(f"❌ Error en Agnes AI: {response.status_code} - {response.text[:200]}")
                # Si el error es por contenido, no reintentamos con el mismo prompt
                if "content_policy_violation" in response.text:
                    print("⚠️ Violación de política de contenido. No se reintentará con este prompt.")
                    return None
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

        if intento < intentos:
            print(f"⏳ Esperando {espera_segundos}s antes de reintentar...")
            time.sleep(espera_segundos)

    return None

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

def main():
    print("👻 Iniciando Bot de Terror (1 relato completo, 300-340 palabras)")
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

    print(f"✅ Historia completa generada ({len(historia_base.split())} palabras aprox)")

    print("🧑 Detectando personaje del relato...")
    personaje = detectar_personaje(historia_base)

    print("🎨 Generando prompt de imagen cinematográfico...")
    prompt_imagen = generar_prompt_imagen(historia_base, tema, personaje)
    print(f"📝 Prompt de imagen: {prompt_imagen[:200]}...")

    image_url = generar_imagen_agnes(prompt_imagen, width=1080, height=1350, intentos=5, espera_segundos=15)

    if image_url is None:
        print("⚠️ Falló imagen, usando placeholder")
        image_url = "https://via.placeholder.com/1080x1350/1a1a1a/ff0000?text=Terror"

    texto_final = agregar_cta_final(historia_base)
    print("✅ CTA, hashtags y leyenda IA agregados")

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
