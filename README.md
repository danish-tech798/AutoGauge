# AutoGauge — AI-Powered Used Car Price Predictor

**Accurate car valuations at a glance.** AutoGauge combines structured machine learning, computer vision-based damage detection, and SHAP explainability to predict used car prices with transparency.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.63%2B-red) ![XGBoost](https://img.shields.io/badge/XGBoost-ML-green) ![YOLOv8](https://img.shields.io/badge/YOLOv8-Vision-blue)

---

## 🎯 Overview

AutoGauge is a **final-year computer science project** that predicts used car prices by fusing three independent pipelines:

1. **Tabular Pipeline** — Car specs (brand, year, mileage, fuel type, etc.) → XGBoost regression model
2. **Image Pipeline** — Car photos → YOLOv8 damage detector → condition score (0–1)
3. **Fusion & Explainability** — Combined predictions with SHAP waterfall reports showing *why* a price was predicted

**Result:** R² = 0.86 on test data, mean error ₹60K–65K

---

## ✨ Features

✅ **Multi-step guided UX** — Welcome → Photos → Details → AI Analysis → Report  
✅ **Damage detection** — Detects dents, scratches, cracks, broken glass, lamps, flat tires  
✅ **Condition scoring** — Converts image damage into a 0–1 condition score  
✅ **Explainable predictions** — SHAP breakdown shows how each feature affects price  
✅ **What-if insights** — "If this car had no damage, it'd be worth ₹X more"  
✅ **Dark, animated UI** — Purple/violet theme with gradient backgrounds and smooth transitions  
✅ **Real-time analysis** — Processing status shown during computation  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Input (Streamlit)                │
│           Photos + Car Specs (Brand, Year, Km)          │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
  ┌──────────────┐          ┌──────────────────┐
  │   Image      │          │   Tabular        │
  │   Pipeline   │          │   Pipeline       │
  │   (YOLOv8)   │          │   (XGBoost)      │
  └──────┬───────┘          └────────┬─────────┘
         │ Damage               │ Specs
         │ Detection            │ Features
         ▼                      ▼
    Condition Score    Price Prediction
    (0–1)              (baseline)
         │                   │
         └───────┬───────────┘
                 ▼
         ┌──────────────────┐
         │   Fusion Model   │
         │   (XGBoost +     │
         │    condition)    │
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │   Explainability │
         │   (SHAP)         │
         │   Waterfall      │
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  Final Report    │
         │  Price +         │
         │  Breakdown       │
         └──────────────────┘
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **R² Score** | 0.8603 |
| **Mean Absolute Error** | ₹63,028 |
| **RMSE** | ₹99,702 |
| **MAPE** | 15.83% |
| **Training Data** | 7,396 cars |
| **Test Set Size** | 1,480 cars |

**Image Model (YOLOv8):**
- mAP50 = 0.713 on CarDD validation set
- 6 damage classes with per-class accuracy:
  - Glass shatter: 99.2% | Tire flat: 94.6% | Lamp broken: 86.8%
  - Dent: 56.0% | Scratch: 55.8% | Crack: 35.4%

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/AutoGauge.git
cd AutoGauge
```

### 2. Set up virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download datasets (one-time)

**Tabular data (CarDekho-style car listings):**
- Already included in `data/raw_cars.csv` (if you've preprocessed)
- Or download from: https://www.kaggle.com/datasets/nehalbirla/vehicle-dataset-from-cardekho

**Image data (CarDD — car damage detection):**
- Download from: https://www.kaggle.com/datasets/gabrielfcarvalho/cardd-with-yolo-annotations-images-labels
- Extract to `data/images/cardd/` so you have:
  ```
  data/images/cardd/
  ├── train/images/
  ├── val/images/
  ├── test/images/
  └── data.yaml
  ```

### 5. Preprocess the data
```bash
python src/data_preprocessing.py --input data/raw_cars.csv --output data/processed_cars.csv
```

### 6. Train the tabular model
```bash
python src/tabular_model.py
```

### 7. (Optional) Train the image model

If you have the CarDD dataset:
```bash
python src/image_model.py
```

This takes ~2 hours on CPU, or ~30 min on Google Colab GPU. Pre-trained weights can be used if available.

### 8. Fuse and finalize
```bash
python src/fusion.py --train
```

### 9. Run the Streamlit app
```bash
streamlit run app/app.py
```

The app opens at **http://localhost:8501**

---

## 📱 Usage

### Via Web UI (AutoGauge Streamlit App)

1. **Welcome** — Read the intro and click "Get Started"
2. **Upload Photos** — Drag-drop car photos (front, back, sides, interior)
3. **Enter Details** — Brand, model, year, km driven, fuel type, transmission, city, body type, ownership
4. **AI Analysis** — The system:
   - Detects damage in photos via YOLOv8 → condition score
   - Extracts features from your specs
   - Fuses both into a final price prediction
5. **View Report** — See:
   - Predicted price (₹)
   - Condition badge (Excellent/Good/Fair/Poor)
   - Damage types detected (if any)
   - Factor-by-factor breakdown (SHAP)
   - What-if insight (price without damage)

### Via Command Line (Direct Scripts)

**Preprocess raw data:**
```bash
python src/data_preprocessing.py --input data/raw_cars.csv --output data/processed_cars.csv
```

**Train tabular model:**
```bash
python src/tabular_model.py
```

**Score a single car photo:**
```bash
python src/condition_scorer.py --image path/to/photo.jpg
```

**Get price prediction + SHAP explanation:**
```bash
python src/explainability.py --predict --photos photo1.jpg photo2.jpg \
    --brand maruti --model_name swift --year 2018 --km_driven 45000 \
    --fuel_type petrol --transmission manual --city pune \
    --body_type hatchback --owner_count 1
```

---

## 📁 Project Structure

```
AutoGauge/
├── .streamlit/
│   └── config.toml                # Streamlit theme (purple/violet)
├── app/
│   └── app.py                     # Main Streamlit app (guided flow)
├── data/
│   ├── raw_cars.csv               # Raw CarDekho listings
│   ├── processed_cars.csv          # Cleaned + engineered features
│   └── images/
│       └── cardd/                 # CarDD damage detection dataset
├── models/
│   ├── xgboost_model.pkl          # Tabular price model
│   ├── fusion_model.pkl           # Fused (tabular + condition) model
│   ├── damage_detector/run/weights/best.pt  # YOLOv8 trained weights
│   └── fusion_metrics.json        # Model performance metrics
├── notebooks/
│   └── eda.ipynb                  # Exploratory data analysis
├── report/
│   └── price_explanation.png      # Sample SHAP breakdown chart
├── src/
│   ├── data_preprocessing.py      # Clean + engineer features
│   ├── tabular_model.py           # XGBoost training
│   ├── image_model.py             # YOLOv8 fine-tuning
│   ├── condition_scorer.py        # Convert detections → condition score
│   ├── fusion.py                  # Merge image + tabular, retrain
│   └── explainability.py          # SHAP waterfall reports
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── .gitignore                     # Git ignore rules
```

---

## 🔧 Technologies Used

| Component | Tool | Version |
|-----------|------|---------|
| **Data Processing** | pandas, numpy | 2.0+, 1.24+ |
| **Tabular ML** | XGBoost | 2.0+ |
| **Computer Vision** | YOLOv8 (Ultralytics) | 8.1+ |
| **Image Processing** | OpenCV, PIL | 4.8+, 10.0+ |
| **Explainability** | SHAP | 0.44+ |
| **Web UI** | Streamlit | 1.30+ |
| **Feature Engineering** | scikit-learn | 1.3+ |

---

## 🎓 Key Learnings & Concepts

### 1. **Weak Supervision / Proxy-Label Training**
The tabular and image datasets don't overlap (no matched "photo + listing + actual price"). To teach the model how condition affects price, we simulated a realistic relationship (worse condition → lower price) for training. At inference, the condition score comes from real YOLO detections on real photos.

### 2. **Multi-Modal Fusion**
Fusing heterogeneous data sources (tabular specs + image features) into a unified predictor is non-trivial. We use feature-level fusion: the image model outputs a single numeric condition score, which is added as a tabular feature before retraining.

### 3. **Explainability via SHAP**
A price prediction is only trustworthy if users understand *why*. SHAP decomposes each prediction into per-feature contributions, answering "how much did car age push the price down?" This is essential for stakeholder buy-in.

### 4. **Handling Data Imbalance**
CarDD has imbalanced classes (glass shatter is rare but visually distinct; scratches are common but subtle). Per-class mAP varies accordingly — a lesson in understanding model limitations.

---

## 🚗 Real-World Workflow

1. **Seller uploads photos** of their car via AutoGauge
2. **System analyzes photos** → detects cosmetic damage
3. **Seller enters specs** (brand, year, mileage, fuel type, etc.)
4. **Model predicts price** using both data sources
5. **Seller sees:**
   - Estimated market price
   - Condition assessment (damage found, if any)
   - Why the price is what it is (SHAP breakdown)
   - What-if scenarios (no damage → higher price)
6. **Seller negotiates** with buyers using this transparent, data-backed valuation

---

## 🔮 Future Enhancements

- [ ] Multi-photo damage severity scoring (weight by angle/resolution)
- [ ] Market trend analysis (price trends over time by location/brand)
- [ ] Financing integration (loan eligibility based on predicted value)
- [ ] Mobile app (React Native or Flutter)
- [ ] PDF report generation (downloadable valuation report)
- [ ] Historical price tracking ("How much have similar cars depreciated?")
- [ ] Comparative analysis ("Similar cars in your area: ₹X–₹Y")
- [ ] Real-time market data integration (live competitor pricing)

---

## 📝 Notes on Datasets

### CarDekho Listings
- **Source:** Kaggle (vehicle-dataset-from-cardekho)
- **Size:** ~14,000 raw entries → 7,396 after filtering (bikes removed, invalid rows dropped)
- **Features:** Brand, model, year, km driven, fuel type, transmission, owner count, city, body type, price
- **Preprocessing:** Unit extraction (e.g., "23.4 kmpl" → 23.4), owner text standardization, depreciation-aware feature engineering

### CarDD Damage Detection
- **Source:** Kaggle (cardd-with-yolo-annotations-images-labels)
- **Size:** ~4,000 images, 9,000+ annotated instances
- **Classes:** Dent, scratch, crack, glass shatter, lamp broken, tire flat
- **Format:** YOLO object-detection labels (bounding boxes)
- **Fine-tuning:** YOLOv8 Nano (3M params) on this dataset → mAP50 = 0.713

---

## ⚖️ Limitations & Honest Assessment

1. **No real photo-price matching** — We simulated the condition-price relationship since the datasets don't overlap. The real effect is validated at demo-time with real photos.
2. **Damage detection accuracy varies** — Glass/tires: 94%+ | Scratches/dents: 56–58% | Cracks: 35% (subtle, harder to detect even for humans).
3. **Data recency** — CarDekho data may be several months old; real-time market prices fluctuate.
4. **Geographic bias** — Model trained on Indian market; extrapolation to other regions uncertain.
5. **Missing factors** — Accident history, service records, insurance claims not captured in photos/specs alone.

---

## 📧 Contact & Attribution

- **Author:** Danish (Final Year CS Student)
- **Project:** AutoGauge - AI-Powered Used Car Price Predictor
- **Institution:** [Your University]
- **Year:** 2026

For questions, issues, or collaboration:
- 📧 Email: [your email]
- 🐙 GitHub: [your GitHub profile]
- 💼 LinkedIn: [your LinkedIn]

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics
- **SHAP** by Scott Lundberg et al.
- **Streamlit** for an amazing web framework
- **CarDD Dataset** for the damage-detection annotations
- **CarDekho** for the real-world vehicle listings

---

## 🎬 Demo & Screenshots

**Welcome Screen:**
```
AutoGauge
AI-Powered Used Car Price Estimator
Upload vehicle images and get an accurate price estimate using advanced AI.
[Get Started]
```

**Photo Upload:**
```
Upload Photos
(drag & drop or click)
[Photo 1] [Photo 2] [Photo 3]
[Next →]
```

**Details Form:**
```
Car Details
Brand: [Maruti ▼]    Fuel Type: [Petrol ▼]
Model: [Swift]       Transmission: [Manual ▼]
Year: 2018           City: [Pune ▼]
Km Driven: 45000     Body Type: [Hatchback ▼]
[Next →]
```

**Price Report:**
```
₹ 4,45,000
✓ Good Condition | Score: 0.87 / 1.0
Damage Detected: scratch, dent

Why this price?
car_age (11 yrs)          - ₹1,20,000
body_type (hatchback)     - ₹ 45,000
brand (maruti)            - ₹ 35,000
condition_score (0.87)    + ₹ 28,000
km_driven (45,000)        - ₹ 15,000
...

💡 Insight: If this car had no visible damage,
   it would be worth ~₹45,000 more
   (₹4,90,000 total)
```

---

**Made with ❤️ for accurate, explainable car valuations.**

---

## 🏁 Getting Help

If you encounter issues:

1. **Check the docs** — Start with SETUP.txt or the Quick Start section
2. **Virtual env problems?** — Ensure `.venv\Scripts\activate` is run (check `(.venv)` prefix in terminal)
3. **Module not found?** — Run `pip install -r requirements.txt` again
4. **Streamlit errors?** — Clear Streamlit cache: `streamlit cache clear`, then rerun
5. **Model not loading?** — Confirm training completed: `python src/fusion.py --train`

Stuck? Open an issue on GitHub with error logs.
