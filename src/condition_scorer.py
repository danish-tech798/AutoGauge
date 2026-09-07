"""
condition_scorer.py
---------------------
Uses the trained damage-detection model (from image_model.py) to look
at a car photo and turn what it sees into NUMBERS that can be added
to the price-prediction model:

    condition_score   -> 0.0 (badly damaged) to 1.0 (no visible damage)
    damage_count       -> how many damage regions were found
    damage_types        -> which kinds of damage (dent, scratch, etc.)
    worst_damage_type  -> the single most "expensive to fix" damage found

How the condition_score is calculated:
    Start at 1.0 (perfect condition) and subtract a penalty for every
    damage found. More severe damage types (like a crack or broken
    glass) subtract more than minor ones (like a small scratch).

Usage (single image):
    python src/condition_scorer.py --image path/to/car_photo.jpg

Usage (folder of images, e.g. multiple photos of the same listing):
    python src/condition_scorer.py --folder path/to/photos/
"""

import argparse
import glob
import os
from ultralytics import YOLO

MODEL_PATH = "models/damage_detector/run/weights/best.pt"

# How much each damage type costs the condition score.
# Crack/glass/lamp are more expensive repairs -> penalized more.
DAMAGE_SEVERITY = {
    "dent": 0.08,
    "scratch": 0.04,
    "crack": 0.15,
    "glass shatter": 0.20,
    "lamp broken": 0.12,
    "tire flat": 0.10,
}


def load_model(model_path: str = MODEL_PATH) -> YOLO:
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No trained damage-detection model found at {model_path}.\n"
            f"Run 'python src/image_model.py' first to train one."
        )
    return YOLO(model_path)


def score_image(model: YOLO, image_path: str, conf_threshold: float = 0.25) -> dict:
    """Runs the model on ONE image and returns a condition score + details."""
    results = model.predict(image_path, conf=conf_threshold, verbose=False)
    result = results[0]

    class_names = result.names
    detections = []
    for box in result.boxes:
        cls_id = int(box.cls[0])
        cls_name = class_names[cls_id]
        confidence = float(box.conf[0])
        detections.append({"type": cls_name, "confidence": round(confidence, 3)})

    # start perfect, subtract penalty per detected damage
    score = 1.0
    for det in detections:
        penalty = DAMAGE_SEVERITY.get(det["type"], 0.05)
        score -= penalty * det["confidence"]  # weight by how sure the model is
    score = max(0.0, min(1.0, score))

    worst_damage = None
    if detections:
        worst_damage = max(
            detections, key=lambda d: DAMAGE_SEVERITY.get(d["type"], 0)
        )["type"]

    return {
        "image": os.path.basename(image_path),
        "condition_score": round(score, 3),
        "damage_count": len(detections),
        "damage_types": list({d["type"] for d in detections}),
        "worst_damage_type": worst_damage,
        "detections": detections,
    }


def score_folder(model: YOLO, folder_path: str) -> dict:
    """Runs on ALL photos in a folder (e.g. multiple angles of one car)
    and combines them into a single overall condition score - using the
    WORST (lowest) score found, since one bad photo reveals real damage
    even if other angles look fine."""
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_paths.extend(glob.glob(os.path.join(folder_path, ext)))

    if not image_paths:
        raise FileNotFoundError(f"No images found in {folder_path}")

    per_image_results = [score_image(model, p) for p in image_paths]
    overall_score = min(r["condition_score"] for r in per_image_results)
    all_damage_types = sorted({
        t for r in per_image_results for t in r["damage_types"]
    })

    return {
        "folder": folder_path,
        "num_images_analyzed": len(per_image_results),
        "overall_condition_score": round(overall_score, 3),
        "all_damage_types_found": all_damage_types,
        "per_image_results": per_image_results,
    }


def print_report(result: dict):
    print("\n" + "=" * 50)
    print("CONDITION ANALYSIS REPORT")
    print("=" * 50)
    if "overall_condition_score" in result:
        print(f"Images analyzed:     {result['num_images_analyzed']}")
        print(f"Overall condition:   {result['overall_condition_score']} / 1.0")
        print(f"Damage types found:  {result['all_damage_types_found'] or 'None'}")
    else:
        print(f"Image:               {result['image']}")
        print(f"Condition score:     {result['condition_score']} / 1.0")
        print(f"Damage count:        {result['damage_count']}")
        print(f"Damage types:        {result['damage_types'] or 'None'}")
        print(f"Worst damage found:  {result['worst_damage_type'] or 'None'}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Score car condition from photo(s)")
    parser.add_argument("--image", type=str, help="Path to a single car photo")
    parser.add_argument("--folder", type=str, help="Path to a folder of car photos")
    parser.add_argument("--model", type=str, default=MODEL_PATH,
                         help="Path to trained damage-detector weights")
    args = parser.parse_args()

    if not args.image and not args.folder:
        parser.error("Provide either --image or --folder")

    model = load_model(args.model)

    if args.image:
        result = score_image(model, args.image)
    else:
        result = score_folder(model, args.folder)

    print_report(result)
    return result


if __name__ == "__main__":
    main()
