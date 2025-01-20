import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import sqlite3
import hashlib

# Database setup
def create_users_table():
    """Create a table to store user credentials if it doesn't exist."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

# Password hashing
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

# User registration
def register_user(username, password):
    """Register a new user."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# User login
def verify_user(username, password):
    """Verify user credentials."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password):
        return True
    return False

# Function to load data
def load_data(file):
    """Load data with error handling."""
    if file is None:
        st.warning("Please upload a file.")
        return None

    file_extension = file.name.split('.')[-1].lower()
    try:
        if file_extension == 'csv':
            return pd.read_csv(file)
        elif file_extension in ['xls', 'xlsx']:
            return pd.read_excel(file)
        elif file_extension == 'json':
            return pd.read_json(file)
        else:
            st.error("Unsupported file format. Supported formats: CSV, Excel, JSON.")
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

# Function to get numeric columns
def get_numeric_columns(df):
    """Return list of numeric columns in dataframe."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

# Function to clean data
def clean_data(df, cleaning_options):
    """Clean dataframe based on selected options."""
    if df is None:
        return None
    
    cleaned_df = df.copy()
    changes = []
    
    if 'remove_duplicates' in cleaning_options:
        initial_rows = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates()
        if len(cleaned_df) != initial_rows:
            changes.append(f"Removed {initial_rows - len(cleaned_df)} duplicate rows")
    
    if 'handle_missing' in cleaning_options:
        missing_strategy = st.selectbox(
            "Choose missing value strategy",
            ["Drop rows", "Mean imputation", "Median imputation", "Zero imputation"]
        )
        
        initial_missing = cleaned_df.isnull().sum().sum()
        
        if missing_strategy == "Drop rows":
            cleaned_df = cleaned_df.dropna()
        else:
            numeric_columns = get_numeric_columns(cleaned_df)
            for col in numeric_columns:
                if cleaned_df[col].isnull().any():
                    if missing_strategy == "Mean imputation":
                        cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mean())
                    elif missing_strategy == "Median imputation":
                        cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
                    elif missing_strategy == "Zero imputation":
                        cleaned_df[col] = cleaned_df[col].fillna(0)
        
        final_missing = cleaned_df.isnull().sum().sum()
        if initial_missing > final_missing:
            changes.append(f"Handled {initial_missing - final_missing} missing values")
    
    if 'normalize_data' in cleaning_options:
        scaling_method = st.selectbox(
            "Choose scaling method",
            ["StandardScaler", "MinMaxScaler"]
        )
        
        numeric_columns = get_numeric_columns(cleaned_df)
        if numeric_columns:
            if scaling_method == "StandardScaler":
                scaler = StandardScaler()
            else:
                scaler = MinMaxScaler()
                
            cleaned_df[numeric_columns] = scaler.fit_transform(cleaned_df[numeric_columns])
            changes.append(f"Normalized {len(numeric_columns)} numeric columns using {scaling_method}")
    
    return cleaned_df, changes

