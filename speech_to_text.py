import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes
import tempfile
from pathlib import Path
import pydub
from pydub.utils import which
import gpt
from const import LINE


async def voice_message_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        voice_ogg_path = tmp_dir / "voice.ogg"

        voice_file = await context.bot.get_file(voice.file_id)
        await voice_file.download_to_drive(voice_ogg_path)

        pydub.AudioSegment.converter = which("ffmpeg")
        voice_mp3_path = tmp_dir / "voice.mp3"
        pydub.AudioSegment.from_file(voice_ogg_path).export(voice_mp3_path, format="mp3")

        with open(voice_mp3_path, "rb") as f:
            transcribed_dict = openai.Audio.transcribe(file=f, model='whisper-1')
            for text in transcribed_dict.values():
                transcribed_text = text

    text = f"🎤: <i>{transcribed_text}</i>"
    context.user_data['transcribed_text'] = transcribed_text
    await update.message.reply_text(text=text,
                                    parse_mode=constants.ParseMode.HTML)

    await audio_option_callback(update, context)


async def audio_message_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        audio_mp3_path = tmp_dir / "audio.mp3"

        audio_file = await context.bot.get_file(audio.file_id)
        await audio_file.download_to_drive(audio_mp3_path)

        pydub.AudioSegment.converter = which("ffmpeg")

        with open(audio_mp3_path, "rb") as f:
            transcribed_dict = openai.Audio.transcribe(file=f, model='whisper-1')
            for text in transcribed_dict.values():
                transcribed_text = text

    text = f"🎤: <i>{transcribed_text}</i>"
    context.user_data['transcribed_text'] = transcribed_text
    await update.message.reply_text(text=text,
                                    parse_mode=constants.ParseMode.HTML)

    await audio_option_callback(update, context)


async def audio_option_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['button_pressed'] = False
    opt_choice_buttons = [[InlineKeyboardButton("Просто хотів дістати текст", callback_data='skip_audio_text')],
                          [InlineKeyboardButton("Направити текст із аудіо до GPT", callback_data='gpt_audio_text')]]
    reply_markup_opt = InlineKeyboardMarkup(opt_choice_buttons)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Що робимо з текстом?', reply_markup=reply_markup_opt)

    await audio_option_callback_choice(update, context)


async def audio_option_callback_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    opt_audio = query.data
    if opt_audio == 'skip_audio_text':
        button_pressed = context.user_data.get('button_pressed', False)
        last_message = context.user_data.get('last_message')
        if not button_pressed:
            if last_message != 'OK!':
                await context.bot.send_message(chat_id=update.effective_chat.id, text="ОК!")
                context.user_data['last_message'] = 'OK!'
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Не треба спамити")
                context.user_data['last_message'] = 'Не треба спамити'
                context.user_data['button_pressed'] = True

    elif opt_audio == 'gpt_audio_text':
        transcribed_text = context.user_data['transcribed_text']
        button_pressed = context.user_data.get('button_pressed', False)
        last_message = context.user_data.get('last_message')
        if not button_pressed:
            if last_message != transcribed_text:
                await gpt.response(update, context, transcribed_text)
                context.user_data['last_message'] = transcribed_text
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Не треба спамити")
                context.user_data['last_message'] = 'Не треба спамити'
                context.user_data['button_pressed'] = True
