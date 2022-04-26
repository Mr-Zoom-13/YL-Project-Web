from flask import Flask, request, render_template
import json
from data import db_session
from data.users import Users
from data.wastes import Wastes
from data.service_providers import Providers
from data.cargo_categories import Categories
from data.communities import Communities
from data.documentation import documentation
import datetime
from requests import get
from data.upcoming_spending import Upcoming
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
sessionStorage = {}
SUGGESTS = {'Main menu': ['Расскажи о навыке', 'Меню трат', 'Меню сообществ',
                          'Изменить имя пользователя'],
            'Yes or no': ['Да', 'Нет'],
            'Documentation': ['Продолжай', 'Хватит'],
            'Wastes Menu': ['Добавь трату', 'Удали трату', 'Моя статистика', 'Установи лимит',
                            'Добавь предстоящую оплату',
                            'За что мне нужно заплатить в этом месяце',
                            'Вернуться в главное меню'],
            'Statistics': [['Нет', 'Отмена'], ['День', 'Месяц', 'Отмена'],
                           ['Рубли', 'Евро', 'Доллары', 'Казахский тенге', 'Отмена']],
            'Limits': ['Удали лимит', 'Отмена'],
            'Communities Menu(team_leader)': ['Мой ID', 'Добавить участника',
                                              'Расформировать сообщество',
                                              'Вернуться в главное меню'],
            'Communities Menu(member)': ['Мой ID', 'Покинуть сообщество',
                                         'Вернуться в главное меню'],
            'Communities Menu(None)': ['Мой ID', 'Создать сообщество',
                                       'Вернуться в главное меню'],
            'Create  Waste': ['Личная', 'Сообщества', 'Отмена']}
MAIN_MENU_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Main menu']]
YES_OR_NO_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Yes or no']]
DOC_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Documentation']]
WASTES_MENU_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Wastes Menu']]
COMMUNITIES_MENU_LEADER_BUTTONS = [{'title': elem, 'hide': False} for elem in
                                   SUGGESTS['Communities Menu(team_leader)']]
COMMUNITIES_MENU_NONE_BUTTONS = [{'title': elem, 'hide': False} for elem in
                                 SUGGESTS['Communities Menu(None)']]
COMMUNITIES_MENU_MEMBER_BUTTONS = [{'title': elem, 'hide': False} for elem in
                                   SUGGESTS['Communities Menu(member)']]
STOP_BUTTON = [{'title': 'Отмена', 'hide': False}]
STAT_NO_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Statistics'][0]]
STAT_TIME_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Statistics'][1]]
STAT_VALUTES_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Statistics'][2]]
LIMIT_BUTTONS = [{'title': elem, 'hide': False} for elem in SUGGESTS['Limits']]
CREATE_WASTE_STAT = [{'title': elem, 'hide': False} for elem in SUGGESTS['Create  Waste']]


@app.route('/stats/<string:yandex_id>')
def stat(yandex_id):
    try:
        statistic = sessionStorage[yandex_id]['Statistics']
        if not statistic[0][0]:
            raise KeyError
        plt.subplot(1, 2, 1)
        plt.pie(statistic[0][0], labels=statistic[0][1], autopct='%1.2f%%')
        plt.axis('equal')
        plt.legend()
        plt.subplot(1, 2, 2)
        plt.pie(statistic[1][0], labels=statistic[1][1], autopct='%1.2f%%')
        plt.axis('equal')
        plt.legend()
        plt.savefig('static/img/1.png')
        plt.close()
        return render_template('statistic.html', date=statistic[2])
    except KeyError:
        return render_template('statistic.html', date=None)


@app.route('/post', methods=['POST'])
def main():
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(request.json, response)
    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']
    user = db_ses.query(Users).filter(Users.yandex_id == user_id).first()
    if req['session']['new']:
        if user:
            res['response']['text'] = f'Здравствуйте, {user.name}! Рада снова вас видеть.'
            res['response']['tts'] = f'Здравствуйте, {user.name}! Рада снова вас видеть.'
            sessionStorage[user_id] = {'Action': None, 'Menu': None}
            res['response']['buttons'] = MAIN_MENU_BUTTONS
        else:
            sessionStorage[user_id] = {'Action': None, 'Menu': None}
            register_user(req, res)
    elif not user:
        register_user(req, res, new_ses=False)
    else:
        # КОМАНДЫ
        if "меню трат" in req['request']['original_utterance'].lower():
            wastes_menu(req, res, user_id, new=True)
        elif "посмотреть диаграммы" in req['request']['original_utterance'].lower():
            wastes_menu(req, res, user_id, new=True)
        elif "меню сообществ" in req['request']['original_utterance'].lower():
            communities_menu(req, res, user_id, new=True)
        elif sessionStorage[user_id]['Menu'] == 'wastes':
            wastes_menu(req, res, user_id)
        elif sessionStorage[user_id]['Menu'] == 'communities':
            communities_menu(req, res, user_id)
        elif "расскажи о навыке" in req['request']['original_utterance'].lower():
            about_us(req, res, user_id, new=True)
        elif sessionStorage[user_id]['Action'] == 'documentation':
            about_us(req, res, user_id, new=False)
        elif 'изменить имя пользователя' in req['request']['original_utterance'].lower():
            change_name(req, res, user_id, new=True)
        elif sessionStorage[user_id]['Action'] == 'change_name':
            change_name(req, res, user_id, new=False)
        else:
            res['response']['text'] = 'Я не распознала команду :('
            res['response']['tts'] = 'Я не распознала команду.'
            res['response']['buttons'] = MAIN_MENU_BUTTONS
        return


