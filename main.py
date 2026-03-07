import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
from flask import Flask
from threading import Thread

# Pon tu Token aquí
TOKEN = '8655781619:AAEq_r9WHinAsFSwj5femv_7xCGPMAl6QZw'
bot = telebot.TeleBot(TOKEN)

# Memoria global para la paginación
user_sessions = {}

# ==========================================
# 1. MENÚ Y MANEJO DE SINTAXIS FLEXIBLE
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    texto = (
        " Bienvenido a la <b>Biblioteca </b> 📚\n\n"
        "<b>¿CÓMO FUNCIONO?</b>\n"
        "El es <code>/buscar</code> seguido del título del libro.\n"
        "👉 <i>Básico:</i> <code>/buscar el principito</code>\n\n"
        " <b>FILTROS  (Úsalos en cualquier orden):</b>\n"
        "📱 <b>Solo Kindle:</b> Escribe <code>kindle</code> para filtrar solo formatos compatibles con e-readers (EPUB, MOBI, AZW3).\n"
        "✍️ <b>Autor:</b> Pon el nombre del autor entre paréntesis <code>(autor)</code>.\n"
        "🌍 <b>Idioma:</b> Pon el idioma entre corchetes <code>[es]</code>, <code>[ing]</code>, <code>[english]</code>...\n\n"
        " <b>EJEMPLOS DE BÚSQUEDAS:</b>\n"
        "• <code>/buscar habitos atomicos kindle</code>\n"
        "• <code>/buscar a good girls guide to murder (holly jackson) kindle [ing]</code>\n\n"
        "➡️ <b>NAVEGACIÓN:</b>\n"
        "Si la búsqueda tiene muchos resultados, usa el comando <code>/siguiente</code> para ver la próxima página.\n\n"
        "Bot diseñado por Jorge Pérez Vallejo"
    )
    bot.send_message(message.chat.id, texto, parse_mode='HTML')

@bot.message_handler(commands=['buscar', 'search'])
def handle_search(message):
    raw_query = message.text.replace('/buscar', '').replace('/search', '').strip()
    
    if len(raw_query) > 0:
        is_kindle_only = False
        lang = 'es' # Español por defecto
        author = ""
        
        # 1. Detectar KINDLE (da igual si es Kindle, KINDLE o kindle)
        if re.search(r'\bkindle\b', raw_query, re.IGNORECASE):
            is_kindle_only = True
            raw_query = re.sub(r'\bkindle\b', '', raw_query, flags=re.IGNORECASE).strip()

        # 2. Detectar AUTOR entre paréntesis ()
        match_author = re.search(r'\((.*?)\)', raw_query)
        if match_author:
            author = match_author.group(1).strip()
            raw_query = re.sub(r'\(.*?\)', '', raw_query).strip()

        # 3. Detectar IDIOMA entre corchetes [] y unificarlo
        match_lang = re.search(r'\[(.*?)\]', raw_query)
        if match_lang:
            raw_lang = match_lang.group(1).lower()
            lang_map = {
                'es': 'es', 'esp': 'es', 'español': 'es', 'spanish': 'es',
                'en': 'en', 'ing': 'en', 'ingles': 'en', 'english': 'en'
            }
            # Si escribes algo raro, se queda con lo que pusiste, si no, lo traduce
            lang = lang_map.get(raw_lang, raw_lang)
            raw_query = re.sub(r'\[.*?\]', '', raw_query).strip()
            
        # Limpiar dobles espacios que hayan quedado al robar palabras
        raw_query = re.sub(r'\s+', ' ', raw_query)
            
        execute_search(message.chat.id, raw_query, 0, lang, is_kindle_only, author, source='api')
    else:
        bot.send_message(message.chat.id, "⚠️ Dime qué buscar. (Ejemplo: <code>/buscar el resplandor</code>)", parse_mode='HTML')

