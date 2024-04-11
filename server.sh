#!/bin/bash
cd /home/ubuntu/gestor-planillas-drep
source venv/bin/activate
exec python manage.py runserver 0.0.0.0:80
