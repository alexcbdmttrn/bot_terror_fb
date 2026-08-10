import requests
import random
import os
import json
import re
from datetime import datetime
import pytz

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
    "⏳ El tiempo se acaba. La Parte 2 mañana te dará el final. 👇"
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
        return ["casa embrujada en un pueblo mexicano", "apariciones en carreteras desiertas"]

# ================================================================
# ESTADO (con guardado mejorado)
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "historia_a": {"tema": "", "parte": 1, "completada": False},
            "historia_b": {"tema": "", "parte": 1, "completada": False},
            "publicados": []
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
# GENERAR PROMPT DE IMAGEN OPTIMIZADO PARA FACEBOOK (Vertical)
# ================================================================
def generar_prompt_imagen(historia, tema, parte):
    prompt = f"""Genera un PROMPT DE IMAGEN en ESPAÑOL para crear una foto vertical (4:5) de alta calidad para Facebook.
Basado en la historia: {historia[:300]}

REGLAS ESTRICTAS:
- La imagen debe ser VERTICAL (proporción 4:5, como para móvil).
- Enfoque en ROSTROS con EMOCIONES FUERTES (miedo, sorpresa, terror).
- Colores contrastantes: NEGRO, ROJO, NARANJA, BLANCO.
- Escenario nocturno, callejones, niebla, edificios coloniales, etc.
- Estilo: "fotografía cinematográfica, hiperrealista, 4k, ultradetallado".
- SIN sangre, SIN zombies, SIN gore.
- Las personas deben ser MEXICANAS de aspecto común, expresión natural.
- La imagen debe ser tan realista que parezca una foto real.

Formato de salida: SOLO el prompt de imagen, sin texto adicional.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 400}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        prompt_imagen += " Vertical format 4:5, cinematic photography, hyperrealistic, 4k, ultra detailed, no text, no words."
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return "Retrato vertical de terror en México, persona con expresión de miedo, callejón oscuro, niebla, estilo cinematográfico, 4k, no text"

# ================================================================
# GENERAR HISTORIA CON DEEPSEEK (max_tokens = 1200)
# ================================================================
def generar_historia_deepseek(tema, parte):
    if parte == 1:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR un testimonio REAL sobre el siguiente tema:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: El lugar específico mencionado en el tema.
- Narración en PRIMERA PERSONA.
- Usa frases típicas de testimonios reales: "en mi pueblo", "cuenta mi abuelo", "la gente dice", "yo mismo lo vi".
- Incluye DETALLES sensoriales: olores, sonidos, sensaciones.
- Describe las REACCIONES de la gente: miedo, incredulidad, respeto.
- Sé SOBRIO y DIRECTO.
- El FINAL debe ser un CLIFFHANGER.
- NO incluyas NINGÚN llamado a la Parte 2. NO uses frases como "mañana", "continuación", "Parte 2", etc. Yo lo agregaré después automáticamente.

Formato EXACTO:
🌙 **El [elemento misterioso] de [municipio], [estado]**

[Texto del testimonio en párrafos cortos, 400 palabras.]

#LeyendasMexicanas #Terror #Misterio
"""
    else:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR el DESENLACE del testimonio sobre el siguiente tema:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: El mismo lugar de la Parte 1.
- Narración en PRIMERA PERSONA.
- Usa frases como "lo que me dijeron después", "la versión que todos conocen".
- Da un DESENLACE basado en lo que la tradición oral cuenta.
- NO incluyas ningún llamado final (yo lo agregaré después).

Formato EXACTO:
🌙 **El [elemento misterioso] de [municipio], [estado]** - Parte 2

[Texto del desenlace en párrafos cortos, 400 palabras.]

