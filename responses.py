from telegram.ext import ContextTypes
from telegram import Update
import muted
import gpt
from const import LINE


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not muted.MUTED:
        text_from_message = update.message.text

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Бот обробляє запит")

        await context.bot.send_message(chat_id=update.effective_chat.id, text=LINE)

        await gpt.response(update, context, text_from_message)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Зачекайте будь ласка, "
                                                                              "GPT обробляє ваш запит")
