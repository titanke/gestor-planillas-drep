#!/bin/bash
cd /home/admin/gestor-planillas-drep
source venv/bin/activate
exec python manage.py runserver 0.0.0.0:8000
