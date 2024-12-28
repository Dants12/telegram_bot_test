import os
import asyncio
import sqlite3
from delivery_dates import generate_delivery_dates
from delivery_dates import get_delivery_dates, get_delivery_times
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
#GROUP_ID = os.getenv('GROUP_ID')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# База данных
DB_PATH = "/home/Dants12/telegram_bot_test/bot_data.db"

#DELIVERY_DATES = ['2024-12-23', '2024-12-24', '2024-12-25', '2024-12-26', '2024-12-27', '2024-12-28', '2024-12-29', '2024-12-30', '2024-12-31']  # Пример данных для выбора даты
#DELIVERY_TIMES = ['08:00 - 10:00', '10:00 - 12:00', '12:00 - 14:00', '14:00 - 17:00', '17:00 - 21:00']  # Пример данных для выбора времени

MENU = {
    '1': {'name': 'Салат Оливье', 'price': 27, 'photo': '/home/Dants12/telegram_bot/img/oliv.jpg', 'ingridients': 'Картофель, морковь, маринованные огурцы, яйцо, горошек, колбаса, майонез, горчица, соль, перец'},
    '2': {'name': 'Салат Селедка под шубой', 'price': 25, 'photo': '/home/Dants12/telegram_bot/img/seld.jpg', 'ingridients': 'Сельдь, свекла, картофель, морковь, майонез, яйцо, лук'},
    '3': {'name': 'Салат Мимоза', 'price': 25, 'photo': '/home/Dants12/telegram_bot/img/mimosa.jpg', 'ingridients': 'Картофель, яйцо, морковь, сыр, лук, тунец'},
    '4': {'name': 'Салат Креветочный', 'price': 30, 'photo': '/home/Dants12/telegram_bot/img/crab.jpg', 'ingridients': 'Рис, свежий огурец, кукуруза, морковь, яйцо, креветка'},
}

# Инициализация базы данных
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER,
            item_id TEXT,
            quantity INTEGER,
            PRIMARY KEY (user_id, item_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def update_cart(user_id, item_id, quantity):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO carts (user_id, item_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?
    ''', (user_id, item_id, quantity, quantity))
    conn.commit()
    conn.close()

def get_cart(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT item_id, quantity FROM carts WHERE user_id = ?
    ''', (user_id,))
    cart = cursor.fetchall()
    conn.close()
    return cart

def update_quantity(user_id, item_id, change):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE carts SET quantity = quantity + ? WHERE user_id = ? AND item_id = ? AND quantity + ? > 0
    ''', (change, user_id, item_id, change))
    conn.commit()
    conn.close()

def clear_cart(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM carts WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

'''
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cart'] = []
    await update.message.reply_text(
        "Добро пожаловать в наш магазин готовой еды! 🚀",
        reply_markup=main_menu_keyboard()
    )
'''
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем корзину
    context.user_data['cart'] = []

    # Сохраняем ID пользователя и имя в файл
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    first_name = update.effective_user.first_name or "Unknown"

    with open("user_ids.txt", "a") as file:
        file.write(f"{user_id},{username},{first_name}\n")

    # Отправляем приветственное сообщение
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_text(
        "Добро пожаловать в наш магазин готовой еды! 🚀",
        reply_markup=main_menu_keyboard()
    )

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton('Дата и время доставки')],
            [KeyboardButton('📋 Меню'), KeyboardButton('🛒 Корзина')],
            [KeyboardButton('🚀 Оформить заказ'), KeyboardButton('💬 Отзывы')],
        ],
        resize_keyboard=True
    )

'''
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for key, item in MENU.items():
        with open(item['photo'], 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=f"{item['name']}\nЦена: {item['price']} EUR\nСостав: {item['ingridients']}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"Добавить {item['name']}", callback_data=f"add_{key}")
                ]])
            )
