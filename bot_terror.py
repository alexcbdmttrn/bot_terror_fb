from datetime import datetime
import json
import os
import random
import re
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
# VARIANTES PARA EL FINAL DE LA PARTE 1
# ================================================================
VARIANTES_FINAL_PARTE1 = [
    "📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇",
    "🔮 ¿Te atreves a imaginar lo que pasó después? La continuación mañana a la misma hora. 👻",
    "👁️ ¿Qué crees que encontró? No te pierdas la Parte 2 mañana a la misma hora. 😱",
    "🌙 La historia continúa mañana a la misma hora. ¿Estás listo para saber el desenlace? 👀",
    "💀 ¿Crees que sobrevivió? La Parte 2 te espera mañana. ¡No faltes! 😈",
    "📌 El misterio aún no termina. La Parte 2 llega mañana a la misma hora. 👇",
    "🌙 La oscuridad guarda más secretos. La Parte 2 mañana a la misma hora. 🕯️",
    "❓ ¿Tienes tu propia teoría? La Parte 2 llega mañana. ¡Te leemos en comentarios! 👇",
    "🌑 La noche guarda el secreto. La Parte 2 llega mañana a la misma hora. 👇",
    "💬 Cuéntanos tu teoría. La Parte 2 mañana a la misma hora. 👻",
    "🔦 ¿Qué crees que había detrás de la puerta? Parte 2 mañana. 🌙",
    "🕸️ El misterio teje su telaraña. La Parte 2 mañana a la misma hora. 😱",
    "📢 ¡Atención! La Parte 2 llega mañana. No te la pierdas. 👀",
    "🤔 ¿Tienes alguna teoría? Parte 2 mañana a la misma hora. 🌙",
    "⏳ El tiempo se acaba. La Parte 2 mañana te dará el final. 👇",
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
        return [
            "casa embrujada en un pueblo mexicano",
            "apariciones en carreteras desiertas",
        ]

# ================================================================
# ESTADO (Soporte para recordar el texto de la Parte 1)
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "historia_a": {
                "tema": "",
                "parte": 1,
                "completada": False,
                "texto_parte1": "",
            },
            "historia_b": {
                "tema": "",
                "parte": 1,
                "completada": False,
                "texto_parte1": "",
            },
            "publicados": [],
        }

def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    print(f"✅ Estado guardado correctamente en {ESTADO_FILE}")

def obtener_tema_no_repetido(temas, estado):
    publicados = set(estado.get("publicados", []))
    disponibles = [t for t in temas if t not in publicados]
    if not disponibles:
        print("🔄 Todos los temas ya han sido publicados. Reiniciando historial.")
        estado["publicados"] = []
        disponibles = temas
    return random.choice(disponibles)

# ================================================================
# LIMPIAR TEXTO PARA GUARDAR (eliminar emojis, llamados, hashtags)
# ================================================================
def limpiar_texto_parte1(texto):
    """Elimina emojis, hashtags y llamados para guardar solo el relato puro."""
    # Eliminar emojis
    texto = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF\U000024C2-\U0001F251]', '', texto)
    # Eliminar hashtags
    texto = re.sub(r'#\w+', '', texto)
    # Eliminar líneas que contengan "Parte 2" o "mañana" o "comentarios"
    lineas = texto.split('\n')
    lineas_limpias = []
    for linea in lineas:
        if not re.search(r'(Parte 2|mañana|comentarios|teoría)', linea, re.IGNORECASE):
            lineas_limpias.append(linea)
    texto = '\n'.join(lineas_limpias)
    # Eliminar saltos de línea excesivos
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()