@bot.message_handler(commands=['siguiente'])
def handle_next(message):
    chat_id = message.chat.id
    if chat_id in user_sessions:
        s = user_sessions[chat_id]
        if s['source'] == 'api':
            execute_search(chat_id, s['query'], s['offset'], s['lang'], s['is_kindle_only'], s['author'], source='api')
        else:
            execute_shadow_search(chat_id, s['query'], s['offset'], s['lang'], s['is_kindle_only'], s['author'], s.get('fallback_lang', False))
    else:
        bot.send_message(chat_id, "⚠️ No hay resultados anteriores para mostrar.", parse_mode='HTML')

# ==========================================
# 2. MOTOR A: BÚSQUEDA LEGAL (API)
# ==========================================
def execute_search(chat_id, query, offset, lang, is_kindle_only, author, source='api'):
    if offset == 0:
        bot.send_message(chat_id, f"🔍 Buscando: <b>{query}</b> [{lang.upper()}]...", parse_mode='HTML')
    
    try:
        search_term = f"{query} {author}".strip()
        url = f"https://gutendex.com/books/?search={urllib.parse.quote(search_term)}&languages={lang}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['count'] > offset:
                limit = 4
                books = data['results'][offset:offset+limit]
                
                texto = f"🏛️ <b>Resultados Oficiales:</b>\n<i>Selecciona uno:</i>"
                markup = InlineKeyboardMarkup(row_width=1)

                for book in books:
                    short_title = book['title'][:35] + "..." if len(book['title']) > 35 else book['title']
                    markup.add(InlineKeyboardButton(f"📖 {short_title}", callback_data=f"book:{book['id']}"))

                if data['count'] > offset + limit:
                    user_sessions[chat_id] = {'query': query, 'lang': lang, 'offset': offset + limit, 'is_kindle_only': is_kindle_only, 'author': author, 'source': 'api'}
                    texto += "\n\n👉 <i>Escribe /siguiente para ver más legales.</i>"
                else:
                    user_sessions[chat_id] = {'query': query, 'lang': lang, 'offset': 0, 'is_kindle_only': is_kindle_only, 'author': author, 'source': 'shadow', 'fallback_lang': False}
                    texto += "\n\n👉 <i>Escribe /siguiente para buscar en servidores externos.</i>"

                bot.send_message(chat_id, texto, reply_markup=markup, parse_mode='HTML')
                return 
    except Exception as e:
        pass

    # FALLBACK A ANNA'S ARCHIVE
    bot.send_message(chat_id, "⏳ Continuando con la búsqueda profunda...", parse_mode='HTML')
    execute_shadow_search(chat_id, query, 0, lang, is_kindle_only, author, fallback_lang=False)

