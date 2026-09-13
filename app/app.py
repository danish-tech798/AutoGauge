"""
app_complete.py - AutoGauge COMPLETE VERSION
With all features + safe error handling
"""

import os, sys, tempfile, time, json
import numpy as np, pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

try:
    from src.db import db
    from src.fusion import get_real_condition_score, DAMAGE_MODEL_PATH
    from src.explainability import load_model_and_features, prepare_for_model, explain, _format_value
except:
    pass

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed_cars.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fusion_model.pkl")
CURRENT_YEAR = 2026

LUXURY_BRANDS = {"bmw", "audi", "mercedes benz", "jaguar", "land rover", "porsche", "volvo"}
PREMIUM_BRANDS = {"toyota", "honda", "hyundai", "skoda", "volkswagen", "kia", "jeep", "mg", "ford"}

CUSTOM_CSS = """
<style>
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.stApp {
    background: linear-gradient(-45deg, #0F0A20, #1a0f2e, #0F0A20, #050a15);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}
.stat-card {
    background: rgba(124, 58, 237, 0.1);
    border: 1px solid rgba(124, 58, 237, 0.2);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.stat-number {
    font-size: 28px;
    font-weight: 900;
    color: #7C3AED;
}
.stat-label {
    color: #A78BFA;
    font-size: 12px;
    margin-top: 4px;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================================
# SAFE DATA CONVERSION
# ============================================================================
def safe_float(val):
    """Safely convert to float"""
    try:
        if val is None or val == 'Unknown':
            return 0.0
        if isinstance(val, bytes):
            return 0.0
        if isinstance(val, str):
            return float(val.strip()) if val.strip() else 0.0
        return float(val)
    except:
        return 0.0

def safe_str(val):
    """Safely convert to string"""
    if val is None:
        return "Unknown"
    if isinstance(val, bytes):
        return "Unknown"
    return str(val).title() if val else "Unknown"

def brand_tier(brand):
    b = safe_str(brand).lower()
    if b in LUXURY_BRANDS:
        return "luxury"
    if b in PREMIUM_BRANDS:
        return "premium"
    return "economy"

# ============================================================================
# CACHE FUNCTIONS
# ============================================================================
@st.cache_data
def load_options():
    if not os.path.exists(DATA_PATH):
        return {"brand": ["maruti", "hyundai"], "fuel_type": ["petrol", "diesel"], 
                "transmission": ["manual", "automatic"], "city": ["pune", "mumbai"], 
                "body_type": ["hatchback", "sedan"]}
    try:
        df = pd.read_csv(DATA_PATH)
        return {
            "brand": sorted(df["brand"].dropna().unique().tolist()),
            "fuel_type": sorted(df["fuel_type"].dropna().unique().tolist()),
            "transmission": sorted(df["transmission"].dropna().unique().tolist()),
            "city": sorted(df["city"].dropna().unique().tolist()),
            "body_type": sorted(df["body_type"].dropna().unique().tolist()),
        }
    except:
        return {"brand": ["maruti"], "fuel_type": ["petrol"], "transmission": ["manual"], 
                "city": ["pune"], "body_type": ["hatchback"]}

@st.cache_resource
def load_model():
    try:
        return load_model_and_features()
    except:
        return None, None

# ============================================================================
# LOGIN PAGE
# ============================================================================
def page_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<h1 style="text-align:center; background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">AutoGauge</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#A78BFA;">AI-Powered Used Vehicle Price Estimator</p>', unsafe_allow_html=True)
        st.write("")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.markdown("### Welcome Back")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", use_container_width=True, type="primary"):
                if email and password:
                    success, user_data = db.login(email, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_data["id"]
                        st.session_state.user_name = user_data.get("full_name") or email.split("@")[0]
                        st.session_state.page = "dashboard"
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            st.markdown("### Create Account")
            full_name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm", type="password", key="signup_confirm")
            phone = st.text_input("Phone", key="signup_phone")
            
            if st.button("Sign Up", use_container_width=True, type="primary"):
                if not all([full_name, email, password, confirm]):
                    st.error("Fill all required fields")
                elif password != confirm:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be 6+ characters")
                else:
                    success, msg = db.signup(email, password, full_name, phone)
                    if success:
                        st.success(msg)
                        st.info("Now login with your credentials!")
                    else:
                        st.error(msg)

# ============================================================================
# DASHBOARD PAGE
# ============================================================================
def page_dashboard():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f'<h3>Welcome back, <span style="color:#EC4899;">{st.session_state.get("user_name", "User")}</span>!</h3>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Stats
    try:
        est_count = db.get_estimation_count(st.session_state.user_id)
        saved_count = len(db.get_saved_vehicles(st.session_state.user_id))
    except:
        est_count, saved_count = 0, 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{est_count}</div><div class="stat-label">Total Estimations</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{saved_count}</div><div class="stat-label">Saved Vehicles</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">⭐</div><div class="stat-label">Premium Member</div></div>', unsafe_allow_html=True)
    
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔮 New Estimation", use_container_width=True, type="primary"):
            st.session_state.page = "welcome"
            st.rerun()
    with col2:
        if st.button("📋 My History", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
    with col3:
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Recent Estimations")
    
    try:
        history = db.get_estimation_history(st.session_state.user_id, limit=5)
        if history:
            for est in history:
                brand = safe_str(est.get('brand'))
                model = safe_str(est.get('model'))
                year = est.get('year', 'N/A')
                price = safe_float(est.get('predicted_price'))
                km = est.get('km_driven', 0)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{brand} {model}** ({year}) • {km:,} km")
                with col2:
                    st.markdown(f'<p style="color:#7C3AED; font-weight:700;">₹ {price:,.0f}</p>', unsafe_allow_html=True)
                with col3:
                    st.caption(est.get('created_at', '')[:10])
        else:
            st.info("No estimations yet")
    except Exception as e:
        st.error(f"Error loading history")

# ============================================================================
# HISTORY PAGE
# ============================================================================
def page_history():
    st.markdown("### 📋 Estimation History")
    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    try:
        history = db.get_estimation_history(st.session_state.user_id, limit=50)
        if history:
            for est in history:
                brand = safe_str(est.get('brand'))
                model = safe_str(est.get('model'))
                year = est.get('year', 'N/A')
                price = safe_float(est.get('predicted_price'))
                km = est.get('km_driven', 0)
                score = safe_float(est.get('condition_score'))
                created = est.get('created_at', '')[:10]
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{brand} {model}** ({year})")
                    st.caption(f"{km:,} km")
                with col2:
                    st.markdown(f'<p style="color:#7C3AED; font-weight:700;">₹ {price:,.0f}</p>', unsafe_allow_html=True)
                with col3:
                    st.caption(f"Score: {score:.2f}")
                with col4:
                    st.caption(created)
        else:
            st.info("No history")
    except:
        st.error("Error loading history")

# ============================================================================
# PROFILE PAGE
# ============================================================================
def page_profile():
    st.markdown("### 👤 My Profile")
    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    try:
        user = db.get_user(st.session_state.user_id)
        if user:
            st.text_input("Email", value=user.get('email', ''), disabled=True)
            new_name = st.text_input("Full Name", value=user.get('full_name', '') or "")
            new_phone = st.text_input("Phone", value=user.get('phone', '') or "")
            
            if st.button("Update Profile", use_container_width=True):
                success, msg = db.update_user_profile(st.session_state.user_id, new_name, new_phone)
                if success:
                    st.success(msg)
                    st.session_state.user_name = new_name
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
    except:
        st.error("Error loading profile")

# ============================================================================
# WELCOME PAGE
# ============================================================================
def page_welcome():
    st.markdown('<h1 style="text-align:center; color:#A78BFA;">AutoGauge</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#7C3AED;">Upload vehicle images and get accurate price estimate</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("Get Started →", use_container_width=True, type="primary"):
            st.session_state.page = "photos"
            st.rerun()

# ============================================================================
# PHOTOS PAGE
# ============================================================================
def page_photos():
    st.markdown("### 📸 Upload Vehicle Photos")
    uploaded = st.file_uploader("Upload car photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded:
        st.session_state.uploaded_files = uploaded
        cols = st.columns(min(len(uploaded), 3))
        for i, f in enumerate(uploaded):
            with cols[i % 3]:
                st.image(f, use_container_width=True, caption=f.name)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "welcome"
            st.rerun()
    with col2:
        if st.button("Next →", use_container_width=True, type="primary"):
            if uploaded:
                st.session_state.page = "details"
                st.rerun()
            else:
                st.error("Upload at least 1 photo")

# ============================================================================
# DETAILS PAGE
# ============================================================================
def page_details():
    st.markdown("### 🚗 Vehicle Details")
    options = load_options()
    
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("Brand", options["brand"], key="detail_brand")
        st.session_state.brand = brand
        year = st.slider("Year", 1995, CURRENT_YEAR, 2018, key="detail_year")
        st.session_state.year = year
        fuel = st.selectbox("Fuel Type", options["fuel_type"], key="detail_fuel")
        st.session_state.fuel_type = fuel
        km = st.number_input("Kilometers Driven", 0, 500000, 45000, step=1000, key="detail_km")
        st.session_state.km_driven = km
    
    with col2:
        model = st.text_input("Model", key="detail_model")
        st.session_state.model_name = model
        trans = st.selectbox("Transmission", options["transmission"], key="detail_trans")
        st.session_state.transmission = trans
        city = st.selectbox("City", options["city"], key="detail_city")
        st.session_state.city = city
        owner = st.slider("Number of Owners", 0, 5, 1, key="detail_owner")
        st.session_state.owner_count = owner
    
    body = st.selectbox("Body Type", options["body_type"], key="detail_body")
    st.session_state.body_type = body
    
    condition = st.radio("Vehicle Condition", ["Excellent", "Good", "Average", "Poor"], horizontal=True, key="detail_condition")
    st.session_state.condition = condition
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "photos"
            st.rerun()
    with col2:
        if st.button("Estimate Price →", use_container_width=True, type="primary"):
            if model:
                st.session_state.page = "analyzing"
                st.rerun()
            else:
                st.error("Enter model name")

# ============================================================================
# ANALYZING PAGE
# ============================================================================
def page_analyzing():
    st.markdown("### ⏳ AI Analyzing...")
    
    with st.spinner("Processing..."):
        time.sleep(2)
        
        try:
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
            
            # Get condition score from photos
            photo_paths = []
            if st.session_state.get("uploaded_files"):
                tmp_dir = tempfile.mkdtemp()
                for f in st.session_state.uploaded_files:
                    path = os.path.join(tmp_dir, f.name)
                    with open(path, "wb") as out:
                        out.write(f.getbuffer())
                    photo_paths.append(path)
            
            condition_result = get_real_condition_score(photo_paths)
            
            # Get price prediction
            model, feature_cols = load_model()
            if model and feature_cols:
                row = {col: car_details.get(col, np.nan) for col in feature_cols}
                row["condition_score"] = condition_result["condition_score"]
                X_row = pd.DataFrame([row])[feature_cols]
                
                cat_cols = ["brand", "fuel_type", "transmission", "city", "body_type", "brand_tier"]
                for col in cat_cols:
                    if col in X_row.columns:
                        X_row[col] = X_row[col].astype("category")
                
                result = explain(model, X_row)
                
                # What-if perfect condition
                row_perfect = dict(row)
                row_perfect["condition_score"] = 1.0
                X_perfect = pd.DataFrame([row_perfect])[feature_cols]
                for col in cat_cols:
                    if col in X_perfect.columns:
                        X_perfect[col] = X_perfect[col].astype("category")
                result_perfect = explain(model, X_perfect)
                condition_cost = result_perfect["final_price"] - result["final_price"]
                
                # Save to database
                estimation_data = {
                    **car_details,
                    "predicted_price": result["final_price"],
                    "condition_score": condition_result["condition_score"],
                    "damage_detected": condition_result.get("damage_types", []),
                    "base_price": result.get("base_price", result["final_price"]),
                }
                
                success, est_id = db.save_estimation(st.session_state.user_id, estimation_data)
                st.session_state.estimation_id = est_id
                st.session_state.result = result
                st.session_state.condition_result = condition_result
                st.session_state.condition_cost = condition_cost
                
                st.session_state.page = "report"
                st.rerun()
            else:
                st.error("Model not loaded. Train with: python src/fusion.py --train")
        
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")

# ============================================================================
# REPORT PAGE
# ============================================================================
def page_report():
    st.markdown("### 💰 Price Report")
    
    result = st.session_state.get("result", {})
    condition_result = st.session_state.get("condition_result", {})
    condition_cost = st.session_state.get("condition_cost", 0)
    
    price = safe_float(result.get("final_price"))
    
    st.markdown(f'<h2 style="text-align:center; background:linear-gradient(135deg, #7C3AED 0%, #EC4899 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">₹ {price:,.0f}</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        score = condition_result.get("condition_score", 0)
        st.metric("Condition Score", f"{score:.2f} / 1.0")
    with col2:
        damage = condition_result.get("damage_types", [])
        if damage:
            st.write(f"**Damage Detected:** {', '.join(damage)}")
    
    st.markdown("---")
    st.markdown("### Price Breakdown")
    
    breakdown = result.get("breakdown", [])
    for item in breakdown[:8]:
        sign = "+" if item["rupee_impact"] >= 0 else "−"
        color = "#10B981" if item["rupee_impact"] >= 0 else "#EF4444"
        st.markdown(f'<div style="display:flex; justify-content:space-between; padding:8px; background:rgba(124,58,237,0.05); border-radius:8px; margin-bottom:8px;"><span>{item["feature"]}</span><span style="color:{color}; font-weight:700;">{sign}₹ {abs(item["rupee_impact"]):,.0f}</span></div>', unsafe_allow_html=True)
    
    if condition_cost > 1000:
        perfect_price = price + condition_cost
        st.markdown(f'<div style="background:rgba(59,130,246,0.1); border-left:4px solid #3B82F6; padding:12px; border-radius:8px; margin-top:16px;">💡 If no damage: ₹ {perfect_price:,.0f}</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Vehicle", use_container_width=True):
            try:
                est_id = st.session_state.get("estimation_id", 0)
                if est_id > 0:
                    brand = safe_str(st.session_state.brand)
                    model = safe_str(st.session_state.model_name)
                    db.save_vehicle(st.session_state.user_id, est_id, f"{brand} {model}")
                    st.success("Vehicle saved!")
            except:
                st.error("Could not save")
    
    with col2:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    
    with col3:
        if st.button("🔄 New Estimation", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                if key not in ["logged_in", "user_id", "user_name"]:
                    del st.session_state[key]
            st.session_state.page = "welcome"
            st.rerun()

# ============================================================================
# MAIN
# ============================================================================
def main():
    st.set_page_config(page_title="AutoGauge", page_icon="🚗", layout="wide")
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    if not st.session_state.logged_in:
        page_login()
    elif st.session_state.page == "dashboard":
        page_dashboard()
    elif st.session_state.page == "history":
        page_history()
    elif st.session_state.page == "profile":
        page_profile()
    elif st.session_state.page == "welcome":
        page_welcome()
    elif st.session_state.page == "photos":
        page_photos()
    elif st.session_state.page == "details":
        page_details()
    elif st.session_state.page == "analyzing":
        page_analyzing()
    elif st.session_state.page == "report":
        page_report()

if __name__ == "__main__":
    main()