#LeyendasMexicanas #Terror #Misterio
"""

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    # 🔥 max_tokens aumentado a 1200 para evitar textos cortados
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.85, "max_tokens": 1200}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return f"🌙 {tema} (Parte {parte})\n\n[Error al generar el testimonio.]"

# ================================================================
# AGREGAR LLAMADO A LA PARTE 2 (SIEMPRE, FORZADO)
# ================================================================
def agregar_llamado_parte2(texto, parte):
    if parte == 1:
        llamado = random.choice(VARIANTES_FINAL_PARTE1)
        # Limpiar cualquier llamado previo
        patrones = [
            r"📌.*?Parte 2.*?",
            r"🔮.*?continuación.*?",
            r"👁️.*?Parte 2.*?",
            r"🌙.*?continúa.*?",
            r"💀.*?Parte 2.*?",
            r"📌.*?mañana.*?",
            r"👻.*?mañana.*?",
            r"👇.*?mañana.*?"
        ]
        for patron in patrones:
            texto = re.sub(patron, "", texto, flags=re.IGNORECASE | re.DOTALL)
        texto = "\n".join(line for line in texto.split("\n") if line.strip())
        return texto + "\n\n" + llamado
    elif parte == 2:
        llamado = "\n\n💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇"
        patrones = [
            r"💀.*?Cuéntanos.*?",
            r"👇.*?comentarios.*?"
        ]
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
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt_limpio,
        "width": width,
        "height": height,
        "num_images": 1
    }
    
    try:
        print("🎨 Generando imagen vertical para Facebook...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
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
    payload = {"message": message, "image_url": image_url, "timestamp": datetime.now().isoformat()}
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
    print("👻 Iniciando Bot de Terror (Vertical 1080x1350)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")
    
    estado = cargar_estado()
    print(f"📖 Estado cargado: {estado}")
    
    # ================================================================
    # USAR RANGOS DE HORAS (CORRECCIÓN DE GEMINI)
    # ================================================================
    cdmx = pytz.timezone('America/Mexico_City')
    hora_cdmx = datetime.now(cdmx).hour
    print(f"🕒 Hora en CDMX: {hora_cdmx}:00 hs")
    
    # Selección robusta del bloque según el rango de horario
    if 13 <= hora_cdmx <= 17:  # 1 PM a 5 PM → historia_a (3 PM)
        clave = "historia_a"
    elif 19 <= hora_cdmx <= 23:  # 7 PM a 11 PM → historia_b (8 PM)
        clave = "historia_b"
    else:
        # Si está fuera de rango, elegir la que no esté completada
        if not estado["historia_a"]["completada"] and estado["historia_a"].get("tema"):
            clave = "historia_a"
        elif not estado["historia_b"]["completada"] and estado["historia_b"].get("tema"):
            clave = "historia_b"
        else:
            clave = random.choice(["historia_a", "historia_b"])
        print(f"⚠️ Horario no programado (hora CDMX: {hora_cdmx}), eligiendo: {clave}")
    
    historia = estado[clave]
    print(f"📖 {clave}: Parte {historia['parte']} - Tema: {historia['tema'] if historia['tema'] else 'Ninguno'}")
    
    # Si la historia está completada o no tiene tema, asignar nuevo tema
    if historia.get("completada", False) or not historia.get("tema"):
        print(f"🔄 {clave} completada o sin tema. Eligiendo nuevo tema...")
        nuevo_tema = obtener_tema_no_repetido(temas, estado)
        historia["tema"] = nuevo_tema
        historia["parte"] = 1
        historia["completada"] = False
        guardar_estado(estado)
        print(f"🌙 Nuevo tema para {clave}: {nuevo_tema}")
    
    tema = historia["tema"]
    parte = historia["parte"]
    
    print(f"📖 Publicando {clave}: {tema} - Parte {parte}")
    
    # Generar historia
    print("📝 Generando testimonio con DeepSeek...")
    texto = generar_historia_deepseek(tema, parte)
    texto = agregar_llamado_parte2(texto, parte)
    print("✅ Testimonio generado y llamado agregado")
    
    # Generar prompt de imagen vertical
    print("🎨 Generando prompt de imagen vertical...")
    prompt_imagen = generar_prompt_imagen(texto, tema, parte)
    print(f"📝 Prompt de imagen: {prompt_imagen[:150]}...")
    
    # Generar imagen vertical (1080x1350)
    image_url = generar_imagen_agnes(prompt_imagen, width=1080, height=1350)
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen vertical generada: {image_url}")
        enviar_a_make(texto, image_url)
    
    # Actualizar estado
    if parte == 1:
        if tema not in estado.get("publicados", []):
            estado["publicados"].append(tema)
            print(f"✅ Tema agregado al historial: {tema}")
        historia["parte"] = 2
        print(f"✅ {clave} pasa a Parte 2")
    elif parte == 2:
        historia["completada"] = True
        print(f"✅ {clave} completada (Parte 2 publicada)")
    
    guardar_estado(estado)
    print("🎉 Proceso completado")
    print(f"📖 Estado final: {estado}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
