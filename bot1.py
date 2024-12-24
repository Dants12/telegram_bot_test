import os
import asyncio
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
GROUP_ID = os.getenv('GROUP_ID')

DELIVERY_DATES = ['2024-12-23', '2024-12-24', '2024-12-25', '2024-12-26', '2024-12-27', '2024-12-28', '2024-12-29', '2024-12-30', '2024-12-31']  # Пример данных для выбора даты
DELIVERY_TIMES = ['08:00 - 10:00', '10:00 - 12:00', '12:00 - 14:00', '14:00 - 17:00', '17:00 - 21:00']  # Пример данных для выбора времени

MENU = {
    '1': {'name': 'Салат Оливье', 'price': 27, 'photo': '/home/Dants12/telegram_bot/img/oliv.jpg', 'ingridients': 'Картофель, морковь, маринованные огурцы, яйцо, горошек, колбаса, майонез, горчица, соль, перец'},
    '2': {'name': 'Салат Селедка под шубой', 'price': 25, 'photo': '/home/Dants12/telegram_bot/img/seld.jpg', 'ingridients': 'Сельдь, свекла, картофель, морковь, майонез, яйцо, лук'},
    '3': {'name': 'Салат Мимоза', 'price': 25, 'photo': '/home/Dants12/telegram_bot/img/mimosa.jpg', 'ingridients': 'Картофель, яйцо, морковь, сыр, лук, тунец'},
    '4': {'name': 'Салат Креветочный', 'price': 30, 'photo': '/home/Dants12/telegram_bot/img/crab.jpg', 'ingridients': 'Рис, свежий огурец, кукуруза, морковь, яйцо, креветка'},
}

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
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=f"{item['name']}\nЦена: {item['price']} EUR\nСостав: {item['ingridients']}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"Добавить {item['name']}", callback_data=f"add_{key}")
                ]])
            )

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

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('📋 Меню'), menu))
    app.add_handler(MessageHandler(filters.Regex('🛒 Корзина'), view_cart))
    app.add_handler(MessageHandler(filters.Regex('🚀 Оформить заказ'), process_order))
    app.add_handler(MessageHandler(filters.Regex('Дата и время доставки'), choose_delivery_time))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(request_delivery_address, pattern="^date_"))
    app.add_handler(CallbackQueryHandler(save_delivery_address, pattern="^time_"))
#    app.add_handler(CallbackQueryHandler(handle_payment_selection, pattern="^(paypal_payment|bank_transfer)$"))
#    app.add_handler(CommandHandler("confirm_payment", confirm_payment))
    app.add_handler(MessageHandler(filters.TEXT, save_address))  # Обработчик ввода адреса

    app.run_polling()

if __name__ == '__main__':
    main()
