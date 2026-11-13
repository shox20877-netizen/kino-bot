import telebot
import json
import os
import threading
from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# 1. BOT TOKENINGIZ
TOKEN = "8574631606:AAGIQIXSh8iW1VigMq3ZLnvg_pZlsWUimM0"
bot = telebot.TeleBot(TOKEN)

# 2. ADMIN ID RAQAMINGIZ
ADMIN_ID = 1302032021

# --- RENDER UCHUN WEB SERVER (Port ochish uchun) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Veb-serverni alohida oqimda ishga tushiramiz
threading.Thread(target=run_web).start()


# Fayl nomlari
CHANNELS_FILE = "channels.json"
DB_FILE = "kinolar.json"
USERS_FILE = "users.json"

def yuklash_fayl(file_path, default_val):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_val

def saqlash_fayl(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

KINOLAR = yuklash_fayl(DB_FILE, {})
FOYDALANUVCHILAR = yuklash_fayl(USERS_FILE, [])
DEFAULT_CHANNELS = [{"username": "@mahamadal1yev_sh", "name": "1-Kanal"}]
MAJBURIY_KANALLAR = yuklash_fayl(CHANNELS_FILE, DEFAULT_CHANNELS)

# Admin vaqtinchalik video saqlashi uchun lug'at
KUTISH_ZONASI = {}

def obunani_tekshir(user_id):
    for kanal in MAJBURIY_KANALLAR:
        try:
            holat = bot.get_chat_member(chat_id=kanal["username"], user_id=user_id).status
            if holat in ['left', 'kicked']:
                return False
        except:
            return False
    return True

# --- FAQAT ADMIN UCHUN DOIMIY PASTKI TUGMALAR ---
def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    kb.add(KeyboardButton("📊 Statistika"), KeyboardButton("📋 Kinolar ro'yxati"))
    kb.add(KeyboardButton("🗑 Kinoni o'chirish"), KeyboardButton("📢 Kanallar sozlamasi"))
    kb.add(KeyboardButton("📢 Rassilka (/send)"))
    return kb

# --- START BUYRUQI ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if user_id not in FOYDALANUVCHILAR:
        FOYDALANUVCHILAR.append(user_id)
        saqlash_fayl(USERS_FILE, FOYDALANUVCHILAR)

    if user_id != ADMIN_ID:
        if not obunani_tekshir(user_id):
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup()
            for kanal in MAJBURIY_KANALLAR:
                kb.add(InlineKeyboardButton(text=f"➕ {kanal['name']}ga obuna bo'lish", url=f"https://t.me/{kanal['username'].replace('@', '')}"))
            kb.add(InlineKeyboardButton(text="🔄 Tekshirish", callback_data="tekshirish"))
            bot.send_message(message.chat.id, "⚠️ Botdan foydalanish uchun kanalga obuna bo'ling:", reply_markup=kb)
            return
        
        bot.reply_to(message, "🎬 Assalomu alaykum! Kinoni ko'rish uchun uning **kodini** yuboring (masalan: `1`).", reply_markup=ReplyKeyboardRemove())
        return

    bot.send_message(message.chat.id, "👑 Xush kelibsiz, Admin! Boshqaruv paneli tayyor:", reply_markup=admin_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "tekshirish")
def callback_query(call):
    user_id = call.from_user.id
    if obunani_tekshir(user_id):
        bot.answer_callback_query(call.id, "Rahmat! Obuna tasdiqlandi ✅")
        bot.send_message(call.message.chat.id, "Endi kino kodini yuborishingiz mumkin.")
    else:
        bot.answer_callback_query(call.id, "Siz hali obuna bo'lmadingiz ❌", show_alert=True)

# --- ADMIN PANEL TUGMALARI VA AMALLARI ---
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def admin_actions(message):
    user_id = message.from_user.id
    text = message.text

    if user_id in KUTISH_ZONASI:
        if "|" not in text:
            bot.send_message(message.chat.id, "❌ Xato format! Quyidagicha yuboring:\n`Kod | Kino nomi`\nMisol: `1 | Avatar 2`", parse_mode="Markdown")
            return
        
        try:
            parts = text.split("|")
            kod = parts[0].strip()
            nomi = parts[1].strip()
            v_info = KUTISH_ZONASI[user_id]

            KINOLAR[kod] = {
                "file_id": v_info["file_id"],
                "nomi": nomi,
                "format": v_info["format"],
                "hajmi": v_info["hajmi"]
            }
            saqlash_fayl(DB_FILE, KINOLAR)
            del KUTISH_ZONASI[user_id]

            bot.send_message(message.chat.id, f"✅ Kino muvaffaqiyatli saqlandi!\n\n🆔 Kodi: `{kod}`\n🎬 Nomi: {nomi}\n📁 Formati: {v_info['format']}\n📦 Hajmi: {v_info['hajmi']}", parse_mode="Markdown")
            return
        except Exception as e:
            bot.send_message(message.chat.id, f"Xatolik yuz berdi: {e}")
            return

    if text == "📊 Statistika":
        jami_userlar = len(FOYDALANUVCHILAR)
        jami_kinolar = len(KINOLAR)
        bot.send_message(message.chat.id, f"📊 **Bot Statistikasi:**\n\n👥 Obunachilar soni: `{jami_userlar}` ta\n🎬 Bazadagi kinolar: `{jami_kinolar}` ta", parse_mode="Markdown")
        
    elif text == "📋 Kinolar ro'yxati":
        if not KINOLAR:
            bot.send_message(message.chat.id, "📭 Hozircha bazada kinolar yo'q.")
            return
        matn = "📋 **Bazadagi kinolar ro'yxati:**\n\n"
        for kod, kino in KINOLAR.items():
            matn += f"🆔 **{kod}** — {kino['nomi']} ({kino.get('hajmi', 'Nomaʼlum')})\n"
        if len(matn) > 4000:
            bot.send_message(message.chat.id, "Kinolar soni juda ko'p, ro'yxat sig'madi.")
        else:
            bot.send_message(message.chat.id, matn, parse_mode="Markdown")
            
    elif text == "🗑 Kinoni o'chirish":
        bot.send_message(message.chat.id, "🗑 **Kinoni o'chirish uchun quyidagicha yuboring:**\n`/del <kod>`\nMisol uchun: `/del 1`", parse_mode="Markdown")

    elif text == "📢 Kanallar sozlamasi":
        kanallar_matn = "📢 **Hozirgi majburiy obuna kanallari:**\n\n"
        for i, k in enumerate(MAJBURIY_KANALLAR, 1):
            kanallar_matn += f"{i}. {k['name']} — `{k['username']}`\n"
        kanallar_matn += "\n➕ **Yangi kanal qo'shish uchun:**\n`/addkanal @username | Kanal Nomi`\n\n➖ **Kanalni o'chirish uchun:**\n`/delkanal @username`"
        bot.send_message(message.chat.id, kanallar_matn, parse_mode="Markdown")

    elif text == "📢 Rassilka (/send)":
        bot.send_message(message.chat.id, "📢 Rassilka qilish uchun istalgan xabar yoki videoga **Reply (javob berish)** qilib `/send` deb yuboring.", parse_mode="Markdown")

    elif text.startswith("/del "):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Xato format! Ishlatilishi: `/del 1`", parse_mode="Markdown")
            return
        kod = parts[1].strip()
        if kod in KINOLAR:
            del KINOLAR[kod]
            saqlash_fayl(DB_FILE, KINOLAR)
            bot.send_message(message.chat.id, f"✅ `{kod}` kodli kino bazadan o'chirildi!", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ `{kod}` kodli kino topilmadi.", parse_mode="Markdown")

    elif text.startswith("/addkanal "):
        try:
            params = text.replace("/addkanal ", "").split("|")
            username = params[0].strip()
            name = params[1].strip()
            MAJBURIY_KANALLAR.append({"username": username, "name": name})
            saqlash_fayl(CHANNELS_FILE, MAJBURIY_KANALLAR)
            bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli qo'shildi!\nKanal: {name} ({username})")
        except:
            bot.send_message(message.chat.id, "❌ Xato format! Misol: `/addkanal @kanalusername | Kanal Nomi`", parse_mode="Markdown")

    elif text.startswith("/delkanal "):
        username = text.replace("/delkanal ", "").strip()
        topildi = False
        for kanal in MAJBURIY_KANALLAR:
            if kanal["username"] == username:
                MAJBURIY_KANALLAR.remove(kanal)
                topildi = True
                break
        if topildi:
            saqlash_fayl(CHANNELS_FILE, MAJBURIY_KANALLAR)
            bot.send_message(message.chat.id, f"✅ `{username}` kanali majburiy obunadan olib tashlandi!", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ `{username}` topilmadi. Ro'yxatni tekshirib ko'ring.", parse_mode="Markdown")

    elif text.startswith("/send"):
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "❌ Rassilka qilish uchun xabarga reply qilib yuboring!")
            return
        sent_count = 0
        fail_count = 0
        bot.send_message(message.chat.id, "⏳ Rassilka boshlandi...")
        for user_id in FOYDALANUVCHILAR:
            try:
                bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
                sent_count += 1
            except:
                fail_count += 1
        bot.send_message(message.chat.id, f"✅ Rassilka yakunlandi!\n\n📤 Yuborildi: {sent_count} ta\n❌ Yuborilmadi: {fail_count} ta")

    else:
        kod = text.strip()
        if kod in KINOLAR:
            kino = KINOLAR[kod]
            caption_text = (
                f"🎬 **Kino nomi:** {kino['nomi']}\n"
                f"🆔 **Kodi:** `{kod}`\n"
                f"📁 **Formati:** {kino.get('format', 'MP4')}\n"
                f"📦 **Hajmi:** {kino.get('hajmi', 'Nomaʼlum')}"
            )
            bot.send_video(message.chat.id, kino['file_id'], caption=caption_text, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Noma'lum buyruq yoki bunday kodli kino topilmadi.")

# --- ADMIN VIDEO YUBORGANDA ---
@bot.message_handler(content_types=['video'])
def kino_qoshish(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Kechirasiz, oddiy foydalanuvchilarga video yuborish taqiqlangan! Faqat kino kodini kiriting.")
        return
    
    file_id = message.video.file_id
    file_size_bytes = message.video.file_size if message.video.file_size else 0
    file_size_mb = round(file_size_bytes / (1024 * 1024), 1)
    hajmi_str = f"{file_size_mb} MB"
    
    file_name = message.video.file_name if message.video.file_name else "video.mp4"
    file_format = file_name.split('.')[-1].upper() if '.' in file_name else "MP4"

    KUTISH_ZONASI[message.from_user.id] = {
        "file_id": file_id,
        "format": file_format,
        "hajmi": hajmi_str
    }

    bot.reply_to(message, f"📥 **Video qabul qilindi!**\n📊 Hajmi: `{hajmi_str}`\n📁 Formati: `{file_format}`\n\nIltimos, bu videoga **Kod va Nom** yuboring (masalan):\n`1 | Avatar 2`", parse_mode="Markdown")

# --- RASM, STIKER VA BOSHQA FAYLLARNI CHEKLASH ---
@bot.message_handler(content_types=['photo', 'audio', 'document', 'sticker', 'voice', 'animation', 'video_note'])
def boshqa_fayllarni_cheklash(message):
    if message.from_user.id == ADMIN_ID:
        return
    bot.reply_to(message, "❌ Botga rasm, stiker yoki boshqa fayllar tashlash taqiqlangan!\nIltimos, faqat kinoning **kodini** (masalan: `1`) yuboring.")

# --- ODDIY FOYDALANUVCHILAR KINO QIDIRISHI ---
@bot.message_handler(func=lambda message: True)
def kino_qidirish(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return

    if not obunani_tekshir(user_id):
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        for kanal in MAJBURIY_KANALLAR:
            kb.add(InlineKeyboardButton(text=f"➕ {kanal['name']}ga obuna bo'lish", url=f"https://t.me/{kanal['username'].replace('@', '')}"))
        kb.add(InlineKeyboardButton(text="🔄 Tekshirish", callback_data="tekshirish"))
        bot.reply_to(message, "⚠️ Avval kanallarga obuna bo'ling:", reply_markup=kb)
        return

    kod = message.text.strip()
    if kod in KINOLAR:
        kino = KINOLAR[kod]
        caption_text = (
            f"🎬 **Kino nomi:** {kino['nomi']}\n"
            f"🆔 **Kodi:** `{kod}`\n"
            f"📁 **Formati:** {kino.get('format', 'MP4')}\n"
            f"📦 **Hajmi:** {kino.get('hajmi', 'Nomaʼlum')}"
        )
        bot.send_video(message.chat.id, kino['file_id'], caption=caption_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Bunday kodli kino topilmadi. Iltimos, to'g'ri kino kodini kiriting!")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.remove_webhook()
    bot.infinity_polling(none_stop=True)