# ================================================================
# GENERAR PROMPT DE IMAGEN AMBIENTAL Y CINEMATOGRÁFICO (Vertical 4:5)
# ================================================================
def generar_prompt_imagen(historia, tema, parte):
    prompt = f"""Genera un PROMPT DE IMAGEN EN INGLÉS para una fotografía cinematográfica vertical (aspect ratio 4:5).

Escena de la historia: {historia[:300]}

REGLAS DE COMPOSICIÓN CINEMATOGRÁFICA:
- PLANO: Wide angle or Medium shot (Plano general o plano medio). NUNCA primeros planos de caras ni rostros gigantes.
- ENFOQUE: La arquitectura colonial, callejones oscuros, niebla densa, iluminación de faroles antiguos, casas abandonadas, carreteras oscuras o paisajes nocturnos.
- SUJETOS: Un solo individuo de espaldas o a la distancia caminando, o un entorno totalmente vacío pero con vibra misteriosa.
- ESTILO: Cinema 35mm photograph, moody realistic lighting, dark teal and warm amber streetlights, atmospheric fog, high detail 4k.
- RESTRICCIONES: CERO caras en primer plano, CERO expresiones exageradas gritando, CERO personas duplicadas, CERO texto, CERO gore.

Formato de salida: SOLO el prompt en inglés, directo y sin introducciones.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
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
        prompt_imagen += ", vertical composition 4:5, cinematic atmosphere, sharp focus, establishing shot, no faces close up, single person in distance, no duplicate people, no text"
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return "Vertical 4:5 cinematic photo, dark empty Mexican colonial street at night, atmospheric fog, streetlamp lighting, mysterious mood, wide shot, no text"

# ================================================================
# GENERAR HISTORIA CON DEEPSEEK (CON CONTINUIDAD)
# ================================================================
def generar_historia_deepseek(tema, parte, texto_parte1=""):
    if parte == 1:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR la PARTE 1 de un testimonio REAL sobre:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: Mención exacta del lugar.
- Narración en PRIMERA PERSONA.
- Extensión: MÁXIMO 320 palabras. Asegúrate de TERMINAR la última oración completamente (no dejes frases a la mitad).
- El final debe ser un cliffhanger suspenso, pero concluyendo la frase.
- NO incluyas llamado a la Parte 2 (yo lo agregaré después).

Formato EXACTO:
🌙 **El [elemento misterioso] de [municipio], [estado]**

[Texto del testimonio]

#LeyendasMexicanas #Terror #Misterio
"""
    else:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es escribir la PARTE 2 Y FINAL del testimonio sobre: "{tema}".

AQUÍ TIENES EL TEXTO EXACTO DE LA PARTE 1 QUE YA SE PUBLICÓ:
\"\"\"
{texto_parte1}
\"\"\"

REGLAS ESTRICTAS DE CONTINUIDAD:
- DEBES MANTENER los mismos personajes, el mismo lugar específico y los mismos elementos mencionados en la Parte 1.
- Da el DESENLACE a los hechos ocurridos en la Parte 1.
- Extensión: MÁXIMO 320 palabras. Concluye totalmente todas las oraciones.
- NO incluyas ningún llamado a comentar final (yo lo agregaré después).

Formato EXACTO:
🌙 **El [mismo título de la Parte 1]** - Parte 2

[Texto del desenlace]

