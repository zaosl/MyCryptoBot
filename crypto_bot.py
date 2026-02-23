import telebot
import requests
import threading
import time
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from flask import Flask

TOKEN = '8303500826:AAEDHAgN5eTChMz6QT5zDyuV3XSrv3AqhgQ'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8411101062 

USER_LANGS = {} 
USER_ALERTS = {}

COIN_BUTTONS = [
    '💎 BTC', '💠 ETH', '🟡 BNB',
    '🪙 SOL', '💧 XRP', '🐕 DOGE',
    '🔵 ADA', '🔺 AVAX', '🔴 TRX',
    '🟣 DOT', '🔗 LINK', '🐶 SHIB',
    '🔷 TON', '⚡️ LTC'
]

COIN_MAP = {
    'بیت': ('BTCUSDT', 'bitcoin-btc'), 'بیت کوین': ('BTCUSDT', 'bitcoin-btc'),
    'اتریوم': ('ETHUSDT', 'ethereum-eth'), 'اتر': ('ETHUSDT', 'ethereum-eth'),
    'سولانا': ('SOLUSDT', 'solana-sol'), 'سول': ('SOLUSDT', 'solana-sol'),
    'دوج': ('DOGEUSDT', 'dogecoin-doge'), 'دوج کوین': ('DOGEUSDT', 'dogecoin-doge'),
    'ترون': ('TRXUSDT', 'tron-trx'),
    'شیبا': ('SHIBUSDT', 'shiba-inu-shib'),
    'تون': ('TONUSDT', 'toncoin-ton'), 'تون کوین': ('TONUSDT', 'toncoin-ton'),
    'ریپل': ('XRPUSDT', 'xrp-xrp'),
    'کاردانو': ('ADAUSDT', 'cardano-ada'),
    'لایت کوین': ('LTCUSDT', 'litecoin-ltc'),
    'بی ان بی': ('BNBUSDT', 'bnb-bnb')
}

TEXTS = {
    'fa': {
        'welcome': "👑 **خوش آمدید رئیس!**\nارز یا ابزار مورد نظر خود را انتخاب کنید 📊👇",
        'whales': "🐋 شکارچی نهنگ‌ها", 'fng': "🧭 ترس و طمع",
        'wait': "⏳ در حال ارتباط با هسته بایننس...",
        'toman': "🇮🇷 معادل تومان: `{:,} تومان`",
        'donate_msg': "❤️ **حمایت از ما**\n\nاگر این ربات برات مفیده و دوست داری به ما انرژی بدی، می‌تونی ازمون حمایت مالی کنی. (کاملاً اختیاری!)",
        'btn_donate': "☕️ حمایت مالی (دونیت)",
        'btn_free': "ادامه استفاده رایگان ➡️",
        'wallet_msg': "دمت گرم رئیس! 🙏\nبرای حمایت می‌تونی از آدرس تتر (TRC20) زیر استفاده کنی:\n\n`آدرس_تتر_خودت_را_اینجا_بذار`",
        'btn_main_menu': "بازگشت به منوی اصلی 🏠"
    },
    'en': {
        'welcome': "👑 **Welcome Boss!**\nSelect your tool or coin 📊👇",
        'whales': "🐋 Whale Hunter", 'fng': "🧭 Fear & Greed",
        'wait': "⏳ Fetching data...",
        'donate_msg': "❤️ **Support Us**\n\nIf you find this bot useful, consider supporting us! (Completely optional)",
        'btn_donate': "☕️ Donate",
        'btn_free': "Continue for Free ➡️",
        'wallet_msg': "Thank you for your support! 🙏\nUSDT (TRC20):\n\n`YOUR_USDT_ADDRESS_HERE`",
        'btn_main_menu': "Main Menu 🏠"
    },
    'ru': {
        'welcome': "👑 **Добро пожаловать!**\nВыберите инструмент 📊👇",
        'whales': "🐋 Охотник на китов", 'fng': "🧭 Индекс страха",
        'wait': "⏳ Обработка...",
        'donate_msg': "❤️ **Поддержите нас**\n\nЕсли этот бот вам полезен, вы можете поддержать нас! (Необязательно)",
        'btn_donate': "☕️ Пожертвовать",
        'btn_free': "Продолжить бесплатно ➡️",
        'wallet_msg': "Спасибо за вашу поддержку! 🙏\nUSDT (TRC20):\n\n`ВАШ_АДРЕС_USDT`",
        'btn_main_menu': "Главное меню 🏠"
    },
    'ar': {
        'welcome': "👑 **أهلاً بك أيها الزعيم!**\nاختر أداتك 📊👇",
        'whales': "🐋 صياد الحيتان", 'fng': "🧭 مؤشر الخوف",
        'wait': "⏳ جاري المعالجة...",
        'donate_msg': "❤️ **ادعمنا**\n\nإذا كان هذا الروبوت مفيدًا لك، يمكنك دعمنا! (اختياري تمامًا)",
        'btn_donate': "☕️ تبرع",
        'btn_free': "الاستمرار مجانًا ➡️",
        'wallet_msg': "شكرا لدعمك! 🙏\nعنوان USDT (TRC20):\n\n`عنوان_USDT_الخاص_بك`",
        'btn_main_menu': "القائمة الرئيسية 🏠"
    }
}

app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Bot is alive and running 24/7! (Created by @zaosl)"
def run_web():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    threading.Thread(target=run_web).start()

