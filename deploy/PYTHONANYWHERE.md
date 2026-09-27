# PythonAnywhere: CounterStrikeStat

ตำแหน่งโครงการ: `/home/CounterStrikeStat/cs2-stat-tracker` โดยยังใช้ Django settings module ชื่อ `cs2stats.settings`

## ลำดับการย้าย

1. Clone repository ไปที่ `/home/CounterStrikeStat/cs2-stat-tracker` แล้วสร้าง virtualenv `.venv`
2. สร้าง `.env` โดยตั้ง `DEBUG=0`, `ALLOWED_HOSTS=counterstrikestat.pythonanywhere.com` และ `SECRET_KEY` แบบสุ่มที่ปลอดภัย ไม่ต้องใส่ `LEETIFY_API_KEY` เพราะผู้ใช้กรอก key ใน browser
3. ใน Bash console ของ PythonAnywhere ใช้ virtualenv ของโปรเจกต์ แล้วรันคำสั่งต่อไปนี้:

```bash
cd /home/CounterStrikeStat/cs2-stat-tracker
.venv/bin/python --version
.venv/bin/python -m django --version
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
test -s staticfiles/output.css
```

ไฟล์ `static/output.css` เป็น CSS ที่ build มาแล้ว จึงไม่ต้องติดตั้ง Node.js บน PythonAnywhere หากแก้ template หรือคลาส Tailwind ให้รัน `npm run build` ในเครื่องก่อนส่งไฟล์ขึ้นใหม่ แล้วรัน `collectstatic` อีกครั้ง

4. ใน Web tab ตั้ง **Static files** เพียงแถวเดียว: URL `/static/` → Directory `/home/CounterStrikeStat/cs2-stat-tracker/staticfiles` ตั้ง Source code และ Working directory เป็น `/home/CounterStrikeStat/cs2-stat-tracker`
5. แทนไฟล์ `/var/www/counterstrikestat_pythonanywhere_com_wsgi.py` ด้วยเนื้อหาจาก `deploy/pythonanywhere_wsgi.py` และตั้ง virtualenv เป็น `/home/CounterStrikeStat/cs2-stat-tracker/.venv` (Python 3.11)
6. กด **Reload** จากนั้นเปิด `https://counterstrikestat.pythonanywhere.com/static/output.css` ต้องได้ CSS ไม่ใช่หน้า 404

ตั้ง **Force HTTPS** ใน Web tab หลังเว็บทำงานบน HTTPS แล้ว โดยไม่ต้องตั้ง `SECURE_SSL_REDIRECT` ซ้ำใน Django ([คู่มือ PythonAnywhere](https://help.pythonanywhere.com/pages/ForcingHTTPS))

อ้างอิงขั้นตอน static ของ [PythonAnywhere](https://help.pythonanywhere.com/pages/DjangoStaticFiles) ซึ่งกำหนด `STATIC_ROOT`, `collectstatic` และ Static Files Mapping ทั้งสามส่วน

## Leetify API บนบัญชีฟรี

หลังล็อกอิน ให้ผู้ใช้กรอก Leetify API key ในช่องบน navigation bar ค่านี้เก็บใน `sessionStorage` ของ browser และส่งตรงไปยัง Leetify ไม่ถูกส่งหรือบันทึกใน Django หากไม่กรอก key ระบบจะใช้เส้นทาง server เดิม ซึ่งอาจติด outbound allowlist ของบัญชีฟรี

## ย้อนกลับ

หากเว็บมีปัญหา ให้ตรวจ error log, WSGI path, virtualenv และ Static Files Mapping ก่อนย้อน commit ใน GitHub
