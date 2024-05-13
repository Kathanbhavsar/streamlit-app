import streamlit as st
import dashboard
import analysis
import growth_comparison
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Set page configuration
st.set_page_config(page_title="Dealership Dashboard", layout="wide")

# Define the user credentials
with open("/Users/apple/Desktop/rocked/streamlit-app/config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create an instance of the Authenticate class
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["preauthorized"],
)

# Custom CSS styles
st.markdown(
    """
    <style>
    body {
        background-color: #f0f2f6 !important;
    }
    .stButton button {
        background-color: #6C5CE7;
        color: white;
        font-weight: bold;
        border-radius: 0.25rem;
        padding: 0.5rem 1rem;
        margin-top: 1rem;
    }
    .stTextInput input {
        border-radius: 0.25rem;
        padding: 0.5rem;
        border: 1px solid #dcdfe6;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Login page
def login():
    st.markdown('<div class="logo-container"></div>', unsafe_allow_html=True)
    st.image(
        "/Users/apple/Desktop/rocked/streamlit-app/Capture-2024-05-08-153659.png",
        width=200,
    )  # Replace with your logo image
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("Login")
    authenticator.login()
    if st.session_state["authentication_status"]:
        st.success("Logged in successfully!")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# Check authentication status
if st.session_state["authentication_status"]:
    # Create a sidebar menu for navigation
    menu = ["Dashboard", "User Analytics", "Growth Comparison"]
    choice = st.sidebar.selectbox("Select a page", menu)

    # Display the selected page
    if choice == "Dashboard":
        dashboard.main()
    elif choice == "User Analytics":
        analysis.main()
    elif choice == "Growth Comparison":
        growth_comparison.main()

    # Logout button
    authenticator.logout("Logout", "sidebar")
else:
    login()
