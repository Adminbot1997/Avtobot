import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Token va sozlamalar
TOKEN = '7726541153:AAHJfZOwetxIRoJ5UvNjOmZwEHNYbktX0xM'  # <-- bu yerga o'zingizning bot tokeningizni yozing
GROUP_ID = -1001234567890       # <-- bu yerga e'lon yuboriladigan guruh ID sini yozing
ADMIN_USERNAME = 'elon_admin'   # <-- bu yerga admin username yozing

bot = telebot.TeleBot(TOKEN)

# Holatlar va ma'lumotlar
user_states = {}
ad_data = {}
user_history = {}

# Maydonlar
fields = [
    "Mashina modeli", "Pozitsiya", "Kiraska", "Rangi", "Yili",
    "Probegi", "Yoqilg'i", "Holati", "Narxi",
    "Manzil", "Aloqa", "Qo‘shimcha"
]

# Tugmalar
skip_btn = "O‘tkazib yuborish"
back_btn = "Orqaga"
cancel_btn = "Bekor qilish"
menu_btn = "Asosiy menyuga qaytish"

# Asosiy menyu
def main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("E’lon yuborish"),
        KeyboardButton("E’lonni tahrirlash"),
        KeyboardButton("E’lonlar tarixi"),
        KeyboardButton("E’lonni izlash"),
        KeyboardButton("Admin bilan bog‘lanish")
    )
    bot.send_message(chat_id, "Asosiy menyu", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "Admin bilan bog‘lanish")
def contact_admin(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Admin", url=f"https://t.me/{ADMIN_USERNAME}"))
    bot.send_message(message.chat.id, "Admin bilan bog‘lanish uchun tugmani bosing:", reply_markup=markup)

# E’lon boshlash
@bot.message_handler(func=lambda m: m.text == "E’lon yuborish")
def start_ad(message):
    user_id = message.from_user.id
    user_states[user_id] = 0
    ad_data[user_id] = {"photos": []}
    ask_field(message.chat.id, user_id)

def get_next_field(user_id):
    current = user_states[user_id]
    for idx in range(current, len(fields)):
        if fields[idx] not in ad_data[user_id]:
            return idx
    return None

def ask_field(chat_id, user_id):
    idx = get_next_field(user_id)
    if idx is not None:
        user_states[user_id] = idx
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(skip_btn, back_btn)
        markup.add(cancel_btn, menu_btn)
        bot.send_message(chat_id, f"{fields[idx]} ni kiriting:", reply_markup=markup)
    else:
        preview_and_confirm(chat_id, user_id)

# E’lonni ko‘rsatish va yuborish
def preview_and_confirm(chat_id, user_id):
    text = "\n".join(f"{k}: {v}" for k, v in ad_data[user_id].items() if k != "photos")
    media = ad_data[user_id]["photos"]
    if media:
        bot.send_photo(chat_id, media[0], caption=text)
        bot.send_photo(GROUP_ID, media[0], caption=text)
    else:
        bot.send_message(chat_id, text)
        bot.send_message(GROUP_ID, text)

    user_history.setdefault(user_id, []).append({"text": text, "photo": media[0] if media else None})
    bot.send_message(chat_id, "✅ E'loningiz guruhga yuborildi.")
    user_states.pop(user_id, None)
    ad_data.pop(user_id, None)
    main_menu(chat_id)

# Rasm qabul qilish
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in ad_data:
        ad_data[user_id]["photos"].append(message.photo[-1].file_id)
        bot.send_message(message.chat.id, "📸 Rasm saqlandi.")
    else:
        bot.send_message(message.chat.id, "Avval 'E’lon yuborish' tugmasini bosing.")

# Matnli xabarlar
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text == "E’lonni tahrirlash":
        if user_id in user_history and user_history[user_id]:
            last = user_history[user_id][-1]
            if last["photo"]:
                bot.send_photo(message.chat.id, last["photo"], caption=last["text"])
            else:
                bot.send_message(message.chat.id, last["text"])
            bot.send_message(message.chat.id, "Yangi e’lon yuborish uchun 'E’lon yuborish' ni bosing.")
        else:
            bot.send_message(message.chat.id, "Sizda hali e’lon yo‘q.")
        return

    if text == "E’lonlar tarixi":
        if user_id in user_history and user_history[user_id]:
            for ad in user_history[user_id][-3:]:
                if ad["photo"]:
                    bot.send_photo(message.chat.id, ad["photo"], caption=ad["text"])
                else:
                    bot.send_message(message.chat.id, ad["text"])
        else:
            bot.send_message(message.chat.id, "E’lonlar yo‘q.")
        return

    if text == "E’lonni izlash":
        bot.send_message(message.chat.id, "Izlash uchun kalit so‘z yuboring.")
        user_states[user_id] = "search"
        return

    if user_states.get(user_id) == "search":
        results = []
        keyword = text.lower()
        for ad in user_history.get(user_id, []):
            if keyword in ad["text"].lower():
                results.append(ad)
        if results:
            for ad in results:
                if ad["photo"]:
                    bot.send_photo(message.chat.id, ad["photo"], caption=ad["text"])
                else:
                    bot.send_message(message.chat.id, ad["text"])
        else:
            bot.send_message(message.chat.id, "Mos e’lon topilmadi.")
        user_states.pop(user_id, None)
        return

    if user_id not in user_states:
        return

    if text == cancel_btn or text == menu_btn:
        user_states.pop(user_id, None)
        ad_data.pop(user_id, None)
        bot.send_message(message.chat.id, "Bekor qilindi." if text == cancel_btn else "Asosiy menyuga qaytdingiz.")
        main_menu(message.chat.id)
        return

    if text == back_btn:
        current = user_states[user_id]
        if isinstance(current, int) and current > 0:
            user_states[user_id] = current - 1
        ask_field(message.chat.id, user_id)
        return

    if isinstance(user_states[user_id], int):
        field = fields[user_states[user_id]]
        if text != skip_btn:
            ad_data[user_id][field] = text
        ask_field(message.chat.id, user_id)

# Botni ishga tushirish
print("✅ Bot ishga tushdi...")
bot.polling(none_stop=True)

