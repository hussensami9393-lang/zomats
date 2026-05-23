# 🚀 دليل الرفع على fly.io - NexusAI Bot

## المتطلبات الأولى

1. **حساب على fly.io**: https://fly.io/app/sign-up (مجاني)
2. **تثبيت flyctl**: https://fly.io/docs/hands-on/install-flyctl/
3. **حساب MongoDB Atlas**: https://cloud.mongodb.com (مجاني)
4. **بوت تلغرام**: أنشئه من @BotFather وخذ الـ token

---

## خطوات الإعداد

### 1. إعداد MongoDB Atlas (مجاني)
1. سجّل في https://cloud.mongodb.com
2. أنشئ Cluster مجاني (M0)
3. أنشئ Database User
4. احصل على Connection String
   - يبدو هكذا: `mongodb+srv://user:pass@cluster.mongodb.net/`

### 2. تجهيز الملفات
```bash
# انسخ ملف الإعدادات
cp .env.example .env

# عدّل القيم في .env
nano .env
```

### 3. تسجيل الدخول لـ fly.io
```bash
flyctl auth login
```

### 4. إنشاء التطبيق
```bash
# عدّل اسم التطبيق في fly.toml أولاً، ثم:
flyctl apps create nexusai-bot
```

### 5. رفع المتغيرات السرية
```bash
flyctl secrets set \
  TELEGRAM_BOT_TOKEN="TOKEN_من_BotFather" \
  TELEGRAM_WEBHOOK_URL="https://nexusai-bot.fly.dev" \
  OPENAI_API_KEY="sk-..." \
  ANTHROPIC_API_KEY="sk-ant-..." \
  MONGODB_URI="mongodb+srv://..." \
  MONGODB_DB_NAME="nexusai_db" \
  ADMIN_IDS="123456789" \
  ADMIN_PANEL_USERNAME="admin" \
  ADMIN_PANEL_PASSWORD="كلمة_سر_قوية" \
  SECRET_KEY="مفتاح_سري_عشوائي_طويل"
```

### 6. النشر
```bash
flyctl deploy
```

### 7. تأكيد النجاح
```bash
# تحقق من السجلات
flyctl logs

# تحقق من الصحة
curl https://nexusai-bot.fly.dev/health
```

---

## هيكل الملفات النهائي
```
nexusai-bot/
├── main.py              ✅ نقطة الدخول (جديد)
├── fly.toml             ✅ إعدادات fly.io (جديد)
├── Dockerfile           ✅ Docker (جديد)
├── .env.example         ✅ قالب المتغيرات (جديد)
├── requirements.txt
├── config/
│   └── settings.py
├── database/
│   └── mongodb.py
├── handlers/
│   ├── start.py
│   ├── messages.py
│   ├── media.py
│   ├── callbacks.py
│   └── admin.py
├── services/
│   ├── ai_service.py
│   ├── image_service.py
│   └── voice_service.py
├── middleware/
│   └── security.py
├── utils/
│   ├── keyboards.py
│   └── messages.py
└── admin/
    └── panel.py
```

---

## تشغيل محلي (للتطوير)
```bash
pip install -r requirements.txt
cp .env.example .env
# عدّل .env ثم:
BOT_MODE=polling python main.py
```

---

## ملاحظات مهمة
- **fly.io المجاني**: يوقف التطبيق عند عدم الاستخدام، لكن يشتغل تلقائياً عند الطلب
- **MongoDB Atlas M0**: 512MB مجاناً - كافٍ للبداية
- **OPENAI_API_KEY**: مطلوب للعمل الأساسي
- **ANTHROPIC_API_KEY**: اختياري - يُستخدم كـ backup فقط
- لوحة الإدارة: https://nexusai-bot.fly.dev/admin
