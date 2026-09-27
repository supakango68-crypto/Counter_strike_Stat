# PythonAnywhere: cs2ttracker

ตำแหน่งโครงการหลังย้าย: `/home/cs2ttracker/cs2-stat-tracker` โดยยังใช้ Django settings module ชื่อ `cs2stats.settings` ชื่อนี้เป็น Python package และไม่จำเป็นต้องเปลี่ยนตามชื่อโฟลเดอร์

## ลำดับการย้าย

1. เก็บโฟลเดอร์เดิม `/home/cs2ttracker/API_CS2_StatsTailwind ver/API_CS2_StatsTailwind ver/API_CS2_Stats` ไว้เพื่อย้อนกลับ ห้ามลบก่อนตรวจเว็บใหม่เสร็จ ตรวจว่าโฟลเดอร์ใหม่ยังไม่มีอยู่ แล้วคัดลอกโครงการไป `/home/cs2ttracker/cs2-stat-tracker` โดยต้องมี `manage.py`, `templates/`, `static/output.css`, `db.sqlite3` และ `.env` อยู่ครบ อย่าเผยแพร่ `.env` หรือ `db.sqlite3` ผ่าน static mapping
2. ใน `.env` ที่โฟลเดอร์ใหม่ ตั้ง `DEBUG=0`, `ALLOWED_HOSTS=cs2ttracker.pythonanywhere.com` และ `SECRET_KEY` แบบสุ่มที่ปลอดภัย เก็บ `LEETIFY_API_KEY` เดิมหากมี
3. ใน Bash console ของ PythonAnywhere ใช้ virtualenv ของโปรเจกต์ แล้วรันคำสั่งต่อไปนี้:

```bash
cd /home/cs2ttracker/cs2-stat-tracker
.venv/bin/python --version
.venv/bin/python -m django --version
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
test -s staticfiles/output.css
```

ไฟล์ `static/output.css` เป็น CSS ที่ build มาแล้ว จึงไม่ต้องติดตั้ง Node.js บน PythonAnywhere หากแก้ template หรือคลาส Tailwind ให้รัน `npm run build` ในเครื่องก่อนส่งไฟล์ขึ้นใหม่ แล้วรัน `collectstatic` อีกครั้ง

4. ใน Web tab ตั้ง **Static files** เพียงแถวเดียวสำหรับแอปนี้: URL `/static/` → Directory `/home/cs2ttracker/cs2-stat-tracker/staticfiles` (ไม่ใช่ `static/` ต้นทาง) ตั้ง Source code และ Working directory เป็น `/home/cs2ttracker/cs2-stat-tracker` หากมีช่องเหล่านี้
5. แทนไฟล์ `/var/www/cs2ttracker_pythonanywhere_com_wsgi.py` ด้วยเนื้อหาจาก `deploy/pythonanywhere_wsgi.py` และตั้ง Web tab ให้ใช้ virtualenv `/home/cs2ttracker/cs2-stat-tracker/.venv` (Python 3.11)
6. กด **Reload** ใน Web tab จากนั้นเปิด `https://cs2ttracker.pythonanywhere.com/static/output.css` ต้องได้ CSS ไม่ใช่หน้า 404 และเปิดหน้าแรก/หน้า login เพื่อดูสไตล์ ตรวจ error log หากมี 500

ตั้ง **Force HTTPS** ใน Web tab หลังเว็บทำงานบน HTTPS แล้ว โดยไม่ต้องตั้ง `SECURE_SSL_REDIRECT` ซ้ำใน Django ([คู่มือ PythonAnywhere](https://help.pythonanywhere.com/pages/ForcingHTTPS))

อ้างอิงขั้นตอน static ของ [PythonAnywhere](https://help.pythonanywhere.com/pages/DjangoStaticFiles) ซึ่งกำหนด `STATIC_ROOT`, `collectstatic` และ Static Files Mapping ทั้งสามส่วน

## Leetify API บนบัญชีฟรี

ทดสอบจาก Bash console แล้ว `api-public.cs-prod.leetify.com` ถูก outbound proxy ของ PythonAnywhere ตอบ `403 Forbidden` ก่อนคำขอไปถึง Leetify จึงยังค้นหาสถิติบนเว็บจริงไม่ได้ แม้ CSS และ Django จะทำงานแล้ว ส่วน `steamcommunity.com` ตอบ HTTP 200 ตามปกติ

บัญชีฟรีของ PythonAnywhere ใช้ [allowlist สำหรับการเชื่อมต่อออก](https://help.pythonanywhere.com/pages/403ForbiddenError) เจ้าของบัญชีสามารถ [ขอเพิ่มโดเมน](https://help.pythonanywhere.com/pages/RequestingAllowlistAdditions/) `api-public.cs-prod.leetify.com` โดยแนบ [เอกสาร API ทางการของ Leetify](https://api-public-docs.cs-prod.leetify.com/) และระบุโดเมนที่ API ให้บริการ อีกทางเลือกคืออัปเกรดบัญชี PythonAnywhere ซึ่งต้องเป็นการตัดสินใจของเจ้าของบัญชี หลัง PythonAnywhere อนุญาตโดเมนแล้ว ให้ Reload เว็บและทดสอบค้นหาด้วย Steam64 ID

ส่งคำขอ allowlist ผ่านแบบฟอร์มของ Anaconda Support แล้วเมื่อ 27 กันยายน 2026 และหน้าเว็บยืนยันว่า `Your request was successfully submitted.` ระหว่างรออนุมัติ หน้าเว็บและระบบ Login ใช้งานได้ แต่การค้นหาสถิติจาก Leetify จะยังแสดงข้อผิดพลาดการเชื่อมต่อ

## ย้อนกลับ

หากเว็บใหม่มีปัญหา ให้เปลี่ยน WSGI และ Static Files Mapping กลับไปยังโฟลเดอร์เดิม แล้ว Reload ก่อน จากนั้นค่อยตรวจข้อมูลที่เกิดขึ้นในฐานข้อมูลระหว่างการสลับ ห้ามลบโฟลเดอร์ใหม่หรือฐานข้อมูลระหว่างตรวจสอบ
