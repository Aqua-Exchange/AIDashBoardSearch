import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="AquaExchange Dashboard",
    page_icon="🌊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stDataFrame {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def fetch_ponds_data(query_params):
    """Fetch data from the farm ponds API"""
    url = "https://ax-ai-reports-912635809422.asia-south1.run.app/api/getFarmPonds"
    
    try:
        # Create the payload with the query parameters
        try:
            payload = {
                "api_name": "getFarmPonds",
                "query": query_params
            }
        except Exception as e:
            st.error(f"Error creating payload: {str(e)}")
            return pd.DataFrame()
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract the data array from the response
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        
        # Convert to DataFrame
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            # Convert date columns to datetime if they exist (exclude 'DOC' as it's an integer)
            date_columns = [col for col in df.columns 
                          if any(x in col.lower() for x in ['date', 'lastupdated']) 
                          and 'doc' not in col.lower()]
            for col in date_columns:
                try:
                    # First try with dayfirst=True for d-m-Y format
                    df[col] = pd.to_datetime(df[col], 
                                          dayfirst=True, 
                                          errors='coerce',
                                          format='mixed')
                except Exception as e:
                    st.warning(f"Could not convert column '{col}' to datetime: {str(e)}")
                    continue
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def main():
    # Main app content
    st.title("🌊 AquaExchange Dashboard")
    st.markdown("View and filter farm ponds data")
    
    # Default query parameters
    default_query = 'ponds with > 80 doc but not done any harvest'
    
    # Add a text area for query parameters
    query_params = st.text_area(
        "Search (ex: ponds with > 80 doc but not done any harvest)",
        value=default_query,
        height=100,
        help="Enter to get the information of pond details"
    )
    
    # Add a refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Fetch Data"):
            st.cache_data.clear()
    
    # Fetch data with caching
    with st.spinner('Loading data...'):
        df = fetch_ponds_data(query_params)
    
    if not df.empty:
        # Display basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Ponds", len(df))
        
        # Add filters in sidebar
        st.sidebar.header("Filters")
        
        # Dynamic filters for each column
        for column in df.select_dtypes(include=['object']).columns:
            unique_vals = df[column].unique()
            if len(unique_vals) < 20:  # Only show filter for columns with limited unique values
                selected = st.sidebar.multiselect(
                    f"Filter by {column}",
                    options=unique_vals,
                    default=unique_vals.tolist()
                )
                if len(selected) > 0:
                    df = df[df[column].isin(selected)]
        
        # Date range filter for date columns (exclude 'DOC' as it's an integer)
        date_columns = [col for col in df.columns 
                       if 'date' in col.lower() 
                       and 'doc' not in col.lower()]
        if date_columns:
            date_col = st.sidebar.selectbox("Filter by date column", date_columns)
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            
            date_range = st.sidebar.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df[date_col].dt.date >= start_date) & 
                       (df[date_col].dt.date <= end_date)]
        
        # Show the data table
        st.subheader("Ponds Data")
        st.dataframe(df, use_container_width=True, height=600)
        
        # Add download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"farm_ponds_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
    else:
        st.warning("No data available or failed to fetch data from the API.")

if __name__ == "__main__":
    main()
#password ax@4321