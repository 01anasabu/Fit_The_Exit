import streamlit as st
import json
import pandas as pd
import time
import os
import sys
from typing import Dict, List, Any
 
# Add the current directory to the path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
 
# Import the actual analysis functions directly
from dotenv import load_dotenv
load_dotenv()
 
# Import the analysis modules
from models.state import WebsiteType, AgentState, FinalReport
from models.state import TrafficEngagementAnalysis, UserJourneyAnalysis, DeviceLocationAnalysis
from graph.workflow import build_graph
from reporting.markdown import generate_markdown_report
 
import plotly.express as px
import plotly.graph_objs as go
 
 
def safe_pie_chart(data_series, title="Distribution"):
    """
    Create a pie chart with robust handling of different data scenarios
    """
    # Convert to value counts if not already
    if not isinstance(data_series, pd.Series):
        data_series = pd.Series(data_series)
   
    # Handle cases with few unique values
    value_counts = data_series.value_counts()
   
    # If only one unique value, add a dummy category
    if len(value_counts) == 1:
        value_counts['Other'] = 0
   
    # Create pie chart
    fig = px.pie(
        values=value_counts.values,
        names=value_counts.index,
        title=title
    )
    return fig
 
def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert potentially string columns to numeric, handling errors gracefully
    """
    # Columns that should be numeric
    numeric_columns = [
        'bounces', 'timeOnSite', 'pageviews', 'hitCount',
        'visits', 'visitNumber', 'newVisits'
    ]
   
    for col in numeric_columns:
        if col in df.columns:
            try:
                # First, replace any non-numeric values with NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Fill NaN with 0 to avoid issues with aggregations
                df[col] = df[col].fillna(0)
            except Exception as e:
                st.warning(f"Could not convert {col} to numeric: {e}")
   
    return df
 
def create_dashboard(sessions_json: List[Dict]):
    """
    Generate a comprehensive dashboard with multiple visualizations and insights
    based on the uploaded session data.
    """
    # Convert to DataFrame
    df = pd.json_normalize(sessions_json)
   
    # Convert numeric columns
    df = convert_numeric_columns(df)
   
    # Dashboard Layout
    st.title("Website Session Analytics Dashboard")
   
    # Top-level KPIs
    col1, col2, col3= st.columns(3)
   
    # with col1:
    #     st.metric(label="Total Sessions", value=len(df))
   
    with col1:
        # Use safe calculation for bounce rate
        bounce_rate = (df['bounces'].sum() / len(df) * 100).round(2)
        st.metric(label="Bounce Rate", value=f"{bounce_rate}%")
   
    with col2:
        # Handle potential zero division or NaN
        avg_time_on_site = df['timeOnSite'].mean()
        st.metric(label="Avg. Time on Site (sec)",
                  value=f"{avg_time_on_site:.2f}" if pd.notna(avg_time_on_site) else "N/A")
   
    with col3:
        # Safely calculate new visits rate
        new_visits_rate = (df['newVisits'].sum() / len(df) * 100).round(2)
        st.metric(label="New Visits", value=f"{new_visits_rate}%")
   
    # Visualizations Grid
    st.markdown("## Detailed Analytics")
   
    # First Row of Visualizations
    col1, col2 = st.columns(2)
   
    with col1:
        # Device Category Distribution
        st.markdown("### Device Usage")
        if 'deviceCategory' in df.columns:
            fig_devices = safe_pie_chart(df['deviceCategory'], "Device Category Distribution")
            st.plotly_chart(fig_devices, use_container_width=True)
        else:
            st.warning("Device category data not available")
   
    with col2:
        # Traffic Sources
        st.markdown("### Traffic Sources")
        if 'source' in df.columns:
            source_counts = df['source'].value_counts().head(10)
            fig_sources = px.bar(
                x=source_counts.index,
                y=source_counts.values,
                title="Top Traffic Sources",
                labels={'x': 'Source', 'y': 'Number of Sessions'}
            )
            st.plotly_chart(fig_sources, use_container_width=True)
        else:
            st.warning("Source data not available")
   
    # Second Row of Visualizations
    col1, col2 = st.columns(2)
   
    with col1:
        # Bounce Rate by Channel
        st.markdown("### Bounce Dynamics")
        if all(col in df.columns for col in ['channelGrouping', 'bounces']):
            bounce_by_channel = df.groupby('channelGrouping')['bounces'].mean().sort_values(ascending=False)
            fig_bounce = px.bar(
                x=bounce_by_channel.index,
                y=bounce_by_channel.values,
                title="Average Bounce Rate by Channel",
                labels={'x': 'Channel', 'y': 'Bounce Rate'}
            )
            st.plotly_chart(fig_bounce, use_container_width=True)
        else:
            st.warning("Channel or bounce data not available")
   
    with col2:
        # Time on Site Distribution
        st.markdown("### User Engagement")
        if 'timeOnSite' in df.columns:
            # Filter out zeros and NaNs
            time_data = df[df['timeOnSite'] > 0]['timeOnSite']
            if not time_data.empty:
                fig_time = px.histogram(
                    x=time_data,
                    title="Time on Site Distribution",
                    labels={'x': 'Time on Site (seconds)', 'y': 'Number of Sessions'}
                )
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.warning("No valid time on site data")
        else:
            st.warning("Time on site data not available")
   
    # Geographical Insights
    st.markdown("## Geographical Breakdown")
    col1, col2 = st.columns(2)
   
    with col1:
        # Sessions by Continent
        if 'continent' in df.columns:
            fig_continent = safe_pie_chart(df['continent'], "Sessions by Continent")
            st.plotly_chart(fig_continent, use_container_width=True)
        else:
            st.warning("Continent data not available")
   
    with col2:
        # Top Countries
        if 'country' in df.columns:
            country_counts = df['country'].value_counts().head(10)
            fig_countries = px.bar(
                x=country_counts.index,
                y=country_counts.values,
                title="Top 10 Countries by Sessions",
                labels={'x': 'Country', 'y': 'Number of Sessions'}
            )
            st.plotly_chart(fig_countries, use_container_width=True)
        else:
            st.warning("Country data not available")
   
    # Browser and Mobile Insights
    st.markdown("## Browser and Mobile Insights")
    col1, col2 = st.columns(2)
   
    with col1:
        # Browser Distribution
        if 'browser' in df.columns:
            fig_browsers = safe_pie_chart(df['browser'], "Browser Distribution")
            st.plotly_chart(fig_browsers, use_container_width=True)
        else:
            st.warning("Browser data not available")
   
    with col2:
        # Mobile vs Desktop
        if 'isMobile' in df.columns:
            # Ensure boolean values are converted to strings
            mobile_labels = df['isMobile'].map({True: 'Mobile', False: 'Desktop'})
            fig_mobile = safe_pie_chart(mobile_labels, "Device Type")
            st.plotly_chart(fig_mobile, use_container_width=True)
        else:
            st.warning("Mobile device data not available")
   
    # Key Insights Section
    st.markdown("## Key Insights")
   
    # Collect insights
    insights = []
   
    # Bounce Rate Insight
    if 'bounces' in df.columns:
        avg_bounce_rate = (df['bounces'].sum() / len(df) * 100)
        if avg_bounce_rate > 50:
            insights.append(f"🚨 High Bounce Rate Alert: {avg_bounce_rate:.2f}% of sessions are bouncing quickly")
   
    # Top Traffic Channel
    if 'channelGrouping' in df.columns:
        top_channel = df['channelGrouping'].mode().values[0]
        insights.append(f"📈 Primary Traffic Channel: {top_channel}")
   
    # Mobile Usage
    if 'isMobile' in df.columns:
        mobile_percentage = (df['isMobile'].sum() / len(df)) * 100
        insights.append(f"📱 Mobile Traffic: {mobile_percentage:.2f}% of sessions")
   
    # Display Insights
    for insight in insights:
        st.info(insight)
   
    # Detailed Data Table
    with st.expander("View Detailed Data"):
        st.dataframe(df)
 
 
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
    page_title="InsightFlow",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# Navigation setup
tabs = ["Home", "LLM Driven Insights", "Data Visualization"]
selected_tab = st.tabs(tabs)
 
# Sample data for downloads
sample_data_1 = [
{"fullVisitorId":"0000027376579751715","visitId":"1486866293","visitNumber":"1","visits":"1","hitCount":"6","pageviews":"5","timeOnSite":"49","bounces":"0","newVisits":"1","source":"(direct)","medium":"(none)","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"United States","city":"not available in demo dataset","channelGrouping":"Organic Search","landingScreenName":"www.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/accessories/stickers/home","navigationFlow":"/home -\u003e /home -\u003e /google+redesign/shop+by+brand/google -\u003e /google+redesign/accessories/stickers/home -\u003e /google+redesign/accessories/stickers//quickview -\u003e /google+redesign/accessories/stickers/home","pageTitleFlow":"Google Online Store -\u003e Home -\u003e Google | Shop by Brand | Google Merchandise Store -\u003e Stickers | Accessories | Google Merchandise Store -\u003e Stickers | Accessories | Google Merchandise Store -\u003e Stickers | Accessories | Google Merchandise Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000039460501403861","visitId":"1490629516","visitNumber":"1","visits":"1","hitCount":"2","pageviews":"2","timeOnSite":"99","bounces":"0","newVisits":"1","referralPath":"/yt/about/pt-BR/","source":"youtube.com","medium":"referral","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"Brazil","city":"not available in demo dataset","channelGrouping":"Social","landingScreenName":"www.googlemerchandisestore.com/home","exitScreenName":"www.googlemerchandisestore.com/home","navigationFlow":"/home -\u003e /home","pageTitleFlow":"Google Online Store -\u003e Google Online Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000040862739425590","visitId":"1486836571","visitNumber":"1","visits":"1","hitCount":"2","pageviews":"2","timeOnSite":"14","bounces":"0","newVisits":"1","source":"(direct)","medium":"(none)","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"United States","city":"Oakland","channelGrouping":"Paid Search","landingScreenName":"shop.googlemerchandisestore.com/google redesign/apparel/men s/men s t shirts","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/google redesign/apparel/men s/men s t shirts -\u003e /home","pageTitleFlow":"Page Unavailable -\u003e Home","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000040862739425590","visitId":"1486838824","visitNumber":"2","visits":"1","hitCount":"3","pageviews":"3","timeOnSite":"35","bounces":"0","newVisits":"0","source":"(direct)","medium":"(none)","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"United States","city":"Oakland","channelGrouping":"Paid Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/men++s/men++s+outerwear","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/kid+s/kid+s+infant","navigationFlow":"/google+redesign/apparel/men++s/men++s+outerwear -\u003e /store.html -\u003e /google+redesign/apparel/kid+s/kid+s+infant","pageTitleFlow":"Men's Outerwear | Apparel | Google Merchandise Store -\u003e Men's Outerwear | Apparel | Google Merchandise Store -\u003e Infant | Kids' Apparel | Google Merchandise Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000068403966359845","visitId":"1491281649","visitNumber":"1","visits":"1","hitCount":"2","pageviews":"2","timeOnSite":"18","bounces":"0","newVisits":"1","source":"google","medium":"organic","browser":"Safari","isMobile":True,"deviceCategory":"tablet","continent":"Americas","country":"United States","city":"Los Angeles","channelGrouping":"Organic Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/android","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/google+redesign/shop+by+brand/android -\u003e /home","pageTitleFlow":"Android | Shop by Brand | Google Merchandise Store -\u003e Home","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000176652019531658","visitId":"1484597865","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","referralPath":"/yt/about/","source":"youtube.com","medium":"referral","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Asia","country":"Bangladesh","city":"not available in demo dataset","channelGrouping":"Social","landingScreenName":"shop.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/home","pageTitleFlow":"Home","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000197671390269035","visitId":"1493772870","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","referralPath":"/","source":"m.facebook.com","medium":"referral","browser":"Android Webview","isMobile":True,"deviceCategory":"mobile","continent":"Americas","country":"United States","city":"not available in demo dataset","channelGrouping":"Social","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/waze+dress+socks.axd","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/waze+dress+socks.axd","navigationFlow":"/google+redesign/shop+by+brand/waze+dress+socks.axd","pageTitleFlow":"Waze Dress Socks","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000213131142648941","visitId":"1493419318","visitNumber":"1","visits":"1","hitCount":"14","pageviews":"13","timeOnSite":"272","bounces":"0","newVisits":"1","source":"(direct)","medium":"(none)","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"United States","city":"San Francisco","channelGrouping":"Direct","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/mens+outerwear/blm+sweatshirt.axd","exitScreenName":"shop.googlemerchandisestore.com/ordercompleted.html","navigationFlow":"/google+redesign/apparel/mens+outerwear/blm+sweatshirt.axd -\u003e /home -\u003e /signin.html -\u003e /store.html -\u003e /google+redesign/apparel/mens+outerwear/blm+sweatshirt.axd -\u003e /google+redesign/apparel/mens+outerwear/blm+sweatshirt.axd -\u003e /basket.html -\u003e /basket.html -\u003e /basket.html -\u003e /yourinfo.html -\u003e /payment.html -\u003e /revieworder.html -\u003e /ordercompleted.html -\u003e /ordercompleted.html","pageTitleFlow":"Page Unavailable -\u003e Home -\u003e The Google Merchandise Store - Log In -\u003e Home -\u003e BLM Sweatshirt -\u003e BLM Sweatshirt -\u003e Shopping Cart -\u003e Shopping Cart -\u003e Shopping Cart -\u003e Checkout Your Information -\u003e Payment Method -\u003e Checkout Review -\u003e Checkout Confirmation -\u003e Checkout Confirmation","exceptions":[],"fatalExceptions":[]}
]
 
sample_data_2 = [
{"fullVisitorId":"000026722803385797","visitId":"1496658394","visitNumber":"1","visits":"1","hitCount":"3","pageviews":"2","timeOnSite":"18","bounces":"0","newVisits":"1","source":"google","medium":"organic","browser":"Safari","isMobile":False,"deviceCategory":"desktop","continent":"Europe","country":"United Kingdom","city":"not available in demo dataset","channelGrouping":"Organic Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/youtube","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/youtube/quickview","navigationFlow":"/google+redesign/shop+by+brand/youtube -\u003e /google+redesign/shop+by+brand/youtube -\u003e /google+redesign/shop+by+brand/youtube/quickview","pageTitleFlow":"YouTube | Shop by Brand | Google Merchandise Store -\u003e YouTube | Shop by Brand | Google Merchandise Store -\u003e YouTube | Shop by Brand | Google Merchandise Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000291342601222013","visitId":"1491064213","visitNumber":"1","visits":"1","hitCount":"3","pageviews":"3","timeOnSite":"16","bounces":"0","newVisits":"1","source":"google","medium":"organic","browser":"Chrome","isMobile":True,"deviceCategory":"mobile","continent":"Americas","country":"United States","city":"Los Angeles","channelGrouping":"Organic Search","landingScreenName":"www.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/shop+by+brand/google","navigationFlow":"/home -\u003e /home -\u003e /google+redesign/shop+by+brand/google","pageTitleFlow":"Google Online Store -\u003e Home -\u003e Google | Shop by Brand | Google Merchandise Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000458812883559498","visitId":"1495066298","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","source":"google","medium":"organic","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"United States","city":"San Bruno","channelGrouping":"Organic Search","landingScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/mens+tshirts/google+mens+bike+short+tee+charcoal.axd","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/mens+tshirts/google+mens+bike+short+tee+charcoal.axd","navigationFlow":"/google+redesign/apparel/mens+tshirts/google+mens+bike+short+tee+charcoal.axd","pageTitleFlow":"Google Men's Bike Short Sleeve Tee Charcoal","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000485418944539313","visitId":"1487159075","visitNumber":"2","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"0","source":"google","medium":"organic","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Europe","country":"Germany","city":"Hamburg","channelGrouping":"Organic Search","landingScreenName":"www.googlemerchandisestore.com/home","exitScreenName":"www.googlemerchandisestore.com/home","navigationFlow":"/home","pageTitleFlow":"Google Online Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000496879625382660","visitId":"1487604659","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","referralPath":"/yt/about/","source":"youtube.com","medium":"referral","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Asia","country":"India","city":"not available in demo dataset","channelGrouping":"Social","landingScreenName":"shop.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/home","pageTitleFlow":"Home","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000530033766739584","visitId":"1489667400","visitNumber":"1","visits":"1","hitCount":"4","pageviews":"4","timeOnSite":"556","bounces":"0","newVisits":"1","source":"(direct)","medium":"(none)","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Europe","country":"Poland","city":"not available in demo dataset","channelGrouping":"Direct","landingScreenName":"www.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/home","navigationFlow":"/home -\u003e /home -\u003e /google+redesign/apparel/womens/womens+t+shirts -\u003e /home","pageTitleFlow":"Google Online Store -\u003e Home -\u003e Women's T-Shirts | Apparel | Google Merchandise Store -\u003e Home","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000543175149799625","visitId":"1485675517","visitNumber":"1","visits":"1","hitCount":"1","pageviews":"1","timeOnSite":"0","bounces":"1","newVisits":"1","referralPath":"/yt/about/ja/","source":"youtube.com","medium":"referral","browser":"Android Webview","isMobile":True,"deviceCategory":"mobile","continent":"Asia","country":"Japan","city":"not available in demo dataset","channelGrouping":"Social","landingScreenName":"www.googlemerchandisestore.com/home","exitScreenName":"www.googlemerchandisestore.com/home","navigationFlow":"/home","pageTitleFlow":"Google Online Store","exceptions":[],"fatalExceptions":[]},
{"fullVisitorId":"0000572434142265465","visitId":"1494990076","visitNumber":"1","visits":"1","hitCount":"2","pageviews":"2","timeOnSite":"43","bounces":"0","newVisits":"1","referralPath":"/","source":"(direct)","medium":"(none)","browser":"Chrome","isMobile":False,"deviceCategory":"desktop","continent":"Americas","country":"United States","city":"New York","channelGrouping":"Referral","landingScreenName":"shop.googlemerchandisestore.com/home","exitScreenName":"shop.googlemerchandisestore.com/google+redesign/apparel/mens/mens+outerwear","navigationFlow":"/home -\u003e /google+redesign/apparel/mens/mens+outerwear","pageTitleFlow":"Home -\u003e Men's Outerwear | Apparel | Google Merchandise Store","exceptions":[],"fatalExceptions":[]}
 
]
 
# Sidebar setup
with st.sidebar:
    # Logo
    st.image("image.png", width=100)
    # Sample data download buttons with smaller font and side by side
   
    st.download_button(
        label="Sample Data 1(Jan 2025)",
        data=json.dumps(sample_data_1, indent=3),
        file_name="ecommerce_sample.json",
        mime="application/json",
        use_container_width=True)
    st.download_button(
        label="Sample Data 2(Feb 2025)",
        data=json.dumps(sample_data_2, indent=3),
        file_name="blog_sample.json",
        mime="application/json",
        use_container_width=True
    )
   
    # Upload file section with smaller header
    st.markdown("**Upload Data:**")
    uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])
   
    if uploaded_file is not None:
        try:
            sessions_json = json.load(uploaded_file)
            num_sessions = len(sessions_json)
            st.success("Loaded session data successfully")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            sessions_json = None
    else:
        sessions_json = None
   
   
   
    # Submit button
    analyze_button = st.button("Submit", disabled=(sessions_json is None), use_container_width=True)
 
# Home tab content
with selected_tab[0]:
    st.markdown("""
    ### Quick Start Guide:
   
    1. **Get Sample Data**: Download one of our sample JSON files from the sidebar to see the expected format
   
    2. **Upload Your Data**: Prepare your session data in JSON format and upload it using the sidebar uploader
   
    3. **Generate Insights**: Click the Submit button to run the analysis
   
    4. **Review Results**: Navigate to the "LLM Driven Insights" tab to see AI-generated recommendations and to "Data Viz" to explore visualizations
   
    ### What You Can Learn:
               
    - Insights which cannot be seen just by looking at dashboard
    - Traffic & engagement patterns
    - User journey optimization opportunities
    - Device & location-based insights
    - Actionable Recommendations to improve customer retention
   
    """)
   
    st.info("InsightFlow uses AI to analyze patterns in your website session data that may be contributing to customer dropoffs.")
 
# LLM Driven Insights tab content
with selected_tab[1]:
    # st.header("LLM Driven Insights")
   
    if analyze_button and sessions_json is not None:
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Add info about expected processing time
        st.info("This process usually takes 1-2 minutes. If you want, you can look at the sample output file while waiting.")
        
        # Add sample file download button for PDF during loading process
        try:
            with open("second_page.pdf", "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
            
            st.download_button(
                label="Download Sample Report",
                data=pdf_bytes,
                file_name="second_page.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.warning(f"Sample PDF not available: {str(e)}")
            # Fallback if PDF file is not found
            st.write("Contact support to get a sample report.")
       
        try:
            # Set environment variables for chunk size and max workers
            # os.environ["CHUNK_SIZE"] = str(chunk_size)
            # os.environ["MAX_WORKERS"] = str(max_workers)
           
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
                "",
                "",
                sessions_json
            )
           
            status_text.text("Step 3/3: Generating report...")
            progress_bar.progress(90)
           
            # Remove the placeholder
            results_placeholder.empty()
           
            # Display the report
            st.subheader("Analysis Report")
            st.markdown(markdown_report)
           
            # Provide download link
            report_filename = "Analysis_report.md"
           
            st.download_button(
                label="Download Report as Markdown",
                data=markdown_report,
                file_name=report_filename,
                mime="text/markdown",
            )
           
            # Clean up
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
               
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
    else:
        st.info("Upload your session data and click 'Submit' in the sidebar to generate LLM-driven insights.")
       
        # Placeholder for what insights will look like
        with st.expander("Preview of Insights"):
            st.markdown("""
            ## Prioritized Action Plan
### 1. High bounce rate on the website [PRIORITY: HIGH]

#### Supporting Data:
- User engagement data is missing
- Unable to determine specific high bounce rate pages

#### Corrective Measures:
- Re-evaluate and fix the traffic and engagement analysis aggregation process
- Identify and optimize high bounce rate pages once data is available

### 2. Low conversion rate on the website [PRIORITY: HIGH]

#### Supporting Data:
- Conversion insights are missing
- Unable to determine specific drop-off points in the user journey

#### Corrective Measures:
- Re-evaluate and fix the user journey analysis aggregation process
- Identify and optimize conversion funnel once data is available

            """)

# Data Viz tab content
with selected_tab[2]:
    # st.header("Comprehensive Data Visualization")
   
    if analyze_button and sessions_json is not None:
        try:
            create_dashboard(sessions_json)
        except Exception as e:
            st.error(f"Error creating dashboard: {e}")
            # Print detailed traceback for debugging
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("Upload your session data and click 'Submit' in the sidebar to generate a comprehensive dashboard.")
st.markdown("---")
st.markdown("InsightFlow - Analyzing customer drop-offs and providing actionable recommendations | © 2025")