'''

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем информацию о пользователе в файл
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    first_name = update.effective_user.first_name or "Unknown"

    with open("user_activity_log.txt", "a") as file:
        file.write(f"{user_id},{username},{first_name},нажал 'Меню'\n")

    # Отправляем пользователю меню
    for key, item in MENU.items():
        with open(item['photo'], 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"{item['name']}\nЦена: {item['price']} EUR\nСостав: {item['ingridients']}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(f"Добавить {item['name']}", callback_data=f"add_{key}"),
                        InlineKeyboardButton("-", callback_data=f"decrease_{key}"),
                        InlineKeyboardButton("+", callback_data=f"increase_{key}")
                    ]
                ])
            )

'''
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = query.data.split('_')[1]
    item = MENU[item_id]

    if 'cart' not in context.user_data or not isinstance(context.user_data['cart'], dict):
        context.user_data['cart'] = {}

    if item_id in context.user_data['cart']:
        context.user_data['cart'][item_id]['quantity'] += 1
    else:
        context.user_data['cart'][item_id] = {'name': item['name'], 'price': item['price'], 'quantity': 1}

    await query.edit_message_caption(
        f"{item['name']} добавлено в корзину 🛒\nКоличество: {context.user_data['cart'][item_id]['quantity']}"
    )
'''

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = query.data.split('_')[1]
    add_item_to_cart(query.from_user.id, item_id, 1)

    await query.edit_message_caption(f"Товар добавлен в корзину 🛒")#(f"{item['name']} добавлено в корзину 🛒\nКоличество: {context.user_data['cart'][item_id]['quantity']}")

'''
#рабочая функция выбора дат
async def choose_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:  # Теперь мы обрабатываем сообщение, а не callback
        # Генерация клавиатуры для выбора даты
      #  keyboard = [
         #   [InlineKeyboardButton(date, callback_data=f"date_{date}") for date in DELIVERY_DATES]
      #  ]

         keyboard = [
             [InlineKeyboardButton(DELIVERY_DATES[i], callback_data=f"date_{DELIVERY_DATES[i]}"),
              InlineKeyboardButton(DELIVERY_DATES[i+1], callback_data=f"date_{DELIVERY_DATES[i+1]}"),
              InlineKeyboardButton(DELIVERY_DATES[i+2], callback_data=f"date_{DELIVERY_DATES[i+2]}")]
             for i in range(0, len(DELIVERY_DATES), 3)
         ]

        # Отправляем сообщение с кнопками для выбора даты
         await update.message.reply_text(
            "Выберите дату доставки:",
            reply_markup=InlineKeyboardMarkup(keyboard)
         )
'''

async def generate_delivery_dates():
    today = datetime.utcnow()
    return [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

# Выбор даты доставки
async def choose_delivery_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:  # Если это текстовое сообщение
        delivery_dates = generate_delivery_dates()
        keyboard = [[InlineKeyboardButton(date, callback_data=f"date_{date}")] for date in delivery_dates]

        await update.message.reply_text(
            "Выберите дату доставки:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.callback_query:  # Если это нажатие на кнопку
        query = update.callback_query
        await query.answer()

        selected_date = query.data.split('_')[1]
        context.user_data['delivery_date'] = selected_date

        # После выбора даты предлагаем выбрать время
        times = ["10:00 - 12:00", "12:00 - 14:00", "14:00 - 16:00", "16:00 - 18:00"]
        time_keyboard = [[InlineKeyboardButton(time, callback_data=f"time_{time}")] for time in times]

        await query.edit_message_text(
            f"Вы выбрали дату: {selected_date}\nТеперь выберите время доставки:",
            reply_markup=InlineKeyboardMarkup(time_keyboard)
        )

# Выбор времени доставки
'''async def choose_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_time = query.data.split('_')[1]
    context.user_data['delivery_time'] = selected_time

    # Подтверждение выбора
    selected_date = context.user_data.get('delivery_date', 'Не выбрана')
    await query.edit_message_text(
        f"Вы выбрали доставку на {selected_date} в {selected_time}.\nПожалуйста, введите адрес доставки."
    )
    context.user_data['awaiting_address'] = True
