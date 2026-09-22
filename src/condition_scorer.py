"""
condition_scorer.py

Uses a trained YOLO damage-detection model to analyze car photos
and calculate a vehicle condition score.

condition_score     -> 0.0 (bad condition) to 1.0 (excellent condition)
damage_count        -> number of detected damage regions
damage_types        -> types of damage detected
worst_damage_type   -> most severe detected damage
"""

import argparse
import glob
import os

from ultralytics import YOLO


# ---------------------------------------------------------
# MODEL PATH
# ---------------------------------------------------------

MODEL_PATH = "models/damage_detector/run/weights/best.pt"


# ---------------------------------------------------------
# DAMAGE SEVERITY
# ---------------------------------------------------------

DAMAGE_SEVERITY = {
    "dent": 0.08,
    "scratch": 0.04,
    "crack": 0.15,
    "glass shatter": 0.20,
    "lamp broken": 0.12,
    "tire flat": 0.10,
}


# ---------------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------------

def load_model(model_path: str = MODEL_PATH) -> YOLO:
    """
    Load the trained YOLO damage-detection model.
    """

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No trained damage-detection model found at:\n"
            f"{model_path}\n\n"
            f"Make sure best.pt exists at this location."
        )

    return YOLO(model_path)


# ---------------------------------------------------------
# SCORE ONE IMAGE
# ---------------------------------------------------------

