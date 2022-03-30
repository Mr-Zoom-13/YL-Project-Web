from flask import Flask, request
import logging
import json
from data import db_session
from data.users import Users
from data.wastes import Wastes
from data.service_providers import Providers
from data.cargo_categories import Categories
from data.documentation import documentation
import datetime
from requests import get

app = Flask(__name__)
sessionStorage = {}
suggests = {'Main menu': ['Расскажи о навыке', 'Меню трат', 'Изменить имя пользователя'],
            'Yes or no': ['Да', 'Нет'],
            'Documentation': ['Продолжай', 'Хватит'],
            'Wastes Menu': ['Добавь трату', 'Удали трату', 'Моя статистика', 'Установи лимит',
                            'Вернуться в главное меню'],
            'Statistics': [['Нет', 'Отмена'], ['День', 'Месяц', 'Отмена'],
                           ['Рубли', 'Евро', 'Доллары', 'Казахский тенге', 'Отмена']],
            'Limits': ['Удали лимит', 'Отмена']}
main_menu_buttons = [{'title': elem, 'hide': False} for elem in suggests['Main menu']]
yes_or_no_buttons = [{'title': elem, 'hide': False} for elem in suggests['Yes or no']]
doc_buttons = [{'title': elem, 'hide': False} for elem in suggests['Documentation']]
wastes_menu_buttons = [{'title': elem, 'hide': False} for elem in suggests['Wastes Menu']]
stop_button = [{'title': 'Отмена', 'hide': False}]
stat_no_buttons = [{'title': elem, 'hide': False} for elem in suggests['Statistics'][0]]
stat_time_buttons = [{'title': elem, 'hide': False} for elem in suggests['Statistics'][1]]
stat_valutes_buttons = [{'title': elem, 'hide': False} for elem in suggests['Statistics'][2]]
limit_buttons = [{'title': elem, 'hide': False} for elem in suggests['Limits']]


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
            res['response']['buttons'] = main_menu_buttons
        else:
            sessionStorage[user_id] = {'Action': None, 'Menu': None}
            register_user(req, res)
    elif not user:
        register_user(req, res, new_ses=False)
        res['response']['buttons'] = main_menu_buttons
        res['response']['card'] = {'type': 'BigImage',
                                   'image_id': '1652229/6e5a88eb19ed626ed515',
                                   'title': 'Успешно!', 'description': ''}
    else:
        # КОМАНДЫ
        if "меню трат" in req['request']['original_utterance'].lower():
            wastes_menu(req, res, user_id, new=True)
        elif sessionStorage[user_id]['Menu'] == 'wastes':
            wastes_menu(req, res, user_id)
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
            res['response']['buttons'] = main_menu_buttons
        return


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
    elif 'вернуться в главное меню' in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id]['Menu'] = None
        res['response']['text'] = 'Вы находитесь в главном меню.'
        res['response']['buttons'] = main_menu_buttons
    else:
        res['response']['text'] = 'Я не распознала команду :('
        res['response']['tts'] = 'Я не распознала команду.'
        res['response']['buttons'] = wastes_menu_buttons
    if new:
        res['response']['text'] = 'Вы находитесь в меню трат.'
        res['response']['tts'] = 'Вы находитесь в меню трат.'
        sessionStorage[yandex_id]['Menu'] = 'wastes'
        res['response']['buttons'] = wastes_menu_buttons


