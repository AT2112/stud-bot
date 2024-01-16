import openai
import muted
from const import REPLY, API_KEY_GPT
from telegram import Update, constants
from telegram.ext import ContextTypes

openai.api_key = API_KEY_GPT


async def response(update: Update, context: ContextTypes.DEFAULT_TYPE, quest):

    muted.MUTED = True

    completion = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo",
                                                     messages=[{"role": "user", "content": quest}])

    resp = completion.choices[0].message.content

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=REPLY,
                                   parse_mode=constants.ParseMode.HTML)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=resp)

    muted.MUTED = False