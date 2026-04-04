"""
BerryMind — Modulo 2: Agente de Visión Artificial
==================================================
Clasifica el estado de hojas de arándano en 3 categorías:
  - SANO:     Hoja verde, sin manchas, turgente
  - ALERTA:   Amarillamiento, clorosis, estrés hídrico
  - BOTRYTIS: Manchas grises/pardas de Botrytis cinerea (moho gris)

Estrategia dual:
  1. Si hay modelo YOLOv8 fine-tuneado disponible → lo usa
  2. Si no → usa análisis de color HSV (heurístico) que funciona sin GPU

Uso:
    python vision_agent.py --test                      # Clasifica imágenes de prueba
    python vision_agent.py --image ruta/hoja.jpg       # Clasifica una imagen específica

API:
    from vision_agent import analyze_leaf
    result = analyze_leaf("hoja.jpg")
    # → {"estado": "Sano", "confianza": 0.91, "detalles": "...", "color_stats": {...}}
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
    Análisis de color en espacio HSV para detectar condición de la hoja.
    
    Lógica basada en fitopatología:
    - Verde saturado (H: 35-85, S>50, V>50)  → SANO
    - Amarillo/marrón (H: 20-35 o S<30)       → ALERTA
    - Gris/musgo (H: 0-20, S: 10-30, V: 30-60)→ BOTRYTIS
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

    # Calcular distribución de H en la hoja (excluir fondo muy oscuro o muy claro)
    mask = (v_channel > 0.15) & (v_channel < 0.95) & (s_channel > 0.1)
    if mask.sum() < 100:
        # Imagen casi vacía o fondo
        return {"estado": "Sano", "confianza": 0.55, "detalles":
                "Imagen con poco contraste, análisis limitado.", "color_stats": {}}

    h_vals  = h_channel[mask]
    s_vals  = s_channel[mask]
    v_vals  = v_channel[mask]

    # Porcentaje de píxeles en cada rango de color (OpenCV: H en 0-179)
    pct_green  = float(np.mean((h_vals >= 35) & (h_vals <= 85) & (s_vals > 0.35)))
    pct_yellow = float(np.mean((h_vals >= 20) & (h_vals < 35) | ((s_vals < 0.25) & (v_vals > 0.5))))
    pct_gray   = float(np.mean((s_vals < 0.2) & (v_vals > 0.25) & (v_vals < 0.70)))
    pct_brown  = float(np.mean((h_vals < 20) & (s_vals > 0.2) & (v_vals < 0.55)))

    mean_h = float(np.mean(h_vals))
    mean_s = float(np.mean(s_vals))
    mean_v = float(np.mean(v_vals))

    color_stats = {
        "pct_verde":    round(pct_green * 100, 1),
        "pct_amarillo": round(pct_yellow * 100, 1),
        "pct_gris":     round(pct_gray * 100, 1),
        "pct_marron":   round(pct_brown * 100, 1),
        "h_promedio":   round(mean_h, 1),
        "s_promedio":   round(mean_s, 3),
        "v_promedio":   round(mean_v, 3),
    }

    # ── Lógica de clasificación ────────────────────────────────────────────
    botrytis_score = pct_gray * 2.0 + pct_brown * 0.8
    alerta_score   = pct_yellow * 1.8 + (1 - pct_green) * 0.5
    sano_score     = pct_green * 2.0 + mean_s * 0.5

    scores = {
        "Botrytis": botrytis_score,
        "Alerta":   alerta_score,
        "Sano":     sano_score,
    }

    predicted_class = max(scores, key=scores.get)
    total_score     = sum(scores.values()) + 1e-6
    confidence      = round(scores[predicted_class] / total_score, 2)
    confidence      = min(max(confidence, 0.52), 0.97)

    # ── Generación de detalles descriptivos ───────────────────────────────
    details_map = {
        "Sano": (
            f"La hoja presenta coloración verde saludable ({pct_green*100:.0f}% de área verde). "
            f"Saturación de color normal ({mean_s:.2f}), sin signos claros de enfermedad. "
            f"Se recomienda monitoreo rutinario."
        ),
        "Alerta": (
            f"Se detecta amarillamiento en aproximadamente {pct_yellow*100:.0f}% del área foliar. "
            f"Posible clorosis, deficiencia de hierro/manganeso o estrés hídrico. "
            f"Se recomienda verificar pH del suelo (óptimo 4.5-5.5) y revisar riego."
        ),
        "Botrytis": (
            f"Se detectan zonas grises/pardas ({pct_gray*100:.0f}% gris + {pct_brown*100:.0f}% marrón) "
            f"compatibles con Botrytis cinerea (moho gris). "
            f"ACCIÓN INMEDIATA: aplicar fungicida (Iprodione o Fenhexamid) y mejorar ventilación."
        ),
    }

    return {
        "estado":       predicted_class,
        "confianza":    confidence,
        "detalles":     details_map[predicted_class],
        "color_stats":  color_stats,
        "metodo":       "HSV_heuristico",
        "timestamp":    datetime.now().isoformat(),
    }


def _fallback_pil_analysis(image_path: str) -> dict:
    """Análisis básico con PIL cuando OpenCV no está disponible."""
    if not PIL_AVAILABLE:
        return {
            "estado": "Sano", "confianza": 0.60,
            "detalles": "OpenCV y PIL no disponibles. Resultado simulado.",
            "color_stats": {}, "metodo": "fallback_simulado"
        }

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=float)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    pct_green  = float(np.mean((g > r * 1.1) & (g > b * 1.1) & (g > 50)))
    pct_yellow = float(np.mean((r > 150) & (g > 130) & (b < 80)))
    pct_gray   = float(np.mean((np.abs(r - g) < 30) & (np.abs(g - b) < 30) & (r < 180) & (r > 60)))

    if pct_green > 0.35:
        estado, conf = "Sano", round(0.55 + pct_green * 0.4, 2)
    elif pct_yellow > 0.20:
        estado, conf = "Alerta", round(0.55 + pct_yellow * 0.4, 2)
    else:
        estado, conf = "Botrytis", round(0.55 + pct_gray * 0.4, 2)

    return {
        "estado": estado, "confianza": min(conf, 0.97),
        "detalles": f"Análisis PIL básico. Verde: {pct_green*100:.0f}%, Amarillo: {pct_yellow*100:.0f}%",
        "color_stats": {"pct_verde": round(pct_green*100, 1)},
        "metodo": "PIL_basico"
    }


# ─────────────────────────────────────────────────────────────────────────────
# CARGADOR DE MODELO YOLOV8 (Opcional)
# ─────────────────────────────────────────────────────────────────────────────

_yolo_model = None
CLASS_NAMES  = ["Sano", "Alerta", "Botrytis"]

def _load_yolo_model():
    """Intenta cargar el modelo YOLOv8 si está disponible."""
    global _yolo_model
    model_path = BASE_DIR / "modelo" / "best.pt"

    if not model_path.exists():
        return False

    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(str(model_path))
        _yolo_model.to("cpu")   # Forzar CPU
        print("[Vision] Modelo YOLOv8 personalizado cargado.")
        return True
    except Exception as e:
        print(f"[Vision] No se pudo cargar YOLOv8: {e}. Usando análisis HSV.")
        return False


def _analyze_with_yolo(image_path: str) -> dict:
    """Clasifica con el modelo YOLOv8 fine-tuneado."""
    results = _yolo_model(image_path, verbose=False)
    probs   = results[0].probs

    top_idx   = int(probs.top1)
    top_conf  = float(probs.top1conf)
    class_name = CLASS_NAMES[top_idx] if top_idx < len(CLASS_NAMES) else f"Clase_{top_idx}"

    all_probs = {CLASS_NAMES[i]: round(float(probs.data[i]), 3)
                 for i in range(min(len(CLASS_NAMES), len(probs.data)))}

    return {
        "estado":      class_name,
        "confianza":   round(top_conf, 2),
        "detalles":    f"Clasificación YOLOv8: {class_name} con {top_conf*100:.1f}% de confianza.",
        "color_stats": {},
        "all_probs":   all_probs,
        "metodo":      "YOLOv8_finetuned",
        "timestamp":   datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE ANÁLISIS (API pública)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_leaf(image_path: str) -> dict:
    """
    Analiza una imagen de hoja de arándano y retorna su estado fitosanitario.

    Args:
        image_path: Ruta a la imagen (JPG, PNG, WEBP)

    Returns:
        {
            "estado":     "Sano" | "Alerta" | "Botrytis",
            "confianza":  float (0.0 – 1.0),
            "detalles":   str   (descripción y recomendaciones),
            "color_stats": dict (estadísticas de color),
            "metodo":     str   ("YOLOv8_finetuned" | "HSV_heuristico" | ...)
        }
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

    # Intentar primero con YOLOv8 si está disponible
    if _yolo_model is not None:
        return _analyze_with_yolo(image_path)

    # Análisis HSV como método principal
    return _analyze_hsv(image_path)


