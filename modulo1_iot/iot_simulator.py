"""
BerryMind — Modulo 1: Simulador IoT
====================================
Simula sensores de campo para cultivos de arándanos en Valle de Sotaquirá.

Uso:
    python iot_simulator.py                    # Modo normal
    python iot_simulator.py --mode helada      # Simular helada
    python iot_simulator.py --mode sequia      # Simular sequía
    python iot_simulator.py --mode lluvia      # Simular lluvia intensa
    python iot_simulator.py --server           # Iniciar servidor HTTP en puerto 5001

El servidor expone:
    GET  /sensors          → Datos actuales en JSON
    GET  /sensors/history  → Historial de últimas N lecturas
    POST /set_mode         → Cambiar modo de simulación (body: {"mode": "helada"})
"""

import json
import random
import math
import time
import threading
import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# ── Cargar configuración ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "sensor_config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SENSORS = CONFIG["sensors"]
MODES   = CONFIG["simulation_modes"]

# ── Estado global compartido ─────────────────────────────────────────────────
state = {
    "mode": "normal",
    "current_data": {},
    "history": [],          # lista de últimas 288 lecturas (24h a 5min)
    "alerts": [],
    "step": 0,              # tick de simulación (0-287 = ciclo de 24h)
    "running": True,
}
_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _get_time_factor(step: int) -> dict:
    """
    Genera factores diurnos realistas basados en el paso de simulación.
    step 0 = medianoche, step 144 = mediodía (ciclo de 288 pasos = 24h)
    """
    hour_fraction = (step / 288) * 2 * math.pi          # 0 → 2π en 24h
    # Temperatura: máximo al mediodía, mínimo al amanecer
    temp_factor   = math.sin(hour_fraction - math.pi / 2)  # -1 a +1
    # Luz: solo hay luz de día (pasos 72–216 aprox. = 6am–6pm)
    light_factor  = max(0, math.sin(hour_fraction))
    return {"temp": temp_factor, "light": light_factor}


def generate_reading(mode: str = "normal", step: int = 0) -> dict:
    """Genera una lectura coherente de todos los sensores según el modo."""
    m   = MODES[mode]
    tf  = _get_time_factor(step)
    now = datetime.now()

    # Temperatura con ciclo diurno
    temp = m["temp_base"] + tf["temp"] * m["temp_variation"] + random.gauss(0, 0.3)
    temp = round(_clamp(temp, -10, 45), 2)

    # Humedad relativa (inversamente proporcional a temperatura)
    hr_base   = m["humidity_base"] - tf["temp"] * 8
    hum_rel   = round(_clamp(hr_base + random.gauss(0, 2), 20, 100), 1)

    # pH del suelo (relativamente estable, ruido pequeño)
    ph_base   = 4.9 + random.gauss(0, 0.08)
    if mode == "sequia":
        ph_base += 0.3      # suelo seco tiende a alcalinizarse
    ph        = round(_clamp(ph_base, 3.0, 8.0), 2)

    # Conductividad eléctrica
    cond_base = 1.1
    if mode == "sequia":
        cond_base = 2.8     # concentración de sales en sequía
    elif mode == "lluvia":
        cond_base = 0.4     # dilución en lluvia
    cond      = round(_clamp(cond_base + random.gauss(0, 0.05), 0.0, 5.0), 2)

    # Luminosidad (solo de día)
    lux_base  = tf["light"] * 45000
    if mode == "lluvia":
        lux_base *= 0.35    # nubes reducen la luz
    lux       = round(_clamp(lux_base + random.gauss(0, 500), 0, 100000), 0)

    # Humedad del suelo
    soil_base = m["soil_moisture_base"]
    if mode == "lluvia":
        soil_base = min(soil_base + step * 0.1, 100)   # sube progresivamente
    soil_hum  = round(_clamp(soil_base + random.gauss(0, 1.5), 0, 100), 1)

    reading = {
        "timestamp":         now.isoformat(),
        "timestamp_human":   now.strftime("%Y-%m-%d %H:%M:%S"),
        "mode":              mode,
        "temperatura":       temp,
        "humedad_relativa":  hum_rel,
        "ph_suelo":          ph,
        "conductividad":     cond,
        "luminosidad":       int(lux),
        "humedad_suelo":     soil_hum,
    }

    # ── Calcular alertas ────────────────────────────────────────────────────
    alerts = []
    for sensor_key, val in [
        ("temperatura",      temp),
        ("humedad_relativa", hum_rel),
        ("ph_suelo",         ph),
        ("conductividad",    cond),
        ("humedad_suelo",    soil_hum),
    ]:
        cfg = SENSORS[sensor_key]
        if val <= cfg["critical_min"] or val >= cfg["critical_max"]:
            level = "CRÍTICO"
        elif val <= cfg["alert_min"] or val >= cfg["alert_max"]:
            level = "ALERTA"
        else:
            level = "OK"

        if level != "OK":
            alerts.append({
                "sensor": sensor_key,
                "value":  val,
                "unit":   cfg["unit"],
                "level":  level,
                "msg":    f"{cfg['description']}: {val}{cfg['unit']} [{level}]"
            })

    reading["alerts"]      = alerts
    reading["alert_count"] = len(alerts)
    reading["status"]      = "CRÍTICO" if any(a["level"] == "CRÍTICO" for a in alerts) \
                             else ("ALERTA" if alerts else "NORMAL")

    return reading


