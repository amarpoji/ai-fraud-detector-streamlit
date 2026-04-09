"""
Streamlit Frontend for Phishing Detection
Provides an interactive UI for analyzing emails and messages
"""

import streamlit as st
import requests
import json
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Phishing Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .risk-high {
        color: #d32f2f;
        font-weight: bold;
    }
    .risk-medium {
        color: #f57c00;
        font-weight: bold;
    }
    .risk-low {
        color: #388e3c;
        font-weight: bold;
    }
    .metric-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Configuration
# ============================================================================

import os
API_URL = os.getenv("API_URL", "http://localhost:8000")


@st.cache_resource
def get_api_client():
    """Get API client (cached)"""
    return requests.Session()


def get_available_models():
    """Fetch available models from API"""
    try:
        response = requests.get(f"{API_URL}/models", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.warning(f"Could not fetch models: {e}")
        return None


def analyze_message(message: str, run_id: Optional[str] = None) -> dict:
    """Send message to API for analysis"""
    try:
        payload = {
            "message": message,
            "model_run_id": run_id
        }
        
        response = requests.post(
            f"{API_URL}/analyze",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure the backend is running: `python -m uvicorn backend.src.app:app --reload`")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def draw_risk_gauge(risk_score: float):
    """Draw a risk gauge visualization"""
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(projection='polar'))
    
    # Gauge parameters
    theta = np.linspace(np.pi, 2*np.pi, 100)
    r_inner = 0.5
    r_outer = 1.0
    
    # Color zones
    # Green zone: 0-33
    theta_green = np.linspace(np.pi, np.pi + np.pi/3, 50)
    ax.fill_between(theta_green, r_inner, r_outer, color='#388e3c', alpha=0.6, label='Safe')
    
    # Yellow zone: 33-66
    theta_yellow = np.linspace(np.pi + np.pi/3, np.pi + 2*np.pi/3, 50)
    ax.fill_between(theta_yellow, r_inner, r_outer, color='#f57c00', alpha=0.6, label='Suspicious')
    
    # Red zone: 66-100
    theta_red = np.linspace(np.pi + 2*np.pi/3, 2*np.pi, 50)
    ax.fill_between(theta_red, r_inner, r_outer, color='#d32f2f', alpha=0.6, label='Danger')
    
    # Needle
    needle_angle = np.pi + (risk_score / 100) * np.pi
    ax.plot([needle_angle, needle_angle], [0, r_outer], 'k-', linewidth=3)
    ax.plot(needle_angle, r_outer, 'ko', markersize=10)
    
    # Text labels
    ax.text(np.pi + np.pi/6, r_outer + 0.3, '33', ha='center', fontsize=10, weight='bold')
    ax.text(np.pi + np.pi/2, r_outer + 0.3, '66', ha='center', fontsize=10, weight='bold')
    
    # Center text with risk score
    ax.text(0, 0, f'{risk_score:.1f}', ha='center', va='center', 
            fontsize=24, weight='bold', transform=ax.transData)
    
    ax.set_ylim(0, 1.3)
    ax.set_theta_offset(0)
    ax.set_theta_direction(1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    plt.tight_layout()
    return fig


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Responding")
    except:
        st.error("❌ Cannot reach API")
    
    st.divider()
    
    # Model Selection
    st.subheader("Model Selection")
    
    models_data = get_available_models()
    if models_data and models_data.get('models'):
        models = models_data['models']
        model_options = {m['name']: m['run_id'] for m in models}
        
        selected_model = st.selectbox(
            "Choose Model",
            options=list(model_options.keys()),
            help="Select which trained model to use for analysis"
        )
        selected_run_id = model_options[selected_model]
        
        # Show model stats
        selected_model_data = next((m for m in models if m['name'] == selected_model), None)
        if selected_model_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("F1", f"{selected_model_data['f1_score']:.4f}")
            with col2:
                st.metric("Accuracy", f"{selected_model_data['accuracy']:.4f}")
            with col3:
                st.metric("ROC-AUC", f"{selected_model_data['roc_auc']:.4f}")
    else:
        st.warning("No models available. Run training first.")
        selected_run_id = None
    
    st.divider()
    
    # Analysis History
    st.subheader("📊 Analysis History")
    if 'history' in st.session_state:
        for i, item in enumerate(st.session_state.history[-5:], 1):  # Show last 5
            with st.expander(f"{i}. {item['label']} - {item['risk_score']:.1f}%"):
                st.text(item['message'][:100] + "..." if len(item['message']) > 100 else item['message'])
    else:
        st.info("No analysis history yet")
    
    st.divider()
    
    # About
    st.subheader("ℹ️ About")
    st.info(
        """
        **Phishing Detector v1.0**
        
        AI-powered analysis for detecting phishing and fraudulent messages.
        
        - 🤖 Multiple models
        - 📊 Risk scoring
        - 🚩 Red flag detection
        """
    )


# ============================================================================
# Main Content
# ============================================================================

st.title("🔍 Phishing Detector")
st.markdown("AI-Powered Email & Message Analysis")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []


# ============================================================================
# Input Section
# ============================================================================

st.header("📨 Analyze Message")

col1, col2 = st.columns([3, 1])

with col1:
    message = st.text_area(
        "Paste the email or message text:",
        placeholder="Dear Customer, Please verify your account...",
        height=150,
        key="message_input"
    )

with col2:
    st.markdown("")  # Spacer
    st.markdown("")  # Spacer
    analyze_button = st.button("🔍 Analyze", use_container_width=True, type="primary")


# ============================================================================
# Analysis Results
# ============================================================================

if analyze_button and message:
    if not selected_run_id:
        st.error("❌ No model selected. Please select a model in the sidebar.")
    else:
        with st.spinner("🔄 Analyzing message..."):
            result = analyze_message(message, selected_run_id)
        
        if result:
            # Add to history
            st.session_state.history.append({
                'timestamp': datetime.now().isoformat(),
                'message': message[:100],
                'label': result.get('label'),
                'risk_score': result.get('risk_score', 0),
                'model': result.get('model_used')
            })
            
            # Display results
            st.success("✅ Analysis Complete")
            
            # Risk Score with Gauge
            risk_score = result.get('risk_score', 0)
            label = result.get('label', 'Unknown')
            confidence = result.get('confidence', 0)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Risk indicator
                if risk_score >= 70:
                    risk_class = "risk-high"
                    emoji = "🔴"
                elif risk_score >= 40:
                    risk_class = "risk-medium"
                    emoji = "🟠"
                else:
                    risk_class = "risk-low"
                    emoji = "🟢"
                
                st.markdown(f"""
                <div class="metric-box" style="background: #f0f0f0; border-left: 4px solid {'#d32f2f' if risk_score >= 70 else '#f57c00' if risk_score >= 40 else '#388e3c'};">
                    <p style="margin: 0; color: #666;">Classification</p>
                    <h2 style="margin: 5px 0; {risk_class}">{emoji} {label}</h2>
                    <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">{risk_score:.1f}%</p>
                    <p style="margin: 5px 0; color: #999; font-size: 12px;">Confidence: {confidence:.2%}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Gauge
                fig = draw_risk_gauge(risk_score)
                st.pyplot(fig, use_container_width=True)
            
            st.divider()
            
            # Explanation
            st.subheader("📌 Explanation")
            st.info(result.get('explanation', 'No explanation available'))
            
            st.divider()
            
            # Red Flags
            red_flags = result.get('red_flags', [])
            if red_flags:
                st.subheader("🚩 Red Flags Detected")
                
                for i, flag in enumerate(red_flags, 1):
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        confidence_pct = flag.get('confidence', 0) * 100
                        if confidence_pct >= 70:
                            st.error(f"#{i}")
                        elif confidence_pct >= 40:
                            st.warning(f"#{i}")
                        else:
                            st.info(f"#{i}")
                    
                    with col2:
                        st.markdown(f"""
                        **{flag.get('category', 'Unknown')}**
                        
                        {flag.get('description', 'No description')}
                        
                        _Confidence: {confidence_pct:.1f}%_
                        """)
            else:
                st.success("✅ No red flags detected!")
            
            st.divider()
            
            # Model Info
            st.subheader("🤖 Model Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Model", result.get('model_used', 'Unknown')[:20])
            with col2:
                st.metric("Risk Score", f"{risk_score:.1f}%")
            with col3:
                st.metric("Confidence", f"{confidence:.2%}")

elif analyze_button:
    st.error("❌ Please enter a message to analyze")


# ============================================================================
# Examples Section
# ============================================================================

st.divider()

with st.expander("💡 Example Messages"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Example Phishing")
        phishing_example = "Dear Valued Customer, Your account has been compromised! Click here immediately to verify your credentials. Act NOW or your account will be suspended. https://verify-account-now.com"
        if st.button("📋 Copy Phishing Example"):
            st.session_state.message_input = phishing_example
            st.rerun()
    
    with col2:
        st.subheader("Example Legitimate")
        legitimate_example = "Hi John, Hope you're doing well. Just checking in on the project status. Let me know if you need anything from my end. Best regards, Sarah"
        if st.button("📋 Copy Legitimate Example"):
            st.session_state.message_input = legitimate_example
            st.rerun()


# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Phishing Detector v1.0 | Powered by MLflow & Streamlit</p>
    <p>For questions, visit: <a href="#">Documentation</a></p>
</div>
""", unsafe_allow_html=True)