# ─────────────────────────────────────────────────────────────────────────────
# GENERADOR DE IMÁGENES DE PRUEBA (para demo sin fotos reales)
# ─────────────────────────────────────────────────────────────────────────────

def generate_test_images():
    """Genera imágenes sintéticas de prueba con colores representativos de cada estado."""
    if not CV2_AVAILABLE and not PIL_AVAILABLE:
        print("[Vision] Sin OpenCV ni PIL; no se pueden generar imágenes de prueba.")
        return

    output_dir = BASE_DIR / "test_images"
    output_dir.mkdir(exist_ok=True)

    specs = {
        "sano.jpg":     {"base_h": 60, "base_s": 200, "base_v": 120, "noise": 15,
                         "desc":  "Verde vibrante — hoja saludable"},
        "alerta.jpg":   {"base_h": 28, "base_s": 160, "base_v": 160, "noise": 20,
                         "desc":  "Amarillo-verdoso — clorosis incipiente"},
        "botrytis.jpg": {"base_h": 10, "base_s": 40,  "base_v": 100, "noise": 25,
                         "desc":  "Gris-pardo — Botrytis cinerea"}
    }

    for filename, spec in specs.items():
        img_path = output_dir / filename
        if img_path.exists():
            print(f"[Vision] Ya existe: {img_path}")
            continue

        if CV2_AVAILABLE:
            hsv_img = np.zeros((224, 224, 3), dtype=np.uint8)
            h_noise = np.random.randint(-spec["noise"], spec["noise"], (224, 224))
            s_noise = np.random.randint(-spec["noise"], spec["noise"]//2, (224, 224))
            v_noise = np.random.randint(-spec["noise"]//2, spec["noise"]//2, (224, 224))

            hsv_img[:, :, 0] = np.clip(spec["base_h"] + h_noise, 0, 179)
            hsv_img[:, :, 1] = np.clip(spec["base_s"] + s_noise, 0, 255)
            hsv_img[:, :, 2] = np.clip(spec["base_v"] + v_noise, 0, 255)

            # Añadir forma de hoja (elipse)
            mask = np.zeros((224, 224), dtype=np.uint8)
            cv2.ellipse(mask, (112, 112), (80, 100), 0, 0, 360, 255, -1)
            bgr_leaf = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
            bg = np.zeros_like(bgr_leaf)
            bg[:] = [30, 30, 30]    # Fondo oscuro
            result = np.where(mask[:, :, np.newaxis] > 0, bgr_leaf, bg)
            cv2.imwrite(str(img_path), result)

        elif PIL_AVAILABLE:
            from PIL import ImageDraw
            img = Image.new("RGB", (224, 224), (30, 30, 30))
            draw = ImageDraw.Draw(img)
            color_map = {
                "sano.jpg":     (60, 160, 60),
                "alerta.jpg":   (200, 200, 50),
                "botrytis.jpg": (120, 100, 100),
            }
            draw.ellipse([32, 12, 192, 212], fill=color_map[filename])
            img.save(str(img_path))

        print(f"[Vision] Imagen de prueba generada: {img_path} ({spec['desc']})")


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BerryMind Vision Agent — Clasificación de hojas de arándano"
    )
    parser.add_argument("--image", help="Ruta a la imagen a analizar")
    parser.add_argument("--test",  action="store_true",
                        help="Analizar las imágenes de prueba y salir")
    parser.add_argument("--gen-test-images", action="store_true",
                        help="Generar imágenes de prueba sintéticas")
    args = parser.parse_args()

    # Intentar cargar modelo YOLOv8 fine-tuneado si existe
    _load_yolo_model()

    if args.gen_test_images:
        generate_test_images()
        return

    if args.test:
        print("\n=== TEST: Clasificando imágenes de prueba ===")
        test_dir = BASE_DIR / "test_images"

        # Generar si no existen
        generate_test_images()

        for img_file in sorted(test_dir.glob("*.jpg")):
            try:
                result = analyze_leaf(str(img_file))
                print(f"\n📸 {img_file.name}")
                print(f"   Estado:     {result['estado']}")
                print(f"   Confianza:  {result['confianza'] * 100:.1f}%")
                print(f"   Método:     {result.get('metodo', 'N/A')}")
                print(f"   Detalles:   {result['detalles'][:80]}...")
                if result.get("color_stats"):
                    cs = result["color_stats"]
                    print(f"   Colores:    Verde={cs.get('pct_verde', 0)}%  "
                          f"Amarillo={cs.get('pct_amarillo', 0)}%  "
                          f"Gris={cs.get('pct_gris', 0)}%")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        print("\n✅ Test de visión completado.")
        return

    if args.image:
        _load_yolo_model()
        result = analyze_leaf(args.image)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
