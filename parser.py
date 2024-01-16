from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes, ConversationHandler
import re
import const
import muted


URL_NMU = 'https://asu.nmuofficial.com/time-table/group?type=0'
URL_NUFT = 'https://nmu.nuft.edu.ua/cgi-bin/timetable.cgi'

CHOOSING_NMU, RECEIVING_NMU, RECEIVING_COURSE_NMU = range(3)
RECEIVING_NUFT = range(1)

f = ''
c = ''
g = ''


async def schedule_nmu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await faculty_choice_nmu(update, context)
    return CHOOSING_NMU


async def faculty_choice_nmu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opt_choice_buttons_fac = [[InlineKeyboardButton("медичний №1", callback_data='1'),
                               InlineKeyboardButton("медичний №2", callback_data='2')],
                              [InlineKeyboardButton("медичний №3", callback_data='3'),
                               InlineKeyboardButton("медичний №4", callback_data='4')],
                              [InlineKeyboardButton("стоматологічний", callback_data='5'),
                               InlineKeyboardButton("фармацевтичний", callback_data='6')],
                              [InlineKeyboardButton("медико-психологічний", callback_data='7'),
                               InlineKeyboardButton("підготовки іноземних громадян", callback_data='9')],
                              [InlineKeyboardButton("підготовки лікарів ЗСУ", callback_data='8'),
                               InlineKeyboardButton("Інститут післядипломної освіти", callback_data='12')],
                              [InlineKeyboardButton("підготовче відділення", callback_data='32')]]
    reply_markup_opt_fac = InlineKeyboardMarkup(opt_choice_buttons_fac)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Оберіть факультет:', reply_markup=reply_markup_opt_fac)
    return CHOOSING_NMU


async def course_choice_nmu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    faculty = query.data
    global f
    f = faculty
    context.user_data['faculty'] = faculty

    opt_choice_buttons_course = [[InlineKeyboardButton("1", callback_data='1'),
                                  InlineKeyboardButton("2", callback_data='2')],
                                 [InlineKeyboardButton("3", callback_data='3'),
                                  InlineKeyboardButton("4", callback_data='4')],
                                 [InlineKeyboardButton("5", callback_data='5')]]
    reply_markup_opt_course = InlineKeyboardMarkup(opt_choice_buttons_course)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Оберіть курс:', reply_markup=reply_markup_opt_course)

    return RECEIVING_COURSE_NMU


async def receiving_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    course = query.data
    global c
    c = course

    context.user_data['course'] = course

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Напишіть номер групи:')

    return RECEIVING_NMU


async def group_choice_nmu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    muted.MUTED = True

    group = update.message.text
    global g
    g = group
    if re.search(r'\d', g):
        pass
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Схоже такої групи не існує, спробуйте ще раз')
        muted.MUTED = False
        return ConversationHandler.END

    faculty = context.user_data.get('faculty')
    course = context.user_data.get('course')
    f = faculty
    c = course
    g = group

    await context.bot.send_message(chat_id=update.effective_chat.id, text='Секундочку...')
    await show_schedule_nmu(update, context, f, c, g)
    muted.MUTED = False

    return ConversationHandler.END


