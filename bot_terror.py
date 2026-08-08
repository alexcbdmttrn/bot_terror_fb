import requests
import random
import os
import json
import re
from datetime import datetime

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
    "🌿 El terror no termina aquí. La Parte 2 mañana a la misma hora. 😨",
    "📌 ¿Ya sabes lo que pasó? La Parte 2 mañana te dará el desenlace. 👀",
    "🕯️ La historia aún respira. La Parte 2 llega mañana a la misma hora. 🌙",
    "💀 ¿Qué crees que pasó realmente? La Parte 2 mañana a la misma hora. 👇",
    "👁️ La respuesta está más cerca de lo que crees. Parte 2 mañana. 😱",
    "📌 No te quedes con la duda. La Parte 2 llega mañana a la misma hora. 🌙",
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
# ESTADO (con guardado forzado)
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "historia_a": {"tema": "", "parte": 1, "completada": False},
            "historia_b": {"tema": "", "parte": 1, "completada": False},
            "publicados": []
        }

def guardar_estado(estado):
    with open(ESTADO_FILE, "w") as f:
        json.dump(estado, f, indent=2)
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
# GENERAR HISTORIA CON DEEPSEEK (SIN LLAMADO)
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
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.85, "max_tokens": 650}
    
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
# GENERAR PROMPT DE IMAGEN
# ================================================================
def generar_prompt_imagen(historia, tema, parte):
    prompt = f"""Eres un EXPERTO EN DESCRIPCIÓN DE ESCENAS PARA IA GENERATIVA.

Tu tarea es crear un PROMPT DE IMAGEN detallado y visual basado en la siguiente historia de terror:

===== HISTORIA =====
{historia}
===== FIN DE LA HISTORIA =====

Basado en la historia, crea un prompt para generar una imagen que represente la escena principal, incluyendo:

1. **LUGAR Y AMBIENTACIÓN**: Describe el lugar exacto con detalles visuales.
2. **PERSONAJE(S)**: Describe al personaje principal tal como aparece en la historia.
3. **ELEMENTOS CLAVE**: Objetos o detalles importantes que aparecen en la historia.
4. **ATMOSFERA**: Estado de ánimo, colores predominantes, estilo de iluminación.

REGLAS ESTRICTAS:
- Prompt en ESPAÑOL.
- ULTRADETALLADO y VISUAL.
- Evitar descripciones genéricas.
- El personaje NO debe mirar directamente a la cámara.
- Incluir instrucciones para evitar rostros genéricos y poses de catálogo.

Formato de salida: solo el prompt de imagen.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 400}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt_imagen = r.json()["choices"][0]["message"]["content"].strip()
        prompt_imagen += " Ultrarrealista, 8k, hiperdetallado, estilo cinematográfico de terror. Evitar rostros genéricos, evitar poses de catálogo, evitar sonrisas neutras."
        return prompt_imagen
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return f"Escena de terror basada en: {tema}. Paisaje nocturno, atmósfera misteriosa, ultrarrealista, 8k, hiperdetallado. Evitar rostros genéricos."

# ================================================================
# GENERAR IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt_imagen):
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt_imagen, "width": 1024, "height": 1024, "num_images": 1}
    
    try:
        print("🎨 Generando imagen con Agnes AI...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            print("✅ Imagen generada")
            return image_url
        else:
            print(f"❌ Error en Agnes AI: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
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
    print("👻 Iniciando Bot de Terror (2 historias simultáneas)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")
    
    estado = cargar_estado()
    print(f"📖 Estado cargado: {estado}")
    
    # Determinar qué historia toca según la hora (3 PM = A, 8 PM = B)
    hora = datetime.now().hour
    if hora == 15:
        clave = "historia_a"
    elif hora == 20:
        clave = "historia_b"
    else:
        clave = random.choice(["historia_a", "historia_b"])
        print(f"⚠️ Horario no programado, eligiendo aleatorio: {clave}")
    
    historia = estado[clave]
    print(f"📖 {clave}: Parte {historia['parte']} - Tema: {historia['tema'] if historia['tema'] else 'Ninguno'}")
    
    # Si la historia está completada, resetear y elegir nuevo tema
    if historia.get("completada", False):
        print(f"🔄 {clave} completada. Eligiendo nuevo tema...")
        nuevo_tema = obtener_tema_no_repetido(temas, estado)
        historia["tema"] = nuevo_tema
        historia["parte"] = 1
        historia["completada"] = False
        guardar_estado(estado)  # Guardar después de asignar nuevo tema
        print(f"🌙 Nuevo tema para {clave}: {nuevo_tema}")
    
    # Si no tiene tema, elegir uno
    if not historia.get("tema"):
        nuevo_tema = obtener_tema_no_repetido(temas, estado)
        historia["tema"] = nuevo_tema
        historia["parte"] = 1
        historia["completada"] = False
        guardar_estado(estado)  # Guardar después de asignar nuevo tema
        print(f"🌙 Nuevo tema para {clave}: {nuevo_tema}")
    
    tema = historia["tema"]
    parte = historia["parte"]
    
    print(f"📖 Publicando {clave}: {tema} - Parte {parte}")
    
    # Generar historia
    print("📝 Generando testimonio con DeepSeek...")
    texto = generar_historia_deepseek(tema, parte)
    
    # Forzar el llamado a la Parte 2 (SIEMPRE)
    texto = agregar_llamado_parte2(texto, parte)
    print("✅ Testimonio generado y llamado agregado")
    
    # Generar prompt de imagen basado en la historia
    print("🎨 Generando prompt de imagen basado en la historia...")
    prompt_imagen = generar_prompt_imagen(texto, tema, parte)
    print(f"📝 Prompt de imagen: {prompt_imagen[:150]}...")
    
    # Generar imagen
    image_url = generar_imagen_agnes(prompt_imagen)
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada con prompt personalizado")
        enviar_a_make(texto, image_url)
    
    # Actualizar estado
    if parte == 1:
        if tema not in estado.get("publicados", []):
            estado["publicados"].append(tema)
            print(f"✅ Tema agregado al historial: {tema}")
    elif parte == 2:
        historia["completada"] = True
        print(f"✅ {clave} completada (Parte 2 publicada)")
    
    # Incrementar parte para la próxima ejecución
    historia["parte"] += 1
    guardar_estado(estado)  # Guardar al final
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
