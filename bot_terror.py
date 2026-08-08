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
# 10 FORMATOS DE COMPOSICIÓN PARA IMÁGENES
# ================================================================
ESTILOS_IMAGEN = [
    # Formato 1: Paisaje nocturno con camino
    "Paisaje nocturno de México, camino de terracería que se pierde en la oscuridad, árboles secos y retorcidos a los lados, niebla baja y densa, cielo estrellado, iluminación tenue de luna, atmósfera de misterio y terror, ultrarrealista, 8k, hiperdetallado, composición cinematográfica, sin personas en primer plano, solo el paisaje como protagonista.",
    
    # Formato 2: Casa abandonada en la niebla
    "Casa abandonada en un pueblo de México, fachada descascarada con ventanas rotas, puerta de madera entreabierta, niebla densa que envuelve la estructura, maleza creciendo en el patio, árboles secos alrededor, iluminación nocturna tenue, ultrarrealista, 8k, hiperdetallado, estilo cinematográfico de terror, sin personas visibles, solo el lugar y su atmósfera.",
    
    # Formato 3: Bosque de árboles retorcidos
    "Bosque denso de árboles retorcidos y sin hojas en México, niebla baja y espesa entre los troncos, rocas cubiertas de musgo, arbustos secos, luz de luna filtrándose entre las ramas, atmósfera opresiva y terrorífica, ultrarrealista, 8k, hiperdetallado, sin personas en primer plano, solo el bosque como protagonista.",
    
    # Formato 4: Carretera desierta con neblina
    "Carretera desierta en México, asfalto agrietado, neblina densa que oculta el horizonte, árboles secos y arbustos a los lados, un vehículo abandonado en la cuneta cubierto de óxido, iluminación tenue de amanecer o atardecer, ultrarrealista, 8k, hiperdetallado, composición cinematográfica, sin personas en primer plano.",
    
    # Formato 5: Cementerio antiguo al atardecer
    "Cementerio antiguo en México, cruces de piedra cubiertas de musgo, flores marchitas en algunas tumbas, árboles secos alrededor, cielo de atardecer con tonos naranja y morado, niebla baja que se desliza entre las tumbas, atmósfera de terror y misterio, ultrarrealista, 8k, hiperdetallado, sin personas visibles.",
    
    # Formato 6: Río o lago oscuro con reflejos
    "Río de aguas oscuras y tranquilas en México, vegetación densa en las orillas, árboles con ramas que tocan el agua, reflejos de la luna en la superficie, niebla baja que se eleva desde el agua, atmósfera de misterio y terror, ultrarrealista, 8k, hiperdetallado, sin personas en primer plano.",
    
    # Formato 7: Montañas y barrancas con neblina
    "Paisaje montañoso de México, barrancas profundas cubiertas de neblina, vegetación árida y seca, cielo tormentoso con nubes oscuras, iluminación dramática con rayos de luz atravesando las nubes, ultrarrealista, 8k, hiperdetallado, sin personas visibles, solo el paisaje como protagonista.",
    
    # Formato 8: Pueblo fantasma al amanecer
    "Pueblo fantasma en México, calles de tierra y polvo, edificios abandonados con paredes descascaradas, ventanas sin vidrio, vegetación creciendo en las estructuras, amanecer con luz tenue y dorada, atmósfera de abandono y misterio, ultrarrealista, 8k, hiperdetallado, sin personas visibles.",
    
    # Formato 9: Cueva o gruta oscura
    "Cueva profunda en México, formaciones rocosas de estalactitas y estalagmitas, oscuridad predominante con luz tenue que entra desde la entrada, sombras alargadas, atmósfera opresiva y terrorífica, ultrarrealista, 8k, hiperdetallado, sin personas en primer plano.",
    
    # Formato 10: Puente viejo sobre río seco
    "Puente de piedra viejo en México, arco de piedra cubierto de musgo, río seco con piedras y arena, vegetación seca y árboles retorcidos alrededor, niebla baja y cielo gris, atmósfera de abandono y misterio, ultrarrealista, 8k, hiperdetallado, sin personas visibles."
]

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
# GENERAR HISTORIA CON DEEPSEEK
# ================================================================
def generar_historia_deepseek(tema, parte):
    if parte == 1:
        prompt = f"""Eres un INVESTIGADOR DE LEYENDAS URBANAS Y TRADICIÓN ORAL MEXICANA.

Tu tarea es DOCUMENTAR un testimonio REAL sobre el siguiente tema:
"{tema}"

IMPORTANTE: NO inventes una historia desde cero. ACTÚA como si estuvieras entrevistando a un habitante del lugar.

REGLAS ESTRICTAS:
- Ambientación: El lugar específico mencionado en el tema.
- Narración en PRIMERA PERSONA.
- Usa frases típicas de testimonios reales: "en mi pueblo", "cuenta mi abuelo", "la gente dice", "yo mismo lo vi".
- Incluye DETALLES sensoriales: olores, sonidos, sensaciones.
- Describe las REACCIONES de la gente: miedo, incredulidad, respeto.
- Sé SOBRIO y DIRECTO.
- El FINAL debe ser un CLIFFHANGER.
- NO incluyas ningún llamado a la Parte 2 (yo lo agregaré después).

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
# AGREGAR LLAMADO A LA PARTE 2
# ================================================================
def agregar_llamado_parte2(texto, parte):
    if parte == 1:
        llamado = random.choice(VARIANTES_FINAL_PARTE1)
        if "Parte 2" not in texto and "mañana" not in texto:
            return texto + "\n\n" + llamado
        return texto
    elif parte == 2:
        llamado = "\n\n💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇"
        if "Cuéntanos tu historia" not in texto:
            return texto + llamado
    return texto

# ================================================================
# GENERAR IMAGEN CON AGNES AI (10 FORMATOS DE COMPOSICIÓN)
# ================================================================
def generar_imagen_agnes(tema, parte):
    """
    Genera una imagen con Agnes AI usando uno de los 10 formatos de composición.
    """
    formato = random.choice(ESTILOS_IMAGEN)
    print(f"🎨 Formato seleccionado: {formato[:60]}...")
    
    if parte == 1:
        base = f"Escena de terror basada en: {tema}. "
    else:
        base = f"Momento culminante de terror basado en: {tema}. "
    
    prompt_completo = base + formato
    
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt_completo, "width": 1024, "height": 1024, "num_images": 1}
    
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
    print("👻 Iniciando Bot de Terror (10 formatos de composición)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL_TERROR, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    temas = cargar_temas()
    print(f"📚 {len(temas)} temas cargados")
    
    estado = cargar_estado()
    
    hora = datetime.now().hour
    if hora == 15:
        historia_key = "historia_a"
    elif hora == 20 or hora == 21 or hora == 22:
        historia_key = "historia_b"
    else:
        historia_key = random.choice(["historia_a", "historia_b"])
    
    historia = estado[historia_key]
    
    if historia.get("completada", False):
        historia["titulo"] = ""
        historia["parte"] = 1
        historia["tema"] = ""
        historia["completada"] = False
    
    if not historia["tema"]:
        historia["tema"] = random.choice(temas)
        historia["titulo"] = historia["tema"].split(',')[0].strip()
        print(f"🌙 Nuevo tema: {historia['titulo']}")
    
    print(f"📖 {historia_key}: Parte {historia['parte']}")
    
    print("📝 Generando testimonio con DeepSeek...")
    texto = generar_historia_deepseek(historia["tema"], historia["parte"])
    texto = agregar_llamado_parte2(texto, historia["parte"])
    print("✅ Testimonio generado y llamado agregado")
    
    image_url = generar_imagen_agnes(historia["tema"], historia["parte"])
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada con formato aleatorio")
        enviar_a_make(texto, image_url)
    
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
