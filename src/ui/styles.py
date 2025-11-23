import streamlit as st

# Color Palette
COLORS = {
    "primary": "#FF4B4B",
    "secondary": "#262730",
    "background": "#0E1117",
    "text": "#FAFAFA",
    "success": "#00CC96",
    "warning": "#FFA15A",
    "error": "#EF553B",
    "info": "#636EFA",
    "card_bg": "#1E1E1E",
    "border": "#333333"
}

def load_css():
    """Load custom CSS"""
    st.markdown(f"""
        <style>
            /* Global Settings */
            .stApp {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
            
            /* Card Style */
            .css-card {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            
            /* Sidebar */
            [data-testid="stSidebar"] {{
                background-color: {COLORS['secondary']};
                border-right: 1px solid {COLORS['border']};
            }}
            
            /* Buttons */
            .stButton > button {{
                border-radius: 6px;
                font-weight: 600;
            }}
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
                background-color: transparent;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                height: 40px;
                white-space: pre-wrap;
                background-color: {COLORS['card_bg']};
                border-radius: 6px;
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                padding: 0 16px;
            }}
            
            .stTabs [aria-selected="true"] {{
                background-color: {COLORS['primary']} !important;
                color: white !important;
                border: none;
            }}
            
            /* Dataframes */
            [data-testid="stDataFrame"] {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            
            /* Metric Value Size - Make it smaller and more proportional */
            [data-testid="stMetricValue"] {{
                font-size: 1.5rem !important;
                font-weight: 600;
            }}
            
            /* Metric Label */
            [data-testid="stMetricLabel"] {{
                font-size: 0.875rem !important;
            }}
            
            /* Navigation Spacing */
            .stApp h1 + .nav-container,
            .stApp h2 + .nav-container,
            .stApp h3 + .nav-container {{
                margin-top: 1.5rem !important;
            }}
            
            .nav-container + hr {{
                margin-top: 0rem !important;
                margin-bottom: 0rem !important;
            }}
            
            /* Divider after navigation */
            hr {{
                margin-top: 0rem !important;
                margin-bottom: 3rem !important;
                padding-top: 0rem !important;
                padding-bottom: 0rem !important;
            }}
            
        </style>
    """, unsafe_allow_html=True)

def card_container(key=None):
    """Create a container with card styling"""
    container = st.container()
    return container