def get_tether_to_toman():
    try:
        res = requests.get("https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls", timeout=7).json()
        price_toman = int(float(res['stats']['usdt-rls']['latest']) / 10)
        return price_toman
    except:
        return 65000 

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
        return 50 

def get_whale_movements():
    url = "https://data-api.binance.vision/api/v3/ticker/24hr"
    data = requests.get(url, timeout=10).json()
    usdt_pairs = [item for item in data if item.get('symbol', '').endswith('USDT')]
    usdt_pairs.sort(key=lambda x: float(x.get('priceChangePercent', 0)), reverse=True)
    return usdt_pairs[:5], usdt_pairs[-5:][::-1]

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
def set_language_and_donate(call):
    lang_code = call.data.split('_')[1]
    user_id = call.from_user.id
    USER_LANGS[user_id] = lang_code
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    t = TEXTS[lang_code]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_donate'], callback_data="donate_show"))
    markup.add(InlineKeyboardButton(t['btn_free'], callback_data="donate_skip"))
    
    bot.send_message(call.message.chat.id, t['donate_msg'], reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['donate_show', 'donate_skip'])
def handle_donation_choice(call):
    user_id = call.from_user.id
    lang_code = USER_LANGS.get(user_id, 'fa')
    t = TEXTS[lang_code]
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if call.data == 'donate_show':
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(t['btn_main_menu'], callback_data="donate_skip"))
        bot.send_message(call.message.chat.id, t['wallet_msg'], reply_markup=markup, parse_mode='Markdown')
        
    elif call.data == 'donate_skip':
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        markup.add(*[KeyboardButton(c) for c in COIN_BUTTONS])
        markup.add(KeyboardButton(t['whales']), KeyboardButton(t['fng']))
        bot.send_message(call.message.chat.id, t['welcome'], reply_markup=markup, parse_mode='Markdown')

# --- بخش جدید: طراحی دقیق متن رادار شبیه به عکس ---
@bot.message_handler(func=lambda message: bool(re.search(r"([\d\.]+)\s*(بیت کوین|بیت|اتریوم|اتر|سولانا|سول|دوج کوین|دوج|ترون|شیبا|تون کوین|تون|ریپل|کاردانو|لایت کوین|بی ان بی)", message.text if message.text else "")))
def group_crypto_calculator(message):
    try:
        match = re.search(r"([\d\.]+)\s*(بیت کوین|بیت|اتریوم|اتر|سولانا|سول|دوج کوین|دوج|ترون|شیبا|تون کوین|تون|ریپل|کاردانو|لایت کوین|بی ان بی)", message.text)
        if not match: return
        
        amount = float(match.group(1))
        coin_fa = match.group(2)
        symbol, logo_path = COIN_MAP[coin_fa]
        
        res = requests.get(f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={symbol}", timeout=5).json()
        price = float(res['lastPrice'])
        high = float(res['highPrice'])
        low = float(res['lowPrice'])
        change = float(res['priceChangePercent'])
        
        tether_price = get_tether_to_toman()
        
        total_toman = int(amount * price * tether_price)
        total_usd = amount * price
        
        high_toman = int(high * tether_price)
        low_toman = int(low * tether_price)
        
        change_emoji = "🟢" if change > 0 else "🔴"
        symbol_clean = symbol.replace('USDT', '')
        
        # چیدمان متن دقیقاً مثل اسکرین‌شات (با فرمت HTML)
        caption = f"💎 <b>{amount:g} {symbol_clean} :</b>\n\n"
        caption += f"💸 <b>{total_toman:,}</b> toman\n"
        caption += f"💲 <b>${total_usd:,.3f}</b> dollar\n"
        caption += f"{change_emoji} <b>{change}%</b>\n\n"
        caption += f"<blockquote>📊 <b>High & Low</b> 📉.\n"
        caption += f"💸 {high_toman:,} / {low_toman:,} toman</blockquote>"
        
        photo_url = f"https://cryptologos.cc/logos/{logo_path}-logo.png"
        
        bot.send_photo(message.chat.id, photo_url, caption=caption, reply_to_message_id=message.message_id, parse_mode='HTML')
    except Exception as e:
        pass

@bot.message_handler(func=lambda message: True)
def handle_crypto_request(message):
    user_id = message.from_user.id
    lang = USER_LANGS.get(user_id, 'fa')
    t = TEXTS[lang]
    text = message.text
    
    if text in COIN_BUTTONS:
        msg_wait = bot.reply_to(message, t['wait'])
        try:
            coin_symbol = text.split()[1] + 'USDT'
            url = f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={coin_symbol}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                bot.edit_message_text(f"❌ خطای سرور بایننس: {response.status_code}", chat_id=message.chat.id, message_id=msg_wait.message_id)
                return

            data = response.json()
            price = float(data['lastPrice'])
            change = float(data['priceChangePercent'])
            rsi = calculate_rsi(coin_symbol)
            change_str = f"+{change}%" if change > 0 else f"{change}%"
            
            response_text = f"📊 **{coin_symbol.replace('USDT','')}**\n💰 Price: `${price:,.5f}`\n📈 24h: `{change_str}`\n🧠 **AI (RSI):** {rsi:.1f}/100"
            
            if lang == 'fa':
                tether_price = get_tether_to_toman()
                toman_price = int(price * tether_price)
                response_text += f"\n\n{t['toman'].format(toman_price)}"

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
    print(" 🚀 FINAL BOT (HTML FORMATTED) IS ONLINE ")
    print("="*50)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
