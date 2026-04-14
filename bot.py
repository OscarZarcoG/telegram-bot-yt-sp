import os
import logging
import asyncio
import re
import tempfile
from typing import Final, Optional
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

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

def download_audio(url: str) -> str:
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
                "player_client": ["web_creator"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
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
        "*Bot de descargas para bajo*\n\n"
        "Mandame un link de YouTube o Spotify y te mando el MP3 para que lo metas a Moises.\n\n"
        "Solo pega el link y listo.",
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

    msg = await update.message.reply_text("Descargando... un momento.")

    try:
        loop = asyncio.get_event_loop()
        filepath: str = await loop.run_in_executor(None, download_audio, url)

        await msg.edit_text("Subiendo el archivo...")

        with open(filepath, "rb") as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                caption="Aqui esta. Metelo a Moises.",
            )

        await msg.delete()
        os.remove(filepath)

    except Exception as e:
        logger.error(f"Error descargando {url}: {e}")
        await msg.edit_text(
            "No pude descargar ese link. Puede ser que:\n"
            "- El video tenga restriccion de region\n"
            "- El link de Spotify no tiene equivalente en YouTube\n"
            "- Algo salio mal con el servidor\n\n"
            "Intenta con otro link."
        )

def main() -> None:
    if not TOKEN:
        raise ValueError("Falta la variable de entorno TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
