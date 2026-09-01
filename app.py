from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, send_from_directory
import threading
import os
import random
import string
import json
from datetime import datetime

# ====== إعدادات البوت ======
BOT_TOKEN = '8806867969:AAFLaSJnoAzDPDDVTt61pbDFgHZLIJISnHQ'

# ====== خادم Flask ======
app_flask = Flask(__name__)

# مجلد لتخزين الملفات
os.makedirs('static', exist_ok=True)
os.makedirs('data', exist_ok=True)

# ملف لحفظ البيانات (عشان نتذكر الملفات)
DATA_FILE = 'data/files.json'

# تحميل البيانات السابقة
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        files_db = json.load(f)
else:
    files_db = {}

@app_flask.route('/')
def home():
    return "🤖 البوت شغال!"

@app_flask.route('/static/<filename>')
def serve_file(filename):
    """عرض الملفات المخزنة"""
    return send_from_directory('static', filename)

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app_flask.run(host='0.0.0.0', port=port)

# ====== دوال مساعدة ======
def generate_filename():
    """توليد اسم ملف عشوائي"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def save_html(content, user_id):
    """حفظ ملف HTML وإرجاع الرابط"""
    # نصنع اسم ملف فريد
    filename = f"alert_{generate_filename()}.html"
    filepath = os.path.join('static', filename)
    
    # نحفظ الملف
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # نسجل في قاعدة البيانات
    files_db[filename] = {
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'filepath': filepath
    }
    
    # نحفظ البيانات
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(files_db, f, ensure_ascii=False, indent=2)
    
    # نرجع الرابط
    base_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
    return f"{base_url}/static/{filename}"

# ====== كود البوت ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أرسل لي أي عبارة، وسأصنع لك رابطاً.\n"
        "عند فتح الرابط سيظهر تنبيه (alert) فقط!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    
    # نرسل رسالة "جاري المعالجة"
    processing_msg = await update.message.reply_text("⏳ جاري إنشاء الرابط...")
    
    # ننظف النص عشان ما يسبب مشاكل في JavaScript
    safe_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
    
    # نصنع ملف HTML: فقط Alert
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تنبيه</title>
</head>
<body>
    <script>
        // التنبيه يظهر تلقائياً
        alert("{safe_text}");
        
        // نضيف رسالة في الصفحة بعد التنبيه
        document.write('<h1 style="text-align:center;margin-top:50px;font-family:Arial;">✅ تم عرض التنبيه</h1>');
        document.write('<p style="text-align:center;font-family:Arial;color:#666;">يمكنك إغلاق هذه الصفحة</p>');
    </script>
</body>
</html>'''
    
    try:
        # نحفظ الملف ونحصل على الرابط
        link = save_html(html_content, user_id)
        
        # نحذف رسالة "جاري المعالجة"
        await processing_msg.delete()
        
        # نرسل الرابط للمستخدم
        await update.message.reply_text(
            f"✅ تم إنشاء الرابط!\n\n"
            f"🔗 {link}\n\n"
            f"📱 افتح الرابط من متصفح هاتفك، سيظهر لك تنبيه فقط.\n"
            f"📌 الرابط صالح طالما البوت شغال."
        )
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ خطأ: {e}")

# ====== تشغيل البوت ======
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    # تشغيل Flask في خيط منفصل
    threading.Thread(target=run_flask, daemon=True).start()
    # تشغيل البوت
    run_bot()

@