#LeyendasMexicanas #Terror #Misterio
"""

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 1000,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return f"🌙 {tema} (Parte {parte})\n\n[Error al generar el testimonio.]"

# ================================================================
# AGREGAR LLAMADO A LA PARTE 2
# ================================================================
def agregar_llamado_parte2(texto, parte):
    if parte == 1:
        llamado = random.choice(VARIANTES_FINAL_PARTE1)
        patrones = [
            r"📌.*?Parte 2.*?",
            r"🔮.*?continuación.*?",
            r"👁️.*?Parte 2.*?",
            r"🌙.*?continúa.*?",
            r"💀.*?Parte 2.*?",
            r"📌.*?mañana.*?",
            r"👻.*?mañana.*?",
            r"👇.*?mañana.*?",
        ]
        for patron in patrones:
            texto = re.sub(patron, "", texto, flags=re.IGNORECASE | re.DOTALL)
        texto = "\n".join(line for line in texto.split("\n") if line.strip())
        return texto + "\n\n" + llamado
    elif parte == 2:
        llamado = (
            "\n\n💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en"
            " comentarios. 👇"
        )
        patrones = [r"💀.*?Cuéntanos.*?", r"👇.*?comentarios.*?"]
        for patron in patrones:
            texto = re.sub(patron, "", texto, flags=re.IGNORECASE | re.DOTALL)
        texto = "\n".join(line for line in texto.split("\n") if line.strip())
        return texto + llamado
    return texto

# ================================================================
# GENERAR IMAGEN CON AGNES AI (VERTICAL 1080x1350)
# ================================================================
def generar_imagen_agnes(prompt, width=1080, height=1350):
    prompt_limpio = prompt[:500]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {AGNES_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt_limpio,
        "width": width,
        "height": height,
        "num_images": 1,
    }

    try:
        print("🎨 Generando imagen vertical para Facebook...")
        response = requests.post(
            url, headers=headers, json=payload, timeout=90
        )
        if response.status_code == 200:
            data = response.json()
            image_url = data["data"][0]["url"]
            print("✅ Imagen generada (1080x1350)")
            return image_url
        else:
            print(f"❌ Error en Agnes AI: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión con Agnes AI: {e}")
        return None

# ================================================================
# ENVIAR A MAKE.COM
# ================================================================
def enviar_a_make(message, image_url):
    payload = {
        "message": message,
        "image_url": image_url,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        r = requests.post(
            MAKE_WEBHOOK_URL_TERROR, json=payload, timeout=60
        )
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
    print("👻 Iniciando Bot de Terror (Vertical 1080x1350)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return

    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")

    estado = cargar_estado()

    cdmx = pytz.timezone("America/Mexico_City")
    hora_cdmx = datetime.now(cdmx).hour
    print(f"🕒 Hora en CDMX: {hora_cdmx}:00 hs")

    if 13 <= hora_cdmx <= 17:
        clave = "historia_a"
    elif 19 <= hora_cdmx <= 23:
        clave = "historia_b"
    else:
        if not estado["historia_a"]["completada"] and estado[
            "historia_a"
        ].get("tema"):
            clave = "historia_a"
        elif not estado["historia_b"]["completada"] and estado[
            "historia_b"
        ].get("tema"):
            clave = "historia_b"
        else:
            clave = random.choice(["historia_a", "historia_b"])

    historia = estado[clave]
    print(
        f"📖 {clave}: Parte {historia['parte']} - Tema:"
        f" {historia['tema'] if historia['tema'] else 'Ninguno'}"
    )

    if historia.get("completada", False) or not historia.get("tema"):
        print(f"🔄 {clave} completada o sin tema. Eligiendo nuevo tema...")
        nuevo_tema = obtener_tema_no_repetido(temas, estado)
        historia["tema"] = nuevo_tema
        historia["parte"] = 1
        historia["completada"] = False
        historia["texto_parte1"] = ""
        guardar_estado(estado)

    tema = historia["tema"]
    parte = historia["parte"]
    texto_parte1 = historia.get("texto_parte1", "")

    print(f"📖 Publicando {clave}: {tema} - Parte {parte}")

    print("📝 Generando testimonio con DeepSeek...")
    texto_base = generar_historia_deepseek(tema, parte, texto_parte1)

    # Si estamos en Parte 1, guardamos el texto puro (sin emojis ni llamados) para la Parte 2
    if parte == 1:
        texto_limpio = limpiar_texto_parte1(texto_base)
        historia["texto_parte1"] = texto_limpio
        print("✅ Texto de la Parte 1 guardado (limpio) para continuidad.")

    texto_final = agregar_llamado_parte2(texto_base, parte)
    print("✅ Testimonio generado y llamado agregado")

    print("🎨 Generando prompt de imagen vertical...")
    prompt_imagen = generar_prompt_imagen(texto_base, tema, parte)
    print(f"📝 Prompt de imagen: {prompt_imagen[:150]}...")

    image_url = generar_imagen_agnes(prompt_imagen, width=1080, height=1350)

    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto_final, None)
    else:
        print(f"✅ Imagen vertical generada: {image_url}")
        enviar_a_make(texto_final, image_url)

    if parte == 1:
        if tema not in estado.get("publicados", []):
            estado["publicados"].append(tema)
        historia["parte"] = 2
        print(f"✅ {clave} pasa a Parte 2")
    elif parte == 2:
        historia["completada"] = True
        historia["texto_parte1"] = ""
        print(f"✅ {clave} completada (Parte 2 publicada)")

    guardar_estado(estado)
    print("🎉 Proceso completado")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
