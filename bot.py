import os
import asyncio
import feedparser
import cohere
from flask import Flask
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. المفاتيح والربط ---
COHERE_API_KEY = "cohere_CAJZTEe4eP8HVWmaFbwFftf3VK1VQgXKBO9NshBZ3m1HHv"
TELEGRAM_BOT_TOKEN = "8995537745:AAGPN2CMTSvFnqBIH6B7KQ28kzb-18yOBb0"
TELEGRAM_CHAT_ID = "6935893078"

co = cohere.Client(COHERE_API_KEY)

NEWS_RSS_URL = "https://news.google.com/rss/search?q=%D8%A3%D8%B9%D9%85%D8%A7%D9%لل+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9+OR+%D8%A7%D9%8 للسوق+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A&hl=ar&gl=SA&ceid=SA:ar"
seen_news_links = set()

# --- 2. خادم Flask لإبقاء البوت شغالاً 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --- 3. دالة التحليل الذكي عبر Cohere Generate ---
def get_cohere_response(prompt_text):
    try:
        response = co.generate(
            model='command',
            prompt=prompt_text,
            max_tokens=400,
            temperature=0.7,
        )
        return response.generations[0].text.strip()
    except Exception as e:
        print(f"Cohere Error: {e}")
        return "عذراً، واجهت مشكلة في الاتصال بمحرك الذكاء الاصطناعي."

# --- 4. فحص الأخبار الذكي (يرسل المهم فقط) ---
async def check_news(context: ContextTypes.DEFAULT_TYPE):
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        for entry in feed.entries[:3]:
            link = entry.link
            if link not in seen_news_links:
                seen_news_links.add(link)
                title = entry.title
                summary = entry.get('summary', '')

                prompt = f"""
أنت محلل مالي محترف لسوق الأسهم السعودي. 
قيم هذا الخبر بدقة:
العنوان: {title}
التفاصيل: {summary}

إذا كان عادياً أو تافهاً، اكتب فقط كلمة "تجاهل".
إذا كان مهماً جداً (مثل انخفاض حاد، نتائج مالية، توزيع أرباح)، اكتب تحليلاً مختصراً ومرتباً مع إيموجي مناسب.
"""
                analysis = get_cohere_response(prompt)
                
                if "تجاهل" not in analysis:
                    await context.bot.send_message(
                        chat_id=TELEGRAM_CHAT_ID, 
                        text=f"🚨 **تنبيه استثماري مهم:**\n\n{analysis}\n\n🔗 الرابط: {link}",
                        parse_mode="Markdown"
                    )
    except Exception as e:
        print(f"Error in check_news: {e}")

# --- 5. الرد المباشر على رسائل المستخدم في التليجرام ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    prompt = f"""
أنت مساعد مالي ذكي ومحترف لسوق الأسهم السعودي.
المستخدم سألك التالي: "{user_text}"
قم بالرد عليه بأسلوب مالي دقيق، مباشر، ومرتب باللغة العربية لمساعدته في اتخاذ القرار الاستثماري.
"""
    reply_text = get_cohere_response(prompt)
    await context.bot.send_message(chat_id=chat_id, text=reply_text)

# --- 6. التشغيل الأساسي ---
def main():
    keep_alive()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    job_queue = application.job_queue
    job_queue.run_repeating(check_news, interval=7200, first=10)

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
