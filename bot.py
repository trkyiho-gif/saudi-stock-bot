import os
import asyncio
import feedparser
from groq import Groq
from flask import Flask
import threading
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. المفاتيح والربط ---
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8995537745:AAGPN2CMTSvFnqBIH6B7KQ28kzb-18yOBb0"
TELEGRAM_CHAT_ID = "6935893078"

client = Groq(api_key=GROQ_API_KEY)

NEWS_RSS_URL = "https://news.google.com/rss/search?q=%D8%A3%D8%B9%D9%85%D8%A7%D9%84+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9+OR+%D8%A7%D9%8 للسوق+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A+OR+%D8%AA%D8%AF%D8%A7%D9%88%D9%84&hl=ar&gl=SA&ceid=SA:ar"
seen_news_links = set()

# --- 2. خادم Flask لإبقاء البوت شغالاً 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive and searching live!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --- 3. دالة جلب البيانات والبحث الحي من الإنترنت ---
def fetch_live_market_data(query):
    try:
        search_url = f"https://news.google.com/rss/search?q={query}+السوق+السعودي+تداول&hl=ar&gl=SA&ceid=SA:ar"
        feed = feedparser.parse(search_url)
        
        live_info = ""
        count = 0
        for entry in feed.entries[:3]:
            live_info += f"- العنوان: {entry.title}\n  التفاصيل: {entry.get('summary', '')}\n\n"
            count += 1
            
        if count > 0:
            return f"معلومات حية تم جلبها من السوق:\n{live_info}"
        return "لم يتم العثور على بيانات حية حديثة جداً لهذا الطلب، اعتمد على تحليلك العام."
    except Exception as e:
        print(f"Scraping Error: {e}")
        return ""

# --- 4. دالة التحليل الذكي المدمجة بالبحث الحي عبر Groq ---
def get_groq_smart_response(user_text):
    try:
        live_data = fetch_live_market_data(user_text)
        
        system_prompt = """
أنت مساعد مالي ومحلل محترف وخبير في سوق الأسهم السعودي (تداول).
مهمتك تحليل الأسهم وتقديم المشورة بدقة استناداً إلى البيانات الحية المسترجعة إن وجدت، وبأسلوب مباشر، احترافي، ومرتب مع إيموجي مناسبة.
"""
        user_prompt = f"""
سؤال المستخدم: {user_text}

بيانات حية حديثة من السوق تخص الطلب:
{live_data}

قم بتحليل الطلب والإجابة عليه بدقة واحترافية عالية للمستثمر.
"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        if completion.choices and completion.choices[0].message:
            return completion.choices[0].message.content.strip()
        return "عذراً، لم أتمكن من الحصول على رد من المحرك."
    except Exception as e:
        print(f"Groq Error Detail: {e}")
        return f"عذراً، حدث خطأ تقني أثناء الاتصال: {str(e)}"

# --- 5. فحص الأخبار التلقائي العاجل ---
async def check_news(context: ContextTypes.DEFAULT_TYPE):
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        for entry in feed.entries[:2]:
            link = entry.link
            if link not in seen_news_links:
                seen_news_links.add(link)
                title = entry.title
                summary = entry.get('summary', '')

                prompt = f"""
قيم هذا الخبر الاقتصادي العاجل الخاص بالسوق السعودي بدقة:
العنوان: {title}
التفاصيل: {summary}

إذا كان الخبر عادياً أو غير مؤثر، اكتب فقط كلمة "تجاهل".
إذا كان مهماً ومؤثراً على المستثمرين، اكتب تحليلاً مختصراً ومرتباً يوضح تأثيره على السوق أو الشركات مع إيموجي مناسب.
"""
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                )
                analysis = completion.choices[0].message.content.strip()
                
                if "تجاهل" not in analysis:
                    await context.bot.send_message(
                        chat_id=TELEGRAM_CHAT_ID, 
                        text=f"🚨 **تنبيه استثماري حي وعاجل:**\n\n{analysis}\n\n🔗 الرابط: {link}",
                        parse_mode="Markdown"
                    )
    except Exception as e:
        print(f"Error in check_news: {e}")

# --- 6. الرد المباشر على رسائل المستخدم في التليجرام ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    reply_text = get_groq_smart_response(user_text)
    await context.bot.send_message(chat_id=chat_id, text=reply_text)

# --- 7. التشغيل الأساسي ---
def main():
    keep_alive()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    job_queue = application.job_queue
    job_queue.run_repeating(check_news, interval=7200, first=10)

    print("Bot is running with Live Market Search & Groq...")
    application.run_polling()

if __name__ == '__main__':
    main()