# Function to create visualizations
def create_visualization(df, chart_type, x_col, y_col, color_col=None, color_theme=None, custom_color=None):
    """Create visualization based on selected chart type and columns."""
    try:
        if chart_type == "Bar Chart":
            fig = px.bar(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Line Chart":
            fig = px.line(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Scatter Plot":
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Box Plot":
            fig = px.box(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Histogram":
            fig = px.histogram(df, x=x_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Pie Chart":
            fig = px.pie(df, names=x_col, values=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Area Chart":
            fig = px.area(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Violin Plot":
            fig = px.violin(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Heatmap":
            fig = px.imshow(df.corr(), text_auto=True, color_continuous_scale=custom_color if custom_color else color_theme)
        elif chart_type == "3D Scatter Plot":
            fig = px.scatter_3d(df, x=x_col, y=y_col, z=color_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "3D Surface Plot":
            fig = go.Figure(data=[go.Surface(z=df.values)])
        elif chart_type == "Bubble Chart":
            fig = px.scatter(df, x=x_col, y=y_col, size=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Radar Chart":
            fig = px.line_polar(df, r=y_col, theta=x_col, color=color_col, line_close=True, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Polar Chart":
            fig = px.scatter_polar(df, r=y_col, theta=x_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Tree Map":
            fig = px.treemap(df, path=[x_col], values=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Sunburst Chart":
            fig = px.sunburst(df, path=[x_col], values=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Funnel Chart":
            fig = px.funnel(df, x=x_col, y=y_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Gantt Chart":
            fig = px.timeline(df, x_start=x_col, x_end=y_col, y=color_col, color=color_col, color_discrete_sequence=[custom_color] if custom_color else color_theme)
        elif chart_type == "Candlestick Chart":
            fig = go.Figure(data=[go.Candlestick(x=df[x_col], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        
        # Customize layout
        fig.update_layout(
            title=f"{chart_type} of {y_col} vs {x_col}",
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

# Home Page
def home_page():
    st.markdown(
        """
        <style>
        .welcome {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 80vh;
            font-size: 2.5em;
            font-weight: bold;
            color: var(--primary-color);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="welcome">Welcome to the Data Visualization App</div>', unsafe_allow_html=True)

def login_page():
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 20px;
            border: 1px solid var(--secondary-background-color);
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            background-color: var(--background-color);
        }
        .login-container h1 {
            text-align: center;
            color: var(--primary-color);
        }
        .login-container input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid var(--secondary-background-color);
            border-radius: 5px;
            background-color: var(--secondary-background-color);
            color: var(--text-color);
        }
        .login-container button {
            width: 100%;
            padding: 10px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .login-container button:hover {
            background-color: var(--primary-hover-color);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="login-container"><h1>Login</h1></div>', unsafe_allow_html=True)
    with st.container():
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_submit_button"):
            if not username or not password:
                st.error("Please fill in both username and password.")
            else:
                if verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Logged in successfully!")
                    st.session_state.page = "Data Visualization"  # Redirect to Data Visualization page
                else:
                    st.error("Invalid username or password.")
# Registration Page
def registration_page():
    st.markdown(
        """
        <style>
        .register-container {
            max-width: 400px;
            margin: auto;
            padding: 20px;
            border: 1px solid var(--secondary-background-color);
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            background-color: var(--background-color);
        }
        .register-container h1 {
            text-align: center;
            color: var(--primary-color);
        }
        .register-container input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid var(--secondary-background-color);
            border-radius: 5px;
            background-color: var(--secondary-background-color);
            color: var(--text-color);
        }
        .register-container button {
            width: 100%;
            padding: 10px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .register-container button:hover {
            background-color: var(--primary-hover-color);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="register-container"><h1>Register</h1></div>', unsafe_allow_html=True)
    with st.container():
        username = st.text_input("Choose a Username", key="register_username")
        password = st.text_input("Choose a Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        if st.button("Register", key="register_submit_button"):
            if not username or not password or not confirm_password:
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                if register_user(username, password):
                    st.success("Registration successful! Please login.")
                    st.session_state.page = "Login"  # Redirect to Login page
                else:
                    st.error("Username already exists.")
# Data Visualization Page
def data_visualization_page():
    st.title("Data Visualization")
    
    # File upload
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls', 'json'])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        if df is not None:
            st.success("File uploaded successfully!")
            
            # Display original data summary
            st.header("2. Original Data Summary")
            st.write("Shape:", df.shape)
            st.write("Columns:", df.columns.tolist())
            st.write("Missing values:", df.isnull().sum())
            st.write("Sample of data:", df.head())
            
            # Data cleaning options
            st.header("3. Data Cleaning")
            cleaning_options = st.multiselect(
                "Select cleaning operations:",
                ["remove_duplicates", "handle_missing", "normalize_data"],
                default=["remove_duplicates"]
            )
            
            cleaned_df, changes = clean_data(df, cleaning_options)
            
            if changes:
                st.success("Cleaning operations completed:")
                for change in changes:
                    st.write(f"- {change}")
                
                st.write("Cleaned data sample:", cleaned_df.head())
            
            # Visualization
            st.header("4. Data Visualization")
            chart_type = st.selectbox(
                "Select chart type:",
                [
                    "Bar Chart", "Line Chart", "Scatter Plot", "Box Plot", "Histogram", 
                    "Pie Chart", "Area Chart", "Violin Plot", "Heatmap", "3D Scatter Plot", 
                    "3D Surface Plot", "Bubble Chart", "Radar Chart", "Polar Chart", 
                    "Tree Map", "Sunburst Chart", "Funnel Chart", "Gantt Chart", 
                    "Candlestick Chart"
                ]
            )
            
            cols = cleaned_df.columns.tolist()
            numeric_cols = get_numeric_columns(cleaned_df)
            
            # Column selection based on chart type
            if chart_type in ["Histogram", "Pie Chart", "Tree Map", "Sunburst Chart"]:
                x_col = st.selectbox("Select column for visualization:", cols)
                y_col = None
            elif chart_type in ["Heatmap", "3D Surface Plot", "Candlestick Chart"]:
                x_col = None
                y_col = None
            else:
                x_col = st.selectbox("Select X-axis column:", cols)
                y_col = st.selectbox("Select Y-axis column:", numeric_cols)
            
            color_col = st.selectbox("Select color column (optional):", [None] + cols)
            
            # Color theme selection
            color_theme = st.selectbox(
                "Select color theme:",
                [
                    None, "plotly", "plotly_white", "plotly_dark", "ggplot2", 
                    "seaborn", "simple_white", "viridis", "inferno", "plasma", 
                    "magma", "cividis", "rainbow", "portland", "bluered", "reds", 
                    "greens", "blues", "picnic", "jet", "hot", "blackbody", 
                    "earth", "electric", "viridis", "algae", "deep", "dense", 
                    "gray", "haline", "ice", "matter", "solar", "speed", "tempo", 
                    "thermal", "turbid", "balance", "curl", "delta", "oxy", 
                    "edge", "hsv", "phase", "twilight", "mrybm", "mygbm"
                ]
            )
            
            # Custom color picker
            custom_color = st.color_picker("Pick a custom color for the graph", "#4CAF50")
            
            if st.button("Generate Visualization"):
                fig = create_visualization(cleaned_df, chart_type, x_col, y_col, color_col, color_theme, custom_color)
                if fig is not None:
                    st.plotly_chart(fig)

def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "page" not in st.session_state:
        st.session_state.page = "Home"  # Default to Home page

    # Create users table if it doesn't exist
    create_users_table()

    # Custom CSS for navigation bar
    st.markdown(
        """
        <style>
        .navbar {
            display: flex;
            justify-content: space-around;
            background-color: var(--primary-color);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .navbar button {
            color: white;
            background-color: transparent;
            border: none;
            font-size: 1.2em;
            padding: 10px 20px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .navbar button:hover {
            background-color: var(--primary-hover-color);
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Navigation bar logic
    if st.session_state.logged_in:
        # Show Data Visualization and Logout buttons when logged in
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Home", key="home_button"):
                st.session_state.page = "Home"
        with col2:
            if st.button("Data Visualization", key="data_viz_button"):
                st.session_state.page = "Data Visualization"
        with col3:
            if st.button("Logout", key="logout_button"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.page = "Home"
                st.success("Logged out successfully!")
    else:
        # Show Home, Login, and Register buttons when logged out
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Home", key="home_button"):
                st.session_state.page = "Home"
        with col2:
            if st.button("Login", key="login_button"):
                st.session_state.page = "Login"
        with col3:
            if st.button("Register", key="register_button"):
                st.session_state.page = "Register"

    # Display the selected page
    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Login":
        login_page()
    elif st.session_state.page == "Register":
        registration_page()
    elif st.session_state.page == "Data Visualization":
        if st.session_state.logged_in:
            data_visualization_page()
        else:
            st.warning("Please login to access the Data Visualization page.")
main()
