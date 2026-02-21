import telebot
import requests
import threading
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from flask import Flask

TOKEN = '8303500826:AAH1eRkav40VbGcI8U3lBxusVPDIi0tZBVE'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8411101062 

VIP_FILE = 'vip_users.txt'
USER_LANGS = {} 
USER_ALERTS = {}

COIN_BUTTONS = [
    '💎 BTC', '💠 ETH', '🟡 BNB',
    '🪙 SOL', '💧 XRP', '🐕 DOGE',
    '🔵 ADA', '🔺 AVAX', '🔴 TRX',
    '🟣 DOT', '🔗 LINK', '🐶 SHIB',
    '🔷 TON', '⚡️ LTC'
]

TEXTS = {
    'fa': {
        'welcome': "👑 **خوش آمدید رئیس!**\nارز یا ابزار مورد نظر خود را انتخاب کنید 📊👇",
        'locked': "⛔️ **دسترسی محدود! (فقط VIP)**\n\nبرای خرید اشتراک و فعال‌سازی ربات، لطفاً آیدی عددی زیر را کپی کرده و همراه با فیش واریزی به پشتیبانی ارسال کنید:\n\n👤 **آیدی عددی شما:** `{user_id}`\n👨‍💻 **ارتباط با پشتیبانی:** @zaosl",
        'whales': "🐋 شکارچی نهنگ‌ها", 'fng': "🧭 ترس و طمع",
        'wait': "⏳ در حال ارتباط با هسته بایننس..."
    },
    'en': {
        'welcome': "👑 **Welcome Boss!**\nSelect your tool or coin 📊👇",
        'locked': "⛔️ **Access Denied! (VIP Only)**\n\nTo activate your subscription, please send your ID and payment receipt to support:\n\n👤 **Your ID:** `{user_id}`\n👨‍💻 **Support:** @zaosl",
        'whales': "🐋 Whale Hunter", 'fng': "🧭 Fear & Greed",
        'wait': "⏳ Fetching data..."
    },
    'ru': {
        'welcome': "👑 **Добро пожаловать!**\nВыберите инструмент 📊👇",
        'locked': "⛔️ **Доступ закрыт! (Только VIP)**\n\nОтправьте ваш ID и чек об оплате в поддержку:\n\n👤 **Ваш ID:** `{user_id}`\n👨‍💻 **Поддержка:** @zaosl",
        'whales': "🐋 Охотник на китов", 'fng': "🧭 Индекс страха",
        'wait': "⏳ Обработка..."
    },
    'ar': {
        'welcome': "👑 **أهلاً بك أيها الزعيم!**\nاختر أداتك 📊👇",
        'locked': "⛔️ **تم الرفض! (VIP فقط)**\n\nأرسل معرفك وإيصال الدفع إلى الدعم الفني:\n\n👤 **معرفك:** `{user_id}`\n👨‍💻 **الدعم:** @zaosl",
        'whales': "🐋 صياد الحيتان", 'fng': "🧭 مؤشر الخوف",
        'wait': "⏳ جاري المعالجة..."
    }
}

# --- 🌐 وب‌سرور ضد خواب ---
app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Bot is alive and running 24/7! (Created by @zaosl)"
def run_web():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    threading.Thread(target=run_web).start()

# --- توابع دیتابیس ---
def load_vip_users():
    if not os.path.exists(VIP_FILE): return []
    with open(VIP_FILE, 'r') as f: return [int(line.strip()) for line in f if line.strip().isdigit()]

def save_vip_users(users):
    with open(VIP_FILE, 'w') as f:
        for u in users: f.write(f"{u}\n")

VIP_USERS = load_vip_users()

# --- توابع تحلیلگر (با آدرس‌های بدون تحریم) ---
def calculate_rsi(symbol, period=14):
    try:
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=1h&limit={period+1}"
        res = requests.get(url, timeout=10).json()
        closes = [float(candle[4]) for candle in res]
        gains, losses = [], []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0: gains.append(change)
            else: losses.append(abs(change))
        avg_gain = sum(gains)/period if gains else 0
        avg_loss = sum(losses)/period if losses else 0.0001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except Exception as e: 
        print(f"RSI Error: {e}")
        return 50 

def get_whale_movements():
    url = "https://data-api.binance.vision/api/v3/ticker/24hr"
    data = requests.get(url, timeout=10).json()
    usdt_pairs = [item for item in data if item.get('symbol', '').endswith('USDT')]
    usdt_pairs.sort(key=lambda x: float(x.get('priceChangePercent', 0)), reverse=True)
    return usdt_pairs[:5], usdt_pairs[-5:][::-1]

