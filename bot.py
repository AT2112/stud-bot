from responses import reply
from ocr import choose_language, image_button_callback, text_option_callback_choice
from commands import *
from speech_to_text import voice_message_handle, audio_message_handle, audio_option_callback_choice
from const import API_KEY_TEL
from parser_1 import schedule_nmu, course_choice_nmu, group_choice_nmu, CHOOSING_NMU, RECEIVING_NMU, \
    RECEIVING_COURSE_NMU, receiving_course, schedule_nuft, RECEIVING_NUFT, scraper_nuft
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, CallbackQueryHandler, \
    MessageHandler, filters


def bot():
    application = (
        ApplicationBuilder()
        .token(API_KEY_TEL)
        .concurrent_updates(True)
        .build()
    )
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("help", faq))

    application.add_handler(CommandHandler("get_anime", get_anime))
    application.add_handler(CommandHandler("get_porn", get_porn))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('schedulenmu', schedule_nmu)],
        states={
            CHOOSING_NMU: [CallbackQueryHandler(course_choice_nmu)],
            RECEIVING_COURSE_NMU: [CallbackQueryHandler(receiving_course)],
            RECEIVING_NMU: [MessageHandler(filters.TEXT, group_choice_nmu)],
        },
        fallbacks=[]
    ))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('schedulenuft', schedule_nuft)],
        states={RECEIVING_NUFT: [MessageHandler(filters.TEXT, scraper_nuft)]},
        fallbacks=[]
    ))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # application.add_handler(MessageHandler(filters.Sticker.ALL & ~filters.COMMAND, get_porn))

    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, choose_language))

    application.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, voice_message_handle))

    application.add_handler(MessageHandler(filters.AUDIO & ~filters.COMMAND, audio_message_handle))

    application.add_handler(CallbackQueryHandler(image_button_callback,
                                                 pattern='eng|ukr|rus|fra'))

    application.add_handler(CallbackQueryHandler(text_option_callback_choice,
                                                 pattern='skip_image_text|gpt_image_text'))

    application.add_handler(CallbackQueryHandler(audio_option_callback_choice,
                                                 pattern='skip_audio_text|gpt_audio_text'))

    application.run_polling()
