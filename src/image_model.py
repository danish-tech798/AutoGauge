"""
image_model.py
----------------
Trains a car DAMAGE DETECTION model using YOLOv8.

This model looks at a photo of a car and finds damage: dents, scratches,
cracks, broken glass, broken lamps, flat tires.

It's trained on the CarDD dataset (download instructions below).

------------------------------------------------------------------
HOW TO GET THE DATASET (do this before running this script):
------------------------------------------------------------------
1. Go to: https://www.kaggle.com/datasets/gabrielfcarvalho/cardd-with-yolo-annotations-images-labels
2. Click Download
3. Extract the zip
4. You'll see folders like: train/, val/, test/, and a file called data.yaml
5. Copy ALL of that into: data/images/cardd/
   (so you end up with data/images/cardd/train, data/images/cardd/val, etc.
    and data/images/cardd/data.yaml)
------------------------------------------------------------------

Usage:
    python src/image_model.py
"""

import os
from ultralytics import YOLO

DATA_YAML = "data/images/cardd/data.yaml"
MODEL_OUT_DIR = os.path.abspath("models/damage_detector")
EPOCHS = 50
IMG_SIZE = 640


def check_dataset_exists():
    if not os.path.exists(DATA_YAML):
        print("=" * 60)
        print("DATASET NOT FOUND")
        print("=" * 60)
        print(f"Expected to find: {DATA_YAML}")
        print()
        print("Please download the CarDD dataset first:")
        print("https://www.kaggle.com/datasets/gabrielfcarvalho/cardd-with-yolo-annotations-images-labels")
        print()
        print("Then extract it into: data/images/cardd/")
        print("(so data/images/cardd/data.yaml exists)")
        print("=" * 60)
        return False
    return True


def train_damage_model():
    # Start from a small pretrained YOLOv8 model (already knows how to
    # "see" general objects/shapes) and fine-tune it on car damage photos.
    # yolov8n = "nano" - smallest/fastest version, good for a student
    # laptop without a powerful GPU. Use yolov8s.pt for better accuracy
    # if you have a good GPU / more time.
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        project=MODEL_OUT_DIR,
        name="run",
        patience=10,       # stop early if it stops improving
        exist_ok=True,
    )

    print("\nTraining complete!")
    print(f"Best model weights saved at: {MODEL_OUT_DIR}/run/weights/best.pt")
    return results


def main():
    if not check_dataset_exists():
        return
    train_damage_model()


if __name__ == "__main__":
    main()
