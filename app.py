from flask import Flask, render_template, request, jsonify
from bot_engine import BotEngine

app = Flask(__name__)
bot = BotEngine()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "running": bot.running,
        "message": bot.status_message,
        "logs": bot.logs[-30:],
        "services": bot.services_status
    })


@app.route("/api/check-services", methods=["POST"])
def check_services():
    """Abre Chrome, pide captcha y actualiza estados."""
    if bot.running:
        return jsonify({"ok": False, "error": "Hay un proceso en ejecución"}), 400

    statuses = bot.check_services()
    return jsonify({"ok": True, "services": statuses})


@app.route("/api/start", methods=["POST"])
def start():
    data = request.get_json() or {}
    service = data.get("service")
    video_url = (data.get("video_url") or "").strip()

    if not service or service not in BotEngine.SERVICES:
        return jsonify({"ok": False, "error": "Servicio no válido"}), 400
    if not video_url or "tiktok.com" not in video_url.lower():
        return jsonify({"ok": False, "error": "URL de TikTok no válida"}), 400
    if bot.running:
        return jsonify({"ok": False, "error": "Ya hay un proceso en ejecución"}), 400

    bot.start_service(service, video_url)
    return jsonify({"ok": True, "message": "Proceso iniciado"})


@app.route("/api/stop", methods=["POST"])
def stop():
    bot.stop()
    return jsonify({"ok": True})


@app.route("/api/close-browser", methods=["POST"])
def close_browser():
    bot.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  TikTok Dashboard  →  http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
