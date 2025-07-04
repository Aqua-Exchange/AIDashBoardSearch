import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import os

# Set page config
st.set_page_config(
    page_title="AquaExchange Dashboard",
    page_icon="",
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

def fetch_ponds_data(query_params, skip=None, limit=None, applied_filters=None, total_count=None, total_acres=None):
    """Fetch data from the farm ponds API with pagination support"""
    url = "https://ax-ai-reports-912635809422.asia-south1.run.app/api/getFarmPonds"
    
    try:
        # Create the payload with the query parameters and pagination
        try:
            payload = {
                "query": query_params
            }
            if total_count:
                payload["totalCount"] = total_count
            if total_acres:
                payload["totalAcres"] = total_acres
            
            # Add appliedFilters only if provided and not empty
            if applied_filters:
                payload["appliedFilters"] = applied_filters
            if skip:
                payload["skip"] = skip
            if limit:
                payload["limit"] = limit
        except Exception as e:
            st.error(f"Error creating payload: {str(e)}")
            return pd.DataFrame(), "", 0, []
            
        print(payload)
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract the data array, cypher query, total count, and total acres from the response
        cypher_query = ""
        response_filters = []
        
        if isinstance(data, dict):
            # Get cypher query
            if 'cypher' in data:
                cypher_query = data['cypher']
            elif 'response' in data and isinstance(data['response'], dict) and 'cypher' in data['response']:
                cypher_query = data['response']['cypher']
            
            # Get total count
            if 'totalCount' in data:
                total_count = int(data['totalCount'])
                st.session_state.total_count = total_count
            elif 'response' in data and 'totalCount' in data['response']:
                total_count = int(data['response']['totalCount'])
                st.session_state.total_count = total_count
                
            # Get total acres
            if 'totalAcres' in data:
                total_acres = float(data['totalAcres'])
                st.session_state.total_acres = total_acres
            elif 'response' in data and 'totalAcres' in data['response']:
                total_acres = float(data['response']['totalAcres'])
                st.session_state.total_acres = total_acres
            
            # Get applied filters if available
            if 'appliedFilters' in data and data['appliedFilters']:
                response_filters = data['appliedFilters']
                st.session_state.applied_filters = response_filters
            
            # Get the data array
            if 'data' in data:
                data_array = data['data']
            elif 'response' in data and 'data' in data['response']:
                data_array = data['response']['data']
            else:
                data_array = []
        else:
            data_array = []
        
        # Convert to DataFrame
        if isinstance(data_array, list) and len(data_array) > 0:
            df = pd.DataFrame(data_array)
            # Convert date columns to datetime if they exist (exclude 'DOC' as it's an integer)
            date_columns = [col for col in df.columns 
                          if any(x in col.lower() for x in ['datalastupdated','feedlastupdated','nettinglastupdatedat']) 
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
            return df, cypher_query, total_count, response_filters, total_acres if 'total_acres' in locals() else 0
        return pd.DataFrame(), cypher_query, total_count, response_filters, total_acres if 'total_acres' in locals() else 0
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame(), "", 0, [], 0

def main():
    # Main app content with logo
    col1, col2 = st.columns([1, 5])
    
    with col1:
        # Load and display the logo
        logo_path = "aqualogo.png"
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            st.image(logo, width=100)
    
    with col2:
        st.title("🌊 AquaExchange Dashboard")
        st.markdown("View and filter farm ponds data")
    
    # Initialize session state for pagination and feedback
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'per_page' not in st.session_state:
        st.session_state.per_page = 100
    if 'applied_filters' not in st.session_state:
        st.session_state.applied_filters = None
    if 'total_count' not in st.session_state:
        st.session_state.total_count = None
    if 'total_acres' not in st.session_state:
        st.session_state.total_acres = None
    if 'skip' not in st.session_state:
        st.session_state.skip = None
    if 'limit' not in st.session_state:
        st.session_state.limit = None
    if 'show_feedback' not in st.session_state:
        st.session_state.show_feedback = False
    
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
            st.session_state.page = 0  # Reset to first page on new search
            st.session_state.applied_filters = None
            st.session_state.total_count = None
    
    # Calculate skip based on current page
    skip = st.session_state.page * st.session_state.per_page
    
    # Only include pagination parameters if not the first page
    pagination_params = {}
    if st.session_state.page > 0:
        pagination_params['skip'] = skip
    if st.session_state.per_page != 100:  # Only include if not default
        pagination_params['limit'] = st.session_state.per_page
    
    # Only fetch data if we're not in the middle of a form submission
    if 'feedback_submitted' not in st.session_state or not st.session_state.feedback_submitted:
        with st.spinner('Loading data...'):
            try:
                df, cypher_query, total_count, response_filters, total_acres = fetch_ponds_data(
                    query_params,
                    **pagination_params,
                    total_count=st.session_state.get('total_count'),
                    total_acres=st.session_state.get('total_acres'),
                    applied_filters=st.session_state.get('applied_filters')
                )
                
                # Store data in session state for later use
                st.session_state.current_data = df
                st.session_state.total_count = total_count
                st.session_state.total_acres = total_acres
                
                # Store applied filters from the response if available
                if response_filters:
                    st.session_state.applied_filters = response_filters
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
                df = pd.DataFrame()
                total_count = 0
                total_acres = 0
    else:
        # Use existing data from session state
        df = st.session_state.get('current_data', pd.DataFrame())
        total_count = st.session_state.get('total_count', 0)
        total_acres = st.session_state.get('total_acres', 0)
    
    # Display the Cypher query in an expandable section
    if cypher_query and cypher_query.strip():
        with st.expander("View Generated Cypher Query"):
            st.code(cypher_query, language="cypher")
    
    if not df.empty:
        # Calculate pagination info
        if hasattr(st.session_state, 'total_count') and st.session_state.total_count > 0:
            total_count = st.session_state.total_count
            
        total_pages = (total_count + st.session_state.per_page - 1) // st.session_state.per_page
        start_record = skip + 1
        end_record = min(skip + len(df), total_count)
        
        
        
        # Display basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Ponds", f"{total_count:,}")
        with col2:
            # Handle None value for total_acres
            acres_value = total_acres if total_acres is not None else 0
            st.metric("Total Acres", f"{acres_value:,.2f}")
        
        # Add index column based on pagination
        if not df.empty:
            # Create a new column with 1-based index based on current page and items per page
            df_display = df.copy()
            start_idx = st.session_state.page * st.session_state.per_page + 1
            df_display.index = range(start_idx, start_idx + len(df))
            
            # Show the data table with index
            st.subheader("Ponds Data")
            st.dataframe(df_display, use_container_width=True, height=600)
        
        # Display record count info
        st.caption(f"Showing {total_count:,} records total")
        
        # Pagination controls with Rows per page selector
        col1, col2, col3, col4 = st.columns([2, 4, 2, 3])
        
        with col1:
            if st.session_state.page > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.page = 0  # Reset to first page when changing page size
                    st.rerun()
        
        # Display pagination info
        st.caption(f"Showing {start_record:,} - {end_record:,} of {total_count:,} records")
        with col2:
            st.write(f"Page {st.session_state.page + 1} of {max(1, total_pages)}")
        
        with col3:
            if (st.session_state.page + 1) * st.session_state.per_page < total_count:
                if st.button("Next ➡️"):
                    st.session_state.page += 1
                    st.rerun()
        
        with col4:
            # Rows per page selector
            new_per_page = st.selectbox(
                "Rows per page:",
                options=[50, 100, 200, 500],
                index=[50, 100, 200, 500].index(st.session_state.per_page) if st.session_state.per_page in [50, 100, 200, 500] else 1,
                key='per_page_selector',
                label_visibility="collapsed"
            )
            if new_per_page != st.session_state.per_page:
                st.session_state.per_page = new_per_page
                st.session_state.page = 0  # Reset to first page when changing page size
                st.rerun()
        
        # Add download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Current Page as CSV",
            data=csv,
            file_name=f"farm_ponds_page_{st.session_state.page + 1}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
        
        # Feedback UI after pagination and download button
        # st.subheader("📝 Provide Feedback")
        
        # # Store form submission state to prevent rerunning API calls
        # if 'feedback_submitted' not in st.session_state:
        #     st.session_state.feedback_submitted = False
            
        # with st.form("feedback_form"):
        #     col1, col2 = st.columns([3, 1])
        #     with col1:
        #         # Feedback options
        #         feedback_type = st.radio(
        #             "How well did the results match your query?",
        #             ["👍 Relevant", "👎 Not Relevant", "🤔 Partially Relevant"],
        #             horizontal=True
        #         )
            
        #     # Additional feedback
        #     feedback_text = st.text_area(
        #         "Additional feedback (optional)",
        #         placeholder="Please share any additional comments or suggestions...",
        #         height=100
        #     )
            
        #     # Display applied filters if any
        #     if st.session_state.get('applied_filters'):
        #         with st.expander("Applied Filters"):
        #             st.json(st.session_state.applied_filters)
            
        #     # Submit button
        #     submitted = st.form_submit_button("Submit Feedback")
            
        #     if submitted and not st.session_state.feedback_submitted:
        #         st.session_state.feedback_submitted = True
                
        #         # Prepare feedback data
        #         feedback_data = {
        #             "query": query_params,
        #             "feedback_type": feedback_type,
        #             "feedback_text": feedback_text,
        #             "applied_filters": st.session_state.get('applied_filters'),
        #             "timestamp": datetime.now().isoformat()
        #         }
                
        #         # Store feedback locally for backup
        #         if 'feedback_history' not in st.session_state:
        #             st.session_state.feedback_history = []
        #         st.session_state.feedback_history.append(feedback_data)
                
        #         try:
        #             # Just show success message without making API call
        #             st.success("Thank you for your feedback! It has been recorded.")
                    
        #             # Commented out the problematic API call that causes 500 error
        #             '''
        #             feedback_url = "https://us-central1-nextaqua-22991.cloudfunctions.net/storeApiFeedback"
        #             # Set a timeout to prevent hanging
        #             response = requests.post(feedback_url, json=feedback_data, timeout=5)
                    
        #             if response.status_code == 200:
        #                 st.success("Thank you for your feedback! It has been submitted successfully.")
        #             else:
        #                 st.warning(f"Feedback submission had an issue. Status code: {response.status_code}")
        #                 st.info("Your feedback has been saved locally as a backup.")
        #             '''
        #         except Exception as e:
        #             st.error(f"Unexpected error: {str(e)}")
        #             st.info("Your feedback has been saved locally.")
            
        #     # Show message if already submitted
        #     elif submitted and st.session_state.feedback_submitted:
        #         st.info("Your feedback has already been recorded. Thank you!")
                
        # Add a button to reset the feedback form if needed
        # if st.session_state.feedback_submitted:
        #     if st.button("Submit another feedback"):
        #         st.session_state.feedback_submitted = False
        #         st.rerun()
    else:
        st.warning("No data available or failed to fetch data from the API.")

if __name__ == "__main__":
    main()
#password ax@4321