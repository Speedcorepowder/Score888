import logging
from datetime import datetime
import random
from keep_alive import keep_alive
from replit import db

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import Update

# Токен вашего бота (получите у @BotFather в Telegram)  
import os
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Константы
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',') if os.getenv('ADMIN_IDS') else []
ADMIN_CONTACT = "@aksy_can_help"
CRYPTO_ADDRESSES = {
    "BTC": "bc1qexampleaddressbtc",
    "USDT": "TExampleUSDTAddress",
    "TON": "EQCexampleTONaddress",
    "LTC": "ltc1qexampleltcaddress",
    "Monero": "4AexampleMoneroAddress",
    "Перевод на счёт": "IBAN: LV00BANK0123456789012"
}
PRICES = {
    "1 упаковка": {"regular": "15€", "crypto": "13.5€"},
    "5 упаковок": {"regular": "50€", "crypto": "45€"},
    "10 упаковок": {"regular": "70€", "crypto": "63€"}
}

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Функции для работы с базой данных
def get_referral_system():
    return db.get("referral_system", {})

def save_referral_system(data):
    db["referral_system"] = data

def get_ratings():
    return db.get("ratings", {})

def save_ratings(data):
    db["ratings"] = data

def get_rated_orders():
    return db.get("rated_orders", {})

def save_rated_orders(data):
    db["rated_orders"] = data

def get_orders():
    return db.get("orders", {
        'active': [],
        'accepted': [],
        'completed': [],
        'cancelled': []
    })

def save_orders(data):
    db["orders"] = data

def get_user_gifts(user_id):
    return db.get(f"user_gifts_{user_id}", [])

def save_user_gifts(user_id, gifts):
    db[f"user_gifts_{user_id}"] = gifts

def get_user_data(user_id, key=None, default=None):
    if key is None:
        return db.get(f"user_{user_id}", {})
    return db.get(f"user_{user_id}_{key}", default)

def save_user_data(user_id, key_or_data, value=None):
    if value is None:
        # Сохраняем весь объект данных пользователя
        db[f"user_{user_id}"] = key_or_data
    else:
        # Сохраняем конкретный ключ
        db[f"user_{user_id}_{key_or_data}"] = value

# Функция для восстановления данных при запуске
def restore_data():
    global referral_system, ratings, rated_orders, orders
    
    # Восстанавливаем данные из базы
    referral_system = get_referral_system()
    ratings = get_ratings()
    rated_orders = get_rated_orders()
    orders = get_orders()
    
    # Статистика восстановленных данных
    users_count = len(referral_system)
    total_orders = sum(len(orders[status]) for status in ['active', 'accepted', 'completed', 'cancelled'])
    total_ratings = len(ratings)
    
    print(f"📊 Данные восстановлены:")
    print(f"👥 Пользователей в реферальной системе: {users_count}")
    print(f"📦 Всего заказов: {total_orders}")
    print(f"⭐ Всего оценок: {total_ratings}")
    print(f"📝 Оцененных заказов: {len(rated_orders)}")

# Инициализация данных из базы
restore_data()

# Тексты на разных языках
TEXTS = {
    'ru': {
        'speedcore_intro': """🚀 Ты попал в SpeedCore 🚀

⚡️ Здесь кофе - это не напиток... это реакция!
🧪 Забудь про зёрна. Включи химический режим.
💥 Готов к максимальной скорости?

Выбери язык для продолжения:""",
        'welcome': """🌟 Добро пожаловать в SpeedCore! 🌟

📦 VX Coffee - товар высшего качества
💯 Гарантия качества
🚀 Быстрая доставка

Выберите действие:""",
        'make_order': "✨ Сделать Заказ ✨",
        'select_amount': "Выберите количество упаковок:\n\n💎 Премиум качество\n🌟 Лучшие цены",
        'select_payment': "Вы выбрали: VX Coffee {}\nВыберите способ оплаты:",
        'select_delivery': "🚚 Выберите способ доставки:",
        'drop': "📍 Дроп (закладка)",
        'mail': "📦 Почтовая посылка",
        'select_district': "📍 Выберите район:",
        'order_id': "Ваш заказ #{}: \n📦 Товар: VX Coffee {}\n💰 Цена: {}\n💳 Оплата через: {}\n🚚 Доставка: {}\n📍 Район: {}\n\nАдрес для оплаты:\n{}\n\nПосле оплаты отправьте скриншот и ваш ник в {}",
        'new_order': """🆕 Новый заказ #{}!
👤 От: @{}
📦 Товар: {}
💰 Цена: {}
🚚 Доставка: {}
📍 Район: {}
📅 Дата: {}""",
        'no_orders': "Нет {} заказов",
        'active_orders': "{} заказы:\n\n",
        'order_info': "🔸 Заказ #{}\n👤 Пользователь: @{}\n📦 Товар: {}\n💰 Цена: {}\n🚚 Доставка: {}\n📍 Район: {}\n📅 Дата: {}\n───────────────\n",
        'admin_panel': "🔐 Админ-панель\nВыберите действие:",
        'confirm_order': "✅ Подтвердить #{}",
        'cancel_order': "❌ Отменить #{}",
        'back': "⬅️ Назад",
        'confirmed': "✅ Ваш заказ #{} подтвержден!",
        'cancelled_order': "❌ Ваш заказ #{} отменен.",
        'admin_access_denied': "⛔️ У вас нет доступа к админ-панели. Ваш ID: {}"
    },
    'lv': {
        'speedcore_intro': """🚀 *Tu esi iekļuvis SpeedCore* 🚀

⚡️ Šeit kafija nav dzēriens... tā ir reakcija!
🧪 Aizmirsti par graudiem. Ieslēdz ķīmisko režīmu.
💥 Gatavs maksimālajam ātrumam?

Izvēlies valodu, lai turpinātu:""",
        'welcome': """🌟 Laipni lūdzam SpeedCore! 🌟

📦 VX Coffee - augstākās kvalitātes produkts
💯 Kvalitātes garantija
🚀 Ātra piegāde

Izvēlieties darbību:""",
        'make_order': "✨ Veikt Pasūtījumu ✨",
        'select_amount': "Izvēlieties iepakojumu skaitu:\n\n💎 Premium kvalitāte\n🌟 Labākās cenas",
        'select_payment': "Jūs izvēlējāties: VX Coffee {}\nIzvēlieties maksājuma veidu:",
        'select_delivery': "🚚 Izvēlieties piegādes veidu:",
        'drop': "📍 Drop (slēpnis)",
        'mail': "📦 Pasta sūtījums",
        'select_district': "📍 Izvēlieties rajonu:",
        'order_id': "*Jūsu pasūtījums #{}*: \n📦 Prece: VX Coffee {}\n💰 Cena: {}\n💳 Maksājums caur: {}\n🚚 Piegāde: {}\n📍 Rajons: {}\n\n*Maksājuma adrese:*\n{}\n\nPēc apmaksas nosūtiet ekrānuzņēmumu un savu lietotājvārdu uz {}",
        'new_order': """🆕 *Jauns pasūtījums #{}!*
👤 No: @{}
📦 Prece: {}
💰 Cena: {}
🚚 Piegāde: {}
📍 Rajons: {}
📅 Datums: {}""",
        'no_orders': "Nav {} pasūtījumu",
        'active_orders': "*{} pasūtījumi:*\n\n",
        'order_info': "🔸 Pasūtījums #{}\n👤 Lietotājs: @{}\n📦 Prece: {}\n💰 Cena: {}\n🚚 Piegāde: {}\n📍 Rajons: {}\n📅 Datums: {}\n───────────────\n",
        'admin_panel': "*🔐 Admin-panelis*\nIzvēlieties darbību:",
        'confirm_order': "✅ Apstiprināt #{}",
        'cancel_order': "❌ Atcelt #{}",
        'back': "⬅️ Atpakaļ",
        'confirmed': "✅ Jūsu pasūtījums #{} ir apstiprināts!",
        'cancelled_order': "❌ Jūsu pasūtījums #{} ir atcelts.",
        'admin_access_denied': "⛔️ Jums nav pieejas admin-panelim. Jūsu ID: {}"
    },
    'en': {
        'speedcore_intro': """🚀 *You've entered SpeedCore* 🚀

⚡️ Here coffee is not a drink... it's a reaction!
🧪 Forget about beans. Turn on chemical mode.
💥 Ready for maximum speed?

Choose language to continue:""",
        'welcome': """🌟 Welcome to SpeedCore! 🌟

📦 VX Coffee - highest quality product
💯 Quality guarantee
🚀 Fast delivery

Choose action:""",
        'make_order': "✨ Make Order ✨",
        'select_amount': "Select number of packages:\n\n💎 Premium quality\n🌟 Best prices",
        'select_payment': "You selected: VX Coffee {}\nChoose payment method:",
        'select_delivery': "🚚 Choose delivery method:",
        'drop': "📍 Drop (dead drop)",
        'mail': "📦 Postal package",
        'select_district': "📍 Choose district:",
        'order_id': "*Your order #{}*: \n📦 Product: VX Coffee {}\n💰 Price: {}\n💳 Payment via: {}\n🚚 Delivery: {}\n📍 District: {}\n\n*Payment address:*\n{}\n\nAfter payment, send a screenshot and your nickname to {}",
        'new_order': """🆕 *New order #{}!*
👤 From: @{}
📦 Product: {}
💰 Price: {}
🚚 Delivery: {}
📍 District: {}
📅 Date: {}""",
        'no_orders': "No {} orders",
        'active_orders': "*{} orders:*\n\n",
        'order_info': "🔸 Order #{}\n👤 User: @{}\n📦 Product: {}\n💰 Price: {}\n🚚 Delivery: {}\n📍 District: {}\n📅 Date: {}\n───────────────\n",
        'admin_panel': "*🔐 Admin panel*\nChoose action:",
        'confirm_order': "✅ Confirm #{}",
        'cancel_order': "❌ Cancel #{}",
        'back': "⬅️ Back",
        'confirmed': "✅ Your order #{} has been confirmed!",
        'cancelled_order': "❌ Your order #{} has been cancelled.",
        'admin_access_denied': "⛔️ You don't have access to the admin panel. Your ID: {}"
    }
}

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    args = context.args

    # Инициализируем реферальную систему для пользователя если её нет
    if user_id not in referral_system:
        referral_system[user_id] = {
            "invited": [],
            "orders": 0,
            "ref_code": f"ref_{user_id}",
            "raffle_number": len(referral_system) + 1,
            "invited_by": None  # Добавляем поле для отслеживания кто пригласил
        }
        save_referral_system(referral_system)

    if args and args[0].startswith('ref_'):
        invited_by = args[0].split('_')[1]

        # Проверяем валидность реферальной ссылки
        if invited_by != user_id and invited_by in referral_system:
            # Инициализируем приглашающего если нужно
            if "invited" not in referral_system[invited_by]:
                referral_system[invited_by]["invited"] = []

            # Проверяем что пользователь еще не был приглашен
            if user_id not in referral_system[invited_by]["invited"] and referral_system[user_id]["invited_by"] is None:
                referral_system[invited_by]["invited"].append(user_id)
                referral_system[user_id]["invited_by"] = invited_by  # Сохраняем кто пригласил
                save_referral_system(referral_system)

                try:
                    # Получаем информацию о пригласившем пользователе
                    inviter_chat = await context.bot.get_chat(int(invited_by))
                    inviter_username = inviter_chat.username or f"ID{invited_by}"

                    # Отправляем уведомление приглашенному
                    await update.message.reply_text(
                        f"👋 Добро пожаловать!\n"
                        f"Вы перешли по приглашению от @{inviter_username}\n"
                        f"За каждый ваш заказ реферер получит бонус!"
                    )

                    # Отправляем уведомление пригласившему
                    await context.bot.send_message(
                        chat_id=invited_by,
                        text=f"🎯 Новый реферал! @{update.effective_user.username or 'Аноним'} присоединился по вашей ссылке!"
                    )
                except Exception as e:
                    print(f"Error in referral handling: {e}")

    # Показываем приветствие SpeedCore с выбором языка
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇱🇻 Latviešu", callback_data="lang_lv")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Приветствие SpeedCore на всех языках
    speedcore_text = """🚀 Ты попал в SpeedCore 🚀
⚡️ Здесь кофе - это не напиток... это реакция!
🧪 Забудь про зёрна. Включи химический режим.
💥 Готов к максимальной скорости?

🚀 Tu esi iekļuvis SpeedCore 🚀
⚡️ Šeit kafija nav dzēriens... tā ir reakcija!
🧪 Aizmirsti par graudiem. Ieslēdz ķīmisko režīmu.
💥 Gatavs maksimālajam ātrumam?

🚀 You've entered SpeedCore 🚀
⚡️ Here coffee is not a drink... it's a reaction!
🧪 Forget about beans. Turn on chemical mode.
💥 Ready for maximum speed?

Выбери язык для продолжения:"""

    await update.message.reply_text(speedcore_text, reply_markup=reply_markup)

