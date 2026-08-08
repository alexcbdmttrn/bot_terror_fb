import requests
import random
import os
import json
from datetime import datetime

# ================================================================
# CONFIGURACIÓN (variables desde GitHub Secrets)
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL_TERROR = os.getenv("MAKE_WEBHOOK_URL_TERROR")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

# ================================================================
# ESTADO: controla qué historia y parte toca publicar
# ================================================================
ESTADO_FILE = "estado_terror.json"

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
# GENERAR HISTORIA CON DEEPSEEK (Parte 1, 2 o 3)
# ================================================================
def generar_historia_deepseek(tema, parte):
    prompt = f"""Eres un escritor de terror especializado en leyendas urbanas de México.

Escribe la PARTE {parte} de una historia de terror de EXACTAMENTE 400 palabras, basada en este tema:
"{tema}"

Requisitos:
- Ambientación: Un municipio real de México (elige uno al azar).
- Narración en primera persona (testimonio).
- Debe sonar como una anécdota real (usa frases como "en mi pueblo", "cuenta mi abuelo", "yo mismo lo vi").
- Estilo: párrafos cortos, lenguaje sencillo, atmosférico.
- La Parte 1 debe presentar el misterio y terminar con un cliffhanger.
- La Parte 2 debe desarrollar la tensión y terminar con un giro o revelación.
- La Parte 3 debe dar el desenlace (puede ser terrorífico o emotivo).

Formato EXACTO:
🌙 [Título: "El [elemento misterioso] de [municipio], [estado]"]

[Texto de la historia en párrafos cortos, sin viñetas, con saltos de línea.]

📌 ¿Qué crees que pasó después? La Parte {parte+1} llega mañana a la misma hora.
Te espero en comentarios. 👇

#LeyendasMexicanas #Terror #Misterio
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
# GENERAR IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt):
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt, "width": 1024, "height": 1024, "num_images": 1}
    
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
    
    # Validar variables
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    # Cargar estado
    estado = cargar_estado()
    
    # Determinar qué historia toca (3 PM = A, 8 PM = B)
    hora = datetime.now().hour
    historia_key = "historia_a" if hora == 15 else "historia_b"  # 3 PM = 15, 8 PM = 20
    historia = estado[historia_key]
    
    # Si la historia ya está completada, resetear
    if historia.get("completada", False):
        historia["titulo"] = ""
        historia["parte"] = 1
        historia["tema"] = ""
        historia["completada"] = False
    
    # Si no hay tema, generar uno nuevo
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
    
    # Generar historia con DeepSeek
    print("📝 Generando historia con DeepSeek...")
    texto = generar_historia_deepseek(historia["tema"], historia["parte"])
    print("✅ Historia generada")
    
    # Generar imagen con Agnes AI
    prompt_img = f"{historia['tema']}, atmósfera de terror, estilo cinematográfico, 8k"
    image_url = generar_imagen_agnes(prompt_img)
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada: {image_url}")
        enviar_a_make(texto, image_url)
    
    # Actualizar estado
    historia["parte"] += 1
    if historia["parte"] > 3:
        historia["completada"] = True
        print("✅ Historia completada (3 partes)")
    
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
