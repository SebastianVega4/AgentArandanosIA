"""
BerryMind — Simulador de Alertas WhatsApp (Capa 4)
==================================================
Simula el envío de notificaciones push/WhatsApp al productor.
"""

import time
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
WHATSAPP_LOG = ROOT / "logs" / "whatsapp_alerts.json"

def send_whatsapp_alert(message: str, priority: str = "NORMAL"):
    """
    Simula el envío de un mensaje de WhatsApp guardándolo en un log persistente.
    """
    alert = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "to": "+57 310 BERRY-AID",
        "message": message,
        "priority": priority,
        "status": "SENT_SIMULATED"
    }
    
    # Asegurar que el directorio existe
    WHATSAPP_LOG.parent.mkdir(exist_ok=True)
    
    try:
        alerts = []
        if WHATSAPP_LOG.exists():
            with open(WHATSAPP_LOG, "r", encoding="utf-8") as f:
                alerts = json.load(f)
        
        alerts.append(alert)
        
        # Mantener últimos 20 mensajes
        if len(alerts) > 20:
            alerts = alerts[-20:]
            
        with open(WHATSAPP_LOG, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2, ensure_ascii=False)
            
        print(f"\n[WhatsApp Alert] 📱 {message} (Prioridad: {priority})")
        return True
    except Exception as e:
        print(f"[WhatsApp Alert] Error al simular envío: {e}")
        return False

def format_whatsapp_message(state: dict) -> str:
    """Genera un mensaje formateado según el estado del sistema."""
    irrigation = state.get("irrigation_command")
    vision = state.get("vision_result")
    sensor = state.get("sensor_data", {})
    
    msg = "🫐 BerryMind Alerta:\n"
    
    if irrigation:
        msg += f"🚨 ACCIÓN: {irrigation['accion']}\n📍 Zonas: {irrigation['zonas']}\n📝 {irrigation['mensaje']}\n"
    
    if vision and vision.get("estado") == "Botrytis":
        msg += f"⚠️ FITOSANITARIO: Se detectó Botrytis ({vision['confianza']:.0%}). Favor revisar manual de tratamiento en el Dashboard.\n"
        
    if not irrigation and not (vision and vision.get("estado") == "Botrytis"):
        msg = f"🫐 BerryMind Reporte: El cultivo en Sotaquirá se encuentra en estado {sensor.get('status', 'NORMAL')}. Todo bajo control."
        
    return msg
