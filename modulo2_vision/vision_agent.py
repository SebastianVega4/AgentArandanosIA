"""
BerryMind — Modulo 2: Agente de Visión Artificial
==================================================
Clasifica el estado de hojas de arándano en 4 categorías:
  - SANO:               Hoja verde, sin manchas, turgente.
  - ESTRÉS / CLOROSIS:   Amarillamiento, falta de nutrientes o estrés hídrico.
  - INFECCIÓN TEMPRANA:  Pequeñas manchas pardas/rojizas (inicio de Botrytis).
  - BOTRYTIS (AVANZADO): Manchas grises/pardas extensas de Botrytis cinerea.

Estrategia dual:
  1. Si hay modelo YOLOv8 fine-tuneado disponible → lo usa
  2. Si no → usa análisis de color HSV (heurístico) mejorado.
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime

# Intentar importar OpenCV y PIL
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[Vision] OpenCV no disponible. Instala: pip install opencv-python")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

BASE_DIR = Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────────────
# ANALIZADOR HSV (No requiere GPU ni modelo entrenado)
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_hsv(image_path: str) -> dict:
    """
    Análisis de color en espacio HSV optimizado para fitopatología de arándano.
    
    Lógica basada en colorimetría de lesiones:
    - Verde: H(35-85), S(>30), V(>30)  -> SANO
    - Amarillo: H(20-35), S(>40)       -> CLOROSIS
    - Marrón/Rojo: H(<20 o >160), S(>40) -> INFECCIÓN TEMPRANA (Necrosis inicial)
    - Gris/Pardo: S(<30), V(40-70)     -> BOTRYTIS AVANZADO (Micelio)
    """
    if not CV2_AVAILABLE:
        return _fallback_pil_analysis(image_path)

    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    # Redimensionar para uniformidad
    img_bgr = cv2.resize(img_bgr, (224, 224))
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    h_channel = img_hsv[:, :, 0].flatten().astype(float)
    s_channel = img_hsv[:, :, 1].flatten().astype(float) / 255.0
    v_channel = img_hsv[:, :, 2].flatten().astype(float) / 255.0

    # Máscara para excluir fondo (típicamente oscuro o muy brillante)
    mask = (v_channel > 0.15) & (v_channel < 0.90) & (s_channel > 0.05)
    if mask.sum() < 100:
        return {"estado": "Sano", "confianza": 0.50, "detalles": "Imagen no conclusiva (posible fondo).", "color_stats": {}}

    h_vals = h_channel[mask]
    s_vals = s_channel[mask]
    v_vals = v_channel[mask]

    # Porcentajes por rangos fitopatológicos (OpenCV H: 0-179)
    pct_green   = float(np.mean((h_vals >= 35) & (h_vals <= 85) & (s_vals > 0.30)))
    pct_yellow  = float(np.mean((h_vals >= 20) & (h_vals < 35) & (s_vals > 0.25)))
    pct_reddish = float(np.mean(((h_vals < 15) | (h_vals > 165)) & (s_vals > 0.30)))
    pct_gray    = float(np.mean((s_vals < 0.25) & (v_vals > 0.20) & (v_vals < 0.75)))
    pct_brown   = float(np.mean((h_vals < 20) & (s_vals > 0.20) & (v_vals < 0.50)))

    # ── Lógica de Clasificación 4-Estados ─────────────────────────────────
    scores = {
        "Sano":               pct_green * 2.0 + 0.1,
        "Estrés / Clorosis":  pct_yellow * 2.5 + (1.0 - pct_green) * 0.5,
        "Infección Temprana": pct_reddish * 3.0 + pct_brown * 1.5,
        "Botrytis (Avanzado)": pct_gray * 3.5 + pct_brown * 2.0
    }

    predicted_class = max(scores, key=scores.get)
    total_score     = sum(scores.values()) + 1e-6
    confidence      = round(scores[predicted_class] / total_score, 2)
    confidence      = min(max(confidence, 0.55), 0.98)

    # ── Generación de detalles descriptivos ───────────────────────────────
    details_map = {
        "Sano": (
            f"Follaje con coloración verde óptima ({pct_green*100:.1f}%). "
            "No se observan anomalías cromáticas significativas. Mantener plan de nutrición actual."
        ),
        "Estrés / Clorosis": (
            f"Detección de amarillamiento ({pct_yellow*100:.1f}%) sin presencia de necrosis. "
            "Sugerencia: Revisar niveles de Nitrógeno y Magnesio, y verificar pH del sustrato."
        ),
        "Infección Temprana": (
            f"Alerta: Se detectan puntos necróticos iniciales ({pct_reddish*100:.1f}%). "
            "Posible incubación de Botrytis cinerea. Se recomienda aplicación preventiva de extracto de cítricos o Trichoderma."
        ),
        "Botrytis (Avanzado)": (
            f"Estado Crítico: Presencia clara de moho gris y necrosis extendida ({pct_gray*100:.1f}%). "
            "Acción: Poda de saneamiento inmediata y aplicación de fungicida sistémico (ej. Fenhexamid)."
        ),
    }

    color_stats = {
        "pct_verde":    round(pct_green * 100, 1),
        "pct_amarillo": round(pct_yellow * 100, 1),
        "pct_rojo_marron": round((pct_reddish + pct_brown) * 100, 1),
        "pct_gris":     round(pct_gray * 100, 1),
    }

    return {
        "estado":       predicted_class,
        "confianza":    confidence,
        "detalles":     details_map[predicted_class],
        "color_stats":  color_stats,
        "metodo":       "HSV_heuristico_v2",
        "timestamp":    datetime.now().isoformat(),
    }


def _fallback_pil_analysis(image_path: str) -> dict:
    """Análisis básico con PIL cuando OpenCV no está disponible."""
    if not PIL_AVAILABLE:
        return {"estado": "Sano", "confianza": 0.50, "detalles": "Sin librerías de visión.", "color_stats": {}}

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=float)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # Heurística simple RGB
    pct_green = float(np.mean((g > r * 1.1) & (g > b * 1.1)))
    pct_red   = float(np.mean((r > g * 1.2) & (r > b * 1.1)))
    
    if pct_green > 0.4:  estado = "Sano"
    elif pct_red > 0.15: estado = "Infección Temprana"
    else:                estado = "Estrés / Clorosis"

    return {
        "estado": estado, "confianza": 0.65, "detalles": "Análisis PIL básico.",
        "color_stats": {"pct_verde": round(pct_green*100,1)}, "metodo": "PIL_basico"
    }


# ─────────────────────────────────────────────────────────────────────────────
# CARGADOR DE MODELO YOLOV8 (Opcional)
# ─────────────────────────────────────────────────────────────────────────────

_yolo_model = None
CLASS_NAMES  = ["Sano", "Estrés / Clorosis", "Infección Temprana", "Botrytis (Avanzado)"]

def _load_yolo_model():
    """Intenta cargar el modelo YOLOv8 si está disponible."""
    global _yolo_model
    model_path = BASE_DIR / "modelo" / "best.pt"

    if not model_path.exists():
        return False

    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(str(model_path))
        _yolo_model.to("cpu")
        print("[Vision] Modelo YOLOv8 cargado.")
        return True
    except Exception as e:
        print(f"[Vision] Error YOLOv8: {e}")
        return False


def _analyze_with_yolo(image_path: str) -> dict:
    """Clasifica con el modelo YOLOv8."""
    results = _yolo_model(image_path, verbose=False)
    probs   = results[0].probs

    top_idx   = int(probs.top1)
    top_conf  = float(probs.top1conf)
    class_name = CLASS_NAMES[top_idx] if top_idx < len(CLASS_NAMES) else f"Clase_{top_idx}"

    return {
        "estado":      class_name,
        "confianza":   round(top_conf, 2),
        "detalles":    f"Detección neuronal (YOLOv8): {class_name}.",
        "color_stats": {},
        "metodo":      "YOLOv8_finetuned",
        "timestamp":   datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# API PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────

def analyze_leaf(image_path: str) -> dict:
    """Analiza una imagen de hoja de arándano y retorna su estado fitosanitario."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

    if _yolo_model is not None:
        try:
            return _analyze_with_yolo(image_path)
        except:
            pass

    return _analyze_hsv(image_path)


