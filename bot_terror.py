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
# VARIANTES PARA EL FINAL DE LA PARTE 1 (23 opciones)
# ================================================================
VARIANTES_FINAL_PARTE1 = [
    # Originales (15)
    "📌 ¿Qué crees que pasó después? La Parte 2 llega mañana a la misma hora. ¡No te la pierdas! 👇",
    "🔮 ¿Te atreves a imaginar lo que pasó después? La continuación mañana a la misma hora. 👻",
    "👁️ ¿Qué crees que encontró? No te pierdas la Parte 2 mañana a la misma hora. 😱",
    "🌙 La historia continúa mañana a la misma hora. ¿Estás listo para saber la verdad? 👀",
    "💀 ¿Crees que sobrevivió? La Parte 2 te espera mañana. ¡No faltes! 😈",
    "📌 El misterio aún no termina. La Parte 2 llega mañana a la misma hora. 👇",
    "🔥 ¿Qué pasaría si fuera cierto? Mañana la Parte 2 te dará la respuesta. 🌙",
    "👻 La oscuridad guarda más secretos. La Parte 2 mañana a la misma hora. 🕯️",
    "❓ ¿Tienes tu propia teoría? La Parte 2 llega mañana. ¡Te leemos en comentarios! 👇",
    "🌿 El terror no termina aquí. La Parte 2 mañana a la misma hora. 😨",
    "📌 ¿Ya sabes lo que pasó? La Parte 2 mañana te dará el desenlace. 👀",
    "🕯️ La historia aún respira. La Parte 2 llega mañana a la misma hora. 🌙",
    "💀 ¿Qué crees que pasó realmente? La Parte 2 mañana a la misma hora. 👇",
    "👁️ La respuesta está más cerca de lo que crees. Parte 2 mañana. 😱",
    "📌 No te quedes con la duda. La Parte 2 llega mañana a la misma hora. 🌙",
    # Nuevas (8)
    "⚠️ ¿Y si todo esto fue real? La Parte 2 mañana te lo confirma. 😨",
    "🌑 La noche guarda el secreto. La Parte 2 llega mañana a la misma hora. 👇",
    "💬 Cuéntanos tu teoría. La Parte 2 mañana a la misma hora. 👻",
    "🔦 ¿Qué crees que había detrás de la puerta? Parte 2 mañana. 🌙",
    "🕸️ El misterio teje su telaraña. La Parte 2 mañana a la misma hora. 😱",
    "📢 ¡Atención! La Parte 2 llega mañana. No te la pierdas. 👀",
    "🤔 ¿Tienes miedo de saber la verdad? Parte 2 mañana a la misma hora. 🌙",
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
# GENERAR HISTORIA CON DEEPSEEK (TESTIMONIO REAL)
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
- NO incluyas ningún llamado a la Parte 2 en el texto (yo lo agregaré después).

Formato EXACTO (copia esto):
🌙 **El [elemento misterioso] de [municipio], [estado]**

[Texto del testimonio en párrafos cortos, 400 palabras, como si lo contara un habitante del lugar.]

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
- NO incluyas ningún llamado final (yo lo agregaré después).

Formato EXACTO (copia esto):
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
# AGREGAR LLAMADO A LA PARTE 2 (CON VARIANTES)
# ================================================================
def agregar_llamado_parte2(texto, parte):
    """Agrega un llamado variado a la Parte 2 (si no está ya presente)."""
    if parte == 1:
        # Elegir un mensaje aleatorio de la lista
        llamado = random.choice(VARIANTES_FINAL_PARTE1)
        # Verificar si el mensaje ya está en el texto (por si DeepSeek lo puso)
        if "Parte 2" not in texto and "mañana" not in texto:
            return texto + "\n\n" + llamado
        else:
            # Si ya hay un llamado, no duplicarlo
            return texto
    elif parte == 2:
        llamado = "\n\n💀 ¿Te ha pasado algo parecido? Cuéntanos tu historia en comentarios. 👇"
        if "Cuéntanos tu historia" not in texto:
            return texto + llamado
    return texto

# ================================================================
# GENERAR IMAGEN CON AGNES AI (CON TEXTO Y COLORES TENEBROSOS)
# ================================================================
def generar_imagen_agnes(tema, parte, titulo_corto):
    """
    Genera una imagen con Agnes AI que incluye un título o frase corta
    con colores tenebrosos: negro, morado, naranja y blanco.
    """
    if parte == 1:
        prompt = (
            f"Escena de terror de {tema}, ambientación nocturna y tenebrosa. "
            f"Incluye el texto '{titulo_corto}' escrito con tipografía gótica estilizada "
            f"en la parte inferior de la imagen, con letras de color naranja brillante y "
            f"bordes blancos y morados. Fondo en tonos negros y morados oscuros. "
            f"Composición cinematográfica, niebla, iluminación dramática, "
            f"estilo de cartel de película de terror, 8k, hiperrealista."
        )
    else:
        prompt = (
            f"Momento culminante de terror en {tema}, revelación o giro final. "
            f"Incluye la frase corta '{titulo_corto} - Parte 2' en la parte superior "
            f"con letras de color blanco fantasmal y sombras moradas. "
            f"Colores dominantes: negro, morado, naranja intenso y blanco. "
            f"Estilo fotorrealista, atmósfera de terror, 8k."
        )
    
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt, "width": 1024, "height": 1024, "num_images": 1}
    
    try:
        print(f"🎨 Generando imagen con texto para Parte {parte}...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            print("✅ Imagen generada con texto")
            return image_url
        else:
            print(f"❌ Error en Agnes AI: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ================================================================
# EXTRAER TÍTULO CORTO DEL TEMA
# ================================================================
def extraer_titulo_corto(tema):
    """
    Extrae un título corto y llamativo del tema para ponerlo en la imagen.
    Ej: "El jinete sin sombra de la carretera a El Oro" -> "El jinete sin sombra"
    """
    # Intentar extraer la primera parte del tema (hasta la primera coma o "de")
    partes = tema.split(',')
    if len(partes) > 0:
        titulo = partes[0].strip()
        # Limitar a 50 caracteres
        if len(titulo) > 50:
            titulo = titulo[:47] + "..."
        return titulo
    # Si no hay coma, tomar los primeros 50 caracteres
    if len(tema) > 50:
        return tema[:47] + "..."
    return tema

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
    print("👻 Iniciando Bot de Terror (Imágenes con Texto)")
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
        historia["titulo"] = extraer_titulo_corto(historia["tema"])
        print(f"🌙 Nuevo tema: {historia['titulo']}")
    
    print(f"📖 {historia_key}: Parte {historia['parte']} - {historia['tema']}")
    
    # Generar testimonio con DeepSeek
    print("📝 Generando testimonio con DeepSeek...")
    texto = generar_historia_deepseek(historia["tema"], historia["parte"])
    
    # Agregar llamado a la Parte 2 (con variantes)
    texto = agregar_llamado_parte2(texto, historia["parte"])
    print("✅ Testimonio generado y llamado agregado")
    
    # Extraer título corto para la imagen
    titulo_imagen = extraer_titulo_corto(historia["tema"])
    if historia["parte"] == 2:
        titulo_imagen = titulo_imagen + " - Parte 2"
    
    # Generar imagen con Agnes AI (incluyendo título)
    image_url = generar_imagen_agnes(historia["tema"], historia["parte"], titulo_imagen)
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen con texto generada: {image_url}")
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