# --- هندلرهای ربات ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    markup.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")
    )
    bot.reply_to(message, "🌍 Please select your language:\nلطفا زبان خود را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang_code = call.data.split('_')[1]
    user_id = call.from_user.id
    USER_LANGS[user_id] = lang_code
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    t = TEXTS[lang_code]
    if user_id not in VIP_USERS and user_id != ADMIN_ID:
        bot.send_message(call.message.chat.id, t['locked'].format(user_id=user_id), parse_mode='Markdown')
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(*[KeyboardButton(c) for c in COIN_BUTTONS])
    markup.add(KeyboardButton(t['whales']), KeyboardButton(t['fng']))
    bot.send_message(call.message.chat.id, t['welcome'], reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['add'])
def add_vip_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        new_user_id = int(message.text.split()[1])
        if new_user_id not in VIP_USERS:
            VIP_USERS.append(new_user_id)
            save_vip_users(VIP_USERS)
            bot.reply_to(message, f"✅ کاربر `{new_user_id}` با موفقیت ثبت شد.")
            try:
                success_msg = "🎉 **تایید حساب کاربری!**\n\nهم‌اکنون به امکانات VIP دسترسی دارید.\n👉 /start"
                bot.send_message(new_user_id, success_msg, parse_mode='Markdown')
            except Exception as e:
                bot.reply_to(message, f"⚠️ کاربر ثبت شد اما ارسال پیام به او با خطا مواجه شد: {e}")
        else:
            bot.reply_to(message, "⚠️ این کاربر از قبل در سیستم است.")
    except Exception as e: 
        bot.reply_to(message, f"❌ فرمت اشتباه است. مثال: `/add 123456789`\nارور: {e}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_crypto_request(message):
    user_id = message.from_user.id
    lang = USER_LANGS.get(user_id, 'fa')
    t = TEXTS[lang]
    if user_id not in VIP_USERS and user_id != ADMIN_ID: return
    text = message.text
    
    if text in COIN_BUTTONS:
        msg_wait = bot.reply_to(message, t['wait'])
        try:
            coin_symbol = text.split()[1] + 'USDT'
            url = f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={coin_symbol}"
            response = requests.get(url, timeout=10)
            
            # اگر بایننس بهمون ارور داد، ربات بهمون بگه
            if response.status_code != 200:
                bot.edit_message_text(f"❌ خطای سرور بایننس: {response.status_code}", chat_id=message.chat.id, message_id=msg_wait.message_id)
                return

            data = response.json()
            price = float(data['lastPrice'])
            change = float(data['priceChangePercent'])
            rsi = calculate_rsi(coin_symbol)
            change_str = f"+{change}%" if change > 0 else f"{change}%"
            response_text = f"📊 **{coin_symbol.replace('USDT','')}**\n💰 Price: `${price:,.5f}`\n📈 24h: `{change_str}`\n🧠 **AI (RSI):** {rsi:.1f}/100"
            bot.edit_message_text(response_text, chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')
        except Exception as e: 
            bot.edit_message_text(f"❌ خطای دریافت اطلاعات:\n`{e}`", chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')
            
    elif text == t.get('fng') or text == "🧭 ترس و طمع":
        try:
            res = requests.get("https://api.alternative.me/fng/", timeout=10).json()
            val = res['data'][0]['value']
            status = res['data'][0]['value_classification']
            bot.send_message(message.chat.id, f"🧭 **Fear & Greed Index**\nScore: {val}/100\nStatus: **{status}**")
        except Exception as e: 
            bot.send_message(message.chat.id, f"❌ خطا: {e}")
            
    elif text == t.get('whales') or text == "🐋 شکارچی نهنگ‌ها":
        msg_wait = bot.reply_to(message, t['wait'])
        try:
            gainers, losers = get_whale_movements()
            response = "🚀 **PUMP:**\n"
            for g in gainers: response += f"🟢 {g['symbol'].replace('USDT','')} : +{g['priceChangePercent']}%\n"
            response += "\n🩸 **DUMP:**\n"
            for l in losers: response += f"🔴 {l['symbol'].replace('USDT','')} : {l['priceChangePercent']}%\n"
            bot.edit_message_text(response, chat_id=message.chat.id, message_id=msg_wait.message_id)
        except Exception as e: 
            bot.edit_message_text(f"❌ خطا در شکار نهنگ‌ها:\n`{e}`", chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')

if __name__ == '__main__':
    keep_alive() 
    print("="*50)
    print(" ☁️ ANTI-FILTER CLOUD BOT IS ONLINE ")
    print("="*50)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)