async def show_schedule_nmu(update: Update, context: ContextTypes.DEFAULT_TYPE, fac, cour, gro):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_path = "chromedriver.exe"
    driver = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)
    driver.get(URL_NMU)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'timetableform-facultyid')))

    selector_element_fac = driver.find_element(By.XPATH, '//*[@id="select2-timetableform-facultyid-container"]')
    ActionChains(driver).move_to_element(selector_element_fac).click().perform()
    faculty_select = Select(driver.find_element(By.ID, 'timetableform-facultyid'))

    faculty_select.select_by_value(fac)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="timetableform-course"]/option[1]')))
    selector_element_course = driver.find_element(By.XPATH, '//*[@id="select2-timetableform-course-container"]')
    ActionChains(driver).move_to_element(selector_element_course).click().perform()
    course_select = Select(driver.find_element(By.ID, 'timetableform-course'))
    course_select.select_by_visible_text(cour)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="timetableform-groupid"]/option[1]')))
    selector_element_group = driver.find_element(By.XPATH, '//*[@id="select2-timetableform-groupid-container"]')
    ActionChains(driver).move_to_element(selector_element_group).click().perform()
    group_select = Select(driver.find_element(By.ID, 'timetableform-groupid'))

    try:
        group_select.select_by_visible_text(gro)

    except NoSuchElementException:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=const.SCHEDULE_ERROR)
        driver.quit()
        return ConversationHandler.END

    wait = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tbody')))

    lessons = driver.find_elements(By.XPATH, './/*[@id="timeTable"]/tbody/tr/td[1]/div')
    lessons_next = driver.find_elements(By.XPATH, './/*[@id="timeTable"]/tbody/tr/td[2]/div')
    days = driver.find_elements(By.XPATH, './/*[@id="timeTable"]/tbody/tr/th[1]')
    lessons_arr = []
    days_arr = []
    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

    if len(lessons) > 2:
        for lesson in lessons:
            less = lesson.text.replace('\n', ' ').split()
            less_cleaned = [l for l in less if ':' not in l]
            less = ' '.join(less_cleaned)
            if len(less) > 16:
                less = less[0:16]
            less = " -  "+less
            lessons_arr.append(less)

    else:
        for lesson_next in lessons_next:
            less_next = lesson_next.text.replace('\n', ' ').split()
            less_next_cleaned = [l for l in less_next if ':' not in l]
            less_next = ' '.join(less_next_cleaned)
            if len(less_next) > 16:
                less_next = less_next[0:16]
            less_next = " -  "+less_next
            lessons_arr.append(less_next)

    for day in days:
        d = day.text.replace('\n', ' - ')
        days_split = d.split()
        if len(days_split) > 1:
            days_split.remove(days_split[0])
        days_cleaned = [d for d in days_split if 'пара' not in d]
        d = ' '.join(days_cleaned)
        if len(d) > 2:
            d = d[2:len(d)]
        days_arr.append(d)

    if len(lessons_arr) != len(days_arr):
        for i in range((len(days_arr)-len(lessons_arr))-7):
            lessons_arr.insert(0, ' - ')

    for i, day in enumerate(days_arr):
        if day in days_of_week:
            index = days_arr.index(day)
            lessons_arr.insert(index, " ")

    schedule = {"Пари": days_arr, "Предмети": lessons_arr}
    df_of_schedule = pd.DataFrame(schedule)
    print_schedule = df_of_schedule.to_string(index=False)
    await context.bot.send_message(text=print_schedule, chat_id=update.effective_chat.id)

    driver.quit()


async def schedule_nuft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(text="Напишіть назву групи:", chat_id=update.effective_chat.id)
    return RECEIVING_NUFT


async def scraper_nuft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    muted.MUTED = True
    await context.bot.send_message(text="Секундочку...", chat_id=update.effective_chat.id)
    group = update.message.text
    timings_arr = []
    days_arr_nuft = []
    lessons_arr_nuft = []

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL_NUFT)

    input = driver.find_element(By.XPATH, '//*[@id="group"]')
    input.send_keys(group)
    input.submit()

    try:
        table = driver.find_element(By.TAG_NAME, 'table')
    except NoSuchElementException:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=const.SCHEDULE_ERROR)
        driver.quit()
        muted.MUTED = False
        return ConversationHandler.END

    dates = driver.find_elements(By.XPATH, '//*[@id="wrap"]/div/div/div/div[4]/div/div/h4')
    time = driver.find_elements(By.XPATH, '//*[@id="wrap"]/div/div/div/div[4]/div/div/table/tbody/tr/td[2]')
    lessons = driver.find_elements(By.XPATH, '//*[@id="wrap"]/div/div/div/div[4]/div/div/table/tbody/tr/td[3]')

    for date in dates:
        day = date.text
        days_arr_nuft.append(day[:10])

    for i, t in enumerate(time):
        tim = t.text.replace('\n', '-')
        timings_arr.append(tim)

    for lesson in lessons:
        less = lesson.text.replace('\n', '-')
        if len(less) > 1:
            if 'онлайн' in less:
                less = less[7:]
                index_less = less.find(')')
                if index_less != -1:
                    name_lesson = less[:index_less + 1]
                    lessons_arr_nuft.append(name_lesson)
            else:
                index_less = less.find(')')
                if index_less != -1:
                    name_lesson = less[:index_less + 1]
                    lessons_arr_nuft.append(name_lesson)
        else:
            lessons_arr_nuft.append('-')

    result = ""
    y = 0
    for i, timing in enumerate(timings_arr):
        if timing == '08:15-09:35':
            result += f"<b>{days_arr_nuft[y]}</b>\n\n"
            y += 1

        result += timing + "\n" + lessons_arr_nuft[i] + "\n\n"

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=result,
                                   parse_mode=constants.ParseMode.HTML)

    driver.quit()
    muted.MUTED = False
    return ConversationHandler.END