def score_image(
    model: YOLO,
    image_path: str,
    conf_threshold: float = 0.25
) -> dict:
    """
    Run the YOLO model on one image and calculate
    the vehicle condition score.
    """

    # Check whether image exists
    if not os.path.exists(image_path):
        return {
            "image": os.path.basename(image_path),
            "condition_score": 0.0,
            "damage_count": 0,
            "damage_types": [],
            "worst_damage_type": None,
            "detections": [],
            "message": f"Image not found: {image_path}"
        }

    # Run YOLO prediction
    results = model.predict(
        image_path,
        conf=conf_threshold,
        verbose=False
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # YOLO normally returns a list containing Result objects.
    # If the list is empty, do not access results[0].
    # -----------------------------------------------------

    if results is None or len(results) == 0:
        return {
            "image": os.path.basename(image_path),
            "condition_score": 1.0,
            "damage_count": 0,
            "damage_types": [],
            "worst_damage_type": None,
            "detections": [],
            "message": "No YOLO result was returned."
        }

    # Get first YOLO result
    result = results[0]

    # Get class names
    class_names = result.names

    # List for detected damage
    detections = []

    # -----------------------------------------------------
    # PROCESS DETECTIONS
    # -----------------------------------------------------

    if result.boxes is not None and len(result.boxes) > 0:

        for box in result.boxes:

            # Class ID
            cls_id = int(box.cls[0])

            # Get class name safely
            if isinstance(class_names, dict):
                cls_name = class_names.get(
                    cls_id,
                    str(cls_id)
                )
            else:
                if cls_id < len(class_names):
                    cls_name = class_names[cls_id]
                else:
                    cls_name = str(cls_id)

            # Confidence
            confidence = float(box.conf[0])

            # Save detection
            detections.append(
                {
                    "type": str(cls_name),
                    "confidence": round(
                        confidence,
                        3
                    )
                }
            )

    # -----------------------------------------------------
    # CALCULATE CONDITION SCORE
    # -----------------------------------------------------

    # Start with perfect condition
    score = 1.0

    # Subtract penalty for each detected damage
    for detection in detections:

        damage_type = detection["type"]
        confidence = detection["confidence"]

        # Default penalty for unknown damage type
        penalty = DAMAGE_SEVERITY.get(
            damage_type.lower(),
            0.05
        )

        # Apply confidence-weighted penalty
        score -= penalty * confidence

    # Keep score between 0 and 1
    score = max(
        0.0,
        min(1.0, score)
    )

    # -----------------------------------------------------
    # FIND WORST DAMAGE
    # -----------------------------------------------------

    worst_damage = None

    if detections:

        worst_damage = max(
            detections,
            key=lambda detection: DAMAGE_SEVERITY.get(
                detection["type"].lower(),
                0.05
            )
        )["type"]

    # -----------------------------------------------------
    # GET UNIQUE DAMAGE TYPES
    # -----------------------------------------------------

    damage_types = sorted(
        list(
            {
                detection["type"]
                for detection in detections
            }
        )
    )

    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {
        "image": os.path.basename(image_path),
        "condition_score": round(
            score,
            3
        ),
        "damage_count": len(detections),
        "damage_types": damage_types,
        "worst_damage_type": worst_damage,
        "detections": detections
    }


# ---------------------------------------------------------
# SCORE FOLDER
# ---------------------------------------------------------

def score_folder(
    model: YOLO,
    folder_path: str
) -> dict:
    """
    Analyze all JPG, JPEG and PNG images inside a folder.

    The lowest condition score is used as the overall score.
    """

    # Check folder
    if not os.path.exists(folder_path):
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    # Check folder type
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(
            f"Not a directory: {folder_path}"
        )

    # -----------------------------------------------------
    # FIND IMAGES
    # -----------------------------------------------------

    image_paths = []

    extensions = (
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.JPG",
        "*.JPEG",
        "*.PNG"
    )

    for extension in extensions:

        image_paths.extend(
            glob.glob(
                os.path.join(
                    folder_path,
                    extension
                )
            )
        )

    # Remove duplicates and sort
    image_paths = sorted(
        list(set(image_paths))
    )

    # No images
    if not image_paths:
        raise FileNotFoundError(
            f"No JPG, JPEG or PNG images found in:\n"
            f"{folder_path}"
        )

    # -----------------------------------------------------
    # SCORE EVERY IMAGE
    # -----------------------------------------------------

    per_image_results = []

    for image_path in image_paths:

        try:

            result = score_image(
                model,
                image_path
            )

            per_image_results.append(result)

        except Exception as error:

            print(
                f"Warning: Could not analyze "
                f"{image_path}: {error}"
            )

            # Keep application running
            per_image_results.append(
                {
                    "image": os.path.basename(
                        image_path
                    ),
                    "condition_score": 1.0,
                    "damage_count": 0,
                    "damage_types": [],
                    "worst_damage_type": None,
                    "detections": [],
                    "message": str(error)
                }
            )

    # -----------------------------------------------------
    # OVERALL CONDITION SCORE
    # -----------------------------------------------------

    overall_score = min(
        result["condition_score"]
        for result in per_image_results
    )

    # -----------------------------------------------------
    # ALL DAMAGE TYPES
    # -----------------------------------------------------

    all_damage_types = sorted(
        {
            damage_type
            for result in per_image_results
            for damage_type in result["damage_types"]
        }
    )

    # -----------------------------------------------------
    # RETURN FOLDER RESULT
    # -----------------------------------------------------

    return {
        "folder": folder_path,
        "num_images_analyzed": len(
            per_image_results
        ),
        "overall_condition_score": round(
            overall_score,
            3
        ),
        "all_damage_types_found": all_damage_types,
        "per_image_results": per_image_results
    }


# ---------------------------------------------------------
# PRINT REPORT
# ---------------------------------------------------------

def print_report(result: dict):
    """
    Print a readable condition-analysis report.
    """

    print()
    print("=" * 60)
    print("CONDITION ANALYSIS REPORT")
    print("=" * 60)

    # Folder result
    if "overall_condition_score" in result:

        print(
            f"Images analyzed:    "
            f"{result['num_images_analyzed']}"
        )

        print(
            f"Overall condition:  "
            f"{result['overall_condition_score']} / 1.0"
        )

        print(
            f"Damage types found: "
            f"{result['all_damage_types_found'] or 'None'}"
        )

        print()
        print("Individual image results:")
        print("-" * 60)

        for image_result in result[
            "per_image_results"
        ]:

            print(
                f"Image: {image_result['image']}"
            )

            print(
                f"Score: "
                f"{image_result['condition_score']} / 1.0"
            )

            print(
                f"Damage count: "
                f"{image_result['damage_count']}"
            )

            print(
                f"Damage types: "
                f"{image_result['damage_types'] or 'None'}"
            )

            print(
                f"Worst damage: "
                f"{image_result['worst_damage_type'] or 'None'}"
            )

            print("-" * 60)

    # Single image result
    else:

        print(
            f"Image:              "
            f"{result['image']}"
        )

        print(
            f"Condition score:    "
            f"{result['condition_score']} / 1.0"
        )

        print(
            f"Damage count:       "
            f"{result['damage_count']}"
        )

        print(
            f"Damage types:       "
            f"{result['damage_types'] or 'None'}"
        )

        print(
            f"Worst damage:       "
            f"{result['worst_damage_type'] or 'None'}"
        )

        if "message" in result:

            print(
                f"Message:            "
                f"{result['message']}"
            )

    print("=" * 60)


# ---------------------------------------------------------
# COMMAND-LINE INTERFACE
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Analyze vehicle condition "
            "from car photos"
        )
    )

    # Single image
    parser.add_argument(
        "--image",
        type=str,
        help="Path to a single car photo"
    )

    # Folder
    parser.add_argument(
        "--folder",
        type=str,
        help="Path to a folder containing car photos"
    )

    # Model
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL_PATH,
        help=(
            "Path to trained "
            "damage-detection model"
        )
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # VALIDATE INPUT
    # -----------------------------------------------------

    if not args.image and not args.folder:

        parser.error(
            "Provide either --image or --folder"
        )

    # -----------------------------------------------------
    # LOAD MODEL
    # -----------------------------------------------------

    print()
    print("Loading damage-detection model...")

    model = load_model(
        args.model
    )

    print("Model loaded successfully.")

    # -----------------------------------------------------
    # ANALYZE IMAGE
    # -----------------------------------------------------

    if args.image:

        result = score_image(
            model,
            args.image
        )

    # -----------------------------------------------------
    # ANALYZE FOLDER
    # -----------------------------------------------------

    else:

        result = score_folder(
            model,
            args.folder
        )

    # -----------------------------------------------------
    # PRINT REPORT
    # -----------------------------------------------------

    print_report(
        result
    )

    return result


# ---------------------------------------------------------
# PROGRAM ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()

