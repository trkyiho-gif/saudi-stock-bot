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
TELEGRAM_BOT_TOKEN ="8995537745:AAGPN2CMTSvFnqBIH6B7KQ28kzb-18yOBb0
TELEGRAM_CHAT_ID = "6935893078
co = cohere.Client(COHERE_API_KEY)

NEWS_RSS_URL = "https://news.google.com/rss/search?q=%D8%A3%D8%B9%D9%85%D8%A7%D9%84+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9+OR+%D8%A7%D9%84%D8%B3%D9%88%D9%82+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A+%OR+%D8%A3%D8%B1%D8%A7%D9%85%D已%B3%D9%88&hl=ar&gl=SA&ceid=SA:ar"
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

# --- 3. دالة التحليل الذكي والتصفية الصارمة (منع الإزعاج) ---
def analyze_news_with_cohere(news_title, news_summary):
    prompt = f"""
أنت محلل مالي محترف لسوق الأسهم السعودي. 
عليك تقييم هذا الخبر بدقة شديدة:
العنوان: {news_title}
التفاصيل: {news_summary}

الشروط الصارمة جداً:
- إذا كان الخبر عادياً، تافهاً، أو مكرراً، أجب فقط بكلمة "تجاهل".
- لا ترسل الخبر إلا إذا كان "مهماً جداً ومؤثراً للغاية" (مثل: انخفاض حاد بأكثر من 5%، خبر جوهري عن الشركة، إعلان نتائج مالية صادمة، اندماج، أو توزيع أرباح ضخم).
- إذا كان مهماً، اكتب لي تحليلاً مختصراً ومرتباً باللغة العربية مع إيموجي مناسب (مثل 🚨 أو 📊 أو 💰) يوضح التأثير على المستثمر.
"""
    response = co.chat(model='command', message=prompt)
    return response.text.strip()

# --- 4. فحص الأخبار الذكي (يرسل فقط المهم) ---
async def check_news(context: ContextTypes.DEFAULT_TYPE):
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        for entry in feed.entries[:5]:
            link = entry.link
            if link not in seen_news_links:
                seen_news_links.add(link)
                title = entry.title
                summary = entry.get('summary', '')

                # تحليل الخبر عبر الذكاء الاصطناعي مع فرض الصمت لو غير مهم
                analysis = analyze_news_with_cohere(title, summary)
                
                if "تجاهل" not in analysis:
                    await context.bot.send_message(
                        chat_id=TELEGRAM_CHAT_ID, 
                        text=f"🚨 **تنبيه استثماري مهم:**\n\n{analysis}\n\n🔗 الرابط: {link}",
                        parse_mode="Markdown"
                    )
    except Exception as e:
        print(f"Error in check_news: {e}")

# --- 5. الرد المباشر عند محادثة البوت (اكتب له بالسليقة) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    prompt = f"""
أنت مساعد مالي ذكي ومحترف لسوق الأسهم السعودي.
المستخدم سألك أو طلب منك التالي: "{user_text}"
قم بالرد عليه بناءً على خبرتك وتحليلك المالي بأسلوب دقيق، مباشر، ومفيد للمستثمر باللغة العربية.
"""
    try:
        response = co.chat(model='command', message=prompt)
        await context.bot.send_message(chat_id=chat_id, text=response.text.strip())
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="عذراً، حدث خطأ أثناء معالجة طلبك.")

# --- 6. التشغيل الأساسي ---
def main():
    keep_alive() # تشغيل خادم الويب السحابي

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # استقبال رسايل المستخدم والرد عليها مباشرة
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # جدولة فحص الأخبار (كل ساعتين مثلاً عشان ما يصير إزعاج)
    job_queue = application.job_queue
    job_queue.run_repeating(check_news, interval=7200, first=10)

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
    asyncio.run(main())
