"""
app.py - AutoGauge v2
-----------------------
A guided, step-by-step UX following the flow:
Welcome → Photos Upload → Details Input → AI Analyzing → Price Report

Built with Streamlit session state for smooth multi-page navigation,
animated CSS backgrounds, and violet/purple theme inspired by modern
fintech design (matching the mockup provided).
"""

import os
import sys
import tempfile
import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fusion import get_real_condition_score, DAMAGE_MODEL_PATH
from explainability import (
    load_model_and_features,
    prepare_for_model,
    explain,
    _format_value,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed_cars.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fusion_model.pkl")
CURRENT_YEAR = 2026

LUXURY_BRANDS = {"bmw", "audi", "mercedes benz", "mercedes-benz", "jaguar",
                  "land rover", "porsche", "volvo", "lexus"}
PREMIUM_BRANDS = {"toyota", "honda", "hyundai", "skoda", "volkswagen", "kia",
                   "jeep", "mg", "ford"}

# ============================================================================
# THEME & STYLING
# ============================================================================
CUSTOM_CSS = """
<style>
/* ---- animated gradient background ---- */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.stApp {
    background: linear-gradient(-45deg, #1a0033, #2d0052, #1a0033, #0f001a);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}

/* ---- main container ---- */
.main-card {
    background: rgba(15, 15, 35, 0.8);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 8px 32px rgba(124, 58, 237, 0.15);
    backdrop-filter: blur(10px);
}

/* ---- step indicator ---- */
.step-indicator {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 32px;
}

.step {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
    transition: all 0.3s ease;
}

.step.active {
    background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%);
    color: white;
    box-shadow: 0 0 20px rgba(124, 58, 237, 0.6);
}

.step.done {
    background: #10B981;
    color: white;
}

.step.pending {
    background: rgba(124, 58, 237, 0.2);
    color: #A78BFA;
    border: 1px solid rgba(124, 58, 237, 0.4);
}

/* ---- hero title ---- */
.hero-title {
    font-size: 48px;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 12px;
}

.hero-subtitle {
    font-size: 18px;
    color: #A78BFA;
    text-align: center;
    margin-bottom: 32px;
}

/* ---- button styling ---- */
.btn-next {
    background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
    color: white;
    padding: 14px 32px;
    border-radius: 12px;
    font-weight: 600;
    border: none;
    cursor: pointer;
    width: 100%;
    transition: all 0.3s ease;
}

.btn-next:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(124, 58, 237, 0.4);
}

/* ---- input styling ---- */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > select {
    background: rgba(124, 58, 237, 0.1) !important;
    border: 1px solid rgba(124, 58, 237, 0.3) !important;
    color: #FAFAFA !important;
    border-radius: 8px !important;
}

/* ---- photo upload area ---- */
.photo-upload-area {
    border: 2px dashed rgba(124, 58, 237, 0.5);
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    background: rgba(124, 58, 237, 0.05);
    transition: all 0.3s ease;
}

.photo-upload-area:hover {
    border-color: #7C3AED;
    background: rgba(124, 58, 237, 0.1);
}

/* ---- loading animation ---- */
@keyframes pulse-ring {
    0% { transform: scale(1); opacity: 1; }
    100% { transform: scale(1.8); opacity: 0; }
}

.loading-ring {
    width: 80px;
    height: 80px;
    border: 3px solid rgba(124, 58, 237, 0.3);
    border-top: 3px solid #7C3AED;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 40px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-pulse {
    animation: pulse-ring 2s infinite;
}

/* ---- price display ---- */
.price-display {
    font-size: 56px;
    font-weight: 900;
    background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin: 20px 0;
}

/* ---- condition badge ---- */
.condition-badge {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
    text-align: center;
}

.condition-excellent {
    background: rgba(16, 185, 129, 0.2);
    color: #10B981;
}

.condition-good {
    background: rgba(59, 130, 246, 0.2);
    color: #3B82F6;
}

.condition-fair {
    background: rgba(245, 158, 11, 0.2);
    color: #F59E0B;
}

.condition-poor {
    background: rgba(239, 68, 68, 0.2);
    color: #EF4444;
}

/* ---- factor breakdown ---- */
.factor-card {
    background: rgba(124, 58, 237, 0.05);
    border: 1px solid rgba(124, 58, 237, 0.2);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.factor-label {
    color: #A78BFA;
    font-weight: 500;
}

.factor-value-positive {
    color: #10B981;
    font-weight: 600;
}

.factor-value-negative {
    color: #EF4444;
    font-weight: 600;
}

/* ---- tips box ---- */
.tips-box {
    background: rgba(59, 130, 246, 0.1);
    border-left: 4px solid #3B82F6;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.tips-box p {
    color: #93C5FD;
    margin: 8px 0;
}

/* ---- color picker grid ---- */
.color-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}

.color-option {
    width: 50px;
    height: 50px;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s ease;
}

.color-option:hover {
    border-color: #7C3AED;
    transform: scale(1.1);
}

.color-option.selected {
    border-color: #7C3AED;
    box-shadow: 0 0 15px rgba(124, 58, 237, 0.6);
}
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
@st.cache_data
def load_dropdown_options():
    if not os.path.exists(DATA_PATH):
        return {
            "brand": ["maruti", "hyundai", "honda", "toyota", "tata"],
            "fuel_type": ["petrol", "diesel", "cng"],
            "transmission": ["manual", "automatic"],
            "city": ["pune", "mumbai", "delhi"],
            "body_type": ["hatchback", "sedan", "suv"],
        }
    df = pd.read_csv(DATA_PATH)
    return {
        "brand": sorted(df["brand"].dropna().unique().tolist()),
        "fuel_type": sorted(df["fuel_type"].dropna().unique().tolist()),
        "transmission": sorted(df["transmission"].dropna().unique().tolist()),
        "city": sorted(df["city"].dropna().unique().tolist()),
        "body_type": sorted(df["body_type"].dropna().unique().tolist()),
    }


@st.cache_resource
def load_model():
    return load_model_and_features()


def save_uploaded_photos(uploaded_files) -> list:
    paths = []
    tmp_dir = tempfile.mkdtemp()
    for f in uploaded_files:
        path = os.path.join(tmp_dir, f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        paths.append(path)
    return paths


def brand_tier(brand: str) -> str:
    b = str(brand).lower()
    if b in LUXURY_BRANDS:
        return "luxury"
    if b in PREMIUM_BRANDS:
        return "premium"
    return "economy"


def get_condition_badge_html(score: float) -> str:
    if score >= 0.75:
        cls, label = "condition-excellent", "✓ Excellent Condition"
    elif score >= 0.55:
        cls, label = "condition-good", "✓ Good Condition"
    elif score >= 0.35:
        cls, label = "condition-fair", "⚠ Fair Condition"
    else:
        cls, label = "condition-poor", "✗ Needs Attention"
    return f'<span class="condition-badge {cls}">{label}</span>'


def step_indicator(current_step: int, total_steps: int = 4):
    """Renders the step progress indicator at the top."""
    html = '<div class="step-indicator">'
    for i in range(1, total_steps + 1):
        if i < current_step:
            cls = "step done"
            label = "✓"
        elif i == current_step:
            cls = "step active"
            label = str(i)
        else:
            cls = "step pending"
            label = str(i)
        html += f'<div class="{cls}">{label}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# PAGE: WELCOME
# ============================================================================
def page_welcome():
    step_indicator(1)
    st.markdown(
        '<h1 class="hero-title">AutoGauge</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero-subtitle">AI-Powered Used Car Price Estimation</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            ### How it works:
            1. 📸 **Upload photos** of your car from different angles
            2. 📝 **Enter details** about your vehicle
            3. 🤖 **AI analyzes** damage and specs
            4. 💰 **Get price** with detailed breakdown

            ### Why AutoGauge?
            - **Accurate pricing** using ML + photo analysis
            - **Damage detection** via computer vision
            - **Transparent reasoning** showing why the price is what it is
            - **Market insights** comparing to similar cars
            """
        )

    with col2:
        st.image(
            "https://via.placeholder.com/300x400/7C3AED/FFFFFF?text=Your+Car+Here",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Get Started", key="welcome_btn", use_container_width=True):
        st.session_state.page = "photos"
        st.rerun()


# ============================================================================
# PAGE: PHOTOS UPLOAD
# ============================================================================
def page_photos():
    step_indicator(2)
    st.markdown(
        '<h1 class="hero-title">Upload Photos</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero-subtitle">Upload clear images of your vehicle from different angles</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tips-box">', unsafe_allow_html=True)
    st.markdown("""
    ✓ **Upload clear, high-resolution images**
    
    ✓ **Include all sides of the vehicle** (front, back, sides)
    
    ✓ **Good lighting** on sunny days (no blurry photos)
    
    ✓ **Show interior** and odometer if possible
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="photo-upload-area">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Drag and drop photos here or click to browse",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="photo_uploader",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_files:
        st.markdown("### Uploaded Photos")
        cols = st.columns(min(len(uploaded_files), 4))
        for i, f in enumerate(uploaded_files):
            with cols[i % 4]:
                st.image(f, use_container_width=True, caption=f.name)
        st.session_state.uploaded_files = uploaded_files
    else:
        st.info("📸 No photos uploaded yet. Upload at least one photo to continue.")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "welcome"
            st.rerun()
    with col_next:
        if st.button("Next →", use_container_width=True, type="primary"):
            if uploaded_files:
                st.session_state.page = "details"
                st.rerun()
            else:
                st.error("Please upload at least one photo to continue.")


# ============================================================================
# PAGE: DETAILS INPUT
# ============================================================================
def page_details():
    step_indicator(3)
    st.markdown(
        '<h1 class="hero-title">Car Details</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero-subtitle">Tell us about your vehicle</p>',
        unsafe_allow_html=True,
    )

    options = load_dropdown_options()

    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("Brand", options["brand"], key="detail_brand")
        st.session_state.brand = brand
        model_name = st.text_input("Model", key="detail_model")
        st.session_state.model_name = model_name
        year = st.slider("Year of Manufacture", min_value=1995, max_value=CURRENT_YEAR,
                          value=2018, key="detail_year")
        st.session_state.year = year
        km_driven = st.number_input("Kilometers Driven", min_value=0, value=45000,
                                     step=1000, key="detail_km")
        st.session_state.km_driven = km_driven

    with col2:
        fuel_type = st.selectbox("Fuel Type", options["fuel_type"], key="detail_fuel")
        st.session_state.fuel_type = fuel_type
        transmission = st.selectbox("Transmission", options["transmission"], key="detail_trans")
        st.session_state.transmission = transmission
        city = st.selectbox("City", options["city"], key="detail_city")
        st.session_state.city = city
        body_type = st.selectbox("Body Type", options["body_type"], key="detail_body")
        st.session_state.body_type = body_type

    st.markdown("### Ownership")
    owner_count = st.slider("Number of Previous Owners", min_value=0, max_value=5,
                             value=1, key="detail_owner")
    st.session_state.owner_count = owner_count

    st.markdown("### Vehicle Condition")
    condition = st.radio("Select condition from photos:", ["Excellent", "Good", "Fair", "Poor"],
                         horizontal=True, key="detail_condition")
    st.session_state.condition = condition

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "photos"
            st.rerun()
    with col_next:
        if st.button("Next →", use_container_width=True, type="primary"):
            st.session_state.page = "loading"
            st.rerun()


# ============================================================================
# PAGE: LOADING / AI ANALYZING
# ============================================================================
def page_loading():
    st.markdown(
        '<h1 class="hero-title">AI Analyzing...</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero-subtitle">Processing your vehicle data</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            ✓ Analyzing images
            
            ✓ Detecting damage
            
            ⏳ Evaluating specs
            """
        )
    with col2:
        st.markdown('<div class="loading-ring"></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(
            """
            ⏳ Computing price
            
            ⏳ Comparing market
            
            ⏳ Building report
            """
        )

    time.sleep(2)

    # --- do the actual prediction ---
    if not os.path.exists(MODEL_PATH):
        st.error("Model not found. Run `python src/fusion.py --train` first.")
        return

    car_age = CURRENT_YEAR - st.session_state.year
    km_per_year = st.session_state.km_driven / car_age if car_age > 0 else st.session_state.km_driven

    car_details = {
        "brand": st.session_state.brand,
        "year": st.session_state.year,
        "km_driven": st.session_state.km_driven,
        "fuel_type": st.session_state.fuel_type,
        "transmission": st.session_state.transmission,
        "city": st.session_state.city,
        "body_type": st.session_state.body_type,
        "car_age": car_age,
        "km_per_year": km_per_year,
        "brand_tier": brand_tier(st.session_state.brand),
        "age_squared": car_age ** 2,
        "is_new_ish": int(car_age <= 3),
        "owner_count": st.session_state.owner_count,
    }

    photo_paths = save_uploaded_photos(st.session_state.uploaded_files) if st.session_state.uploaded_files else []
    condition_result = get_real_condition_score(photo_paths)

    model, feature_cols = load_model()
    row = {col: car_details.get(col, np.nan) for col in feature_cols}
    row["condition_score"] = condition_result["condition_score"]
    X_row = pd.DataFrame([row])[feature_cols]

    # categorical handling
    cat_cols = ["brand", "fuel_type", "transmission", "city", "body_type", "brand_tier"]
    for col in cat_cols:
        if col in X_row.columns:
            X_row[col] = X_row[col].astype("category")

    result = explain(model, X_row)

    # what-if perfect
    row_perfect = dict(row)
    row_perfect["condition_score"] = 1.0
    X_perfect = pd.DataFrame([row_perfect])[feature_cols]
    for col in cat_cols:
        if col in X_perfect.columns:
            X_perfect[col] = X_perfect[col].astype("category")
    result_perfect = explain(model, X_perfect)
    condition_cost = result_perfect["final_price"] - result["final_price"]

    st.session_state.result = result
    st.session_state.condition_result = condition_result
    st.session_state.condition_cost = condition_cost

    time.sleep(1)
    st.session_state.page = "report"
    st.rerun()


# ============================================================================
# PAGE: PRICE REPORT
# ============================================================================
def page_report():
    step_indicator(4)

    result = st.session_state.result
    condition_result = st.session_state.condition_result
    condition_cost = st.session_state.condition_cost

    st.markdown(
        '<p class="hero-subtitle">Your Estimated Price</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="price-display">₹ {result["final_price"]:,.0f}</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            get_condition_badge_html(condition_result["condition_score"]),
            unsafe_allow_html=True,
        )
    with col2:
        st.metric("Score", f'{condition_result["condition_score"]:.2f} / 1.0')
    with col3:
        if condition_result["damage_types"]:
            st.caption(f'🔍 Damage: {", ".join(condition_result["damage_types"])}')

    st.markdown("### Why this price?")
    for item in result["breakdown"][:10]:
        sign = "+" if item["rupee_impact"] >= 0 else "−"
        cls = "factor-value-positive" if item["rupee_impact"] >= 0 else "factor-value-negative"
        st.markdown(
            f'''
            <div class="factor-card">
                <div class="factor-label">{item["feature"]}</div>
                <span class="{cls}">{sign}₹ {abs(item["rupee_impact"]):,.0f}</span>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    if condition_cost > 1000:
        st.markdown(
            f'<div class="tips-box">'
            f'💡 <strong>Insight:</strong> If this car had no visible damage, '
            f'it would likely be worth ~₹ {condition_cost:,.0f} more '
            f'(₹ {result["final_price"] + condition_cost:,.0f})'
            f'</div>',
            unsafe_allow_html=True,
        )

    col_back, col_restart = st.columns(2)
    with col_back:
        if st.button("← Back to Details", use_container_width=True):
            st.session_state.page = "details"
            st.rerun()
    with col_restart:
        if st.button("🔄 Start Over", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    st.set_page_config(page_title="AutoGauge", page_icon="🚗", layout="wide")
    inject_css()

    if "page" not in st.session_state:
        st.session_state.page = "welcome"

    if st.session_state.page == "welcome":
        page_welcome()
    elif st.session_state.page == "photos":
        page_photos()
    elif st.session_state.page == "details":
        page_details()
    elif st.session_state.page == "loading":
        page_loading()
    elif st.session_state.page == "report":
        page_report()


if __name__ == "__main__":
    import time
    main()
