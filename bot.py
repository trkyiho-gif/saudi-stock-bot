import os
import asyncio
import feedparser
from groq import Groq
from flask import Flask
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. المفاتيح والربط ---
GROQ_API_KEY = "Gsk_8jcKoWjAUIi786DcofJOWGdyb3FY9NJiWPfKhfEiIQkQrvUVtZDK"
TELEGRAM_BOT_TOKEN = "8995537745:AAGPN2CMTsvFnqBIH687KQ28kzb-18y0Bb0"
TELEGRAM_CHAT_ID = "6935893078"

client = Groq(api_key=GROQ_API_KEY)

NEWS_RSS_URL = "https://news.google.com/rss/search?q=%D8%A3%D8%B9%D9%85%D8%A7%D9%84+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9+OR+%D8%A7%D9%84%D8%B3%D9%88%D9%82+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A&hl=ar&gl=SA&ceid=SA:ar"
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

# --- 3. دالة التحليل الذكي عبر Groq ---
def get_groq_response(prompt_text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت مساعد مالي ومحلل محترف لسوق الأسهم السعودي."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=600,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq Error: {e}")
        return "عذراً، واجهت مشكلة في الاتصال بمحرك الذكاء الاصطناعي."

# --- 4. فحص الأخبار الذكي ---
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
قيم هذا الخبر الاقتصادي الخاص بالسوق السعودي بدقة:
العنوان: {title}
التفاصيل: {summary}

إذا كان الخبر عادياً أو غير مؤثر، اكتب فقط كلمة "تجاهل".
إذا كان مهماً ومؤثراً على المستثمرين، اكتب تحليلاً مختصراً ومرتباً مع إيموجي مناسب.
"""
                analysis = get_groq_response(prompt)
                
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

    prompt = f"المستخدم سألك التالي: '{user_text}'. أجب عليه بأسلوب مالي دقيق ومباشر ومفيد لمستثمر في السوق السعودي."
    reply_text = get_groq_response(prompt)
    await context.bot.send_message(chat_id=chat_id, text=reply_text)

# --- 6. التشغيل الأساسي ---
def main():
    keep_alive()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    job_queue = application.job_queue
    job_queue.run_repeating(check_news, interval=7200, first=10)

    print("Bot is running with Groq...")
    application.run_polling()

if __name__ == '__main__':
    main()
