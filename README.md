# TikTok Dashboard

Panel de control web propio para automatizar métricas de TikTok usando Zefoy por detrás.

En lugar de usar la interfaz de zefoy.com, tienes **tu propia página** moderna y limpia.

---

## Características

- Interfaz web propia (no usas la página de Zefoy)
- Detección automática de servicios online / offline
- Selección visual de servicio
- Logs en tiempo real
- Control de inicio / parada del bot
- Chrome se abre solo cuando lo necesitas

---

## Requisitos

- Python 3.9+
- Google Chrome instalado

---

## Instalación

```bash
cd tiktok-dashboard
pip install -r requirements.txt
```

---

## Uso

1. Arranca el servidor:
```bash
python app.py
```

2. Abre en tu navegador:
```
http://127.0.0.1:5000
```

3. Flujo de uso:
   - Pega la URL del video de TikTok
   - Pulsa **Comprobar servicios** → se abrirá Chrome y tendrás que resolver el captcha
   - El panel mostrará qué servicios están disponibles
   - Selecciona un servicio ONLINE
   - Pulsa **Iniciar**
   - El bot trabajará en segundo plano (puedes ver los logs)
   - Usa **Detener** cuando quieras parar

---

## Estructura

```
tiktok-dashboard/
├── app.py              # Servidor Flask
├── bot_engine.py       # Lógica del bot (Selenium)
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

---

## Nota

Este proyecto sigue usando Zefoy como backend de envío. La página propia es solo la interfaz de control.

Uso exclusivamente educativo.
