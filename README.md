# CS2 Stat Tracker

เว็บ Django สำหรับดูโปรไฟล์ ประวัติแมตช์ และเปรียบเทียบผู้เล่นจาก Leetify API พร้อมบัญชีผู้ใช้และประวัติการค้นหา

## เริ่มใช้งานบน Windows

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv\Scripts\python.exe manage.py migrate
npm install
npm run build
.venv\Scripts\python.exe manage.py runserver
```

เปิด `http://127.0.0.1:8000/` แล้วสมัครสมาชิก หากมีบัญชีจาก Flask เดิม ให้รัน `.venv\Scripts\python.exe manage.py import_flask_users` หลัง `migrate` คำสั่งนี้นำเข้าบัญชีจาก `instance/users.db` โดยเก็บรหัสผ่านเดิมและข้ามบัญชีที่มีอยู่แล้ว (รองรับ hash แบบ `pbkdf2:sha256` ของ Werkzeug)

ปรับ `.env` ก่อนนำเว็บขึ้นเซิร์ฟเวอร์: ตั้ง `DEBUG=0`, `SECRET_KEY` ที่สุ่มใหม่, `ALLOWED_HOSTS` เป็นโฮสต์จริง และใส่ `LEETIFY_API_KEY` หากมี ห้ามเผยแพร่ `.env` หรือฐานข้อมูลผู้ใช้

## โครงสร้างและสิ่งที่เรียน

| หัวข้อ | ตำแหน่ง |
| --- | --- |
| Django Model / CRUD | `tracker/models.py`, `tracker/views.py`, `templates/history*.html` |
| Forms / Login / Logout | `tracker/forms.py`, `tracker/urls.py`, `templates/login.html`, `templates/register.html` |
| Leetify JSON API | `leetify_client.py` |
| Tailwind layout, flexbox, typography, form, menu, utilities | `templates/`, `static/input.css`, `static/output.css` |
| HTMX partial update | `templates/profile.html`, `templates/partials/profile_result.html` |
| Alpine state / filter / modal | `templates/history.html`, `templates/partials/profile_result.html` |
| JavaScript พื้นฐาน | `static/app.js` (คัดลอก Steam64 ID) |

การค้นหาโปรไฟล์สำเร็จจะสร้างประวัติ (Create) หน้า `/history/` แสดงและกรองรายการ (Read) ผู้ใช้แก้บันทึกส่วนตัว (Update) และลบรายการด้วย POST (Delete) ได้เฉพาะของตนเอง การค้นหาแบบ HTMX ส่งฟอร์มและแทนเฉพาะผลลัพธ์โดยไม่รีโหลดหน้า; หาก JavaScript ไม่ทำงาน ฟอร์มยังส่งแบบปกติ

ประวัติเก็บ **คำค้นที่ผู้ใช้ป้อนเอง** และบันทึกส่วนตัวเท่านั้น ข้อมูลสถิติจาก Leetify ไม่ถูกบันทึกลงฐานข้อมูล และดึงใหม่ตามคำขอ เพื่อให้ตรงกับ [แนวทางนักพัฒนา Leetify](https://leetify.com/blog/leetify-api-developer-guidelines/). หน้าเว็บแสดงตรา “Data Provided by Leetify” และลิงก์กลับไปยังโปรไฟล์ต้นทาง

## ทดสอบ

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test tracker
```

ขั้นตอน deploy และแก้ Static Files บน PythonAnywhere อยู่ใน [`deploy/PYTHONANYWHERE.md`](deploy/PYTHONANYWHERE.md)

API รองรับ Steam64 ID, Steam profile URL, Steam2/Steam3 ID และ Steam vanity URL/ชื่อ Vanity; **ชื่อเล่นใน Leetify ที่ไม่ใช่ Vanity URL ค้นหาไม่ได้** เพราะ endpoint ที่ใช้รับ Steam ID เป็นหลัก โปรไฟล์ที่ตั้งเป็นส่วนตัวอาจไม่มีข้อมูลให้แสดง
