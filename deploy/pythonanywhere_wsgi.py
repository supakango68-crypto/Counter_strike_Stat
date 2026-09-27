"""Paste into /var/www/cs2ttracker_pythonanywhere_com_wsgi.py on PythonAnywhere."""
import os
import sys
from pathlib import Path

project_home = Path("/home/cs2ttracker/cs2-stat-tracker")
if not (project_home / "manage.py").is_file():
    raise RuntimeError(f"Django project not found: {project_home}")

sys.path.insert(0, str(project_home))
os.environ["DJANGO_SETTINGS_MODULE"] = "cs2stats.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
