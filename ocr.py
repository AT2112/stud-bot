from telegram.ext import ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import pytesseract
from PIL import Image
import gpt
from const import TESSERACT_PATH, LINE
from pathlib import Path
import tempfile

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

file_id = None


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global file_id
    file_id = update.message.photo[-1].file_id

    lang_choice_buttons = [[InlineKeyboardButton("English🇬🇧", callback_data='eng'),
                            InlineKeyboardButton("Українська🇺🇦", callback_data='ukr')],
                           [InlineKeyboardButton("Русский🇷🇺", callback_data='rus'),
                            InlineKeyboardButton("Française🇫🇷", callback_data='fra')]]
    reply_markup_lang = InlineKeyboardMarkup(lang_choice_buttons)
    await update.message.reply_text('Оберіть мову тексту на вашому зображенні:', reply_markup=reply_markup_lang)


async def image_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if query is None:
        return
    await query.answer()
    language = query.data

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        new_file = await context.bot.get_file(file_id)
        new_image = tmp_dir/f'{new_file.file_id}.jpg'
        await new_file.download_to_drive(custom_path=new_image)

        image = Image.open(new_image)
        text_from_image = pytesseract.image_to_string(image, lang=language)

        if text_from_image == '' or text_from_image is None:
            await query.message.reply_text('Схоже на зображенні немає тексту...')

        else:
            context.user_data['text_from_image'] = text_from_image
            context.user_data['language'] = language

            await query.message.reply_html("<u>Текста з вашого зображення</u>",)

            await query.message.reply_text(text=text_from_image)

            await query.message.reply_html(text="<u>Якщо текст зчитано неправильно "
                                                "- скопіюйте та відредагуйте його самостійно.</u>",)

            await text_option_callback(update, context)


async def text_option_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['button_pressed'] = False
    opt_choice_buttons = [[InlineKeyboardButton("Просто хотів дістати текст",
                                                callback_data='skip_image_text')],
                          [InlineKeyboardButton("Направити текст із зображення до GPT",
                                                callback_data='gpt_image_text')]]
    reply_markup_opt = InlineKeyboardMarkup(opt_choice_buttons)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Що робимо з текстом?', reply_markup=reply_markup_opt)
    await text_option_callback_choice(update, context)


async def text_option_callback_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    opt = query.data
    if opt == 'skip_image_text':
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

    elif opt == 'gpt_image_text':
        text_from_image = context.user_data['text_from_image']
        button_pressed = context.user_data.get('button_pressed', False)
        last_message = context.user_data.get('last_message')
        if not button_pressed:
            if last_message != '<u>Якщо текст зчитано неправильно - скопіюйте та відредагуйте його самостійно.</u>':
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Сек дд я думаю")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=LINE)
                context.user_data['last_message'] = '<u>Якщо текст зчитано неправильно - скопіюйте та відредагуйте його самостійно.</u>'
                await gpt.response(update, context, text_from_image)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Не треба спамити")
                context.user_data['last_message'] = 'Не треба спамити'
                context.user_data['button_pressed'] = True
