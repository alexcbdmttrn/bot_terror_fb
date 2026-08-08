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
# LISTA DE ARQUETIPOS DE PERSONAJES (para variedad)
# ================================================================
ARQUETIPOS_PERSONAJES = [
    # Edad, vestimenta, postura, expresión
    "hombre de 40 años, sombrero de charro desgastado, camisa blanca arrugada, pantalón oscuro, botas de cuero, postura erguida pero tensa, rostro con rasgos mestizos marcados, barba de varios días, mirada seria y desafiante",
    "mujer de 30 años, vestido negro largo y holgado, cabello largo y suelto, rostro pálido, expresión triste y perdida, postura encorvada, manos entrelazadas",
    "niño de 10 años, ropa vieja y desgastada, cabello despeinado, rostro sucio, mirada asustada y curiosa, postura encogida como si tuviera frío",
    "hombre de 60 años, camisa de cuadros, pantalón de mezclilla, sombrero de paja, rostro arrugado y curtido, expresión seria, postura firme con las manos en los bolsillos",
    "mujer de 50 años, vestido de flores descolorido, rebozo, cabello recogido en un moño, rostro con arrugas profundas, expresión preocupada, postura recta con los brazos cruzados",
    "hombre de 25 años, chamarra de cuero, camiseta negra, pantalón oscuro, botas, rostro con rasgos jóvenes, expresión desafiante, postura relajada pero alerta",
    "mujer de 20 años, vestido blanco sencillo, cabello largo y oscuro, rostro de facciones finas, expresión melancólica, postura erguida con las manos juntas",
    "anciano de 70 años, camisa blanca, bastón de madera, sombrero de ala ancha, rostro marcado por el tiempo, expresión sabia y seria, postura encorvada apoyado en el bastón",
    "adolescente de 15 años, sudadera con capucha, jeans rasgados, tenis, rostro joven, expresión asustada y curiosa, postura encogida con las manos en las bolsas",
    "hombre de 45 años, traje oscuro desgastado, corbata floja, rostro serio y cansado, postura recta pero con los hombros caídos"
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
# GENERAR HISTORIA + PROMPT DE IMAGEN CON PERSONAJE VARIADO
# ================================================================
def generar_historia_deepseek(tema, parte):
    # Elegir un arquetipo de personaje al azar
    personaje = random.choice(ARQUETIPOS_PERSONAJES)
    
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
- NO incluyas ningún llamado a la Parte 2.

Formato EXACTO:
🌙 **El [elemento misterioso] de [municipio], [estado]**

[Texto del testimonio en párrafos cortos, 400 palabras.]

#LeyendasMexicanas #Terror #Misterio

===== PROMPT_IMAGEN =====
[Genera un prompt detallado para crear una imagen que represente la escena principal de esta historia. La imagen debe incluir un personaje con las siguientes características: {personaje}. Describe la escena con lujo de detalle, incluyendo lugar, hora, elementos del entorno (árboles, casas, caminos, niebla, etc.), colores predominantes, atmósfera, y la figura del personaje en su entorno. El personaje no debe mirar directamente a la cámara a menos que sea parte de la historia. **Evitar rostros genéricos, evitar poses de modelo de catálogo, evitar expresiones neutras.**]
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
- NO incluyas ningún llamado final.

Formato EXACTO:
🌙 **El [elemento misterioso] de [municipio], [estado]** - Parte 2

[Texto del desenlace en párrafos cortos, 400 palabras.]

#LeyendasMexicanas #Terror #Misterio

===== PROMPT_IMAGEN =====
[Genera un prompt detallado para crear una imagen que represente la escena principal de esta historia. La imagen debe incluir un personaje con las siguientes características: {personaje}. Describe la escena con lujo de detalle, incluyendo lugar, hora, elementos del entorno, colores predominantes, atmósfera, y la figura del personaje en su entorno. **Evitar rostros genéricos, evitar poses de modelo de catálogo, evitar expresiones neutras.**]
"""

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.85, "max_tokens": 700}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        respuesta = r.json()["choices"][0]["message"]["content"].strip()
        
        if "===== PROMPT_IMAGEN =====" in respuesta:
            partes = respuesta.split("===== PROMPT_IMAGEN =====")
            historia = partes[0].strip()
            prompt_imagen = partes[1].strip() if len(partes) > 1 else f"Escena de terror basada en: {tema}. Paisaje nocturno."
            # Añadir instrucciones anti-genéricas al prompt de imagen
            prompt_imagen += " Ultradetallado, fotorealista, 8k. Evitar rostros genéricos. Evitar poses de catálogo. Evitar sonrisas neutras. Dar rasgos distintivos."
            return {"historia": historia, "prompt_imagen": prompt_imagen}
        else:
            return {"historia": respuesta, "prompt_imagen": f"Escena de terror basada en: {tema}. Paisaje nocturno, atmósfera misteriosa. Ultradetallado, fotorealista, 8k. Evitar rostros genéricos."}
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return {"historia": f"🌙 {tema} (Parte {parte})\n\n[Error al generar el testimonio.]", "prompt_imagen": f"Escena de terror en {tema}"}

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
# GENERAR IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt_imagen):
    """
    Genera una imagen con Agnes AI usando el prompt generado por DeepSeek.
    """
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
    print("👻 Iniciando Bot de Terror (Personajes variados)")
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
    
    print("📝 Generando testimonio y prompt de imagen con DeepSeek...")
    resultado = generar_historia_deepseek(historia["tema"], historia["parte"])
    texto = resultado["historia"]
    prompt_imagen = resultado["prompt_imagen"]
    
    texto = agregar_llamado_parte2(texto, historia["parte"])
    print("✅ Testimonio generado y llamado agregado")
    print(f"🎨 Prompt de imagen: {prompt_imagen[:150]}...")
    
    image_url = generar_imagen_agnes(prompt_imagen)
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada con prompt personalizado")
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