# ==========================================
# 3. MOTOR B: WEB SCRAPING Y FILTRO DE IDIOMA
# ==========================================
def execute_shadow_search(chat_id, query, offset, lang, is_kindle_only, author, fallback_lang):
    search_term = f"{query} {author}".strip()
    url_objetivo = f"https://annas-archive.gl/search?q={urllib.parse.quote(search_term)}"
    
    # Si no estamos en modo "todos los idiomas", le pegamos la etiqueta de idioma
    if lang and not fallback_lang:
        url_objetivo += f"&lang={lang}"
        
    cabeceras = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9"
    }

    try:
        respuesta = requests.get(url_objetivo, headers=cabeceras, timeout=15)
        if respuesta.status_code != 200:
            return bot.send_message(chat_id, "❌ Servidor inalcanzable en este momento.")

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        resultados_brutos = soup.select('div.flex.pt-3.pb-3')
        
        resultados_validos = []
        for item in resultados_brutos:
            titulo = ""
            enlace = ""
            for a in item.find_all('a', href=True):
                if '/md5/' in a['href'] and a.get_text(strip=True):
                    titulo = a.get_text(strip=True)
                    enlace = "https://annas-archive.gl" + a['href']
                    break
            
            if not titulo: continue 

            textos_puros = list(item.stripped_strings)
            info_doc = ""
            for cadena in textos_puros:
                if any(x in cadena.upper() for x in ['MB', 'KB', 'EPUB', 'PDF', 'MOBI', 'AZW3', 'FB2']):
                    info_doc = cadena
                    break
            
            info_upper = info_doc.upper()
            has_pdf = 'PDF' in info_upper
            has_kindle = any(fmt in info_upper for fmt in ['EPUB', 'MOBI', 'AZW3'])

            if is_kindle_only and not has_kindle:
                continue

            if has_pdf and has_kindle: etiqueta = "(PDF / Kindle)"
            elif has_pdf: etiqueta = "(PDF)"
            elif has_kindle: etiqueta = "(Kindle)"
            else: etiqueta = "(Otros)"
                
            resultados_validos.append({
                'titulo': titulo, 'enlace': enlace, 
                'info_doc': info_doc, 'etiqueta': etiqueta
            })

        # Lógica de Error / Fallback de Idiomas
        if not resultados_validos or len(resultados_validos) <= offset:
            if offset == 0:
                # Si no encontramos nada y no hemos hecho el fallback, probamos sin idioma
                if not fallback_lang and lang != '':
                    bot.send_message(chat_id, "⚠️ No se encontró en el idioma pedido. Ampliando búsqueda a todos los idiomas...", parse_mode='HTML')
                    return execute_shadow_search(chat_id, query, 0, lang, is_kindle_only, author, fallback_lang=True)
                else:
                    msg = f"❌ <b>No se encontraron resultados</b> para \"<i>{search_term}</i>\"."
                    if is_kindle_only: msg += " (Prueba a quitar la palabra 'kindle' para ver PDFs)."
                    bot.send_message(chat_id, msg, parse_mode='HTML')
            else:
                bot.send_message(chat_id, "🏁 Fin de los resultados de búsqueda.")
                if chat_id in user_sessions: del user_sessions[chat_id]
            return

        texto = f"📚 <b>Resultados para \"{query}\"</b> "
        if author: texto += f"de <i>{author}</i> "
        texto += "\n\n"
        
        limit = 5
        items_a_mostrar = resultados_validos[offset : offset+limit]
        
        for item in items_a_mostrar:
            texto += f"📖 <b><a href='{item['enlace']}'>{item['titulo']}</a></b> <code>{item['etiqueta']}</code>\n"
            if item['info_doc']:
                texto += f"   📄 <i>{item['info_doc'][:60]}</i>\n\n"

        if len(resultados_validos) > offset + limit:
            user_sessions[chat_id] = {'query': query, 'lang': lang, 'offset': offset + limit, 'is_kindle_only': is_kindle_only, 'author': author, 'source': 'shadow', 'fallback_lang': fallback_lang}
            texto += "👉 <i>Escribe /siguiente para ver más opciones.</i>"
        else:
            if chat_id in user_sessions: del user_sessions[chat_id]

        bot.send_message(chat_id, texto, parse_mode='HTML', disable_web_page_preview=True)

    except Exception as e:
        bot.send_message(chat_id, "❌ Error al procesar los datos.")

# ==========================================
# 4. BOTONES DEL MOTOR LEGAL
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('book:'))
def handle_book_query(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    book_id = call.data.split(':')[1]
    
    try:
        response = requests.get(f"https://gutendex.com/books/?ids={book_id}", timeout=10)
        data = response.json()
        if data['count'] == 0: return
            
        book = data['results'][0]
        title = book['title']
        markup = InlineKeyboardMarkup(row_width=1)
        formats = book['formats']
        
        if 'application/epub+zip' in formats:
            markup.add(InlineKeyboardButton("📥 Descargar (Kindle / EPUB)", url=formats['application/epub+zip']))
        
        pdf_text = formats.get('application/pdf') or formats.get('text/html')
        if pdf_text:
            markup.add(InlineKeyboardButton("📄 Leer PDF / Texto", url=pdf_text))
        
        bot.send_message(chat_id, f"📖 <b>{title}</b>", reply_markup=markup, parse_mode='HTML')
    except:
        bot.send_message(chat_id, "❌ Error al cargar opciones.")

# ==========================================
# MARCAPASOS PARA SERVIDORES EN LA NUBE
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "El Bot del TFG está vivo y respirando 24/7."

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# ==========================================
# ARRANQUE DEL MOTOR
# ==========================================
if __name__ == '__main__':
    keep_alive() # Encendemos el marcapasos
    print("🚀 Bot V6 Iniciado en la Nube con Bienvenida actualizada...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)