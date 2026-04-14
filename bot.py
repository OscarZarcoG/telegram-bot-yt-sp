import os
import logging
import asyncio
import re
import tempfile
from typing import Final, Optional
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import urllib.request
import urllib.parse

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger: Final[logging.Logger] = logging.getLogger(__name__)

TOKEN: Final[Optional[str]] = os.environ.get("TELEGRAM_TOKEN")

SPOTIFY_RE: Final[re.Pattern] = re.compile(r"https?://(?:open\.)?spotify\.com/(?:[a-zA-Z-]{2,10}/)?track/[\w]+")
YOUTUBE_RE: Final[re.Pattern] = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+")

def is_spotify(url: str) -> bool:
    return bool(SPOTIFY_RE.search(url))

def is_youtube(url: str) -> bool:
    return bool(YOUTUBE_RE.search(url))

def get_spotify_query(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read(20000).decode("utf-8")
            match = re.search(r"<title>(.*?)</title>", html)
            if match:
                title = match.group(1).split(" | Spotify")[0].strip()
                return f"ytsearch:{title}"
    except Exception:
        pass
    raise ValueError("No se pudo obtener informacion de Spotify")

def download_audio(query: str) -> str:
    temp_dir: str = tempfile.gettempdir()
    output_path: str = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "noprogress": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if info is None:
            raise ValueError("No se pudo obtener informacion del link")
        if "entries" in info:
            info = info["entries"][0]
        filename: str = ydl.prepare_filename(info)
        mp3_path: str = os.path.splitext(filename)[0] + ".mp3"
        return mp3_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "*Bot de descargas*\n\n"
        "Mandame un link de YouTube o Spotify y te mando el MP3.\n\n"
        "Solo pega el link y listo.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "*Instrucciones*\n\n"
        "1. Copia un link de YouTube o Spotify.\n"
        "2. Pegalo en el chat.\n"
        "3. Espera a que procese y descargue el audio.\n\n"
        "Comandos:\n"
        "/start - Iniciar el bot\n"
        "/help - Ver mensajes de ayuda",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return
        
    url: str = update.message.text.strip()

    if not (is_spotify(url) or is_youtube(url)):
        await update.message.reply_text(
            "Mandame un link valido de YouTube o Spotify."
        )
        return

    msg = await update.message.reply_text("Procesando solicitud...")
    loop = asyncio.get_event_loop()

    try:
        if is_spotify(url):
            await msg.edit_text("Buscando informacion en Spotify...")
            query = await loop.run_in_executor(None, get_spotify_query, url)
        else:
            query = url

        await msg.edit_text("Descargando audio de YouTube...")
        filepath = await loop.run_in_executor(None, download_audio, query)

        await msg.edit_text("Enviando archivo...")

        with open(filepath, "rb") as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                caption="Aqui esta.",
            )

        await msg.delete()
        os.remove(filepath)

    except Exception as e:
        logger.error(f"Error procesando {url}: {e}")
        await msg.edit_text(
            "Hubo un problema al procesar el link. Verifica que sea un enlace publico y valido."
        )

async def post_init(application) -> None:
    await application.bot.set_my_commands([
        ("start", "Iniciar el bot"),
        ("help", "Ver instrucciones"),
    ])

def main() -> None:
    if not TOKEN:
        raise ValueError("Falta la variable de entorno TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