def load_historical_data(hours: int = 24, mode: str = "normal") -> list:
    """Genera datos históricos simulados para las últimas N horas."""
    history = []
    steps_per_hour = 12   # cada 5 minutos
    total_steps    = hours * steps_per_hour
    base_time      = datetime.now() - timedelta(hours=hours)

    for i in range(total_steps):
        step_offset = (288 - total_steps + i) % 288
        reading = generate_reading(mode=mode, step=step_offset)
        ts = base_time + timedelta(minutes=i * 5)
        reading["timestamp"]       = ts.isoformat()
        reading["timestamp_human"] = ts.strftime("%Y-%m-%d %H:%M:%S")
        history.append(reading)

    return history


# ─────────────────────────────────────────────────────────────────────────────
# LOOP DE SIMULACIÓN (hilo en segundo plano)
# ─────────────────────────────────────────────────────────────────────────────

def simulation_loop(interval: int = 5):
    """Genera lecturas periódicas y las almacena en el estado global."""
    print(f"[IoT] Simulador iniciado. Intervalo: {interval}s. Modo: {state['mode']}")
    while state["running"]:
        with _lock:
            reading = generate_reading(mode=state["mode"], step=state["step"])
            state["current_data"] = reading
            state["alerts"]       = reading["alerts"]
            state["history"].append(reading)
            if len(state["history"]) > 288:   # mantener solo 24h
                state["history"].pop(0)
            state["step"] = (state["step"] + 1) % 288

        # Guardar en archivo JSON para que el dashboard pueda leerlo
        output_file = BASE_DIR / "latest_reading.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(reading, f, indent=2, ensure_ascii=False)

        if reading["status"] != "NORMAL":
            level_color = "\033[91m" if reading["status"] == "CRÍTICO" else "\033[93m"
            reset = "\033[0m"
            print(f"{level_color}[IoT] [{reading['status']}] T={reading['temperatura']}°C  "
                  f"HR={reading['humedad_relativa']}%  pH={reading['ph_suelo']}  "
                  f"HumedadSuelo={reading['humedad_suelo']}%{reset}")
        else:
            print(f"[IoT] T={reading['temperatura']}°C  HR={reading['humedad_relativa']}%  "
                  f"pH={reading['ph_suelo']}  HumedadSuelo={reading['humedad_suelo']}%  "
                  f"Modo={reading['mode']}")

        time.sleep(interval)


# ─────────────────────────────────────────────────────────────────────────────
# SERVIDOR HTTP (Flask)
# ─────────────────────────────────────────────────────────────────────────────

def start_server(port: int = 5001):
    """Inicia el servidor Flask con los endpoints del simulador IoT."""
    try:
        from flask import Flask, jsonify, request as flask_request
    except ImportError:
        print("[ERROR] Flask no está instalado. Ejecuta: pip install flask")
        sys.exit(1)

    app = Flask("BerryMind-IoT")

    # Silenciar logs de Flask para una salida más limpia
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    @app.route("/sensors", methods=["GET"])
    def get_current():
        with _lock:
            return jsonify(state["current_data"])

    @app.route("/sensors/history", methods=["GET"])
    def get_history():
        n = flask_request.args.get("n", 50, type=int)
        with _lock:
            return jsonify(state["history"][-n:])

    @app.route("/set_mode", methods=["POST"])
    def set_mode():
        data    = flask_request.get_json(force=True)
        new_mode = data.get("mode", "normal")
        if new_mode not in MODES:
            return jsonify({"error": f"Modo inválido. Opciones: {list(MODES.keys())}"}), 400
        with _lock:
            state["mode"] = new_mode
        print(f"[IoT] Modo cambiado a: {new_mode}")
        return jsonify({"ok": True, "mode": new_mode})

    @app.route("/status", methods=["GET"])
    def get_status():
        with _lock:
            return jsonify({
                "running":    state["running"],
                "mode":       state["mode"],
                "step":       state["step"],
                "history_len": len(state["history"]),
                "last_status": state["current_data"].get("status", "DESCONOCIDO"),
            })

    print(f"[IoT] Servidor HTTP en http://localhost:{port}")
    print(f"[IoT] Endpoints: /sensors  /sensors/history  /set_mode  /status")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BerryMind IoT Simulator — Cultivo de Arándanos Valle de Sotaquirá"
    )
    parser.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="normal",
        help="Modo de simulación inicial"
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Iniciar servidor HTTP en puerto 5001"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Intervalo entre lecturas en segundos (default: 5)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Generar una lectura de prueba y salir"
    )
    args = parser.parse_args()

    if args.test:
        print("\n=== TEST: Generando una lectura de prueba ===")
        for mode in MODES.keys():
            reading = generate_reading(mode=mode, step=72)
            print(f"\nModo '{mode}':")
            print(json.dumps(reading, indent=2, ensure_ascii=False))
        print("\n✅ Test completado.")
        return

    state["mode"] = args.mode

    # Precargar historial de 24h simuladas
    print("[IoT] Precargando historial de 24h...")
    state["history"] = load_historical_data(hours=24, mode=args.mode)
    print(f"[IoT] Historial cargado: {len(state['history'])} registros")

    # Iniciar loop de simulación en hilo separado
    sim_thread = threading.Thread(
        target=simulation_loop,
        args=(args.interval,),
        daemon=True
    )
    sim_thread.start()

    if args.server:
        port = int(os.getenv("IOT_SERVER_PORT", 5001))
        start_server(port=port)
    else:
        print("[IoT] Corriendo sin servidor HTTP. Presiona Ctrl+C para detener.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[IoT] Simulador detenido.")
            state["running"] = False


if __name__ == "__main__":
    main()