def communities_menu(req, res, yandex_id, new=False):
    this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
    if 'создать сообщество' in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        create_community(req, res, yandex_id, new=True)
    elif sessionStorage[yandex_id]['Action'] == 'create_community':
        create_community(req, res, yandex_id)
    elif 'мой id' in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        my_id(req, res, yandex_id)
    elif 'расформировать сообщество' in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        delete_community(req, res, this_user, new=True)
    elif sessionStorage[yandex_id]['Action'] == 'delete_community':
        delete_community(req, res, this_user)
    elif 'добавить участника' in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        invite_new_member(req, res, this_user, new=True)
    elif sessionStorage[this_user.yandex_id]['Action'] == 'invite_member':
        invite_new_member(req, res, this_user)
    elif 'покинуть сообщество' in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        left_community(req, res, this_user, new=True)
    elif sessionStorage[this_user.yandex_id]['Action'] == 'left_community':
        left_community(req, res, this_user)
    elif 'вернуться в главное меню' in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id]['Menu'] = None
        res['response']['text'] = 'Вы находитесь в главном меню.'
        res['response']['buttons'] = MAIN_MENU_BUTTONS
    else:
        res['response']['text'] = 'Я не распознала команду :('
        res['response']['tts'] = 'Я не распознала команду.'
        res['response']['buttons'] = buttons_need(this_user)
    if new:
        res['response']['text'] = 'Вы находитесь в меню сообществ.'
        res['response']['tts'] = 'Вы находитесь в меню сообществ.'
        sessionStorage[yandex_id]['Menu'] = 'communities'
        res['response']['buttons'] = buttons_need(this_user)


def wastes_menu(req, res, yandex_id, new=False):
    if "добавь трату" in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        res['response']['buttons'] = None
        create_new_waste(req, res, yandex_id, new=True)
    elif sessionStorage[yandex_id]['Action'] == "create_waste":
        create_new_waste(req, res, yandex_id, new=False)
    elif "удали трату" in req['request']['original_utterance'].lower():
        res['response']['buttons'] = None
        delete_waste(req, res, yandex_id, new=True)
    elif sessionStorage[yandex_id]['Action'] == "delete_waste":
        delete_waste(req, res, yandex_id, new=False)
    elif "моя статистика" in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        res['response']['buttons'] = None
        create_statistics(req, res, yandex_id, True)
    elif sessionStorage[yandex_id]['Action'] == 'get_statistics':
        create_statistics(req, res, yandex_id, False)
    elif "установи лимит" in req['request']['original_utterance'].lower() and \
            not sessionStorage[yandex_id]['Action']:
        res['response']['buttons'] = None
        change_limit(req, res, yandex_id, True)
    elif sessionStorage[yandex_id]['Action'] == 'change_limit':
        change_limit(req, res, yandex_id, False)
    elif 'добавь предстоящую оплату' in req['request']['original_utterance'].lower():
        add_upcoming_spending(req, res, yandex_id, True)
    elif sessionStorage[yandex_id]['Action'] == 'upcoming_spending':
        add_upcoming_spending(req, res, yandex_id, False)
    elif 'за что мне нужно заплатить в этом месяце' in req['request'][
        'original_utterance'].lower():
        inform_upcoming(req, res, yandex_id, True)
    elif sessionStorage[yandex_id]['Action'] == 'inform upcoming':
        inform_upcoming(req, res, yandex_id, False)
    elif 'вернуться в главное меню' in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id]['Menu'] = None
        res['response']['text'] = 'Вы находитесь в главном меню.'
        res['response']['buttons'] = MAIN_MENU_BUTTONS
    else:
        res['response']['text'] = 'Я не распознала команду :('
        res['response']['tts'] = 'Я не распознала команду.'
        res['response']['buttons'] = WASTES_MENU_BUTTONS
    if new:
        res['response']['text'] = 'Вы находитесь в меню трат.'
        res['response']['tts'] = 'Вы находитесь в меню трат.'
        sessionStorage[yandex_id]['Menu'] = 'wastes'
        res['response']['buttons'] = WASTES_MENU_BUTTONS