'''
async def choose_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # Проверка, что query существует
    if query is None:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
        return

    await query.answer()

    selected_date = query.data.split('_')[1]
    context.user_data['delivery_date'] = selected_date

    delivery_times = ["10:00 - 12:00", "12:00 - 14:00", "14:00 - 16:00", "16:00 - 18:00"]
    keyboard = [
        [InlineKeyboardButton(time, callback_data=f"time_{time}")] for time in delivery_times
    ]
    await query.edit_message_text(
        f"Вы выбрали дату: {selected_date}\nТеперь выберите время доставки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# Сохранение адреса доставки
async def save_delivery_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_address'):
        delivery_address = update.message.text
        context.user_data['delivery_address'] = delivery_address
        context.user_data['awaiting_address'] = False

        selected_date = context.user_data.get('delivery_date', 'Не выбрана')
        selected_time = context.user_data.get('delivery_time', 'Не выбрано')

        # Подтверждение выбора
        await update.message.reply_text(
            f"Спасибо! Вы выбрали доставку на {selected_date} в {selected_time}.\n"
            f"Адрес доставки: {delivery_address}."
        )

'''b
async def choose_delivery_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Позволяет выбрать дату доставки из динамически сформированного списка.
    """
    delivery_dates = get_delivery_dates()
    keyboard = [
        [InlineKeyboardButton(date, callback_data=f"date_{date}")]
        for date in delivery_dates
    ]
    await update.message.reply_text(
        "Выберите дату доставки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

''''''
async def choose_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Позволяет выбрать время доставки после выбора даты.
    """
    query = update.callback_query
    if query is None:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
        return
'''
'''
async def choose_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    query = update.callback_query
    if query is None:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
        return
    await query.answer()
'''
'''
    # Извлекаем дату из callback_data
    try:
        selected_date = query.data.split('_')[1]
    except IndexError:
        await query.edit_message_text("Некорректные данные. Пожалуйста, выберите дату снова.")
        return

    context.user_data['delivery_date'] = selected_date

    delivery_times = get_delivery_times()
    keyboard = [
        [InlineKeyboardButton(time, callback_data=f"time_{time}")]
        for time in delivery_times
    ]
    await query.edit_message_text(
        f"Вы выбрали дату: {selected_date}\nТеперь выберите время доставки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
''''''
async def choose_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если это текстовое сообщение
    if update.message:
        await update.message.reply_text(
            "Выберите дату доставки:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("10:00 - 12:00", callback_data="time_10:00 - 12:00")],
                [InlineKeyboardButton("12:00 - 14:00", callback_data="time_12:00 - 14:00")],
                [InlineKeyboardButton("14:00 - 16:00", callback_data="time_14:00 - 16:00")],
                [InlineKeyboardButton("16:00 - 18:00", callback_data="time_16:00 - 18:00")]
            ])
        )
    # Если это нажатие кнопки
    elif update.callback_query:
        query = update.callback_query
        await query.answer()

        selected_time = query.data.split('_')[1]
        context.user_data['delivery_time'] = selected_time

        await query.edit_message_text(
            f"Вы выбрали время доставки: {selected_time}. Пожалуйста, введите адрес."
        )
        context.user_data['awaiting_address'] = True
    else:
        # Если ни то, ни другое
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")


