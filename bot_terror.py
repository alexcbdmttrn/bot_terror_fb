import requests
import random
import os
import json
from datetime import datetime

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL_TERROR = os.getenv("MAKE_WEBHOOK_URL_TERROR")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

ESTADO_FILE = "estado_terror.json"

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
# ESTADO
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "historia_a": {"titulo": "", "parte": 1, "tema": "", "completada": False},
            "historia_b": {"titulo": "", "parte": 1, "tema": "", "completada": False}
        }

def guardar_estado(estado):
    with open(ESTADO_FILE, "w") as f:
        json.dump(estado, f, indent=2)

# ================================================================
# GENERAR HISTORIA CON DEEPSEEK (BASADA EN TESTIMONIOS REALES)
# ================================================================
def generar_historia_deepseek(tema, parte):
    if parte == 1:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR un testimonio REAL sobre el siguiente tema:
"{tema}"

IMPORTANTE: NO inventes una historia desde cero. ACTÚA como si estuvieras entrevistando a un habitante del lugar que te cuenta lo que la gente dice y ha vivido.

REGLAS ESTRICTAS:
- Ambientación: El lugar específico mencionado en el tema (investiga o infiere el municipio y estado).
- Narración en PRIMERA PERSONA, como si fueras el testigo que vivió o escuchó el relato de alguien de confianza.
- Usa frases típicas de testimonios reales: "en mi pueblo", "cuenta mi abuelo", "la gente dice", "yo mismo lo vi", "todos saben que", "desde que tengo memoria".
- Incluye DETALLES que la gente realmente menciona al contar estas historias: olores (a incienso, a tierra mojada, a humedad), sonidos (pasos, susurros, el viento), sensaciones (frío en la nuca, escalofríos).
- Describe las REACCIONES de la gente: miedo, incredulidad, respeto, silencio.
- NO uses lenguaje poético ni exagerado. Sé SOBRIO y DIRECTO, como si estuvieras contando algo que realmente pasó en tu comunidad.
- El FINAL debe ser un CLIFFHANGER: algo que quedó sin explicación, una pregunta sin respuesta, o una advertencia.
- Al FINAL, DEBES incluir este mensaje EXACTO:

"📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇"

Formato EXACTO (copia esto):
🌙 **El [elemento misterioso] de [municipio], [estado]**

[Texto del testimonio en párrafos cortos, 400 palabras, como si lo contara un habitante del lugar.]

📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇

#LeyendasMexicanas #Terror #Misterio
"""
    else:  # Parte 2
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR el DESENLACE del testimonio sobre el siguiente tema:
"{tema}"

IMPORTANTE: El desenlace debe ser lo que la gente del lugar dice que pasó realmente. Puede ser un final trágico, misterioso o sin resolver.

REGLAS ESTRICTAS:
- Ambientación: El mismo lugar de la Parte 1.
- Narración en PRIMERA PERSONA, continuando el testimonio.
- Usa frases como "lo que me dijeron después", "la versión que todos conocen", "dicen que al final".
- Da un DESENLACE basado en lo que la tradición oral cuenta: puede ser que el misterio nunca se resolvió, que alguien pagó las consecuencias, o que la historia sigue viva.
- El final debe ser impactante pero creíble.
- Al FINAL, incluye este mensaje EXACTO:

"💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇"

Formato EXACTO (copia esto):
🌙 **El [elemento misterioso] de [municipio], [estado]** - Parte 2

[Texto del desenlace en párrafos cortos, 400 palabras.]

💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇

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
# GENERAR IMAGEN CON AGNES AI (REALISTA Y PROPORCIONAL)
# ================================================================
def generar_imagen_agnes(tema, parte):
    if parte == 1:
        prompt = (
            f"{tema}, escena de terror realista, atmósfera de misterio, "
            "iluminación natural y dramática, niebla densa, colores oscuros "
            "negro, gris, rojo tenue, estilo fotografía de documental, "
            "sin exageraciones, todo proporcionado, 8k"
        )
    else:
        prompt = (
            f"{tema}, revelación del misterio, momento culminante, "
            "iluminación contrastada, sombras alargadas, colores intensos "
            "negro, rojo, morado, estilo cinematográfico realista, 8k"
        )
    
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt, "width": 1024, "height": 1024, "num_images": 1}
    
    try:
        print(f"🎨 Generando imagen para Parte {parte}...")
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
    print("👻 Iniciando Bot de Terror (Testimonios Reales)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    # Cargar temas desde el JSON
    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")
    
    estado = cargar_estado()
    
    # Determinar qué historia toca (3 PM = A, 8 PM = B)
    hora = datetime.now().hour
    if hora == 15:  # 3 PM
        historia_key = "historia_a"
    elif hora == 20 or hora == 21 or hora == 22:  # 8 PM o cercano
        historia_key = "historia_b"
    else:
        historia_key = random.choice(["historia_a", "historia_b"])
    
    historia = estado[historia_key]
    
    # Si la historia está completada, resetear
    if historia.get("completada", False):
        historia["titulo"] = ""
        historia["parte"] = 1
        historia["tema"] = ""
        historia["completada"] = False
    
    # Si no hay tema, generar uno nuevo
    if not historia["tema"]:
        historia["tema"] = random.choice(temas)
        historia["titulo"] = f"Testimonio sobre {historia['tema']}"
        print(f"🌙 Nuevo tema: {historia['titulo']}")
    
    print(f"📖 {historia_key}: Parte {historia['parte']} - {historia['tema']}")
    
    # Generar testimonio con DeepSeek
    print("📝 Generando testimonio con DeepSeek...")
    texto = generar_historia_deepseek(historia["tema"], historia["parte"])
    print("✅ Testimonio generado")
    
    # Generar imagen con Agnes AI
    image_url = generar_imagen_agnes(historia["tema"], historia["parte"])
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada: {image_url}")
        enviar_a_make(texto, image_url)
    
    # Actualizar estado (2 partes)
    historia["parte"] += 1
    if historia["parte"] > 2:
        historia["completada"] = True
        print("✅ Testimonio completado (2 partes)")
    
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
