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
    "el vagón del tren fantasma",
    "la mujer de blanco en la carretera",
    "el pacto con el diablo en un pueblo minero",
    "la sombra que camina sola en el desierto"
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
# GENERAR HISTORIA CON DEEPSEEK (2 PARTES - REALISTA)
# ================================================================
def generar_historia_deepseek(tema, parte):
    if parte == 1:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS MEXICANAS, NO un escritor de ficción.

Tu tarea es DOCUMENTAR una historia de terror REALISTA basada en el siguiente tema:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: Un municipio REAL de México (investiga y elige uno con historia).
- Narración en PRIMERA PERSONA, como si fueras un testigo o familiar de los hechos.
- Incluye DETALLES SENSORIALES: olores (a tierra mojada, a incienso, a humedad), sonidos (pasos, susurros, el viento), texturas (frío en la piel, paredes ásperas).
- Describe EMOCIONES: miedo, incredulidad, paranoia, escalofríos.
- NO uses lenguaje poético ni exagerado. Sé sobrio, directo, como si estuvieras contando algo que realmente te pasó.
- El FINAL debe ser un CLIFFHANGER que genere intriga, NO un cierre definitivo.
- Al FINAL, DEBES incluir este mensaje EXACTO:

"📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇"

Formato EXACTO:
🌙 **El [elemento misterioso] de [municipio], [estado]**

[Texto de la historia en párrafos cortos, 400 palabras, como testimonio real.]

📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇

#LeyendasMexicanas #Terror #Misterio
"""
    else:  # Parte 2
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS MEXICANAS.

Tu tarea es DOCUMENTAR el DESENLACE de la historia de terror REALISTA basada en este tema:
"{tema}"

REGLAS ESTRICTAS:
- Ambientación: El mismo municipio de la Parte 1.
- Narración en PRIMERA PERSONA, continuando el testimonio.
- Incluye DETALLES SENSORIALES y EMOCIONES.
- Da un DESENLACE: revela qué pasó realmente, el giro final, o la conclusión terrorífica.
- Puede ser terrorífico, triste o con un final abierto pero impactante.
- NO uses lenguaje poético. Sé sobrio y directo.
- Al FINAL, incluye este mensaje EXACTO:

"💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇"

Formato EXACTO:
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
        return f"🌙 {tema} (Parte {parte})\n\n[Error al generar la historia.]"

# ================================================================
# GENERAR IMAGEN CON AGNES AI (REALISTA Y PROPORCIONAL)
# ================================================================
def generar_imagen_agnes(tema, parte, elemento_principal=None):
    """
    Genera imagen con Agnes AI, con prompts mejorados para realismo y proporción.
    elemento_principal: si se pasa, se enfatiza en la imagen (ej: "niño", "charro", "casa").
    """
    if parte == 1:
        if elemento_principal:
            base_prompt = f"Escena de terror en México, {elemento_principal} como centro de atención, atmósfera realista"
        else:
            base_prompt = f"Escena de terror en México, {tema}, atmósfera realista"
        
        prompt = (
            f"{base_prompt}, "
            "composición cinematográfica con profundidad de campo, "
            "elemento principal nítido y en primer plano, fondo desenfocado con niebla y sombras, "
            "iluminación dramática con luces y sombras naturales, "
            "colores oscuros: negro, gris, rojo sangre, naranja tenue, blanco fantasmal, "
            "estilo fotorrealista, texturas detalladas, 8k, "
            "aspecto de fotografía de alta calidad capturada en noche de luna, "
            "sin exageraciones, todo proporcionado según la importancia narrativa"
        )
    else:  # Parte 2 - desenlace
        if elemento_principal:
            base_prompt = f"Revelación terrorífica en México, {elemento_principal} en el centro de la escena"
        else:
            base_prompt = f"Desenlace de terror en México, {tema}, momento culminante"
        
        prompt = (
            f"{base_prompt}, "
            "composición con el elemento principal en primer plano, "
            "iluminación contrastada con destellos de luz roja y naranja, "
            "sombras alargadas que envuelven la escena, "
            "colores intensos: negro, rojo, morado, blanco, "
            "estilo fotorrealista, texturas detalladas, 8k, "
            "atmósfera de terror puro, sin elementos que distraigan, "
            "todo proporcionado según la importancia del elemento central"
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
# EXTRAER ELEMENTO PRINCIPAL DEL TEMA (para la imagen)
# ================================================================
def extraer_elemento_principal(tema):
    """
    Intenta extraer la palabra clave del tema para enfatizarla en la imagen.
    Ej: "casa embrujada" → "casa antigua", "el charro negro" → "charro negro".
    """
    palabras_clave = {
        "casa embrujada": "casa antigua abandonada",
        "apariciones": "figura fantasmal",
        "hospital abandonado": "hospital viejo y oscuro",
        "ovnis": "platillo volador metálico",
        "la llorona": "mujer de blanco",
        "charro negro": "jinete con sombrero negro",
        "fantasmas": "espectro translúcido",
        "brujas": "mujer con cabello largo y garras",
        "túneles secretos": "entrada oscura a un túnel",
        "cementerio": "tumbas y cruces",
        "puente viejo": "puente oxidado",
        "niño que habla con los muertos": "niño con mirada intensa",
        "casa de los susurros": "casa vieja con ventanas rotas",
        "vagón del tren fantasma": "vagón de tren oxidado",
        "mujer de blanco": "figura femenina con vestido blanco",
        "pacto con el diablo": "símbolo oscuro en el suelo",
        "sombra en el desierto": "silueta en la arena"
    }
    
    tema_lower = tema.lower()
    for clave, valor in palabras_clave.items():
        if clave in tema_lower:
            return valor
    # Si no coincide, devolver el primer sustantivo (simple)
    return tema.split()[0] if tema else "figura misteriosa"

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
    
    # Extraer elemento principal para enfatizar en la imagen
    elemento = extraer_elemento_principal(historia["tema"])
    print(f"🎯 Elemento principal destacado: {elemento}")
    
    # Generar imagen con Agnes AI (pasando el elemento principal)
    image_url = generar_imagen_agnes(historia["tema"], historia["parte"], elemento)
    
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
