import streamlit as st
import json
import pandas as pd
import time
import os
import sys
from typing import Dict, List, Any

# Add the current directory to the path so imports work correctly
# This ensures that module imports from the main application work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual analysis functions directly
from dotenv import load_dotenv
load_dotenv()

# Import the analysis modules
from models.state import WebsiteType, AgentState, FinalReport
from models.state import TrafficEngagementAnalysis, UserJourneyAnalysis, DeviceLocationAnalysis
from graph.workflow import build_graph
from reporting.markdown import generate_markdown_report

# Import the main analysis function
def import_analyze_function():
    """Import the analysis function - this approach allows for flexible imports"""
    try:
        # Try importing as a module first
        from analyze_website_session_parallel import analyze_website_session_parallel
        return analyze_website_session_parallel
    except ImportError:
        # If that fails, import from the main script
        from main import analyze_website_session_parallel
        return analyze_website_session_parallel

# Set page config
st.set_page_config(
    page_title="Website Analyzer",
    page_icon="📊",
    layout="wide",
)

# Main title
st.title("📊 Fix The Exit")
st.markdown("Upload your session data and get a comprehensive analysis report.")

# Sidebar
with st.sidebar:
    st.header("Instructions")
    sample_json = [
        {"fullVisitorId":"001107862212762250","visitId":"1494179788","visitNumber":"1","visits":"1","hitCount":"19","pageviews":"13","timeOnSite":"230","bounces":"0","newVisits":"1","source":"google","medium":"organic","browser":"Chrome","isMobile":True,"deviceCategory":"mobile","continent":"Asia","country":"Malaysia","city":"Kuala Lumpur","channelGrouping":"Organic Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/mens/mens+t+shirts","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/bags/backpacks/home -> /google+redesign/office -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+outerwear -> /google+redesign/apparel/mens/mens+performance+wear -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+t+shirts/quickview -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+t+shirts/quickview -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+t+shirts/quickview -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+t+shirts/quickview -> /google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/apparel/mens/mens+t+shirts/quickview -> /google+redesign/apparel/mens/mens+t+shirts -> /home","pageTitleFlow":"Men's T-Shirts | Apparel | Google Merchandise Store -> Backpacks | Bags | Google Merchandise Store -> Office | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's Outerwear | Apparel | Google Merchandise Store -> Men's Performance Wear | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Men's T-Shirts | Apparel | Google Merchandise Store -> Home","exceptions":[],"fatalExceptions":[]},
        {"fullVisitorId":"001108536148130947","visitId":"1492907378","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","referralPath":"/analytics/web/","source":"analytics.google.com","medium":"referral","browser":"Edge","isMobile":False,"deviceCategory":"desktop","continent":"Europe","country":"Spain","city":"not available in demo dataset","channelGrouping":"Referral","landingScreenName":"shop.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/home","pageTitleFlow":"Home","exceptions":[],"fatalExceptions":[]},
        {"fullVisitorId":"0011148821686448845","visitId":"1484167255","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","source":"(direct)","medium":"(none)","browser":"Safari","isMobile":True,"deviceCategory":"mobile","continent":"Europe","country":"United Kingdom","city":"not available in demo dataset","channelGrouping":"Organic Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/youtube","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/youtube","navigationFlow":"/google+redesign/shop+by+brand/youtube","pageTitleFlow":"YouTube | Shop by Brand | Google Merchandise Store","exceptions":[],"fatalExceptions":[]},
        {"fullVisitorId":"0011202659828939277","visitId":"1497396721","visitNumber":"1","visits":"1","hitCount":"2","pageviews":"2","timeOnSite":"45","bounces":"0","newVisits":"1","source":"(direct)","medium":"(none)","browser":"Safari","isMobile":True,"deviceCategory":"tablet","continent":"Americas","country":"United States","city":"Phoenix","channelGrouping":"Organic Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/youtube","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/google+redesign/shop+by+brand/youtube -> /home","pageTitleFlow":"YouTube | Shop by Brand | Google Merchandise Store -> Home","exceptions":[],"fatalExceptions":[]}
    ]
    json_str = json.dumps(sample_json, indent=2)
    st.download_button(
        label="Download Sample JSON",
        data=json_str,
        file_name="sample_sessions.json",
        mime="application/json",
    )
    st.markdown("""
    ### How to use this tool:
    1. Download the sample JSON file below
    2. Upload your JSON file with session data
    3. Select website type and issues to analyze
    4. Click 'Generate Report'
    5. Download your analysis report
    """)
    
    # Sample JSON for download - use the one from your second document

    
    

    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool analyzes website session data to provide insights on:
    - Traffic & engagement metrics
    - User journey patterns
    - Device & location analysis
    - Specific website issues
    """)

# Main content
col1, col2 = st.columns([3, 2])

with col1:
    st.header("Upload Session Data")
    uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])
    
    if uploaded_file is not None:
        try:
            sessions_json = json.load(uploaded_file)
            num_sessions = len(sessions_json)
            st.success(f"Successfully loaded {num_sessions} sessions")
            
            # Show sample data
            if num_sessions > 0:
                with st.expander("Preview loaded data"):
                    st.dataframe(pd.json_normalize(sessions_json[:min(5, num_sessions)]))
        except Exception as e:
            st.error(f"Error loading JSON file: {str(e)}")
            sessions_json = None
    else:
        sessions_json = None

with col2:
    st.header("Analysis Parameters")
    
    website_type = st.selectbox(
        "Website Type", 
        ["e-commerce", "blog", "SaaS", "media", "portfolio", "educational", "corporate"]
    )
    
    issue_options = [
        "high bounce rate", 
        "low conversion", 
        "cart abandonment", 
        "poor mobile experience",
        "slow page load",
        "confusing navigation",
        "content engagement",
        "user retention"
    ]
    
    specific_issues = st.multiselect(
        "Specific Issues to Analyze",
        issue_options,
        default=["high bounce rate", "low conversion"]
    )
    
    # Advanced options in an expander
    # with st.expander("Advanced Options"):
    #     chunk_size = st.slider("Chunk Size", min_value=1, max_value=10, value=4, 
    #                           help="Number of sessions to process in each chunk")
    #     max_workers = st.slider("Parallel Workers", min_value=1, max_value=4, value=1,
    #                            help="Number of parallel processing workers")

# Analysis button
if st.button("Generate Report", disabled=(sessions_json is None)):
    if sessions_json is None:
        st.warning("Please upload a valid JSON file first")
    else:
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Set environment variables for chunk size and max workers
            # os.environ["CHUNK_SIZE"] = str(chunk_size)
            # os.environ["MAX_WORKERS"] = str(max_workers)
            
            # Create a temporary file for the sessions if needed
            temp_json_path = "temp_sessions.json"
            with open(temp_json_path, "w") as f:
                json.dump(sessions_json, f)
            
            status_text.text("Step 1/3: Initializing analysis...")
            progress_bar.progress(10)
            
            # Import the analyze function
            analyze_website_session_parallel = import_analyze_function()
            
            # Progress updates
            status_text.text("Step 2/3: Processing session data...")
            progress_bar.progress(30)
            
            # Create a placeholder for the results
            results_placeholder = st.empty()
            results_placeholder.info("Analysis in progress... This may take several minutes depending on data size.")
            
            # Run the analysis
            final_state, markdown_report = analyze_website_session_parallel(
                website_type, 
                specific_issues, 
                sessions_json
            )
            
            status_text.text("Step 3/3: Generating report...")
            progress_bar.progress(90)
            
            # Remove the placeholder
            results_placeholder.empty()
            
            # Display the report
            st.header("Analysis Report")
            st.markdown(markdown_report)
            
            # Provide download link
            report_filename = f"{website_type.replace(' ', '_')}_analysis_report.md"
            
            st.download_button(
                label="Download Report as Markdown",
                data=markdown_report,
                file_name=report_filename,
                mime="text/markdown",
            )
            
            # Clean up
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            
            # Remove temp file if it was created
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)
                
        except Exception as e:
            # Display error information
            st.error(f"Error during analysis: {str(e)}")
            
            # Show detailed traceback for debugging
            st.expander("View Error Details").code(str(e), language="bash")
            
            # Suggest a solution
            st.warning("""
            Possible solutions:
            1. Check that all required modules are installed
            2. Verify your JSON data format
            3. Check your environment variables
            4. Try with a smaller dataset or reduce chunk size
            """)

# Footer
# st.markdown("---")
# st.markdown("Developed for Website Analytics | © 2025")