def generate_test_images():
    """Genera imágenes sintéticas de prueba con colores representativos."""
    if not CV2_AVAILABLE: return
    output_dir = BASE_DIR / "test_images"
    output_dir.mkdir(exist_ok=True)

    specs = {
        "sano.jpg":     (60, 200, 100),
        "clorosis.jpg": (30, 180, 150),
        "temprano.jpg": (5,  150, 80),
        "botrytis.jpg": (10, 40,  100)
    }

    for filename, (h, s, v) in specs.items():
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        img[:] = [h, s, v]
        mask = np.zeros((224, 224), dtype=np.uint8)
        cv2.ellipse(mask, (112, 112), (80, 100), 0, 0, 360, 255, -1)
        bgr = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        res = cv2.bitwise_and(bgr, bgr, mask=mask)
        cv2.imwrite(str(output_dir / filename), res)


def main():
    parser = argparse.ArgumentParser(description="BerryMind Vision Agent")
    parser.add_argument("--image", help="Ruta a la imagen")
    parser.add_argument("--test",  action="store_true", help="Correr pruebas")
    args = parser.parse_args()

    _load_yolo_model()
    if args.test:
        generate_test_images()
        test_dir = BASE_DIR / "test_images"
        for img in test_dir.glob("*.jpg"):
            res = analyze_leaf(str(img))
            print(f"[{img.name}] -> {res['estado']} ({res['confianza']:.0%})")
    elif args.image:
        print(json.dumps(analyze_leaf(args.image), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
