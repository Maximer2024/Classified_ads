
## 📜 Classified Ads — Доска объявлений для MMORPG сервера

Это веб-платформа для размещения и просмотра объявлений на фанатском сервере MMORPG. Позволяет игрокам общаться, находить группы, предлагать услуги и откликаться на объявления.

---

### 🚀 Возможности

- 🔐 Регистрация по email с подтверждением.
- 📢 Создание объявлений с поддержкой:
  - текста, заголовка;
  - изображений;
  - встроенного видео (YouTube).
- 💬 Отклики на объявления других пользователей:
  - автоматическая отправка уведомлений на email;
  - приватная страница откликов с фильтрацией и управлением ( принятие / удаление).
- 🧙 Категории игроков:
  - Танки, Хилы, ДД, Торговцы, Гидмастеры, Квестгиверы, Кузнецы, Кожевники, Зельевары, Мастера заклинаний.
- 📬 Email-рассылки новостей (Celery + Redis).
- 🧑‍🤝‍🧑 Профили пользователей: аватар, ник, описание.
- 🌐 Фильтрация и сортировка объявлений.

---

### 🧱 Технологии

- Django, Django ORM
- Celery + Redis
- django-allauth (auth)
- Bootstrap, HTML
- SQLite / PostgreSQL
- SMTP (email)

---

### ⚙️ Установка

```bash
git clone https://github.com/your-username/Classified_ads.git
cd Classified_ads
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

### 🚚 Redis + Celery

```bash
celery -A Classified_ads worker -l info
```

---

### 📧 SMTP почта

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yourmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email'
EMAIL_HOST_PASSWORD = 'your_password'
```

---

### 🔮 Тесты

```bash
python manage.py test
```

---

### 👨‍💼 Контакты

Разработка: **Максим Левша**  
Вопросы: [email:levsha.maxim78@gmail.com / telegram:@MamaXl]