async def request_delivery_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:  # Проверяем, что это callback_query
        query = update.callback_query
        await query.answer()

        selected_date = query.data.split('_')[1]
        context.user_data['delivery_date'] = selected_date

        # Теперь отправляем пользователю время
        keyboard = [
            [InlineKeyboardButton(time, callback_data=f"time_{time}") for time in DELIVERY_TIMES]
        ]

        await query.edit_message_text(
            f"Вы выбрали дату: {selected_date}\nТеперь выберите время доставки:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def save_delivery_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:  # Проверяем, что это callback_query
        query = update.callback_query
        await query.answer()

        selected_time = query.data.split('_')[1]
        context.user_data['delivery_time'] = selected_time

        # Подтверждение выбора
        await query.edit_message_text(
            f"Вы выбрали время доставки: {context.user_data['delivery_time']}\n"
            "Теперь введите ваш адрес для доставки."
        )

        context.user_data['awaiting_address'] = True  # Устанавливаем флаг для ожидания адреса

    else:
        await update.message.reply_text("Ошибка: это не callback запрос.")

async def save_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_address'):
        delivery_address = update.message.text
        context.user_data['delivery_address'] = delivery_address
        context.user_data['awaiting_address'] = False

        await update.message.reply_text(
            f"Ваш адрес: {delivery_address}. Теперь выберите состав заказа",
            reply_markup=main_menu_keyboard()
        )
# Отправка заказа в группу
#    await context.bot.send_message(
#        chat_id=GROUP_ID,  # Отправка в группу
 #       text=f"🔔 Новый заказ от пользователя @{update.effective_user.username}:\n{order_summary}"
 #   )
m'''

'''
async def handle_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "paypal_payment":
        await query.edit_message_text(
            "💳 Вы выбрали оплату через PayPal.\n"
            "👉 [Перейти к оплате через PayPal](https://paypal.com)\\.\n"  # Экранируем точку после URL
            "После оплаты отправьте подтверждение командой /confirm_payment.",
            parse_mode="MarkdownV2"  # Используем MarkdownV2 для правильной обработки
        )
    elif query.data == "bank_transfer":
        await query.edit_message_text(
            "🏦 Реквизиты для перевода:\n\n"
            "💳 Номер карты: **1234 5678 9012 3456**\n"
            "Получатель: Karina Usane\n\n"
            "После оплаты отправьте подтверждение командой /confirm_payment.",
            parse_mode="MarkdownV2"  # Используем MarkdownV2 для правильной обработки
        )
'''
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Спасибо за подтверждение оплаты! Мы свяжемся с вами для уточнения деталей.")
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🔔 Пользователь @{update.effective_user.username} подтвердил оплату. Проверьте поступление средств."
    )

async def modify_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action = data[0]
    item_id = data[1]

    if action == "add":
        update_cart(query.from_user.id, item_id, 1)
    elif action == "increase":
        update_quantity(query.from_user.id, item_id, 1)
    elif action == "decrease":
        update_quantity(query.from_user.id, item_id, -1)

    # Получаем обновленное количество товара
    cart = get_cart(query.from_user.id)
    quantity = next((q for i, q in cart if i == item_id), 0)
    item = MENU[item_id]

    # Обновляем сообщение с актуальными данными
    await query.edit_message_caption(
        caption=f"{item['name']}\nЦена: {item['price']} EUR\nКоличество: {quantity}\nСостав: {item['ingridients']}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("-", callback_data=f"decrease_{item_id}"),
                InlineKeyboardButton(f"{quantity}", callback_data="noop"),
                InlineKeyboardButton("+", callback_data=f"increase_{item_id}")
            ]
        ])
    )

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = get_cart(update.effective_user.id)
    if not cart:
        await update.message.reply_text("Ваша корзина пуста.")
        return

    cart_text = "Ваша корзина:\n"
    total_price = 0
    for item_id, quantity in cart:
        item = MENU[item_id]
        cart_text += f"- {item['name']} x{quantity} — {item['price'] * quantity} EUR\n"
        total_price += item['price'] * quantity

    cart_text += f"\nИтого: {total_price} EUR"
    await update.message.reply_text(cart_text)

'''
async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get('cart', {})
    if not cart:
        await update.message.reply_text("Ваша корзина пуста 🛒")
        return

    total_sum = 0
    cart_text = "🛒 Ваша корзина:\n"
    for item_id, details in cart.items():
        subtotal = details['price'] * details['quantity']
        total_sum += subtotal
        cart_text += f"- {details['name']} (x{details['quantity']}) - {subtotal} EUR\n"

    cart_text += f"\n💰 Общая сумма: {total_sum} EUR"
    await update.message.reply_text(cart_text)
'''

async def clear_cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_cart(update.effective_user.id)
    await update.message.reply_text("Корзина очищена.")

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = get_cart(update.effective_user.id)
    if not cart:
        await update.message.reply_text("Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return

    cart_text = "🛒 Ваш заказ:\n"
    total_price = 0
    for item_id, quantity in cart:
        item = MENU[item_id]
        cart_text += f"- {item['name']} x{quantity} — {item['price'] * quantity} EUR\n"

        total_price += item['price'] * quantity

    cart_text += f"\nИтого: {total_price} EUR\n"
    cart_text += f"Дата доставки: {context.user_data.get('delivery_date')}\n"
    cart_text += f"Время доставки: {context.user_data.get('delivery_time')}\n"
    cart_text += f"Адрес доставки: {context.user_data.get('delivery_address')}\n"

    await update.message.reply_text(f"{cart_text}\nСпасибо за ваш заказ! 🚀")

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Новый заказ от @{update.effective_user.username or 'Клиент'}:\n{cart_text}"
    )

    clear_cart(update.effective_user.id)

'''
async def process_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get('cart', {})
    if not cart:
        await update.message.reply_text("Ваша корзина пуста 🛒. Добавьте товары перед оформлением заказа.")
        return

    total_sum = sum(details['price'] * details['quantity'] for details in cart.values())

    order_summary = "🛒 Ваш заказ:\n"
    for item_id, details in cart.items():
        order_summary += f"{details['name']} (x{details['quantity']}) - {details['price']} EUR\n"

    order_summary += f"\n💰 Общая сумма: {total_sum} EUR\n"
    order_summary += f"Дата доставки: {context.user_data.get('delivery_date')}\n"
    order_summary += f"Время доставки: {context.user_data.get('delivery_time')}\n"
    order_summary += f"Адрес доставки: {context.user_data.get('delivery_address')}\n"

    # Отправка заказа в группу
    await context.bot.send_message(
        chat_id=GROUP_ID,  # Отправка в группу
        text=f"🔔 Новый заказ от пользователя @{update.effective_user.username}:\n{order_summary}"
    )

    # Отправляем подтверждение пользователю
    await update.message.reply_text(
        "✅ Заказ успешно оформлен! Мы свяжемся с вами для подтверждения.\nСпасибо за покупку! 😊"
    )

    # Очищаем корзину после оформления заказа
    context.user_data['cart'] = {}
'''
def main():
    initialize_database()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('📋 Меню'), menu))
    app.add_handler(MessageHandler(filters.Regex('🛒 Корзина'), view_cart))
    #app.add_handler(MessageHandler(filters.Regex('🚀 Оформить заказ'), process_order))
    app.add_handler(MessageHandler(filters.Regex('🚀 Оформить заказ'), checkout))
    app.add_handler(MessageHandler(filters.Regex('Очистить корзину'), clear_cart_command))
    app.add_handler(CallbackQueryHandler(modify_cart, pattern="^(add|increase|decrease)_"))
    app.add_handler(MessageHandler(filters.Regex('Дата и время доставки'), choose_delivery_time))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(choose_delivery_time, pattern=r"^date_"))
    #app.add_handler(CallbackQueryHandler(choose_delivery_time, pattern=r"^date_"))
    #app.add_handler(CallbackQueryHandler(request_delivery_address, pattern="^date_"))
    app.add_handler(MessageHandler(filters.Regex('Дата и время доставки'), choose_delivery_time))
    app.add_handler(MessageHandler(filters.Regex('Дата и время доставки'), choose_delivery_date))
    app.add_handler(CallbackQueryHandler(choose_delivery_date, pattern="^date_"))
    app.add_handler(CallbackQueryHandler(choose_delivery_time, pattern="^time_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_delivery_address))
    app.add_handler(CallbackQueryHandler(choose_delivery_time, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(save_delivery_address, pattern="^time_"))
    #app.add_handler(CallbackQueryHandler(handle_payment_selection, pattern="^(paypal_payment|bank_transfer)$"))
    #app.add_handler(CommandHandler("confirm_payment", confirm_payment))
    #app.add_handler(MessageHandler(filters.TEXT, save_address))  # Обработчик ввода адреса

    app.run_polling()

if __name__ == '__main__':
    main()
