# Proyecto Django REST - Configuración Básica

Este proyecto es una base para desarrollar APIs utilizando **Python**, **Django** y **Django REST Framework**.

---

## Requisitos

- Python 3.12 o superior
- pip
- Cuenta en Twilio (opcional, para webhooks)
- [ngrok](https://ngrok.com/) (opcional, para exponer el servidor local)

---

## 1. Crear entorno virtual

```bash
python -m venv venv
```

Activar el entorno:

- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

---

## 2. Instalar dependencias

```bash
pip install django djangorestframework
```

Guardar dependencias:

```bash
pip freeze > requirements.txt
```

---

## 3. Crear proyecto y aplicación

```bash
django-admin startproject myproject .
python manage.py startapp api
```

Agregar en `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    'rest_framework',
    'api',
]
```

---

## 4. Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 5. Crear superusuario

```bash
python manage.py createsuperuser
```

---

## 6. Ejecutar el servidor

```bash
python manage.py runserver
```

Accede desde: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 7. Usar ngrok para pruebas externas (opcional)

```bash
ngrok http 8000
```

Esto genera una URL pública como:

```
https://abcd1234.ngrok.io
```

---

## 8. Configurar webhook en Twilio (opcional)

Usa la URL generada por ngrok para configurar un webhook en tu número de Twilio, por ejemplo:

```
https://abcd1234.ngrok.io/api/webhook/
```

---

## 9. Ejecutar el proyecto completo

```bash
python manage.py runserver
```

---

## Fin

Tu entorno Django REST está listo para comenzar 🚀