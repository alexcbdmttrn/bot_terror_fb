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
# GENERAR HISTORIA CON DEEPSEEK (Parte 1 o 2)
# ================================================================
def generar_historia_deepseek(tema, parte):
    if parte == 1:
        final_parte = """
Al final de la Parte 1, DEBES incluir EXACTAMENTE este texto:

"📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora.  
Te espero en comentarios. 👇"
"""
    else:
        final_parte = """
Al final de la Parte 2, DEBES incluir un cierre con un giro final y este mensaje:

"📌 ¿Te ha pasado algo parecido? Cuéntanos en comentarios. 👇"
"""

    prompt = f"""Eres un escritor de terror especializado en leyendas urbanas de México.

Escribe la PARTE {parte} de una historia de terror de EXACTAMENTE 400 palabras, basada en este tema:
"{tema}"

Requisitos:
- Ambientación: Un municipio real de México (elige uno al azar).
- Narración en primera persona (testimonio).
- Debe sonar como una anécdota real (usa frases como "en mi pueblo", "cuenta mi abuelo", "yo mismo lo vi").
- Estilo: párrafos cortos, lenguaje sencillo, atmosférico.
- La Parte 1 debe presentar el misterio y terminar con un cliffhanger.
- La Parte 2 debe dar el desenlace (puede ser terrorífico o emotivo).

{final_parte}

Formato EXACTO (como ejemplo):
🌙 **El Charro Negro de Jilotepec, Estado de México**

[Texto de la historia en párrafos cortos, 400 palabras.]

[LLAMADO FINAL según la parte]
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.8, "max_tokens": 600}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return f"🌙 {tema} (Parte {parte})\n\n[Error al generar la historia.]"

# ================================================================
# GENERAR IMAGEN CON AGNES AI (prompts mejorados)
# ================================================================
def generar_imagen_agnes(tema, parte):
    if parte == 1:
        prompt_img = f"{tema}, atmósfera de terror oscura, niebla densa, colores negro y naranja, siluetas amenazantes, estilo cinematográfico de terror, 8k, hiperrealista, fotografía nocturna con luz tenue"
    else:
        prompt_img = f"{tema}, desenlace terrorífico, luces rojas y moradas, sombras alargadas, criaturas acechando, estilo cinematográfico de terror, 8k, hiperrealista"

    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt_img, "width": 1024, "height": 1024, "num_images": 1}
    
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
    print("👻 Iniciando Bot de Terror")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    estado = cargar_estado()
    hora = datetime.now().hour
    historia_key = "historia_a" if hora == 15 else "historia_b"
    historia = estado[historia_key]
    
    if historia.get("completada", False):
        historia["titulo"] = ""
        historia["parte"] = 1
        historia["tema"] = ""
        historia["completada"] = False
    
    if not historia["tema"]:
        temas = [
            "casa embrujada en un pueblo mexicano",
            "apariciones en carreteras desiertas",
            "leyendas de hospitales abandonados",
            "ovnis en zonas rurales",
            "la llorona en tiempos modernos",
            "el charro negro en caminos solitarios",
            "fantasmas en antiguas haciendas",
            "brujas en el campo mexicano",
            "túneles secretos con historias ocultas",
            "cementerios con leyendas de ultratumba"
        ]
        historia["tema"] = random.choice(temas)
        historia["titulo"] = f"Historia de {historia['tema']}"
        print(f"🌙 Nueva historia: {historia['titulo']}")
    
    print(f"📖 {historia_key}: Parte {historia['parte']} - {historia['tema']}")
    
    print("📝 Generando historia con DeepSeek...")
    texto = generar_historia_deepseek(historia["tema"], historia["parte"])
    print("✅ Historia generada")
    
    image_url = generar_imagen_agnes(historia["tema"], historia["parte"])
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada: {image_url}")
        enviar_a_make(texto, image_url)
    
    historia["parte"] += 1
    if historia["parte"] > 2:  # Solo 2 partes
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