def add_upcoming_spending(req, res, yandex_id, new):
    if new:
        spending = Upcoming()
        spending.user_id = yandex_id
        sessionStorage[yandex_id] = {'Action': 'upcoming_spending', 'Stage': 'title',
                                     'Spending': spending, 'Menu': 'wastes'}
        res['response']['text'] = 'Введите заметку. (Не более 70 символов)'
        res['response']['tts'] = 'Введите заметку.'
        res['response']['buttons'] = STOP_BUTTON
        sessionStorage[yandex_id]['Stage'] = 'title'
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        res['response']['text'] = 'Вы находитесь в меню трат.'
    elif sessionStorage[yandex_id]['Stage'] == 'title':
        if len(req['request']['command']) <= 70:
            spending = sessionStorage[yandex_id]['Spending']
            spending.title = req['request']['command']
            res['response']['text'] = "Введите сумму оплаты."
            res['response']['tts'] = "Введите сумму оплаты."
            sessionStorage[yandex_id]['Spending'] = spending
            sessionStorage[yandex_id]['Stage'] = 'amount'
        else:
            res['response']['text'] = "Слишком много символов."
            res['response']['tts'] = "Слишком много символов."
            res['response']['buttons'] = STOP_BUTTON
    elif sessionStorage[yandex_id]['Stage'] == 'amount':
        amount = None
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.NUMBER':
                amount = entity['value']
        if not amount:
            res['response']['text'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['tts'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['buttons'] = STOP_BUTTON
        elif amount < 1:
            res['response']['text'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['tts'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['buttons'] = STOP_BUTTON
        else:
            spending = sessionStorage[yandex_id]['Spending']
            spending.amount = amount
            res['response']['text'] = "Напишите дату оплаты. (Формат ДД.ММ)"
            res['response']['tts'] = "Напишите дату оплаты."
            res['response']['buttons'] = STOP_BUTTON
            sessionStorage[yandex_id]['Spending'] = spending
            sessionStorage[yandex_id]['Stage'] = 'date'
    elif sessionStorage[yandex_id]['Stage'] == 'date':
        date = req['request']['command'].split('.')
        today = str(datetime.date.today())
        month = int(today.split('-')[1])
        year = int(today.split('-')[0])
        try:
            if int(date[1]) < month:
                year += 1
            date = datetime.date(day=int(date[0]), month=int(date[1]), year=year)
            spending = sessionStorage[yandex_id]['Spending']
            spending.date = date
            db_ses.add(spending)
            db_ses.commit()
            res['response']['text'] = "Предстоящая оплата добавлена."
            res['response']['tts'] = "Предстоящая оплата добавлена."
            res['response']['buttons'] = WASTES_MENU_BUTTONS
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        except Exception:
            res['response']['text'] = "Неверный формат ввода. Попробуйте ещё раз!"
            res['response']['tts'] = "Неверный формат ввода. Попробуйте ещё раз!"
            res['response']['buttons'] = STOP_BUTTON


def inform_upcoming(req, res, yandex_id, new):
    if new:
        today = str(datetime.date.today())
        month = today.split('-')[1]
        out = ''
        sessionStorage[yandex_id]['Action'] = 'inform upcoming'
        sessionStorage[yandex_id]['Index'] = 1
        i = 1
        if db_ses.query(Upcoming).filter(Upcoming.user_id == yandex_id,
                                         Upcoming.date.like(f'%-{month}-%')).first():
            for spending in db_ses.query(Upcoming).filter(Upcoming.user_id == yandex_id,
                                                          Upcoming.date.like(
                                                              f'%-{month}-%')).all():
                if len(out + f'{i}. {spending.title} {spending.amount} {spending.date}\n') + 11 \
                        <= 1024:
                    out += f'{i}. {spending.title} {spending.amount} {spending.date}\n'
                    i += 1
                else:
                    out += 'Продолжать?'
                    sessionStorage[yandex_id]['Index'] = i
                    res['response']['text'] = out
                    res['response']['buttons'] = YES_OR_NO_BUTTONS
                    return
        else:
            out = 'Вам не нужно ни за что платить в этом месяце!'
        res['response']['text'] = out
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    elif "нет" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        res['response']['text'] = 'Вы находитесь в меню трат.'
    elif 'да' in req['request']['original_utterance'].lower():
        today = str(datetime.date.today())
        month = int(today.split('-')[1])
        out = ''
        i = sessionStorage[yandex_id]['Index']
        ix = 1
        if db_ses.query(Upcoming).filter(Upcoming.user_id == yandex_id,
                                         Upcoming.date.like(f'%-{month}-%')).first():
            for spending in db_ses.query(Upcoming).filter(Upcoming.user_id == yandex_id,
                                                          Upcoming.date.like(
                                                              f'%-{month}-%')).all():
                if len(out + f'{i}. {spending.title} {spending.amount} {spending.date}\n') + 11 \
                        <= 1024:
                    out += f'{i}. {spending.title} {spending.amount} {spending.date}\n'
                    i += 1
                else:
                    out += 'Продолжать?'
                    sessionStorage[yandex_id]['Index'] = i
                    res['response']['text'] = out
                    res['response']['buttons'] = YES_OR_NO_BUTTONS
                    return
            ix += 1
        else:
            out = 'Больше нет трат!'
        res['response']['text'] = out
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    else:
        res['response']['text'] = "Извините, вам нужно ответить 'Да' или 'Нет'."
        res['response']['buttons'] = YES_OR_NO_BUTTONS


def change_limit(req, res, yandex_id, new):
    if new:
        res['response']['text'] = 'Укажите сумму лимита. (Если нужно удалить скажите ' \
                                  '"Удали лимит")'
        res['response']['tts'] = 'Укажите сумму лимита.'
        sessionStorage[yandex_id]['Action'] = 'change_limit'
        sessionStorage[yandex_id]['Stage'] = 'add_limit'
        res['response']['buttons'] = LIMIT_BUTTONS
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes', 'Stage': None}
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        res['response']['text'] = 'Вы находитесь в меню трат.'
    elif sessionStorage[yandex_id]['Stage'] == 'add_limit':
        if 'удали лимит' in req['request']['original_utterance'].lower():
            res['response']['text'] = 'Лимит удалён.'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes', 'Stage': None}
            res['response']['buttons'] = WASTES_MENU_BUTTONS
            user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
            user.limit = None
            db_ses.commit()
            return
        limit = None
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.NUMBER':
                limit = entity['value']
        if not limit:
            res['response']['text'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['tts'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['buttons'] = LIMIT_BUTTONS
        elif limit < 1:
            res['response']['text'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['tts'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['buttons'] = LIMIT_BUTTONS
        else:
            user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
            user.limit = limit
            db_ses.commit()
            sessionStorage[yandex_id]['Stage'] = 'add_remember'
            res['response']['text'] = f'Лимит {limit} установлен.'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes', 'Stage': None}
            res['response']['buttons'] = WASTES_MENU_BUTTONS


def about_us(req, res, yandex_id, new):
    if new:
        sessionStorage[yandex_id] = {"Action": 'documentation', 'Stage': 0, 'Menu': None}
        res['response']['text'] = documentation[
                                      sessionStorage[yandex_id]['Stage']] + '\nПродолжать?'
        res['response']['buttons'] = DOC_BUTTONS
    elif req['request']['original_utterance'].lower() == 'продолжай':
        if sessionStorage[yandex_id]['Stage'] < 12:
            sessionStorage[yandex_id]['Stage'] += 1
            res['response']['buttons'] = DOC_BUTTONS
            res['response']['text'] = documentation[
                                          sessionStorage[yandex_id]['Stage']] + '\nПродолжать?'
        else:
            res['response']['text'] = 'На этом всё!'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
            res['response']['buttons'] = MAIN_MENU_BUTTONS
    elif req['request']['original_utterance'].lower() == 'хватит':
        res['response']['text'] = 'Хорошо. Введите команду.'
        res['response']['buttons'] = MAIN_MENU_BUTTONS
        sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
    else:
        res['response']['text'] = "Извините, вам нужно ответить 'Продолжай' или 'Хватит'."
        res['response']['buttons'] = DOC_BUTTONS
    return


def create_new_waste(req, res, yandex_id, new):
    this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
    if new:
        if this_user.community_id:
            res['response']['text'] = "Это трата личная или сообщества?"
            res['response']['tts'] = "Это трата личная или сообщества?"
            res['response']['buttons'] = CREATE_WASTE_STAT
            sessionStorage[yandex_id] = {"Action": 'create_waste',
                                         'Stage': 'family_waste', 'Menu': 'wastes'}
        else:
            new_waste = Wastes()
            new_waste.user_id = this_user.id
            sessionStorage[yandex_id] = {"Action": 'create_waste',
                                         'Stage': 'add_provider_send',
                                         'Waste': new_waste, 'Menu': 'wastes'}
            res['response']['text'] = "Где вы совершили трату?"
            res['response']['tts'] = "Где вы совершили трату?"
            res['response']['buttons'] = STOP_BUTTON
            sessionStorage[yandex_id]['Stage'] = 'add_provider_get'
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        res['response']['text'] = 'Вы находитесь в меню трат.'
    elif sessionStorage[yandex_id]['Stage'] == 'family_waste':
        new_waste = Wastes()
        if req['request']['original_utterance'].lower() == 'личная':
            new_waste.user_id = this_user.id
        else:
            new_waste.community_id = this_user.community_id
        res['response']['text'] = "Где вы совершили трату?"
        res['response']['tts'] = "Где вы совершили трату?"
        res['response']['buttons'] = STOP_BUTTON
        sessionStorage[yandex_id]['Stage'] = 'add_provider_get'
        sessionStorage[yandex_id]['Waste'] = new_waste
    elif sessionStorage[yandex_id]['Stage'] == 'add_provider_get':
        provider_title = req['request']['command']
        provider_id = db_ses.query(Providers).filter(Providers.title == provider_title).first()
        if not provider_id:
            new_provider = Providers()
            new_provider.title = provider_title
            db_ses.add(new_provider)
            db_ses.commit()
        provider_id = db_ses.query(Providers).filter(Providers.title == provider_title).first()
        sessionStorage[yandex_id]['Waste'].provider = provider_id
        res['response']['text'] = "Какая категория товара?"
        res['response']['tts'] = "Какая категория товара?"
        res['response']['buttons'] = STOP_BUTTON
        sessionStorage[yandex_id]['Stage'] = 'add_category_get'
    elif sessionStorage[yandex_id]['Stage'] == 'add_category_get':
        category_title = req['request']['command']
        if ',' in category_title:
            category_title = 'Прочее'
        category_id = db_ses.query(Categories).filter(
            Categories.title == category_title).first()
        if not category_id:
            new_category = Categories()
            new_category.title = category_title
            db_ses.add(new_category)
            db_ses.commit()
        category_id = db_ses.query(Categories).filter(
            Categories.title == category_title).first()
        sessionStorage[yandex_id]['Waste'].category = category_id
        res['response']['text'] = "Сколько вы потратили?"
        res['response']['tts'] = "Сколько вы потратили?"
        res['response']['buttons'] = STOP_BUTTON
        sessionStorage[yandex_id]['Stage'] = 'add_amount_get'
    elif sessionStorage[yandex_id]['Stage'] == 'add_amount_get':
        amount = None
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.NUMBER':
                amount = entity['value']
        if not amount:
            res['response']['text'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['tts'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['buttons'] = STOP_BUTTON
        elif amount < 1:
            res['response']['text'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['tts'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['buttons'] = STOP_BUTTON
        else:
            limit_info = ''
            overcoming_limit = ''
            sessionStorage[yandex_id]['Waste'].amount = amount
            db_ses.add(sessionStorage[yandex_id]['Waste'])
            db_ses.commit()
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
            user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
            if user.limit:
                limit_info = f'\nВаш лимит - {user.limit}.'
                date_time_str = str(datetime.datetime.utcnow().year) + '-' + str(
                    datetime.datetime.utcnow().month) + '-01'
                date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d')
                all_wastes = db_ses.query(Wastes).filter(Wastes.user == user, Wastes.date >=
                                                         date_time_obj).all()
                sum = 0
                for waste in all_wastes:
                    sum += waste.amount
                if sum >= user.limit:
                    overcoming_limit = '\nВЫ ПРЕОДОЛЕЛИ ЛИМИТ!!!'
                else:
                    overcoming_limit = f'\nДо преодоления лимита - {user.limit - sum}'
            res['response']['text'] = "Трата добавлена." + limit_info + overcoming_limit
            res['response']['tts'] = "Трата добавлена." + limit_info + overcoming_limit
            res['response']['buttons'] = WASTES_MENU_BUTTONS
    return


def delete_waste(req, res, yandex_id, new):
    if new:

        last_waste = db_ses.query(Wastes).filter(Users.yandex_id == yandex_id).all()
        if last_waste:
            last_waste = last_waste[-1]
            res['response']['text'] = f"Вы точно хотите удалить последнюю трату?\n" \
                                      f"({last_waste.provider.title} {last_waste.category.title}" \
                                      f" {last_waste.amount} {last_waste.date})"
            res['response']['tts'] = "Вы точно хотите удалить последнюю трату?"
            res['response']['buttons'] = YES_OR_NO_BUTTONS
            sessionStorage[yandex_id] = {"Action": 'delete_waste', 'Menu': 'wastes'}
        else:
            res['response']['text'] = "Извините, у вас пока нет трат."
            res['response']['tts'] = "Извините, у вас пока нет трат."
            res['response']['buttons'] = WASTES_MENU_BUTTONS
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    elif req['request']['command'].lower() == 'да':
        last_waste = db_ses.query(Wastes).filter(Users.yandex_id == yandex_id).all()[-1]
        db_ses.delete(last_waste)
        db_ses.commit()
        res['response']['text'] = "Трата успешно удалена."
        res['response']['tts'] = "Трата успешно удалена."
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    elif req['request']['command'].lower() == 'нет':
        res['response']['text'] = "Хорошо. Введите команду."
        res['response']['tts'] = "Хорошо. Введите команду."
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    else:
        res['response']['text'] = "Извините, вам нужно ответить 'Да' или 'Нет'."
        res['response']['tts'] = "Извините, вам нужно ответить 'Да' или 'Нет'."
        res['response']['buttons'] = YES_OR_NO_BUTTONS


def register_user(req, res, new_ses=True):
    if new_ses:
        res['response']['text'] = 'Привет, кажется вы впервые у нас. Как мне к вам обращаться?'
        res['response']['tts'] = 'Привет, кажется вы впервые у нас. Как мне к вам обращаться?'
    else:
        name = None
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.FIO':
                name = entity['value'].get('first_name', None).capitalize()
        if name:
            new_user = Users()
            new_user.name = name
            new_user.yandex_id = req['session']['user_id']
            db_ses.add(new_user)
            db_ses.commit()
            res['response']['card'] = {'type': 'BigImage',
                                       'image_id': '1652229/6e5a88eb19ed626ed515',
                                       'title': 'Успешно!', 'description': ''}
            res['response']['text'] = 'Успешно!'
            res['response'][
                'tts'] = '<speaker audio="dialogs-upload/ce3c4e31-be51-47d7-8b66-a026ba0f9333' \
                         '/e650097f-604e-405d-866b-a3695601d0cc.opus">'
            res['response']['buttons'] = MAIN_MENU_BUTTONS
        else:
            res['response']['text'] = 'Извините, я не увидела имени. Напишите снова!'
            res['response']['tts'] = 'Извините, я не увидела имени. Напишите снова!'
    return


def change_name(req, res, yandex_id, new):
    if new:
        res['response']['text'] = 'Введите новое имя.'
        res['response']['tts'] = 'Введите новое имя.'
        sessionStorage[yandex_id] = {'Action': 'change_name', 'Menu': None}
        res['response']['buttons'] = STOP_BUTTON
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
        res['response']['buttons'] = MAIN_MENU_BUTTONS
        res['response']['text'] = 'Вы находитесь в главном меню.'
    else:
        name = None
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.FIO':
                name = entity['value'].get('first_name', None).capitalize()
        if name:
            user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
            user.name = name
            res['response']['text'] = f'Вы успешно сменили имя на {name.capitalize()}'
            res['response']['tts'] = f'Вы успешно сменили имя на {name.capitalize()}'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
            res['response']['buttons'] = MAIN_MENU_BUTTONS
        else:
            res['response']['text'] = 'Извините, я не увидела имени. Напишите снова!'
            res['response']['tts'] = 'Извините, я не увидела имени. Напишите снова!'
            res['response']['buttons'] = STOP_BUTTON


def create_statistics(req, res, yandex_id, new):
    this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
    if new:
        if this_user.community_id:
            res['response']['text'] = 'Статистика личная или сообщества?'
            res['response']['tts'] = 'Статистика личная или сообщества?'
            sessionStorage[yandex_id] = {'Action': 'get_statistics', 'Stage': 'family_stat',
                                         'Menu': 'wastes'}
            res['response']['buttons'] = CREATE_WASTE_STAT
        else:
            res['response'][
                'text'] = 'Назовите категорию по которой вы хотите статистику' \
                          '(Если не хотите - скажите нет).'
            res['response']['tts'] = 'Назовите категорию по которой вы хотите статистику.'
            sessionStorage[yandex_id] = {'Action': 'get_statistics', 'Stage': 'add_category',
                                         'Menu': 'wastes'}
            res['response']['buttons'] = STAT_NO_BUTTONS
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        res['response']['buttons'] = WASTES_MENU_BUTTONS
        res['response']['text'] = 'Вы находитесь в меню трат.'
    else:
        res['response']['buttons'] = STOP_BUTTON
        if sessionStorage[yandex_id]['Stage'] == 'family_stat':
            if req['request']['original_utterance'].lower() == 'сообщества':
                sessionStorage[yandex_id]['Who'] = this_user.community_id
            else:
                sessionStorage[yandex_id]['Who'] = None
            res['response'][
                'text'] = 'Назовите категорию по которой вы хотите статистику' \
                          '(Если не хотите - скажите нет).'
            res['response']['tts'] = 'Назовите категорию по которой вы хотите статистику.'
            sessionStorage[yandex_id]['Stage'] = 'add_category'
            res['response']['buttons'] = STAT_NO_BUTTONS
        elif sessionStorage[yandex_id]['Stage'] == 'add_category':
            if req['request']['original_utterance'].lower() == 'нет':
                sessionStorage[yandex_id]['Category'] = None
            else:
                this_category_title = req['request']['original_utterance'].lower()
                this_category = db_ses.query(Categories).filter(
                    Categories.title == this_category_title).first()
                if this_category:
                    sessionStorage[yandex_id]['Category'] = this_category.id
                else:
                    res['response'][
                        'text'] = 'Такая категория отсутствует, попробуйте еще раз.'
                    res['response']['tts'] = 'Такая категория отсутствует, попробуйте еще раз.'
                    res['response']['buttons'] = STAT_NO_BUTTONS
                    return
            res['response'][
                'text'] = 'Назовите место покупки по которой вы хотите статистику' \
                          '(Если не хотите - скажите нет).'
            res['response']['buttons'] = STAT_NO_BUTTONS
            res['response'][
                'tts'] = 'Назовите место покупки по которой вы хотите статистику.'
            sessionStorage[yandex_id]['Stage'] = 'add_provider'
        elif sessionStorage[yandex_id]['Stage'] == 'add_provider':
            if req['request']['original_utterance'].lower() == 'нет':
                sessionStorage[yandex_id]['Provider'] = None
            else:
                this_provider_title = req['request']['original_utterance'].lower()
                this_provider = db_ses.query(Providers).filter(
                    Providers.title == this_provider_title).first()
                if this_provider:
                    sessionStorage[yandex_id]['Provider'] = this_provider.id
                else:
                    res['response'][
                        'text'] = 'Такое место покупки отсутствует, поробуйте еще раз.'
                    res['response'][
                        'tts'] = 'Такое место покупки отсутствует, поробуйте еще раз.'
                    res['response']['buttons'] = STAT_NO_BUTTONS
                    return
            res['response'][
                'text'] = 'Назовите интервал дат покупки(месяц, день).'
            res['response']['tts'] = 'Назовите интервал дат покупки(месяц, день).'
            res['response']['buttons'] = STAT_TIME_BUTTONS
            sessionStorage[yandex_id]['Stage'] = 'add_interval'
        elif sessionStorage[yandex_id]['Stage'] == 'add_interval':
            date_time_obj = None
            if req['request']['original_utterance'].lower() == 'месяц':
                date_time_str = str(datetime.datetime.utcnow().year) + '-' + str(
                    datetime.datetime.utcnow().month) + '-01'
                date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d')
            elif req['request']['original_utterance'].lower() == 'день':
                date_time_obj = datetime.date.today()
            if not date_time_obj:
                res['response']['text'] = 'Я вас не поняла, пожалуйста повторите.'
                res['response']['tts'] = 'Я вас не поняла, пожалуйста повторите.'
                res['response']['buttons'] = STAT_TIME_BUTTONS
            else:
                if sessionStorage[yandex_id]['Category'] and sessionStorage[yandex_id][
                    'Provider']:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.date >= date_time_obj,
                                                             Wastes.category_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Category'],
                                                             Wastes.provider_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Provider']).all()
                elif sessionStorage[yandex_id]['Category']:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.date >= date_time_obj,
                                                             Wastes.category_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Category']).all()
                elif sessionStorage[yandex_id]['Provider']:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.date >= date_time_obj,
                                                             Wastes.provider_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Provider']).all()
                else:
                    all_wastes = db_ses.query(Wastes).filter(
                        Wastes.date >= date_time_obj).all()
                wastes = []
                if 'Who' in sessionStorage[yandex_id].keys():
                    for i in all_wastes:
                        if ((i.community_id == sessionStorage[yandex_id]['Who']) and
                            sessionStorage[yandex_id]['Who']) or (
                                i.user == this_user and not sessionStorage[yandex_id]['Who']):
                            wastes.append(i)
                    sessionStorage[yandex_id]['Wastes'] = wastes
                else:
                    for i in all_wastes:
                        if i.user == this_user:
                            wastes.append(i)
                sessionStorage[yandex_id]['Wastes'] = wastes
                sessionStorage[yandex_id]['Stage'] = 'add_valute'
                res['response'][
                    'text'] = 'В какой валюте вывести информацию?(рубли, евро, доллары, ' \
                              'казахский тенге)\n P.S В рублях быстрее всего.'
                res['response']['buttons'] = STAT_VALUTES_BUTTONS
                res['response']['tts'] = 'В какой валюте вывести информацию?'
                return
        elif sessionStorage[yandex_id]['Stage'] == 'add_valute':
            sum = 0
            valutes = ['рубли', 'евро', 'доллары', 'казахский тенге']
            this_valute = None
            values_cat = []
            labels_cat = []
            values_prov = []
            labels_prov = []
            if req['request']['original_utterance'].lower() in valutes:
                for waste in sessionStorage[yandex_id]['Wastes']:
                    if req['request']['original_utterance'].lower() == 'рубли':
                        this_valute = 'RUB'
                        sum += waste.amount
                    else:
                        request_api = get(
                            f'http://api.exchangeratesapi.io/v1/{waste.date}?access_key=d47a'
                            f'46acad1a1b4b44b9e4cedfcce038&symbols=USD,KZT,EUR,RUB').json()
                        if req['request']['original_utterance'].lower() == 'доллары':
                            first_number = waste.amount / request_api['rates']['RUB']
                            sum += first_number * request_api['rates']['USD']
                            this_valute = 'USD'
                        elif req['request']['original_utterance'].lower() == 'евро':
                            sum = waste.amount / request_api['rates']['RUB']
                            this_valute = 'EUR'
                        else:
                            first_number = waste.amount / request_api['rates']['RUB']
                            sum += first_number * request_api['rates']['KZT']
                            this_valute = 'KZT'
                    if waste.category.title not in labels_cat:
                        labels_cat.append(waste.category.title)
                        values_cat.append(waste.amount)
                    else:
                        ind = labels_cat.index(waste.category.title)
                        values_cat[ind] += waste.amount
                    if waste.provider.title not in labels_prov:
                        labels_prov.append(waste.provider.title)
                        values_prov.append(waste.amount)
                    else:
                        ind = labels_prov.index(waste.provider.title)
                        values_prov[ind] += waste.amount
                sum = round(sum, 2)
                if not this_valute:
                    res['response']['text'] = 'Трат не было совершено.'
                    res['response']['tts'] = 'Трат не было совершено.'
                    res['response']['buttons'] = WASTES_MENU_BUTTONS
                else:
                    res['response']['text'] = 'Всего было потрачено ' + str(
                        sum) + ' ' + this_valute
                    res['response']['tts'] = 'Всего было потрачено ' + str(
                        sum) + ' ' + this_valute
                sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes',
                                             'Statistics': [[values_cat, labels_cat],
                                                            [values_prov, labels_prov],
                                                            datetime.date.today()]}
                link_buttons = [{'title': 'Посмотреть диаграммы', 'hide': True,
                                 "url": "https://50f9-94-41-167-123.ngrok.io/stats/" + yandex_id},
                                {'title': 'Меню трат', 'hide': False}]
                res['response']['buttons'] = link_buttons
            else:
                res['response']['text'] = 'Я вас не поняла, пожалуйста повторите!'
                res['response']['tts'] = 'Я вас не поняла, пожалуйста повторите!'
                res['response']['buttons'] = STAT_VALUTES_BUTTONS
    return


def create_community(req, res, yandex_id, new=False):
    this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
    if not this_user.community_id:
        if new:
            sessionStorage[yandex_id]['Action'] = 'create_community'
            sessionStorage[yandex_id]['Stage'] = 'add_title'
            res['response']['text'] = "Скажите название вашего нового сообщества."
            res['response']['tts'] = "Скажите название вашего нового сообщества."
        elif sessionStorage[yandex_id]['Stage'] == 'add_title':
            title = req['request']['original_utterance']
            new_community = Communities()
            new_community.title = title
            new_community.team_leader = this_user.id
            db_ses.add(new_community)
            this_new_community = db_ses.query(Communities).filter(
                Communities.team_leader == this_user.id).first()
            this_user.community_id = this_new_community.id
            db_ses.commit()
            res['response']['text'] = "Новое сообщество успешно создано!"
            res['response']['tts'] = "Новое сообщество успешно создано!"
            res['response']['buttons'] = COMMUNITIES_MENU_LEADER_BUTTONS
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'communities'}
    else:
        res['response']['text'] = "Вы уже состоите в сообществе!"
        res['response']['tts'] = "Вы уже состоите в сообществе!"
        res['response']['buttons'] = buttons_need(this_user)
    return


def my_id(req, res, yandex_id):
    this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
    res['response']['text'] = f"Ваш ID в нашей системе: {this_user.id}"
    res['response']['tts'] = f"Ваш ID в нашей системе {this_user.id}"
    res['response']['buttons'] = buttons_need(this_user)
    return


def buttons_need(user):
    if user.community_id and db_ses.query(Communities).filter(
            Communities.team_leader == user.id).first():
        return COMMUNITIES_MENU_LEADER_BUTTONS
    elif user.community_id:
        return COMMUNITIES_MENU_MEMBER_BUTTONS
    else:
        return COMMUNITIES_MENU_NONE_BUTTONS


def delete_community(req, res, user, new=False):
    this_community = db_ses.query(Communities).filter(
        Communities.team_leader == user.id).first()
    if this_community:
        if new:
            sessionStorage[user.yandex_id]['Action'] = 'delete_community'
            sessionStorage[user.yandex_id]['Stage'] = 'accept'
            res['response']['text'] = 'Вы точно хотите расформировать сообщество?'
            res['response']['tts'] = 'Вы точно хотите расформировать сообщество?'
            res['response']['buttons'] = YES_OR_NO_BUTTONS
        else:
            if req['request']['original_utterance'].lower() == 'да':
                for i in db_ses.query(Users).filter(
                        Users.community_id == this_community.id).all():
                    i.community_id = None
                    db_ses.commit()
                db_ses.delete(this_community)
                db_ses.commit()
                res['response']['text'] = 'Ваше сообщество успешно расформировано!'
                res['response']['tts'] = 'Ваше сообщество успешно расформировано!'
                res['response']['buttons'] = COMMUNITIES_MENU_NONE_BUTTONS
            else:
                res['response']['text'] = 'Действие отменено.'
                res['response']['tts'] = 'Действие отменено.'
                res['response']['buttons'] = buttons_need(user)
            sessionStorage[user.yandex_id] = {'Action': None, 'Menu': 'communities'}
    else:
        res['response']['text'] = 'Вы не являетесь владельцем сообщества!'
        res['response']['tts'] = 'Вы не являетесь владельцем сообщества!'
        res['response']['buttons'] = buttons_need(user)


def invite_new_member(req, res, user, new=False):
    this_community = db_ses.query(Communities).filter(
        Communities.team_leader == user.id).first()
    if this_community:
        if new:
            sessionStorage[user.yandex_id]['Action'] = 'invite_member'
            sessionStorage[user.yandex_id]['Stage'] = 'add_id'
            res['response']['text'] = 'Скажите ID нового участника.'
            res['response']['tts'] = 'Скажите ID нового участника.'
        elif sessionStorage[user.yandex_id]['Stage'] == 'add_id':
            new_member_id = None
            for entity in req['request']['nlu']['entities']:
                if entity['type'] == 'YANDEX.NUMBER':
                    new_member_id = entity['value']
            if new_member_id:
                new_member = db_ses.query(Users).filter(Users.id == new_member_id).first()
                if new_member:
                    sessionStorage[user.yandex_id]['Stage'] = 'identification'
                    sessionStorage[user.yandex_id]['Member'] = new_member
                    res['response']['text'] = f'Имя: {new_member.name}\nЭто он?'
                    res['response']['tts'] = f'Имя: {new_member.name}\nЭто он?'
                    res['response']['buttons'] = YES_OR_NO_BUTTONS
                else:
                    res['response']['text'] = 'Некорректный ID.'
                    res['response']['tts'] = 'Некорректный ID.'
            else:
                res['response']['text'] = 'Я не увидела тут ID.'
                res['response']['tts'] = 'Я не увидела тут ID.'
        elif sessionStorage[user.yandex_id]['Stage'] == 'identification':
            if req['request']['original_utterance'].lower() == 'да':
                sessionStorage[user.yandex_id]['Member'].community_id = this_community.id
                db_ses.commit()
                res['response']['text'] = 'Данный участник успешно добавлен!'
                res['response']['tts'] = 'Данный участник успешно добавлен!'
                res['response']['buttons'] = buttons_need(user)
            else:
                res['response']['text'] = 'Действие отменено.'
                res['response']['tts'] = 'Действие отменено.'
                res['response']['buttons'] = buttons_need(user)
            sessionStorage[user.yandex_id] = {'Action': None, 'Menu': 'communities'}
    else:
        res['response']['text'] = 'Вы не являетесь владельцем сообщества!'
        res['response']['tts'] = 'Вы не являетесь владельцем сообщества!'
        res['response']['buttons'] = buttons_need(user)


def left_community(req, res, user, new=False):
    if user.community_id and not db_ses.query(Communities).filter(
            Communities.team_leader == user.id).first():
        if new:
            res['response']['text'] = 'Вы уверены что хотите покинуть сообщество?'
            res['response']['tts'] = 'Вы уверены что хотите покинуть сообщество?'
            res['response']['buttons'] = YES_OR_NO_BUTTONS
            sessionStorage[user.yandex_id]['Action'] = 'left_community'
            sessionStorage[user.yandex_id]['Stage'] = 'accept'
        elif sessionStorage[user.yandex_id]['Stage'] == 'accept':
            if req['request']['original_utterance'].lower() == 'да':
                user.community_id = None
                db_ses.commit()
                res['response']['text'] = 'Вы успешно покинули это сообщество!'
                res['response']['tts'] = 'Вы успешно покинули это сообщество!'
                res['response']['buttons'] = buttons_need(user)
            else:
                res['response']['text'] = 'Действие отменено.'
                res['response']['tts'] = 'Действие отменено.'
                res['response']['buttons'] = buttons_need(user)
            sessionStorage[user.yandex_id] = {'Action': None, 'Menu': 'communities'}

    else:
        res['response'][
            'text'] = 'Вы не состоите ни в каких сообществах или являетесь владельцем сообщества.'
        res['response'][
            'tts'] = 'Вы не состоите ни в каких сообществах или являетесь владельцем сообщества.'
        res['response']['buttons'] = buttons_need(user)


if __name__ == '__main__':
    db_session.global_init('db/home_accountant.db')
    db_ses = db_session.create_session()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # comment
