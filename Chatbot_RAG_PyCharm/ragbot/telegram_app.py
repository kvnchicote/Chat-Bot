"""Interfaz Telegram. El bot consulta un PDF local previamente indexado."""
import asyncio
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from .config import require_secret

LOGGER = logging.getLogger(__name__)


def _allowed(user_id: int | None) -> bool:
    raw = os.getenv('ALLOWED_TELEGRAM_USER_IDS', '').strip()
    if not raw:
        return True
    return str(user_id) in {item.strip() for item in raw.split(',')}


def create_app(qa, kb):
    token = require_secret('TELEGRAM_BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not _allowed(update.effective_user.id):
            return
        await update.message.reply_text(
            '¡Hola! Soy un chatbot RAG. Solo respondo usando citas literales de mi PDF. '
            'Mandame una pregunta. Usá /fuente para ver qué documento está cargado.'
        )

    async def source(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not _allowed(update.effective_user.id):
            return
        info = kb.status()
        msg = (f'📄 PDF activo: {info["filename"]}\nFragmentos: {info["chunks"]}'
               if info['ready'] else 'Todavía no hay ningún PDF indexado.')
        await update.message.reply_text(msg)

    async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return
        if not update.effective_user or not _allowed(update.effective_user.id):
            return
        if not kb.status()['ready']:
            await update.message.reply_text('Primero indexá un PDF desde PyCharm: python main.py indexar documentos/ejemplo.pdf')
            return
        try:
            # Ejecutar búsqueda local y API fuera del event loop para no bloquear Telegram.
            result = await asyncio.to_thread(qa.answer, update.message.text)
            await update.message.reply_text(result[:4000])
        except Exception:
            LOGGER.exception('Fallo al responder una pregunta')
            await update.message.reply_text('No pude procesar esa pregunta (problema técnico). Revisá la consola de PyCharm.')

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('fuente', source))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    return app