async def handle_callback(update: Update, context: CallbackContext):
    global orders, referral_system, raffle_numbers, ratings, rated_orders

    if not isinstance(ratings, dict):
        ratings = {}
    if not isinstance(rated_orders, dict):
        rated_orders = {}

    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.user_data['lang'] = lang

        # Генерация реферальной ссылки
        user_id = str(update.effective_user.id)
        if user_id not in referral_system:
            referral_system[user_id] = {
                "invited": [],
                "orders": 0,
                "ref_code": f"ref_{user_id}",
                "raffle_number": len(referral_system) + 1
            }
            save_referral_system(referral_system)

        ref_data = referral_system[user_id]
        keyboard = [
            [InlineKeyboardButton(TEXTS[lang]['make_order'], callback_data="make_order")],
            [InlineKeyboardButton("🎯 Реферальная система" if lang == 'ru' else "🎯 Atsauces sistēma" if lang == 'lv' else "🎯 Referral system", callback_data="ref_info")],
            [InlineKeyboardButton("⭐ Оценить заказ" if lang == 'ru' else "⭐ Novērtēt pasūtījumu" if lang == 'lv' else "⭐ Rate order", callback_data="rate_info")],
            [InlineKeyboardButton("🎁 Счастливый сундук" if lang == 'ru' else "🎁 Laimīgā lāde" if lang == 'lv' else "🎁 Lucky chest", callback_data="lucky_chest")],
            [InlineKeyboardButton("🎉 Мои подарки" if lang == 'ru' else "🎉 Manas dāvanas" if lang == 'lv' else "🎉 My gifts", callback_data="my_gifts")]
        ]

        # Подсчет средней оценки
        total_ratings = list(ratings.values())
        avg_rating = sum(total_ratings) / len(total_ratings) if total_ratings else 0
        stars = "⭐" * round(avg_rating)

        rating_text = f"Рейтинг магазина: {stars} ({len(total_ratings)} отзывов)" if lang == 'ru' else f"Veikala reitings: {stars} ({len(total_ratings)} atsauksmes)" if lang == 'lv' else f"Shop rating: {stars} ({len(total_ratings)} reviews)"
        raffle_text = f"Ваш номер для розыгрыша: {ref_data['raffle_number']}" if lang == 'ru' else f"Jūsu izlozes numurs: {ref_data['raffle_number']}" if lang == 'lv' else f"Your raffle number: {ref_data['raffle_number']}"
        ref_link_text = "Реферальная ссылка:" if lang == 'ru' else "Atsauces saite:" if lang == 'lv' else "Referral link:"

        welcome_text = f"""{TEXTS[lang]['welcome']}

📊 {rating_text}
🎲 {raffle_text}

🔗 {ref_link_text}
t.me/{context.bot.username}?start={ref_data['ref_code']}"""

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_text, reply_markup=reply_markup)
        return

    lang = context.user_data.get('lang', 'ru')

    if query.data == "order":
        keyboard = [
            [InlineKeyboardButton(TEXTS[lang]['make_order'], callback_data="make_order")],
            [InlineKeyboardButton("🎯 Реферальная система" if lang == 'ru' else "🎯 Atsauces sistēma" if lang == 'lv' else "🎯 Referral system", callback_data="ref_info")],
            [InlineKeyboardButton("⭐ Оценить заказ" if lang == 'ru' else "⭐ Novērtēt pasūtījumu" if lang == 'lv' else "⭐ Rate order", callback_data="rate_info")],
            [InlineKeyboardButton("🎁 Счастливый сундук" if lang == 'ru' else "🎁 Laimīgā lāde" if lang == 'lv' else "🎁 Lucky chest", callback_data="lucky_chest")],
            [InlineKeyboardButton("🎉 Мои подарки" if lang == 'ru' else "🎉 Manas dāvanas" if lang == 'lv' else "🎉 My gifts", callback_data="my_gifts")]
        ]
        await query.edit_message_text(TEXTS[lang]['welcome'], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "make_order":
        packages_keyboard = [[InlineKeyboardButton(f"🎁 VX Coffee {p} — {pr['regular']} 💫", callback_data=f"package_{p}")] for p, pr in PRICES.items()]
        await query.edit_message_text(TEXTS[lang]['select_amount'], reply_markup=InlineKeyboardMarkup(packages_keyboard))

    elif query.data.startswith("package_"):
        p = query.data.split("_", 1)[1]
        context.user_data["package"] = p
        methods = [[InlineKeyboardButton(k, callback_data=f"pay_{k}")] for k in CRYPTO_ADDRESSES.keys()]
        await query.edit_message_text(TEXTS[lang]['select_payment'].format(p), reply_markup=InlineKeyboardMarkup(methods))

    elif query.data.startswith("pay_"):
        m = query.data.split("_")[1]
        p = context.user_data.get("package", "?")
        is_crypto = m in ["BTC", "USDT", "TON", "LTC", "Monero"]
        price = PRICES.get(p, {"regular": "?", "crypto": "?"})
        price = price["crypto"] if is_crypto else price["regular"]
        addr = CRYPTO_ADDRESSES[m]
        context.user_data.update({
            "payment": m,
            "address": addr,
            "price": price
        })

        delivery_keyboard = [
            [InlineKeyboardButton(TEXTS[lang]['drop'], callback_data="delivery_drop")],
            [InlineKeyboardButton(TEXTS[lang]['mail'], callback_data="delivery_mail")]
        ]
        await query.edit_message_text(TEXTS[lang]['select_delivery'], reply_markup=InlineKeyboardMarkup(delivery_keyboard))

    elif query.data.startswith("delivery_"):
        delivery_map = {
            'ru': {"delivery_drop": "Дроп", "delivery_mail": "Почтовая посылка"},
            'lv': {"delivery_drop": "Drop", "delivery_mail": "Pasta sūtījums"},
            'en': {"delivery_drop": "Drop", "delivery_mail": "Postal package"}
        }
        delivery = delivery_map[lang][query.data]
        context.user_data["delivery"] = delivery

        districts_keyboard = [
            [InlineKeyboardButton("🏘️ Болдерая", callback_data="district_bolderaja")],
            [InlineKeyboardButton("🏘️ Иманта", callback_data="district_imanta")],
            [InlineKeyboardButton("🏘️ Ільгуциемс", callback_data="district_ilguciems")],
            [InlineKeyboardButton("🏘️ Золитуде", callback_data="district_zolitude")],
            [InlineKeyboardButton("🏘️ Зепниекалнс", callback_data="district_zep")],
            [InlineKeyboardButton("🏘️ Саркандаугава", callback_data="district_sarkandaugava")],
            [InlineKeyboardButton("🏘️ Межапарк", callback_data="district_mezaparks")],
            [InlineKeyboardButton("🏘️ Плявниеки", callback_data="district_plavnieki")],
            [InlineKeyboardButton("🏘️ Пурвциемс", callback_data="district_purvciems")],
            [InlineKeyboardButton("🏘️ Вецмилгравис", callback_data="district_vecmilgravis")]
        ]
        await query.edit_message_text(
            TEXTS[lang]['select_district'],
            reply_markup=InlineKeyboardMarkup(districts_keyboard)
        )
    elif query.data.startswith("admin_"):
        if query.data == "admin_clients":
            await show_clients_stats(query)
        elif query.data == "admin_referrals":
            await show_referral_stats(query)
        elif query.data == "admin_raffle":
            await conduct_raffle(query, context)
        elif query.data == "admin_back":
            keyboard = [
                [InlineKeyboardButton("📋 Активные заказы", callback_data="admin_active")],
                [InlineKeyboardButton("🔄 Принятые заказы", callback_data="admin_accepted")],
                [InlineKeyboardButton("✅ Выполненные заказы", callback_data="admin_completed")],
                [InlineKeyboardButton("❌ Отмененные заказы", callback_data="admin_cancelled")],
                [InlineKeyboardButton("👥 Статистика клиентов", callback_data="admin_clients")],
                [InlineKeyboardButton("🎯 Реферальная система", callback_data="admin_referrals")],
                [InlineKeyboardButton("🎲 Провести розыгрыш", callback_data="admin_raffle")]
            ]
            await query.edit_message_text(
                TEXTS[lang]['admin_panel'],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            status = query.data.split("_")[1]
            admin_id = str(update.effective_user.id)
            await show_orders(query, status, admin_id)
    elif query.data.startswith("confirm_"):
        order_id = int(query.data.split("_")[1])
        admin_id = str(update.effective_user.id)

        for order in orders['active']:
            if order['id'] == order_id:
                # Закрепляем заказ за админом
                order['assigned_admin'] = admin_id
                order['admin_username'] = update.effective_user.username or f"Admin_{admin_id}"

                # Переносим заказ в состояние "принят" (НЕ в выполненные)
                orders['accepted'].append(order)
                orders['active'].remove(order)
                save_orders(orders)

                # Если это заказ-подарок, обновляем статус подарка у пользователя
                if order.get('is_gift', False):
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"✅ Ваш подарок принят в работу администратором @{order['admin_username']}!\n\n🎁 {order['product']}\n\n⏳ Ожидайте дальнейших инструкций"
                        )
                    except Exception as e:
                        print(f"Error accepting gift: {e}")
                else:
                    # Обычный заказ - уведомляем о принятии
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"✅ Ваш заказ #{order_id} принят администратором @{order['admin_username']}!\n\n📦 Товар: {order['product']}\n💰 Цена: {order['price']}\n\n⏳ Ожидайте дальнейших инструкций по оплате"
                        )
                    except Exception as e:
                        print(f"Error notifying user about order acceptance: {e}")

                # Уведомляем других админов о том, что заказ принят
                for other_admin_id in ADMIN_IDS:
                    if other_admin_id != admin_id:
                        try:
                            await context.bot.send_message(
                                chat_id=other_admin_id,
                                text=f"📋 Заказ #{order_id} принят администратором @{order['admin_username']}"
                            )
                        except Exception as e:
                            print(f"Failed to notify admin {other_admin_id}: {e}")
                break
        await show_orders(query, 'active')
    elif query.data.startswith("paid_"):
        # Обработка кнопки "Оплачено"
        order_id = int(query.data.split("_")[1])
        admin_id = str(update.effective_user.id)

        for order in orders['accepted']:
            if order['id'] == order_id and order.get('assigned_admin') == admin_id:
                orders['completed'].append(order)
                orders['accepted'].remove(order)
                save_orders(orders)  # Сохраняем изменения в базу

                # Обработка реферальной системы при ОПЛАТЕ заказа
                invited_by = order.get('invited_by')
                if invited_by and invited_by in referral_system:
                    ref_data = referral_system[invited_by]

                    # Увеличиваем счетчик заказов реферера только при оплате
                    if "orders" not in ref_data:
                        ref_data["orders"] = 0
                    ref_data["orders"] += 1
                    save_referral_system(referral_system)  # Сохраняем реферальные данные

                    # Уведомление реферера с подробностями
                    try:
                        remaining_orders = 10 - ref_data["orders"]
                        ref_notification = f"""🎯 Заказ вашего реферала @{order['username']} оплачен!

📦 Заказ: #{order['id']} - {order['product']}
📊 Ваших реф. заказов: {ref_data["orders"]}/10
🎁 До подарка осталось: {max(0, remaining_orders)} заказов

{'🎉 Поздравляем! Вы получили подарок за 10 реферальных заказов!' if ref_data["orders"] >= 10 else ''}"""

                        await context.bot.send_message(chat_id=int(invited_by), text=ref_notification)

                        # Если достигли 10 заказов, добавляем подарок
                        if ref_data["orders"] % 10 == 0:
                            # Здесь можно добавить подарок в систему подарков реферера
                            pass

                    except Exception as e:
                        print(f"Failed to notify referrer about payment: {e}")

                # Если это заказ-подарок
                if order.get('is_gift', False):
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"🎉 Ваш подарок выполнен!\n\n🎁 {order['product']}\n\n📞 Свяжитесь с {ADMIN_CONTACT} для уточнения деталей получения подарка!"
                        )
                    except Exception as e:
                        print(f"Error completing gift: {e}")
                else:
                    # Обычный заказ - просим оценить
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"🎉 Ваш заказ #{order_id} выполнен и оплачен!\n\n📦 Товар: {order['product']}\n💰 Сумма: {order['price']}\n\n⭐ Теперь вы можете оценить качество нашего сервиса в боте!\n\n💫 Ваша оценка поможет нам стать лучше!"
                        )
                    except Exception as e:
                        print(f"Error notifying user about completion: {e}")
                break
        await show_orders(query, 'accepted', admin_id)

    elif query.data.startswith("cancel_"):
        order_id = int(query.data.split("_")[1])
        admin_id = str(update.effective_user.id)

        # Проверяем в активных заказах
        for order in orders['active']:
            if order['id'] == order_id:
                orders['cancelled'].append(order)
                orders['active'].remove(order)
                save_orders(orders)

                if order.get('is_gift', False):
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"❌ Заявка на подарок отклонена администратором\n\n🎁 {order['product']}\n\n💭 Подарок остается доступным для повторного использования"
                        )
                    except Exception as e:
                        print(f"Error cancelling gift: {e}")
                else:
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"❌ Ваш заказ #{order_id} отклонен администратором\n\n📦 Товар: {order['product']}\n💰 Цена: {order['price']}\n\n💬 Если у вас есть вопросы, свяжитесь с {ADMIN_CONTACT}"
                        )
                    except Exception as e:
                        print(f"Error notifying user about cancellation: {e}")
                await show_orders(query, 'active')
                return

        # Проверяем в принятых заказах (отмена из-за неоплаты)
        for order in orders['accepted']:
            if order['id'] == order_id and order.get('assigned_admin') == admin_id:
                orders['cancelled'].append(order)
                orders['accepted'].remove(order)
                save_orders(orders)

                if order.get('is_gift', False):
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"❌ Подарок отменен администратором\n\n🎁 {order['product']}\n\n💭 Подарок остается доступным для повторного использования"
                        )
                    except Exception as e:
                        print(f"Error cancelling gift: {e}")
                else:
                    # Уведомление о неоплате
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text=f"❌ Заказ #{order_id} отменен из-за неоплаты\n\n📦 Товар: {order['product']}\n💰 Сумма: {order['price']}\n\n💰 Если вы оплатили заказ, пожалуйста, свяжитесь с {ADMIN_CONTACT} с подтверждением оплаты"
                        )
                    except Exception as e:
                        print(f"Error notifying user about non-payment: {e}")
                await show_orders(query, 'accepted', admin_id)
                return
    elif query.data == "ref_info":
        user_id = str(update.effective_user.id)
        if user_id not in referral_system:
            referral_system[user_id] = {
                "invited": [], 
                "orders": 0,
                "ref_code": f"ref_{user_id}",
                "raffle_number": len(referral_system) + 1,
                "invited_by": None
            }
            save_referral_system(referral_system)

        ref_data = referral_system[user_id]
        invited = len(ref_data.get("invited", []))
        ref_orders = ref_data.get("orders", 0)  # Заказы рефералов
        remaining = max(0, 10 - ref_orders)
        invited_by = ref_data.get("invited_by")

        # Информация о том, кто пригласил
        invited_by_text = ""
        if invited_by:
            try:
                inviter_chat = await context.bot.get_chat(int(invited_by))
                inviter_username = inviter_chat.username or f"ID{invited_by}"
                invited_by_text_map = {
                    'ru': f"\n👤 Вас пригласил: @{inviter_username}",
                    'lv': f"\n👤 Jūs uzaicināja: @{inviter_username}",
                    'en': f"\n👤 You were invited by: @{inviter_username}"
                }
                invited_by_text = invited_by_text_map[lang]
            except:
                invited_by_text_map = {
                    'ru': f"\n👤 Вас пригласил: ID{invited_by}",
                    'lv': f"\n👤 Jūs uzaicināja: ID{invited_by}",
                    'en': f"\n👤 You were invited by: ID{invited_by}"
                }
                invited_by_text = invited_by_text_map[lang]

        text_map = {
            'ru': f"""🎯 Ваша реферальная статистика:{invited_by_text}

👥 Приглашено пользователей: {invited}
📦 Ваши рефералы сделали заказов: {ref_orders}
🎁 Засчитано для подарка: {ref_orders}/10
⏳ До подарка осталось: {remaining} заказов

🔗 Ваша реферальная ссылка:
t.me/{context.bot.username}?start=ref_{user_id}

💡 За каждые 10 заказов ваших рефералов вы получаете подарок!""",
            'lv': f"""🎯 Jūsu atsauces statistika:{invited_by_text}

👥 Uzaicināti lietotāji: {invited}
📦 Jūsu atsauces veica pasūtījumus: {ref_orders}
🎁 Ieskaitīts dāvanai: {ref_orders}/10
⏳ Līdz dāvanai atlicis: {remaining} pasūtījumi

🔗 Jūsu atsauces saite:
t.me/{context.bot.username}?start=ref_{user_id}

💡 Par katram 10 jūsu atsauču pasūtījumiem jūs saņemat dāvanu!""",
            'en': f"""🎯 Your referral statistics:{invited_by_text}

👥 Invited users: {invited}
📦 Your referrals made orders: {ref_orders}
🎁 Counted for gift: {ref_orders}/10
⏳ Orders left for gift: {remaining}

🔗 Your referral link:
t.me/{context.bot.username}?start=t.me/{context.bot.username}?start=ref_{user_id}

💡 For every 10 orders of your referrals you get a gift!"""
        }

        keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]]
        await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "raffle_info":
        user_id = str(update.effective_user.id)
        if user_id not in raffle_numbers:
            raffle_numbers[user_id] = len(raffle_numbers) + 1

        text_map = {
            'ru': f"🎲 Ваш номер для розыгрышей: {raffle_numbers[user_id]}",
            'lv': f"🎲 Jūsu izlozes numurs: {raffle_numbers[user_id]}",
            'en': f"🎲 Your raffle number: {raffle_numbers[user_id]}"
        }
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]]
        await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "rate_info":
        user_id = str(update.effective_user.id)
        completed_orders = []

        # Получаем список уже оцененных заказов для этого пользователя
        user_rated_orders = rated_orders.get(user_id, set())

        for order in orders['completed']:
            if str(order['user_id']) == user_id and order['id'] not in user_rated_orders:
                completed_orders.append(order)

        if not completed_orders:
            # Проверяем, есть ли вообще выполненные заказы у пользователя
            all_user_completed = [order for order in orders['completed'] if str(order['user_id']) == user_id]

            if not all_user_completed:
                message_map = {
                    'ru': "⚠️ У вас нет подтвержденных заказов для оценки.",
                    'lv': "⚠️ Jums nav apstiprinātu pasūtījumu novērtēšanai.",
                    'en': "⚠️ You have no confirmed orders to rate."
                }
            else:
                message_map = {
                    'ru': "⚠️ Все ваши заказы уже оценены.",
                    'lv': "⚠️ Visi jūsu pasūtījumi jau ir novērtēti.",
                    'en': "⚠️ All your orders have already been rated."
                }

            keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data=f"lang_{lang}")]]
            await query.edit_message_text(
                message_map[lang],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        keyboard = []
        text_map = {
            'ru': "📦 Выберите заказ для оценки:\n\n",
            'lv': "📦 Izvēlieties pasūtījumu novērtēšanai:\n\n",
            'en': "📦 Select order to rate:\n\n"
        }
        text = text_map[lang]

        for order in completed_orders:
            order_text_map = {
                'ru': f"Заказ #{order['id']} - {order['product']}",
                'lv': f"Pasūtījums #{order['id']} - {order['product']}",
                'en': f"Order #{order['id']} - {order['product']}"
            }
            keyboard.append([InlineKeyboardButton(
                order_text_map[lang],
                callback_data=f"select_order_{order['id']}"
            )])
        keyboard.append([InlineKeyboardButton(TEXTS[lang]['back'], callback_data=f"lang_{lang}")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("select_order_"):
        order_id = int(query.data.split("_")[2])
        context.user_data['rating_order_id'] = order_id

        text_map = {
            'ru': f"⭐ Оцените заказ #{order_id}\n\nВыберите количество звезд:",
            'lv': f"⭐ Novērtējiet pasūtījumu #{order_id}\n\nIzvēlieties zvaigžņu skaitu:",
            'en': f"⭐ Rate order #{order_id}\n\nSelect number of stars:"
        }
        keyboard = [
            [InlineKeyboardButton("⭐", callback_data="rate_stars_1")],
            [InlineKeyboardButton("⭐⭐", callback_data="rate_stars_2")],
            [InlineKeyboardButton("⭐⭐⭐", callback_data="rate_stars_3")],
            [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_stars_4")],
            [InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_stars_5")],
            [InlineKeyboardButton(TEXTS[lang]['back'], callback_data="rate_info")]
        ]
        await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "lucky_chest":
        user_id = str(update.effective_user.id)
        user_data = get_user_data(user_id)
        last_game_str = user_data.get('last_game_time')
        last_game = datetime.fromisoformat(last_game_str) if last_game_str else None
        now = datetime.now()

        if last_game and (now - last_game).total_seconds() < 86400:  # 24 часа
            remaining_time = 86400 - int((now - last_game).total_seconds())
            hours = remaining_time // 3600
            minutes = (remaining_time % 3600) // 60

            text_map = {
                'ru': f"⏳ Следующая игра будет доступна через {hours} ч. {minutes} мин.",
                'lv': f"⏳ Nākamā spēle būs pieejama pēc {hours} st. {minutes} min.",
                'en': f"⏳ Next game will be available in {hours} h. {minutes} min."
            }
            keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]]
            await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))
            return

        text_map = {
            'ru': "🎲 Выберите один из трёх сундуков:",
            'lv': "🎲 Izvēlieties vienu no trim lādēm:",
            'en': "🎲 Choose one of three chests:"
        }

        chest_text_map = {
            'ru': ["🎁 Сундук 1", "🎁 Сундук 2", "🎁 Сундук 3"],
            'lv': ["🎁 Lāde 1", "🎁 Lāde 2", "🎁 Lāde 3"],
            'en': ["🎁 Chest 1", "🎁 Chest 2", "🎁 Chest 3"]
        }

        keyboard = [
            [InlineKeyboardButton(chest_text_map[lang][0], callback_data="chest_1")],
            [InlineKeyboardButton(chest_text_map[lang][1], callback_data="chest_2")],
            [InlineKeyboardButton(chest_text_map[lang][2], callback_data="chest_3")],
            [InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]
        ]
        await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("chest_"):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Аноним"
        chest_number = query.data.split("_")[1]
        user_data = get_user_data(user_id)

        # Независимый шанс 33% на выигрыш для каждого сундука
        win_chance = random.random() < 0.33  # 33% шанс на выигрыш

        if win_chance:
            prizes_map = {
                'ru': [
                    "VX Coffee 1 упаковка бесплатно! 🎁",
                    "50% скидка на следующий заказ! 💫",
                    "VX Coffee 0.5 упаковки бесплатно! 🎁",
                    "30% скидка на следующий заказ! 💫",
                    "20% скидка на следующий заказ! 💫"
                ],
                'lv': [
                    "VX Coffee 1 iepakojums bez maksas! 🎁",
                    "50% atlaide nākamajam pasūtījumam! 💫",
                    "VX Coffee 0.5 iepakojuma bez maksas! 🎁",
                    "30% atlaide nākamajam pasūtījumam! 💫",
                    "20% atlaide nākamajam pasūtījumam! 💫"
                ],
                'en': [
                    "VX Coffee 1 package for free! 🎁",
                    "50% discount on next order! 💫",
                    "VX Coffee 0.5 package for free! 🎁",
                    "30% discount on next order! 💫",
                    "20% discount on next order! 💫"
                ]
            }
        else:
            prizes_map = {
                'ru': ["Пустой сундук 📦"],
                'lv': ["Tukša lāde 📦"],
                'en': ["Empty chest 📦"]
            }

        prize = random.choice(prizes_map[lang])

        # Получаем данные пользователя
        user_data = get_user_data(user_id)
        user_data['last_game_time'] = datetime.now().isoformat()

        # Инициализируем списки если их нет
        if 'opened_chests' not in user_data:
            user_data['opened_chests'] = []
        if 'gifts' not in user_data:
            user_data['gifts'] = []

        # Если приз не пустой, добавляем его в подарки
        empty_chest_keywords = ["Пустой сундук", "Tukša lāde", "Empty chest"]
        if not any(keyword in prize for keyword in empty_chest_keywords):
            user_data['gifts'].append({
                'description': prize,
                'source': 'chest',
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'used': False
            })

        user_data['opened_chests'].append({
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'prize': prize,
            'chest_number': chest_number
        })

        # Сохраняем все данные пользователя
        save_user_data(user_id, user_data)

        # Уведомление для админов
        admin_text = f"""
🎁 Открыт сундук!
👤 Пользователь: @{username}
📦 Сундук №{chest_number}
🎉 Приз: {prize}
📅 Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        # Отправляем уведомление всем админам
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=admin_text)
            except Exception as e:
                print(f"Failed to notify admin {admin_id} about chest: {e}")

        text_map = {
            'ru': f"🎁 Вы открыли сундук и получили:\n{prize}\n\n📝 История ваших призов сохранена!",
            'lv': f"🎁 Jūs atvērāt lādi un saņēmāt:\n{prize}\n\n📝 Jūsu balvu vēsture ir saglabāta!",
            'en': f"🎁 You opened the chest and received:\n{prize}\n\n📝 Your prize history has been saved!"
        }

        back_text_map = {
            'ru': "⬅️ В меню",
            'lv': "⬅️ Uz izvēlni",
            'en': "⬅️ To menu"
        }

        keyboard = [[InlineKeyboardButton(back_text_map[lang], callback_data="order")]]
        await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("rate_stars_"):
        try:
            rating = int(query.data.split("_")[2])
            order_id = context.user_data.get('rating_order_id')
            user_id = str(update.effective_user.id)

            if order_id:
                # Проверяем, не оценен ли уже этот заказ этим пользователем
                if user_id not in rated_orders:
                    rated_orders[user_id] = set()

                if order_id in rated_orders[user_id]:
                    text_map = {
                        'ru': "⚠️ Вы уже оценили этот заказ!",
                        'lv': "⚠️ Jūs jau esat novērtējuši šo pasūtījumu!",
                        'en': "⚠️ You have already rated this order!"
                    }
                    await query.edit_message_text(
                        text_map[lang],
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="rate_info")]])
                    )
                    return

                # Сохраняем оценку
                ratings[str(order_id)] = rating
                rated_orders[user_id].add(order_id)
                save_ratings(ratings)
                save_rated_orders(rated_orders)

                # Подсчет средней оценки
                total_ratings = list(ratings.values())
                avg_rating = sum(total_ratings) / len(total_ratings) if total_ratings else 0

                thanks_text_map = {
                    'ru': f"✅ Спасибо за ваш отзыв! Ваша оценка: {'⭐' * rating}",
                    'lv': f"✅ Paldies par jūsu atsauksmi! Jūsu vērtējums: {'⭐' * rating}",
                    'en': f"✅ Thank you for your feedback! Your rating: {'⭐' * rating}"
                }

                await query.edit_message_text(
                    thanks_text_map[lang],
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]])
                )

                # Отправка информации в админку всем админам
                rating_notification = f"📊 Новая оценка!\n👤 От: @{update.effective_user.username or 'Аноним'}\nЗаказ #{order_id}: {'⭐' * rating}\n\nСредняя оценка: {avg_rating:.1f}⭐"
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(chat_id=admin_id, text=rating_notification)
                    except Exception as e:
                        print(f"Failed to notify admin {admin_id} about rating: {e}")
            else:
                error_text_map = {
                    'ru': "Ошибка: не найден ID заказа для оценки.",
                    'lv': "Kļūda: nav atrasts pasūtījuma ID novērtēšanai.",
                    'en': "Error: order ID not found for rating."
                }
                await query.edit_message_text(
                    error_text_map[lang],
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]])
                )
        except Exception as e:
            print(f"Error in rating: {e}")
            error_text_map = {
                'ru': "Произошла ошибка при сохранении оценки. Попробуйте позже.",
                'lv': "Radās kļūda, saglabājot vērtējumu. Mēģiniet vēlāk.",
                'en': "An error occurred while saving the rating. Try again later."
            }
            await query.edit_message_text(
                error_text_map[lang],
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]])
            )

    elif query.data.startswith("district_"):
        try:
            if not isinstance(orders, dict):
                orders = {
                    'active': [],
                    'accepted': [],
                    'completed': [],
                    'cancelled': []
                }

            district = query.data.split("_")[1].capitalize()
            p = context.user_data.get("package", "?")
            price = context.user_data.get("price", "?")
            m = context.user_data.get("payment", "?")
            addr = context.user_data.get("address", "?")
            delivery = context.user_data.get("delivery", "?")

            order = {
                'id': len(orders['active']) + len(orders['accepted']) + len(orders['completed']) + len(orders['cancelled']) + 1,
                'user_id': update.effective_user.id,
                'username': update.effective_user.username or "Аноним",
                'product': f"VX Coffee {p}",
                'price': price,
                'payment_method': m,
                'delivery': delivery,
                'district': district,
                'status': 'active',
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            orders['active'].append(order)
            save_orders(orders)  # Сохраняем заказы в базу

            # Сохраняем информацию о реферале в заказе (но не засчитываем пока)
            user_id = str(update.effective_user.id)

            # Инициализируем реферальную систему для пользователя если её нет
            if user_id not in referral_system:
                referral_system[user_id] = {
                    'invited': [],
                    'orders': 0,
                    'ref_code': f"ref_{user_id}",
                    'raffle_number': len(referral_system) + 1,
                    'invited_by': None
                }
                save_referral_system(referral_system)

            # Проверяем, есть ли у пользователя инвайтер и сохраняем в заказе
            invited_by = referral_system[user_id].get("invited_by")
            order['invited_by'] = invited_by if invited_by and invited_by in referral_system else None

            # Уведомление админов
            admin_notification = f"""Новый заказ #{order['id']}!
👤 От: @{order['username']}
📦 Товар: {order['product']}
Цена: {price}
Доставка: {delivery}
Район: {district}
Дата: {order['date']}
Реферал: {'Да' if order['invited_by'] else 'Нет'}"""

            # Отправляем уведомление всем админам
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(chat_id=admin_id, text=admin_notification)
                except Exception as e:
                    print(f"Failed to notify admin {admin_id}: {e}")

            # Отправка подтверждения заказа пользователю
            try:
                confirmation_text_map = {
                    'ru': f"""✅ Ваш заказ #{order['id']} принят!

📦 Товар: VX Coffee {p}
💰 Цена: {price}
💳 Оплата через: {m}
🚚 Доставка: {delivery}
📍 Район: {district}

🔴 **АДРЕС ДЛЯ ОПЛАТЫ:**
💳 **{addr}**

После оплаты отправьте скриншот и ваш ник в {ADMIN_CONTACT}

Спасибо за ваш заказ! 🙏""",
                    'lv': f"""✅ Jūsu pasūtījums #{order['id']} ir pieņemts!

📦 Prece: VX Coffee {p}
💰 Cena: {price}
💳 Maksājums caur: {m}
🚚 Piegāde: {delivery}
📍 Rajons: {district}

🔴 **MAKSĀJUMA ADRESE:**
💳 **{addr}**

Pēc apmaksas nosūtiet ekrānuzņēmumu un savu lietotājvārdu uz {ADMIN_CONTACT}

Paldies par jūsu pasūtījumu! 🙏""",
                    'en': f"""✅ Your order #{order['id']} has been accepted!

📦 Product: VX Coffee {p}
💰 Price: {price}
💳 Payment via: {m}
🚚 Delivery: {delivery}
📍 District: {district}

🔴 **PAYMENT ADDRESS:**
💳 **{addr}**

After payment, send a screenshot and your nickname to {ADMIN_CONTACT}

Thank you for your order! 🙏"""
                }

                # Создаем кнопку для копирования адреса
                copy_button_text_map = {
                    'ru': "📋 Копировать адрес",
                    'lv': "📋 Kopēt adresi", 
                    'en': "📋 Copy address"
                }

                keyboard = [[InlineKeyboardButton(
                    copy_button_text_map[lang], 
                    callback_data=f"copy_address_{addr}"
                )]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    confirmation_text_map[lang], 
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Failed to send confirmation: {e}")
                simple_text_map = {
                    'ru': f"""✅ Ваш заказ #{order['id']} принят!

Товар: VX Coffee {p}
Цена: {price}
Оплата: {m}
Доставка: {delivery}
Район: {district}

🔴 АДРЕС ДЛЯ ОПЛАТЫ:
💳 {addr}

Для подтверждения отправьте скриншот оплаты в {ADMIN_CONTACT}""",
                    'lv': f"""✅ Jūsu pasūtījums #{order['id']} ir pieņemts!

Prece: VX Coffee {p}
Cena: {price}
Maksājums: {m}
Piegāde: {delivery}
Rajons: {district}

🔴 MAKSĀJUMA ADRESE:
💳 {addr}

Apstiprinājumam nosūtiet maksājuma ekrānuzņēmumu uz {ADMIN_CONTACT}""",
                    'en': f"""✅ Your order #{order['id']} has been accepted!

Product: VX Coffee {p}
Price: {price}
Payment: {m}
Delivery: {delivery}
District: {district}

🔴 PAYMENT ADDRESS:
💳 {addr}

For confirmation, send payment screenshot to {ADMIN_CONTACT}"""
                }

                # Создаем кнопку для копирования адреса (резервный вариант)
                copy_button_text_map = {
                    'ru': "📋 Копировать адрес",
                    'lv': "📋 Kopēt adresi", 
                    'en': "📋 Copy address"
                }

                keyboard = [[InlineKeyboardButton(
                    copy_button_text_map[lang], 
                    callback_data=f"copy_address_{addr}"
                )]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    simple_text_map[lang], 
                    reply_markup=reply_markup
                )

        except Exception as e:
            print(f"Error in district handling: {e}")
            await query.answer(f"Произошла ошибка. Попробуйте еще раз или свяжитесь с {ADMIN_CONTACT}")

    elif query.data == "my_gifts":
        user_id = str(update.effective_user.id)
        user_data = get_user_data(user_id)
        # Получаем подарки пользователя из базы данных
        gifts = user_data.get('gifts', [])

        if not gifts:
            text_map = {
                'ru': "🎁 У вас пока нет подарков.",
                'lv': "🎁 Jums pagaidām nav dāvanu.",
                'en': "🎁 You don't have any gifts yet."
            }
            text = text_map[lang]
            keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")]]
        else:
            text_map = {
                'ru': "🎁 Ваши подарки:\n\n",
                'lv': "🎁 Jūsu dāvanas:\n\n",
                'en': "🎁 Your gifts:\n\n"
            }
            text = text_map[lang]
            keyboard = []

            for i, gift in enumerate(gifts):
                used_status = gift.get('used', False)
                if used_status == 'pending':
                    status_text_map = {
                        'ru': " - ⏳ Ожидает подтверждения\n",
                        'lv': " - ⏳ Gaida apstiprinājumu\n",
                        'en': " - ⏳ Awaiting confirmation\n"
                    }
                    text += f"{i+1}. {gift['description']}{status_text_map[lang]}"
                elif used_status == True:
                    status_text_map = {
                        'ru': " - ✅ Использован\n",
                        'lv': " - ✅ Izmantots\n",
                        'en': " - ✅ Used\n"
                    }
                    text += f"{i+1}. {gift['description']}{status_text_map[lang]}"
                else:
                    status_text_map = {
                        'ru': " - 🎁 Доступен\n",
                        'lv': " - 🎁 Pieejams\n",
                        'en': " - 🎁 Available\n"
                    }
                    text += f"{i+1}. {gift['description']}{status_text_map[lang]}"

                    use_text_map = {
                        'ru': f"Использовать {i+1}",
                        'lv': f"Izmantot {i+1}",
                        'en': f"Use {i+1}"
                    }
                    keyboard.append([InlineKeyboardButton(use_text_map[lang], callback_data=f"use_gift_{i}")])
            keyboard.append([InlineKeyboardButton(TEXTS[lang]['back'], callback_data="order")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("use_gift_"):
        gift_index = int(query.data.split("_")[2])
        user_id = str(update.effective_user.id)
        user_data = get_user_data(user_id)
        gifts = user_data.get('gifts', [])

        if 0 <= gift_index < len(gifts):
            gift = gifts[gift_index]
            if not gift.get('used', False):
                # Создаем заказ-подарок в админке
                gift_order = {
                    'id': len(orders['active']) + len(orders['accepted']) + len(orders['completed']) + len(orders['cancelled']) + 1,
                    'user_id': update.effective_user.id,
                    'username': update.effective_user.username or "Аноним",
                    'product': f"🎁 ПОДАРОК: {gift['description']}",
                    'price': "БЕСПЛАТНО",
                    'payment_method': "ПОДАРОК",
                    'delivery': "По согласованию",
                    'district': "По согласованию",
                    'status': 'gift_pending',
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'gift_index': gift_index,
                    'is_gift': True
                }

                orders['active'].append(gift_order)

                # Помечаем подарок как ожидающий подтверждения
                gift['used'] = 'pending'
                gift['order_id'] = gift_order['id']
                user_data['gifts'] = gifts
                save_user_data(user_id, user_data)  # Сохраняем изменения

                # Уведомление админов о новом заказе-подарке
                admin_text = f"""🎁 НОВЫЙ ЗАКАЗ-ПОДАРОК #{gift_order['id']}!
👤 От: @{gift_order['username']}
🎁 Подарок: {gift['description']}
📅 Дата: {gift_order['date']}

⚠️ Требуется подтверждение администратора!"""

                # Отправляем уведомление всем админам
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(chat_id=admin_id, text=admin_text)
                    except Exception as e:
                        print(f"Failed to notify admin {admin_id} about gift order: {e}")

                # Сообщение пользователю
                text_map = {
                    'ru': f"🎁 Заявка на использование подарка отправлена!\n\n📦 Подарок: {gift['description']}\n⏳ Ожидайте подтверждения администратора",
                    'lv': f"🎁 Pieteikums dāvanas izmantošanai ir nosūtīts!\n\n📦 Dāvana: {gift['description']}\n⏳ Gaidiet administratora apstiprinājumu",
                    'en': f"🎁 Gift usage request has been sent!\n\n📦 Gift: {gift['description']}\n⏳ Wait for administrator confirmation"
                }
                keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="my_gifts")]]
                await query.edit_message_text(text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                status_text_map = {
                    'ru': "использован" if gift.get('used') == True else "ожидает подтверждения",
                    'lv': "izmantots" if gift.get('used') == True else "gaida apstiprinājumu",
                    'en': "used" if gift.get('used') == True else "awaiting confirmation"
                }

                warning_text_map = {
                    'ru': f"⚠️ Этот подарок уже {status_text_map[lang]}.",
                    'lv': f"⚠️ Šī dāvana jau ir {status_text_map[lang]}.",
                    'en': f"⚠️ This gift is already {status_text_map[lang]}."
                }

                keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="my_gifts")]]
                await query.edit_message_text(warning_text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            error_text_map = {
                'ru': "⚠️ Неверный индекс подарка.",
                'lv': "⚠️ Nepareizs dāvanas indekss.",
                'en': "⚠️ Invalid gift index."
            }
            keyboard = [[InlineKeyboardButton(TEXTS[lang]['back'], callback_data="my_gifts")]]
            await query.edit_message_text(error_text_map[lang], reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("copy_address_"):
        # Обработчик для копирования адреса оплаты
        address = query.data.replace("copy_address_", "")

        copy_success_text_map = {
            'ru': f"📋 Адрес скопирован в буфер обмена!\n💳 {address}",
            'lv': f"📋 Adrese nokopēta starpliktuvē!\n💳 {address}",
            'en': f"📋 Address copied to clipboard!\n💳 {address}"
        }

        await query.answer(
            copy_success_text_map[context.user_data.get('lang', 'ru')], 
            show_alert=True
        )
        return

    elif query.data == "noop":
        # Обработчик для неактивных кнопок
        noop_text_map = {
            'ru': "Этот заказ уже в работе у другого администратора",
            'lv': "Šis pasūtījums jau ir darbā pie cita administratora",
            'en': "This order is already being handled by another administrator"
        }
        await query.answer(noop_text_map[context.user_data.get('lang', 'ru')], show_alert=True)
        return

async def admin(update: Update, context: CallbackContext):
    """Админ-панель для управления заказами"""
    user_id = str(update.effective_user.id)
    lang = context.user_data.get('lang', 'ru')
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(TEXTS[lang]['admin_access_denied'].format(user_id))
        return

    keyboard = [
        [InlineKeyboardButton("📋 Активные заказы", callback_data="admin_active")],
        [InlineKeyboardButton("🔄 Принятые заказы", callback_data="admin_accepted")],
        [InlineKeyboardButton("✅ Выполненные заказы", callback_data="admin_completed")],
        [InlineKeyboardButton("❌ Отмененные заказы", callback_data="admin_cancelled")],
        [InlineKeyboardButton("👥 Статистика клиентов", callback_data="admin_clients")],
        [InlineKeyboardButton("🎯 Реферальная система", callback_data="admin_referrals")],
        [InlineKeyboardButton("🎲 Провести розыгрыш", callback_data="admin_raffle")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS[lang]['admin_panel'], reply_markup=reply_markup)

async def show_clients_stats(query):
    """Показать статистику клиентов"""
    from datetime import datetime, timedelta
    referral_system = get_referral_system()
    orders = get_orders()
    total_users = len(referral_system)
    total_orders = sum(len(orders[status]) for status in ['active', 'accepted', 'completed', 'cancelled'])

    # Подсчет прибыли
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(weeks=1)
    month_ago = now - timedelta(days=30)

    daily_profit = 0
    weekly_profit = 0
    monthly_profit = 0

    # Собираем информацию о клиентах и прибыли
    client_data = {}

    # Добавляем данные из всех заказов
    for status in ['active', 'accepted', 'completed', 'cancelled']:
        for order in orders.get(status, []):
            user_id = str(order['user_id'])
            username = order.get('username', 'Аноним')
            district = order.get('district', 'Неизвестен')
            order_date = datetime.strptime(order['date'], "%Y-%m-%d %H:%M:%S")

            if user_id not in client_data:
                client_data[user_id] = {
                    'username': username,
                    'districts': set(),
                    'order_count': 0,
                    'unused_gifts': 0
                }

            client_data[user_id]['districts'].add(district)
            client_data[user_id]['order_count'] += 1

            # Подсчет прибыли только с выполненных заказов
            if status == 'completed' and not order.get('is_gift', False):
                price_str = order.get('price', '0€')
                # Извлекаем числовое значение из строки цены
                try:
                    price_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_str.replace(',', '.'))))
                    if order_date >= day_ago:
                        daily_profit += price_value
                    if order_date >= week_ago:
                        weekly_profit += price_value
                    if order_date >= month_ago:
                        monthly_profit += price_value
                except:
                    pass

    # Подсчитываем неиспользованные подарки у клиентов
    for user_id in client_data.keys():
        user_data = get_user_data(user_id)
        gifts = user_data.get('gifts', [])
        unused_count = sum(1 for gift in gifts if not gift.get('used', False))
        client_data[user_id]['unused_gifts'] = unused_count

    text = f"""👥 Статистика клиентов:

📊 Общая статистика:
• Всего пользователей: {total_users}
• Всего заказов: {total_orders}
• Активных заказов: {len(orders.get('active', []))}
• Принятых заказов: {len(orders.get('accepted', []))}
• Выполненных заказов: {len(orders.get('completed', []))}
• Отмененных заказов: {len(orders.get('cancelled', []))}

💰 Прибыль:
• За день: {daily_profit:.1f}€
• За неделю: {weekly_profit:.1f}€
• За месяц: {monthly_profit:.1f}€

📋 Топ клиенты по заказам:
"""

    # Сортируем клиентов по количеству заказов (по убыванию)
    sorted_clients = sorted(client_data.items(), key=lambda x: x[1]['order_count'], reverse=True)

    # Показываем только топ-10 клиентов для компактности
    for i, (user_id, data) in enumerate(sorted_clients[:10], 1):
        username = data['username']
        districts = ', '.join(list(data['districts'])[:3])  # Показываем максимум 3 района
        if len(data['districts']) > 3:
            districts += "..."
        order_count = data['order_count']
        unused_gifts = data['unused_gifts']

        text += f"{i}. @{username} (ID: {user_id})\n"
        text += f"   📍 Районы: {districts}\n"
        text += f"   📦 Заказов: {order_count}\n"
        text += f"   🎁 Неиспользованных подарков: {unused_gifts}\n"
        text += f"───────────────\n"

    if len(sorted_clients) > 10:
        text += f"\n... и еще {len(sorted_clients) - 10} клиентов"

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_referral_stats(query):
    """Показать статистику реферальной системы"""
    referral_system = get_referral_system()
    orders = get_orders()
    text = "🎯 Реферальная система:\n\n"

    if not referral_system:
        text += "📝 Пока нет пользователей в реферальной системе"
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Собираем статистику
    total_invitations = sum(len(data.get('invited', [])) for data in referral_system.values())
    total_ref_orders = sum(data.get('orders', 0) for data in referral_system.values())
    total_gifts_earned = sum(data.get('orders', 0) // 10 for data in referral_system.values())

    text += f"""📊 Общая статистика:
• Всего приглашений: {total_invitations}
• Заказов от рефералов: {total_ref_orders}
• Подарков выдано: {total_gifts_earned}

🏆 Топ рефереры:
"""

    # Сортируем по количеству заказов рефералов
    active_referrers = []
    for user_id, data in referral_system.items():
        invited_count = len(data.get('invited', []))
        ref_orders = data.get('orders', 0)

        if invited_count > 0 or ref_orders > 0:
            # Найдем имя пользователя из заказов
            username = "Неизвестен"
            for status in ['active', 'accepted', 'completed', 'cancelled']:
                for order in orders.get(status, []):
                    if str(order['user_id']) == user_id:
                        username = order.get('username', 'Неизвестен')
                        break
                if username != "Неизвестен":
                    break

            active_referrers.append({
                'user_id': user_id,
                'username': username,
                'invited_count': invited_count,
                'ref_orders': ref_orders,
                'gifts_earned': ref_orders // 10,
                'raffle_number': data.get('raffle_number', 'Не назначен'),
                'invited_by': data.get('invited_by')
            })

    # Сортируем по количеству заказов рефералов
    active_referrers.sort(key=lambda x: x['ref_orders'], reverse=True)

    for i, ref in enumerate(active_referrers[:15], 1):  # Показываем топ-15
        text += f"{i}. @{ref['username']} (ID: {ref['user_id']})\n"
        text += f"   👥 Приглашений: {ref['invited_count']}\n"
        text += f"   📦 Реф.заказов: {ref['ref_orders']}/10\n"
        text += f"   🎁 Подарков: {ref['gifts_earned']}\n"
        text += f"   🎲 Номер розыгрыша: {ref['raffle_number']}\n"

        if ref['invited_by']:
            # Найдем имя пригласившего
            inviter_username = "Неизвестен"
            for status in ['active', 'accepted', 'completed', 'cancelled']:
                for order in orders.get(status, []):
                    if str(order['user_id']) == ref['invited_by']:
                        inviter_username = order.get('username', 'Неизвестен')
                        break
                if inviter_username != "Неизвестен":
                    break
            text += f"   👤 Приглашен: @{inviter_username}\n"

        text += f"───────────────\n"

    if len(active_referrers) > 15:
        text += f"\n... и еще {len(active_referrers) - 15} рефереров"

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def conduct_raffle(query, context=None):
    """Провести розыгрыш"""
    referral_system = get_referral_system()
    if not referral_system:
        text = "🎲 Нет участников для розыгрыша"
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Выбираем случайного победителя
    participants = list(referral_system.keys())
    winner_id = random.choice(participants)
    winner_data = referral_system[winner_id]

    # Отправляем уведомление победителю
    try:
        winner_notification = f"""🎉 Поздравляем! Вы выиграли в розыгрыше!

🏆 Ваш выигрышный номер: {winner_data.get('raffle_number', 'Не назначен')}
🎁 Приз: VX Coffee 1 упаковка бесплатно!

Для получения приза свяжитесь с {ADMIN_CONTACT}"""

        # Отправляем сообщение победителю
        if context:
            await context.bot.send_message(chat_id=int(winner_id), text=winner_notification)
    except Exception as e:
        print(f"Ошибка отправки уведомления победителю: {e}")

    text = f"""🎉 Розыгрыш проведен!

🏆 Победитель: ID {winner_id}
🎲 Номер для розыгрыша: {winner_data.get('raffle_number', 'Не назначен')}
👥 Приглашений: {len(winner_data.get('invited', []))}
📦 Заказов: {winner_data.get('orders', 0)}

Всего участников: {len(participants)}

✅ Уведомление отправлено победителю!
"""

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_orders(query, status, admin_id=None):
    """Показать заказы с определенным статусом"""
    orders = get_orders()
    lang = 'ru'  # Временно используем русский

    if status not in orders:
        orders[status] = []

    status_orders = orders[status]

    # Для принятых заказов показываем все заказы, но с разными правами доступа
    display_orders = status_orders

    if not display_orders:
        status_names = {
            'active': 'активных',
            'accepted': 'принятых', 
            'completed': 'выполненных',
            'cancelled': 'отмененных'
        }
        text = f"Нет {status_names.get(status, status)} заказов"
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    status_names = {
        'active': 'Активные',
        'accepted': 'Принятые',
        'completed': 'Выполненные', 
        'cancelled': 'Отмененные'
    }
    text = f"{status_names.get(status, status.capitalize())} заказы:\n\n"
    keyboard = []

    for order in display_orders:
        admin_info = ""
        if order.get('assigned_admin'):
            admin_info = f"👨‍💼 Админ: @{order.get('admin_username', 'Неизвестен')}\n"

        # Выделяем заказы-подарки
        if order.get('is_gift', False):
            if status == 'accepted':
                text += f"🎁 ПОДАРОК #{order['id']}\n👤 Пользователь: @{order['username']}\n🎁 Подарок: {order['product']}\n💰 Цена: {order['price']}\n{admin_info}📅 Дата: {order['date']}\n🔄 ПРИНЯТ - ОЖИДАЕТ ВЫПОЛНЕНИЯ\n───────────────\n"
            else:
                text += f"🎁 ПОДАРОК #{order['id']}\n👤 Пользователь: @{order['username']}\n🎁 Подарок: {order['product']}\n💰 Цена: {order['price']}\n{admin_info}📅 Дата: {order['date']}\n───────────────\n"
        else:
            if status == 'accepted':
                text += f"🔄 Заказ #{order['id']}\n👤 Пользователь: @{order['username']}\n📦 Товар: {order['product']}\n💰 Цена: {order['price']}\n🚚 Доставка: {order['delivery']}\n📍 Район: {order['district']}\n{admin_info}📅 Дата: {order['date']}\n🔄 ПРИНЯТ - ОЖИДАЕТ ОПЛАТЫ\n───────────────\n"
            else:
                text += f"🔸 Заказ #{order['id']}\n👤 Пользователь: @{order['username']}\n📦 Товар: {order['product']}\n💰 Цена: {order['price']}\n🚚 Доставка: {order['delivery']}\n📍 Район: {order['district']}\n{admin_info}📅 Дата: {order['date']}\n───────────────\n"

        if status == 'active':
            if order.get('is_gift', False):
                keyboard.append([
                    InlineKeyboardButton(f"✅ Принять #{order['id']}", callback_data=f"confirm_{order['id']}"),
                    InlineKeyboardButton(f"❌ Отклонить #{order['id']}", callback_data=f"cancel_{order['id']}")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(f"✅ Принять #{order['id']}", callback_data=f"confirm_{order['id']}"),
                    InlineKeyboardButton(f"❌ Отклонить #{order['id']}", callback_data=f"cancel_{order['id']}")
                ])
        elif status == 'accepted':
            # Показываем кнопки только для заказов, закрепленных за текущим админом
            if order.get('assigned_admin') == admin_id:
                if order.get('is_gift', False):
                    keyboard.append([
                        InlineKeyboardButton(f"🎉 Выполнен #{order['id']}", callback_data=f"paid_{order['id']}"),
                        InlineKeyboardButton(f"❌ Отменить #{order['id']}", callback_data=f"cancel_{order['id']}")
                    ])
                else:
                    keyboard.append([
                        InlineKeyboardButton(f"💰 Оплачено #{order['id']}", callback_data=f"paid_{order['id']}"),
                        InlineKeyboardButton(f"❌ Не оплачено #{order['id']}", callback_data=f"cancel_{order['id']}")
                    ])
            else:
                # Если заказ принят другим админом, показываем неактивную кнопку
                keyboard.append([
                    InlineKeyboardButton(f"🔒 В работе у @{order.get('admin_username', 'другого админа')}", callback_data="noop")
                ])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def error_handler(update: Update, context: CallbackContext):
    print(f'Update {update} caused error {context.error}')

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        print("❌ Ошибка: Токен бота не найден!")
        print("1. Убедитесь, что вы добавили BOT_TOKEN в Secrets")
        print("2. Проверьте правильность написания переменной")
        print("3. Перезапустите бот")
        return

    if not ADMIN_IDS:
        print("❌ Ошибка: ID администраторов не найдены!")
        print("1. Убедитесь, что вы добавили ADMIN_IDS в Secrets")
        print("2. Формат: ID1,ID2,ID3 (через запятую без пробелов)")
        print("3. Перезапустите бот")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    # Запускаем keep_alive сервер для UptimeRobot
    keep_alive()

    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    print("🌐 Keep-alive сервер запущен на порту 5000")
    app.run_polling()

if __name__ == '__main__':
    main()
