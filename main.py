import telebot
from telebot import types
import datetime
import re

BOT_TOKEN = "..."
bot = telebot.TeleBot(BOT_TOKEN)

ORDERS_FILE = "orders.txt"

MENU = {
    "Lavash": 30000,
    "Burger": 25000,
    "Cola": 7000,
    "Pizza": 40000
}

carts = {}
user_steps = {}

# === YORDAMCHI FUNKSIYALAR ===
def is_valid_phone(phone):
    pattern = r'^\+998(93|94|50|51|88|95|97|98|99|33)\d{7}$'
    return re.match(pattern, phone)

def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📜 Menyu", "🛒 Savatcha")
    markup.row("📦 Buyurtma berish", "🎁 Aksiya")
    markup.row("📍 Manzil")
    return markup

def create_menu_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in MENU:
        markup.add(f"➕ {item}")
    markup.add("🔙 Ortga")
    return markup

def create_payment_links():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Payme", url="https://payme.uz"))
    markup.add(types.InlineKeyboardButton("💳 Click", url="https://click.uz"))
    return markup

# === BOSHLANG‘ICH BUYRUQLAR ===
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "Assalomu alaykum! Kafemizga xush kelibsiz.", reply_markup=create_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "📜 Menyu")
def handle_menu(message):
    text = "📋 Bizning menyu:\n" + "\n".join([f"{k} - {v} so'm" for k, v in MENU.items()])
    bot.send_message(message.chat.id, text, reply_markup=create_menu_buttons())

@bot.message_handler(func=lambda msg: msg.text == "🔙 Ortga")
def handle_back(message):
    bot.send_message(message.chat.id, "🔙 Asosiy menyuga qaytdingiz.", reply_markup=create_main_menu())

@bot.message_handler(func=lambda msg: msg.text.startswith("➕"))
def handle_add_item(message):
    item = message.text.replace("➕ ", "")
    if item in MENU:
        carts.setdefault(message.from_user.id, []).append(item)
        bot.send_message(message.chat.id, f"✅ {item} savatchaga qo‘shildi.")
    else:
        bot.send_message(message.chat.id, "❌ Bu mahsulot mavjud emas.")

@bot.message_handler(func=lambda msg: msg.text == "🛒 Savatcha")
def handle_cart(message):
    items = carts.get(message.from_user.id, [])
    if not items:
        bot.send_message(message.chat.id, "🛒 Savatchangiz bo‘sh.")
        return

    total = sum(MENU[item] for item in items)
    item_lines = "\n".join([f"- {item} ({MENU[item]} so'm)" for item in items])
    bot.send_message(message.chat.id, f"🛒 Savatchangiz:\n{item_lines}\n\nJami: {total} so‘m", reply_markup=create_payment_links())

@bot.message_handler(func=lambda msg: msg.text == "📦 Buyurtma berish")
def handle_order(message):
    user_steps[message.chat.id] = {"step": "name"}
    bot.send_message(message.chat.id, "Ismingizni kiriting:")

@bot.message_handler(func=lambda msg: user_steps.get(msg.chat.id, {}).get("step") == "name")
def handle_name(message):
    user_steps[message.chat.id]["name"] = message.text
    user_steps[message.chat.id]["step"] = "phone"
    bot.send_message(message.chat.id, "📱 Telefon raqamingizni kiriting (+998 bilan):")

@bot.message_handler(func=lambda msg: user_steps.get(msg.chat.id, {}).get("step") == "phone")
def handle_phone(message):
    if not is_valid_phone(message.text):
        bot.send_message(message.chat.id, "⚠️ Noto‘g‘ri format. Iltimos, +998 bilan yozing.")
        return
    user_steps[message.chat.id]["phone"] = message.text
    user_steps[message.chat.id]["step"] = "address"
    bot.send_message(message.chat.id, "📍 Manzilingizni kiriting:")

@bot.message_handler(func=lambda msg: user_steps.get(msg.chat.id, {}).get("step") == "address")
def handle_address(message):
    user_steps[message.chat.id]["address"] = message.text
    user_steps[message.chat.id]["step"] = "confirm"
    bot.send_message(message.chat.id, "✅ Buyurtmani tasdiqlaysizmi? (Ha/Yoq)")
@bot.message_handler(func=lambda msg: user_steps.get(msg.chat.id, {}).get("step") == "confirm")
def handle_confirm(message):
    if message.text.lower() != "ha":
        bot.send_message(message.chat.id, "❌ Buyurtma bekor qilindi.", reply_markup=create_main_menu())
        user_steps.pop(message.chat.id, None)
        return

    data = user_steps[message.chat.id]
    items = carts.get(message.from_user.id, [])
    total = sum(MENU[i] for i in items)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    order = (
        f"🕒 {now}\n"
        f"👤 Ism: {data['name']}\n"
        f"📞 Tel: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n\n"
        f"🛒 Buyurtma:\n" + "\n".join(items) + f"\n\n💰 Jami: {total} so‘m\n---\n"
    )

    with open(ORDERS_FILE, "a", encoding="utf-8") as file:
        file.write(order)

    carts[message.from_user.id] = []
    user_steps.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "✅ Buyurtma muvaffaqiyatli qabul qilindi!", reply_markup=create_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "📍 Manzil")
def handle_location(message):
    bot.send_message(message.chat.id, "📍 Navoiy shahar, Mustaqillik ko‘chasi, 12-uy.")

@bot.message_handler(func=lambda msg: msg.text == "🎁 Aksiya")
def handle_promo(message):
    bot.send_message(message.chat.id, "🎉 Bugungi aksiya: Lavash + Cola = 35 000 so‘m!")

# === BOTNI ISHGA TUSHURISH ===
bot.polling()