def change_limit(req, res, yandex_id, new):
    if new:
        res['response']['text'] = 'Укажите сумму лимита. (Если нужно удалить скажите ' \
                                  '"Удали лимит")'
        res['response']['tts'] = 'Укажите сумму лимита.'
        sessionStorage[yandex_id]['Action'] = 'change_limit'
        sessionStorage[yandex_id]['Stage'] = 'add_limit'
        res['response']['buttons'] = limit_buttons
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes', 'Stage': None}
        res['response']['buttons'] = wastes_menu_buttons
        res['response']['text'] = 'Вы находитесь в меню трат.'
    elif sessionStorage[yandex_id]['Stage'] == 'add_limit':
        if 'удали лимит' in req['request']['original_utterance'].lower():
            res['response']['text'] = 'Лимит удалён.'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes', 'Stage': None}
            res['response']['buttons'] = wastes_menu_buttons
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
            res['response']['buttons'] = limit_buttons
        elif limit < 1:
            res['response']['text'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['tts'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['buttons'] = limit_buttons
        else:
            user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
            user.limit = limit
            db_ses.commit()
            sessionStorage[yandex_id]['Stage'] = 'add_remember'
            res['response']['text'] = f'Лимит {limit} установлен.'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes', 'Stage': None}
            res['response']['buttons'] = wastes_menu_buttons


def about_us(req, res, yandex_id, new):
    if new:
        sessionStorage[yandex_id] = {"Action": 'documentation', 'Stage': 0, 'Menu': None}
        res['response']['text'] = documentation[
                                      sessionStorage[yandex_id]['Stage']] + '\nПродолжать?'
        res['response']['buttons'] = doc_buttons
    elif req['request']['original_utterance'].lower() == 'продолжай':
        if sessionStorage[yandex_id]['Stage'] < 7:
            sessionStorage[yandex_id]['Stage'] += 1
            res['response']['buttons'] = doc_buttons
            res['response']['text'] = documentation[
                                          sessionStorage[yandex_id]['Stage']] + '\nПродолжать?'
        else:
            res['response']['text'] = 'На этом всё!'
            sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
            res['response']['buttons'] = main_menu_buttons
    elif req['request']['original_utterance'].lower() == 'хватит':
        res['response']['text'] = 'Хорошо. Введите команду.'
        res['response']['buttons'] = main_menu_buttons
        sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
    else:
        res['response']['text'] = "Извините, вам нужно ответить 'Продолжай' или 'Хватит'."
        res['response']['buttons'] = doc_buttons
    return


def create_new_waste(req, res, yandex_id, new):
    this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
    if new:
        new_waste = Wastes()
        new_waste.user_id = this_user.id
        sessionStorage[yandex_id] = {"Action": 'create_waste', 'Stage': 'add_provider_send',
                                     'Waste': new_waste, 'Menu': 'wastes'}
        res['response']['text'] = "Где вы совершили трату?"
        res['response']['tts'] = "Где вы совершили трату?"
        res['response']['buttons'] = stop_button
        sessionStorage[yandex_id]['Stage'] = 'add_provider_get'
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        res['response']['buttons'] = wastes_menu_buttons
        res['response']['text'] = 'Вы находитесь в меню трат.'
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
        res['response']['buttons'] = stop_button
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
        res['response']['buttons'] = stop_button
        sessionStorage[yandex_id]['Stage'] = 'add_amount_get'
    elif sessionStorage[yandex_id]['Stage'] == 'add_amount_get':
        amount = None
        for entity in req['request']['nlu']['entities']:
            if entity['type'] == 'YANDEX.NUMBER':
                amount = entity['value']
        if not amount:
            res['response']['text'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['tts'] = "Я не увидела здесь число. Напишите снова!"
            res['response']['buttons'] = stop_button
        elif amount < 1:
            res['response']['text'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['tts'] = "Число должно быть больше 0. Напишите снова!"
            res['response']['buttons'] = stop_button
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
            res['response']['buttons'] = wastes_menu_buttons
    return


def delete_waste(req, res, yandex_id, new):
    if new:
        last_waste = db_ses.query(Wastes).filter(Users.yandex_id == yandex_id).all()
        if last_waste:
            last_waste = last_waste[-1]
            res['response']['text'] = f"Вы точно хотите удалить последнюю трату?\n" \
                                      f"({last_waste.provider.title} {last_waste.category.title}" \
                                      f"{last_waste.amount} {last_waste.date})"
            res['response']['tts'] = "Вы точно хотите удалить последнюю трату?"
            res['response']['buttons'] = yes_or_no_buttons
            sessionStorage[yandex_id] = {"Action": 'delete_waste', 'Menu': 'wastes'}
        else:
            res['response']['text'] = "Извините, у вас пока нет трат."
            res['response']['tts'] = "Извините, у вас пока нет трат."
            res['response']['buttons'] = wastes_menu_buttons
            sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    elif req['request']['command'].lower() == 'да':
        last_waste = db_ses.query(Wastes).filter(Users.yandex_id == yandex_id).all()[-1]
        db_ses.delete(last_waste)
        db_ses.commit()
        res['response']['text'] = "Трата успешно удалена."
        res['response']['tts'] = "Трата успешно удалена."
        res['response']['buttons'] = wastes_menu_buttons
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    elif req['request']['command'].lower() == 'нет':
        res['response']['text'] = "Хорошо. Введите команду."
        res['response']['tts'] = "Хорошо. Введите команду."
        res['response']['buttons'] = wastes_menu_buttons
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
    else:
        res['response']['text'] = "Извините, вам нужно ответить 'Да' или 'Нет'."
        res['response']['tts'] = "Извините, вам нужно ответить 'Да' или 'Нет'."
        res['response']['buttons'] = yes_or_no_buttons


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
            res['response']['text'] = 'Вы успешно зарегистрированы!'
            res['response']['tts'] = 'Вы успешно зарегистрированы!'
        else:
            res['response']['text'] = 'Извините, я не увидела имени. Напишите снова!'
            res['response']['tts'] = 'Извините, я не увидела имени. Напишите снова!'
    return


def change_name(req, res, yandex_id, new):
    if new:
        res['response']['text'] = 'Введите новое имя.'
        res['response']['tts'] = 'Введите новое имя.'
        sessionStorage[yandex_id] = {'Action': 'change_name', 'Menu': None}
        res['response']['buttons'] = stop_button
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': None}
        res['response']['buttons'] = main_menu_buttons
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
            res['response']['buttons'] = main_menu_buttons
        else:
            res['response']['text'] = 'Извините, я не увидела имени. Напишите снова!'
            res['response']['tts'] = 'Извините, я не увидела имени. Напишите снова!'
            res['response']['buttons'] = stop_button


def create_statistics(req, res, yandex_id, new):
    if new:
        res['response'][
            'text'] = 'Назовите категорию по которой вы хотите статистику' \
                      '(Если не хотите - скажите нет).'
        res['response']['tts'] = 'Назовите категорию по которой вы хотите статистику.'
        sessionStorage[yandex_id] = {'Action': 'get_statistics', 'Stage': 'add_category',
                                     'Menu': 'wastes'}
        res['response']['buttons'] = stat_no_buttons
    elif "отмена" in req['request']['original_utterance'].lower():
        sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
        res['response']['buttons'] = wastes_menu_buttons
        res['response']['text'] = 'Вы находитесь в меню трат.'
    else:
        this_user = db_ses.query(Users).filter(Users.yandex_id == yandex_id).first()
        res['response']['buttons'] = stop_button
        if sessionStorage[yandex_id]['Stage'] == 'add_category':
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
                    res['response']['buttons'] = stat_no_buttons
                    return
            res['response'][
                'text'] = 'Назовите место покупки по которой вы хотите статистику' \
                          '(Если не хотите - скажите нет).'
            res['response']['buttons'] = stat_no_buttons
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
                    res['response']['buttons'] = stat_no_buttons
                    return
            res['response'][
                'text'] = 'Назовите интервал дат покупки(месяц, день).'
            res['response']['tts'] = 'Назовите интервал дат покупки(месяц, день).'
            res['response']['buttons'] = stat_time_buttons
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
                res['response']['buttons'] = stat_time_buttons
            else:
                if sessionStorage[yandex_id]['Category'] and sessionStorage[yandex_id][
                    'Provider']:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.user == this_user,
                                                             Wastes.date >= date_time_obj,
                                                             Wastes.category_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Category'],
                                                             Wastes.provider_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Provider']).all()
                elif sessionStorage[yandex_id]['Category']:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.user == this_user,
                                                             Wastes.date >= date_time_obj,
                                                             Wastes.category_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Category']).all()
                elif sessionStorage[yandex_id]['Provider']:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.user == this_user,
                                                             Wastes.date >= date_time_obj,
                                                             Wastes.provider_id ==
                                                             sessionStorage[yandex_id][
                                                                 'Provider']).all()
                else:
                    all_wastes = db_ses.query(Wastes).filter(Wastes.user == this_user,
                                                             Wastes.date >= date_time_obj).all()
                sessionStorage[yandex_id]['Stage'] = 'add_valute'
                sessionStorage[yandex_id]['Wastes'] = all_wastes
                res['response'][
                    'text'] = 'В какой валюте вывести информацию?(рубли, евро, доллары, ' \
                              'казахский тенге)\n P.S В рублях быстрее всего.'
                res['response']['buttons'] = stat_valutes_buttons
                res['response']['tts'] = 'В какой валюте вывести информацию?'
                return
        elif sessionStorage[yandex_id]['Stage'] == 'add_valute':
            sum = 0
            valutes = ['рубли', 'евро', 'доллары', 'казахский тенге']
            this_valute = None
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
                sum = round(sum, 2)
                if not this_valute:
                    res['response']['text'] = 'Трат не было совершено.'
                    res['response']['tts'] = 'Трат не было совершено.'
                    res['response']['buttons'] = wastes_menu_buttons
                else:
                    res['response']['text'] = 'Всего было потрачено ' + str(
                        sum) + ' ' + this_valute
                    res['response']['tts'] = 'Всего было потрачено ' + str(
                        sum) + ' ' + this_valute
                sessionStorage[yandex_id] = {'Action': None, 'Menu': 'wastes'}
            else:
                res['response']['text'] = 'Я вас не поняла, пожалуйста повторите!'
                res['response']['tts'] = 'Я вас не поняла, пожалуйста повторите!'
                res['response']['buttons'] = stat_valutes_buttons
    return


if __name__ == '__main__':
    db_session.global_init('db/home_accountant.db')
    db_ses = db_session.create_session()
    app.run()
