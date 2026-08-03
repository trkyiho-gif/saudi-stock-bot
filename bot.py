



import time
import asyncio
import feedparser
import cohere
from telegram import Bot

# ==========================================
# 1. البيانات والمفاتيح
# ==========================================
COHERE_API_KEY = "cohere_CAJZTEe4eP8HVVmaFbwFttf3VK1vQGxKBO9NshBZ3mlHHv"
TELEGRAM_BOT_TOKEN = "8995537745:AAGPN2CMTSvFnqBIH6B7KQ28kzb-18yOBb0"
TELEGRAM_CHAT_ID = "6935893078"

# رابط أخبار الاقتصاد والأسواق (تغذية مباشرة وسريعة)
NEWS_RSS_URL = "https://news.google.com/rss/search?q=%D8%A3%D8%B3%D9%87%D9%85+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A%D8%A9+%D8%A7%D9%84%D8%A7%D9%82%D8%AA%D8%B5%D8%A7%D8%AF&hl=ar&gl=SA&ceid=SA:ar"

seen_news_links = set()

# ==========================================
# 2. دالة تحليل الأخبار عبر Cohere
# ==========================================
def analyze_news_with_cohere(news_title: str, news_summary: str) -> str:
    prompt = f"""
أنت محلل مخاطر وأسواق مالية وسياسية خبير.
قم بتحليل الخبر التالي بأسلوب مباشر ومختصر:

عنوان الخبر: {news_title}
تفاصيل الخبر: {news_summary}

قم بإعطاء تقرير بالصيغة التالية:
1. 📝 ملخص الخبر: (في سطرين)
2. 📈 الشركات أو القطاعات المتأثرة: (اذكر القطاعات أو أسماء الأسهم بالتحديد)
3. 🎯 التوقع: (صعود / هبوط / محايد) مع توضيح السبب في نقطة واحدة
4. ⚠️ نسبة الخطورة: (من 1 إلى 10) مع السبب
5. ✅ نسبة نجاح التوقع: (نسبة مئوية بناءً على قوة وحجم الخبر)
"""
    co = cohere.ClientV2(api_key=COHERE_API_KEY)
    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.message.content[0].text

# ==========================================
# 3. دالة إرسال التقرير لتليجرام
# ==========================================
async def send_telegram_report(message: str):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID, 
        text=message, 
        parse_mode="Markdown"
    )

# ==========================================
# 4. دالة الفحص الدوري للأخبار
# ==========================================
async def check_and_process_news():
    print("🔎 جاري البحث عن أخبار جديدة في السوق...")
    feed = feedparser.parse(NEWS_RSS_URL)
    
    if not feed.entries:
        print("ℹ️ لم يتم العثور على أخبار جديدة في هذه اللحظة.")
        return

    # أخذ أحدث خبرين فقط للبدء
    for entry in feed.entries[:2]:
        news_id = entry.link
        
        if news_id not in seen_news_links:
            print(f"📰 تم العثور على خبر جديد: {entry.title}")
            seen_news_links.add(news_id)
            
            summary = getattr(entry, 'summary', entry.title)
            
            print("⏳ جاري التحليل عبر Cohere...")
            report = analyze_news_with_cohere(entry.title, summary)
            
            full_report = f"🚨 **خبر جديد من السوق** 🚨\n\n{report}\n\n🔗 [رابط الخبر الأصلي]({entry.link})"
            
            print("📲 جاري إرسال التقرير إلى تليجرام...")
            await send_telegram_report(full_report)
            print("✅ تم الإرسال بنجاح!")
            await asyncio.sleep(3)

# ==========================================
# التشغيل المستمر
# ==========================================
async def main():
    print("🚀 البوت الآلي يعمل الآن ومربوط بمصادر الأخبار...")
    while True:
        try:
            await check_and_process_news()
        except Exception as e:
            print(f"❌ حدث خطأ: {e}")
        
        print("⏳ انتظار 5 دقائق قبل الفحص القادم...")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())