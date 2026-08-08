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
# TEMAS DE TERROR
# ================================================================
TEMAS = [
    "casa embrujada en un pueblo mexicano",
    "apariciones en carreteras desiertas",
    "leyendas de hospitales abandonados",
    "ovnis en zonas rurales",
    "la llorona en tiempos modernos",
    "el charro negro en caminos solitarios",
    "fantasmas en antiguas haciendas",
    "brujas en el campo mexicano",
    "túneles secretos con historias ocultas",
    "cementerios con leyendas de ultratumba",
    "aparición en un puente viejo",
    "el niño que habla con los muertos",
    "la casa de los susurros",
    "el vagón del tren fantasma"
]

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
# GENERAR HISTORIA CON DEEPSEEK (2 PARTES)
# ================================================================
def generar_historia_deepseek(tema, parte):
    if parte == 1:
        prompt = f"""Eres un escritor de terror especializado en leyendas urbanas de México.

Escribe la PARTE 1 de una historia de terror de EXACTAMENTE 400 palabras, basada en este tema:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: Un municipio real de México.
- Narración en primera persona.
- Debe sonar como una anécdota real.
- Párrafos cortos, lenguaje sencillo, atmosférico.
- PRESENTA el misterio y DESARROLLA la tensión.
- El FINAL debe ser un CLIFFHANGER que obligue a leer la Parte 2.
- Al FINAL, DEBES incluir este mensaje EXACTO:

"📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇"

Formato EXACTO:
🌙 [Título: "El [elemento misterioso] de [municipio], [estado]"]

[Texto de la historia en párrafos cortos, 400 palabras.]

📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇

#LeyendasMexicanas #Terror #Misterio
"""
    else:  # Parte 2
        prompt = f"""Eres un escritor de terror especializado en leyendas urbanas de México.

Escribe la PARTE 2 (DESENLACE) de una historia de terror de EXACTAMENTE 400 palabras, basada en este tema:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: El mismo municipio de la Parte 1.
- Narración en primera persona.
- Debe sonar como una anécdota real.
- Párrafos cortos, lenguaje sencillo, atmosférico.
- Da el DESENLACE: revela qué pasó realmente, el giro final, o la conclusión terrorífica.
- Puede ser terrorífico, triste o con un final abierto pero impactante.
- Al FINAL, incluye este mensaje EXACTO:

"💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇"

Formato EXACTO:
🌙 [Título: "El [elemento misterioso] de [municipio], [estado]" - Parte 2]

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
        return f"🌙 {tema} (Parte {parte})\n\n[Error al generar la historia.]"

# ================================================================
# GENERAR IMAGEN CON AGNES AI (PROMPTS MEJORADOS)
# ================================================================
def generar_imagen_agnes(tema, parte):
    # Prompts más detallados y terroríficos según la parte
    if parte == 1:
        prompt = (
            f"{tema}, escena oscura y tenebrosa, atmósfera de terror, "
            "niebla densa, iluminación dramática con sombras alargadas, "
            "colores negro, rojo, naranja y morado, estilo cinematográfico de terror, "
            "hiperrealista, 8k, composición vertical para redes sociales"
        )
    else:  # Parte 2 - más intenso
        prompt = (
            f"{tema}, momento de máximo terror, revelación aterradora, "
            "figuras oscuras acechando, luz roja y naranja, sombras amenazantes, "
            "estilo cinematográfico de terror, hiperrealista, 8k, "
            "composición vertical para redes sociales"
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
    print("👻 Iniciando Bot de Terror")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    estado = cargar_estado()
    
    # Determinar qué historia toca (3 PM = A, 8 PM = B)
    hora = datetime.now().hour
    if hora == 15:  # 3 PM
        historia_key = "historia_a"
    elif hora == 20 or hora == 21 or hora == 22:  # 8 PM o cercano
        historia_key = "historia_b"
    else:
        # Si no coincide con los horarios, usar aleatorio
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
        historia["tema"] = random.choice(TEMAS)
        historia["titulo"] = f"Historia de {historia['tema']}"
        print(f"🌙 Nueva historia: {historia['titulo']}")
    
    print(f"📖 {historia_key}: Parte {historia['parte']} - {historia['tema']}")
    
    # Generar historia con DeepSeek
    print("📝 Generando historia con DeepSeek...")
    texto = generar_historia_deepseek(historia["tema"], historia["parte"])
    print("✅ Historia generada")
    
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
    if historia["parte"] > 2:  # SOLO 2 PARTES
        historia["completada"] = True
        print("✅ Historia completada (2 partes)")
    
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
