import streamlit as st
import pandas as pd
import json
import time
import base64
import io
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

# Set page configuration
st.set_page_config(
    page_title="Website Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #38BDF8;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #60A5FA;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    .section-header {
        font-size: 1.2rem;
        color: #7DD3FC;
        margin-top: 1rem;
        font-weight: 600;
    }
    .card {
        background-color: #1E293B;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #0F172A;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94A3B8;
    }
    .highlight {
        background-color: #0F172A;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
    }
    .description {
        color: #E2E8F0;
        margin-bottom: 1rem;
    }
    .note {
        color: #94A3B8;
        font-size: 0.8rem;
        font-style: italic;
    }
    .success-message {
        background-color: #064E3B;
        color: #A7F3D0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .info-message {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .tab-content {
        padding: 1rem;
        border: 1px solid #E5E7EB;
        border-top: none;
        border-radius: 0 0 0.5rem 0.5rem;
    }
    .action-item {
        background-color: #F3F4F6;
        border-left: 4px solid #38BDF8;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    .high-priority {
        border-left: 4px solid #EF4444;
    }
    .medium-priority {
        border-left: 4px solid #F59E0B;
    }
    .low-priority {
        border-left: 4px solid #10B981;
    }
    div[data-testid="stSidebar"] {
        background: #1E3A8A;
        color: white;
    }
    div[data-testid="stSidebar"] .css-17m3m1o {
        color: white;
    }
    .sidebar-content {
        margin-top: 1rem;
        padding: 1rem;
    }
    .sidebar-header {
        font-size: 1.2rem;
        color: white;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .sidebar-subheader {
        font-size: 1rem;
        color: #DBEAFE;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    div[data-testid="stFileUploader"] {
        background-color: #DBEAFE !important;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    div.stButton > button {
        background-color: #2563EB;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #1D4ED8;
    }
    div.stDownloadButton > button {
        background-color: #059669;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        width: 100%;
    }
    div.stDownloadButton > button:hover {
        background-color: #047857;
    }
</style>
""", unsafe_allow_html=True)

# Function to generate a download link for the sample data
def get_sample_data_download_link(filename="sample_data.json"):
    """Generates a link to download the sample data."""
    # Sample data (a subset of the full data)
    sample_data = [
        {
            "fullVisitorId": "001107862212762250",
            "visitId": "1494179788",
            "visitNumber": "1",
            "visits": "1",
            "hitCount": "19",
            "pageviews": "13",
            "timeOnSite": "230",
            "bounces": "0",
            "newVisits": "1",
            "source": "google",
            "medium": "organic",
            "browser": "Chrome",
            "isMobile": True,
            "deviceCategory": "mobile",
            "continent": "Asia",
            "country": "Malaysia",
            "city": "Kuala Lumpur",
            "channelGrouping": "Organic Search",
            "landingScreenName": "shop.googlemerchandisestore.com/google+redesign/apparel/mens/mens+t+shirts",
            "exitScreenName": "shop.googlemerchandisestore.com/home",
            "navigationFlow": "/google+redesign/apparel/mens/mens+t+shirts -> /google+redesign/bags/backpacks/home -> /google+redesign/office",
            "pageTitleFlow": "Men's T-Shirts | Apparel | Google Merchandise Store -> Backpacks | Bags | Google Merchandise Store -> Office | Google Merchandise Store"
        },
        {
            "fullVisitorId": "002138105781380660",
            "visitId": "1494179788",
            "visitNumber": "1",
            "visits": "1",
            "hitCount": "2",
            "pageviews": "1",
            "timeOnSite": "0",
            "bounces": "1",
            "newVisits": "1",
            "source": "facebook",
            "medium": "social",
            "browser": "Chrome",
            "isMobile": False,
            "deviceCategory": "desktop",
            "continent": "Americas",
            "country": "United States",
            "city": "New York",
            "channelGrouping": "Social",
            "landingScreenName": "shop.googlemerchandisestore.com/home",
            "exitScreenName": "shop.googlemerchandisestore.com/home",
            "navigationFlow": "/home",
            "pageTitleFlow": "Home"
        },
        {
            "fullVisitorId": "003457859962723410",
            "visitId": "1494179788",
            "visitNumber": "3",
            "visits": "3",
            "hitCount": "6",
            "pageviews": "3",
            "timeOnSite": "45",
            "bounces": "0",
            "newVisits": "0",
            "source": "(direct)",
            "medium": "(none)",
            "browser": "Safari",
            "isMobile": True,
            "deviceCategory": "mobile",
            "continent": "Europe",
            "country": "United Kingdom",
            "city": "London",
            "channelGrouping": "Direct",
            "landingScreenName": "shop.googlemerchandisestore.com/signin.html",
            "exitScreenName": "shop.googlemerchandisestore.com/google+redesign/apparel/mens/mens+outerwear",
            "navigationFlow": "/signin.html -> /home -> /google+redesign/apparel/mens/mens+outerwear",
            "pageTitleFlow": "Sign In | Google Merchandise Store -> Home -> Men's Outerwear | Apparel | Google Merchandise Store"
        }
    ]
    
    # Convert to JSON string
    json_str = json.dumps(sample_data, indent=4)
    
    # Create a BytesIO object
    buf = io.BytesIO()
    buf.write(json_str.encode())
    buf.seek(0)
    
    # Create a base64 encoded string
    b64 = base64.b64encode(buf.read()).decode()
    
    return f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-link">Download Sample Data</a>'

def extract_value_safely(text, default=0):
    """Safely extract numeric values from text."""
    # Remove any non-numeric characters except for decimal points
    if isinstance(text, str):
        clean_text = re.sub(r'[^0-9.]', '', text)
        if clean_text:
            try:
                return float(clean_text)
            except ValueError:
                pass
    elif isinstance(text, (int, float)):
        return float(text)
    return default

def extract_sections_from_markdown(content):
    """Extract sections from markdown content using regex."""
    # Find all headings and their content
    pattern = r'(#{1,6})\s+(.*?)(?=\n#{1,6}\s+|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    sections = {}
    for level, section_content in matches:
        # Split the section content by newline to get the title and content
        lines = section_content.strip().split('\n', 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        sections[title] = {"level": len(level), "content": content}
    
    return sections

def get_bullet_points(text):
    """Extract bullet points from text."""
    bullet_points = []
    lines = text.split('\n')
    for line in lines:
        if line.strip().startswith(('- ', '* ', '+ ')):
            # Remove the bullet character and trim
            bullet_point = line.strip()[2:].strip()
            bullet_points.append(bullet_point)
    return bullet_points

def parse_report_content(content):
    """Parse the report content to extract key information."""
    # Extract sections
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[3:].strip()
            current_content = []
        elif line.startswith('### '):
            # Include subsection headers
            current_content.append(line)
        else:
            current_content.append(line)
    
    # Add the last section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    # Initialize the report structure
    report = {
        "website_type": "e-commerce",  # Default value
        "specific_issues": ["high bounce rate", "low conversion"],  # Default value
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "executive_summary": "",
        "metrics": {
            "total_visits": 0,
            "total_bounces": 0,
            "bounce_rate": 0.0,
            "average_time_on_site": 0.0,
            "average_pageviews_per_visit": 0.0,
            "conversion_rate": 0.0
        },
        "traffic_analysis": {
            "summary": "",
            "key_findings": []
        },
        "journey_analysis": {
            "summary": "",
            "journey_maps": [],
            "path_patterns": [],
            "conversion_insights": []
        },
        "device_location_analysis": {
            "summary": "",
            "device_breakdown": {
                "desktop": "0%",
                "mobile": "0%",
                "tablet": "0%"
            },
            "location_insights": [],
            "browser_stats": {
                "Chrome": "0%",
                "Safari": "0%",
                "Firefox": "0%",
                "Edge": "0%",
                "Other": "0%"
            }
        },
        "recommendations": []
    }
    
    # Extract executive summary if available
    if "Executive Summary" in sections:
        report["executive_summary"] = sections["Executive Summary"].strip()
    
    # Extract website type and issues from Overview
    if "Overview" in sections:
        for line in sections["Overview"].split('\n'):
            if "Website Type" in line and ":" in line:
                report["website_type"] = line.split(":", 1)[1].strip()
            if "Issues Analyzed" in line and ":" in line:
                issues = line.split(":", 1)[1].strip()
                report["specific_issues"] = [issue.strip() for issue in issues.split(",")]
    
    # Try to extract metrics from multiple possible sections
    metric_sections = ["Key Metrics", "Traffic and Engagement Analysis", "Key Findings"]
    for section_name in metric_sections:
        if section_name in sections:
            section_content = sections[section_name]
            
            # Look for metrics
            metrics_patterns = {
                "total_visits": r'(?:total_visits|total visits).*?(\d+)',
                "total_bounces": r'(?:total_bounces|total bounces).*?(\d+)',
                "bounce_rate": r'(?:bounce_rate|bounce rate).*?([\d.]+)',
                "average_time_on_site": r'(?:average_time_on_site|average time on site).*?([\d.]+)',
                "average_pageviews_per_visit": r'(?:average_pageviews|average pageviews).*?([\d.]+)',
                "total_pageviews": r'(?:total_pageviews|total pageviews).*?(\d+)',
                "conversion_rate": r'(?:conversion_rate|conversion rate).*?([\d.]+)'
            }
            
            for metric, pattern in metrics_patterns.items():
                match = re.search(pattern, section_content, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        # For rates that might be expressed as percentages
                        if metric in ["bounce_rate", "conversion_rate"] and value > 1:
                            value = value / 100
                        report["metrics"][metric] = value
                    except (ValueError, IndexError):
                        pass
    
    # Extract traffic analysis
    if "Traffic and Engagement Analysis" in sections:
        traffic_content = sections["Traffic and Engagement Analysis"]
        report["traffic_analysis"]["summary"] = traffic_content.split('\n\n')[0] if '\n\n' in traffic_content else traffic_content
        report["traffic_analysis"]["key_findings"] = get_bullet_points(traffic_content)
    
    # Extract user journey analysis
    journey_section_names = ["User Journey Analysis", "Journey Analysis"]
    for section_name in journey_section_names:
        if section_name in sections:
            journey_content = sections[section_name]
            report["journey_analysis"]["summary"] = journey_content.split('\n\n')[0] if '\n\n' in journey_content else journey_content
            
            # Look for journey maps, patterns and insights
            journey_subsections = journey_content.split('###')
            for subsection in journey_subsections:
                if not subsection.strip():
                    continue
                
                if 'Journey Maps' in subsection:
                    # Extract journey maps
                    journey_lines = subsection.split('\n')
                    for line in journey_lines:
                        if '->' in line:
                            report["journey_analysis"]["journey_maps"].append(line.strip())
                
                if 'Path Patterns' in subsection:
                    report["journey_analysis"]["path_patterns"] = get_bullet_points(subsection)
                
                if 'Conversion Insights' in subsection:
                    report["journey_analysis"]["conversion_insights"] = get_bullet_points(subsection)
    
    # Extract device and location analysis
    device_section_names = ["Device and Location Analysis", "Device Analysis"]
    for section_name in device_section_names:
        if section_name in sections:
            device_content = sections[section_name]
            report["device_location_analysis"]["summary"] = device_content.split('\n\n')[0] if '\n\n' in device_content else device_content
            
            # Look for device breakdown
            device_match = re.search(r'desktop[^%\d]*(\d+(?:\.\d+)?)%', device_content, re.IGNORECASE)
            if device_match:
                report["device_location_analysis"]["device_breakdown"]["desktop"] = f"{device_match.group(1)}%"
            
            mobile_match = re.search(r'mobile[^%\d]*(\d+(?:\.\d+)?)%', device_content, re.IGNORECASE)
            if mobile_match:
                report["device_location_analysis"]["device_breakdown"]["mobile"] = f"{mobile_match.group(1)}%"
            
            tablet_match = re.search(r'tablet[^%\d]*(\d+(?:\.\d+)?)%', device_content, re.IGNORECASE)
            if tablet_match:
                report["device_location_analysis"]["device_breakdown"]["tablet"] = f"{tablet_match.group(1)}%"
            
            # Look for browser stats
            browser_patterns = {
                "Chrome": r'Chrome[^%\d]*(\d+(?:\.\d+)?)%',
                "Safari": r'Safari[^%\d]*(\d+(?:\.\d+)?)%',
                "Firefox": r'Firefox[^%\d]*(\d+(?:\.\d+)?)%',
                "Edge": r'Edge[^%\d]*(\d+(?:\.\d+)?)%',
                "Other": r'Other[^%\d]*(\d+(?:\.\d+)?)%'
            }
            
            for browser, pattern in browser_patterns.items():
                match = re.search(pattern, device_content, re.IGNORECASE)
                if match:
                    report["device_location_analysis"]["browser_stats"][browser] = f"{match.group(1)}%"
            
            # Extract location insights
            location_subsection = None
            device_subsections = device_content.split('###')
            for subsection in device_subsections:
                if 'Location Insights' in subsection:
                    location_subsection = subsection
                    break
            
            if location_subsection:
                report["device_location_analysis"]["location_insights"] = get_bullet_points(location_subsection)
    
    # Extract recommendations and action items
    recommendation_sections = ["Recommendations", "Action Items"]
    for section_name in recommendation_sections:
        if section_name in sections:
            rec_content = sections[section_name]
            
            # Try to parse structured recommendations with priority
            rec_items = []
            current_item = None
            current_priority = "medium"
            current_impact = ""
            
            for line in rec_content.split('\n'):
                if line.startswith('### '):
                    # Save previous item if exists
                    if current_item:
                        rec_items.append({
                            "title": current_item,
                            "priority": current_priority,
                            "impact": current_impact
                        })
                    
                    # Start new item
                    current_item = line[4:].strip()
                    current_priority = "medium"
                    current_impact = ""
                elif 'Priority' in line and ':' in line:
                    priority_text = line.split(':', 1)[1].strip().lower()
                    if priority_text in ["high", "medium", "low"]:
                        current_priority = priority_text
                elif 'Impact' in line and ':' in line:
                    current_impact = line.split(':', 1)[1].strip()
            
            # Add the last item
            if current_item:
                rec_items.append({
                    "title": current_item,
                    "priority": current_priority,
                    "impact": current_impact
                })
            
            # If we found structured recommendations, use them
            if rec_items:
                report["recommendations"] = rec_items
                break
            
            # Otherwise try to extract simple recommendations from bullet points
            bullet_recs = get_bullet_points(rec_content)
            if bullet_recs:
                report["recommendations"] = [{"title": rec, "priority": "medium", "impact": ""} for rec in bullet_recs]
                break
    
    return report

def create_visualizations(analysis):
    """Creates visualizations based on the analysis data."""
    visualizations = {}
    
    # 1. Bounce Rate Gauge
    bounce_rate = analysis["metrics"].get("bounce_rate", 0.0)
    if isinstance(bounce_rate, str):
        try:
            bounce_rate = float(bounce_rate.strip('%')) / 100
        except ValueError:
            bounce_rate = 0.0
    
    # Make sure bounce_rate is between 0 and 1 for percentage
    if bounce_rate > 1:
        bounce_rate = bounce_rate / 100
    
    fig1 = go.Figure()
    fig1.add_trace(go.Indicator(
        mode="gauge+number",
        value=bounce_rate * 100,  # Convert to percentage for display
        title={"text": "Bounce Rate (%)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#EF4444" if bounce_rate > 0.5 else "#F59E0B"},
            "steps": [
                {"range": [0, 30], "color": "#10B981"},
                {"range": [30, 50], "color": "#F59E0B"},
                {"range": [50, 100], "color": "#EF4444"}
            ]
        }
    ))
    fig1.update_layout(height=250)
    visualizations["bounce_rate_gauge"] = fig1
    
    # 2. Conversion Rate Gauge
    conversion_rate = analysis["metrics"].get("conversion_rate", 0.0)
    if isinstance(conversion_rate, str):
        try:
            conversion_rate = float(conversion_rate.strip('%')) / 100
        except ValueError:
            conversion_rate = 0.0
    
    # Make sure conversion_rate is between 0 and 1 for percentage
    if conversion_rate > 1:
        conversion_rate = conversion_rate / 100
    
    fig2 = go.Figure()
    fig2.add_trace(go.Indicator(
        mode="gauge+number",
        value=conversion_rate * 100,  # Convert to percentage for display
        title={"text": "Conversion Rate (%)"},
        gauge={
            "axis": {"range": [0, 5]},
            "bar": {"color": "#10B981" if conversion_rate > 0.015 else "#F59E0B"},
            "steps": [
                {"range": [0, 1], "color": "#EF4444"},
                {"range": [1, 2], "color": "#F59E0B"},
                {"range": [2, 5], "color": "#10B981"}
            ]
        }
    ))
    fig2.update_layout(height=250)
    visualizations["conversion_rate_gauge"] = fig2
    
    # 3. Device Breakdown
    device_breakdown = analysis["device_location_analysis"]["device_breakdown"]
    device_data = {
        "Device": [],
        "Percentage": []
    }
    
    for device, percentage in device_breakdown.items():
        device_data["Device"].append(device.capitalize())
        # Extract numeric value
        value = extract_value_safely(percentage, 33.3)  # Default to 33.3% if parsing fails
        device_data["Percentage"].append(value)
    
    fig3 = px.pie(
        device_data, 
        values="Percentage", 
        names="Device",
        color="Device",
        color_discrete_map={
            "Desktop": "#38BDF8",
            "Mobile": "#10B981",
            "Tablet": "#F59E0B"
        },
        hole=0.4
    )
    fig3.update_layout(
        title="Device Breakdown",
        height=300
    )
    visualizations["device_breakdown"] = fig3
    
    # 4. Browser Statistics
    browser_stats = analysis["device_location_analysis"]["browser_stats"]
    browser_data = {
        "Browser": [],
        "Percentage": []
    }
    
    for browser, percentage in browser_stats.items():
        browser_data["Browser"].append(browser)
        # Extract numeric value
        value = extract_value_safely(percentage, 20.0)  # Default to 20% if parsing fails
        browser_data["Percentage"].append(value)
    
    fig4 = px.bar(
        browser_data, 
        x="Browser", 
        y="Percentage",
        color="Browser",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig4.update_layout(
        title="Browser Statistics",
        height=300,
        xaxis_title="",
        yaxis_title="Percentage (%)"
    )
    visualizations["browser_stats"] = fig4
    
    # 5. Recommendations Priority
    priority_counts = {"high": 0, "medium": 0, "low": 0}
    for rec in analysis["recommendations"]:
        priority = rec.get("priority", "medium").lower()
        if priority in priority_counts:
            priority_counts[priority] += 1
    
    priority_data = {
        "Priority": ["High", "Medium", "Low"],
        "Count": [priority_counts["high"], priority_counts["medium"], priority_counts["low"]]
    }
    
    fig5 = px.bar(
        priority_data,
        x="Priority",
        y="Count",
        color="Priority",
        color_discrete_map={
            "High": "#EF4444",
            "Medium": "#F59E0B",
            "Low": "#10B981"
        }
    )
    fig5.update_layout(
        title="Recommendations by Priority",
        height=300,
        xaxis_title="",
        yaxis_title="Number of Recommendations"
    )
    visualizations["recommendations"] = fig5
    
    return visualizations

def process_and_display_report(website_type, specific_issues, uploaded_file=None):
    """Process the uploaded data or markdown report and display results."""
    # Check if a file was uploaded
    if uploaded_file is None:
        st.warning("Please upload a data file to analyze.")
        return False
    
    try:
        # Check if the uploaded file is a markdown report or data
        if uploaded_file.name.endswith('.md'):
            # Read the markdown content
            content = uploaded_file.read().decode('utf-8')
            
            # Parse the report content
            analysis = parse_report_content(content)
            
            # Create visualizations
            visualizations = create_visualizations(analysis)
            
            # Store results in session state
            st.session_state.analysis_results = {
                'analysis': analysis,
                'visualizations': visualizations,
                'markdown_report': content
            }
            
            # Show success message
            st.success("Report loaded successfully! Scroll down to view the dashboard.")
            return True
            
        elif uploaded_file.name.endswith('.json'):
            # Process JSON data
            data = json.load(uploaded_file)
            st.info("Running analysis on uploaded JSON data... (This would typically call your analyze_website_session_parallel function)")
            
            # For demo purposes, let's assume we saved the results to a markdown file
            # In a real app, you would call your analysis function here
            md_file_path = f"{website_type}_analysis_report.md"
            
            # Check if the report file exists (it would be generated by your analysis function)
            if os.path.exists(md_file_path):
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the report content
                analysis = parse_report_content(content)
                
                # Create visualizations
                visualizations = create_visualizations(analysis)
                
                # Store results in session state
                st.session_state.analysis_results = {
                    'analysis': analysis,
                    'visualizations': visualizations,
                    'markdown_report': content
                }
                
                # Show success message
                st.success("Analysis completed successfully! Scroll down to view the report.")
                return True
            else:
                st.error(f"Analysis report file '{md_file_path}' not found. This would typically be generated by your analysis function.")
                return False
        else:
            st.error("Unsupported file format. Please upload a .md, .json, or .csv file.")
            return False
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)
        return False

# Main function
def main():
    # Check if the analysis results are already in the session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">Website Analytics Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-subheader">Instructions</div>', unsafe_allow_html=True)
        st.markdown("""
        1. Select the type of website you're analyzing
        2. Enter the specific issues you want to address
        3. Upload your analytics data in JSON/CSV format or a markdown report
        4. Click "Process Uploaded File" to process the data or view the report
        5. View the comprehensive report and visualizations
        """)
        
        st.markdown('<div class="sidebar-subheader">Sample Data</div>', unsafe_allow_html=True)
        st.markdown("Download sample data to test the application:")
        st.markdown(get_sample_data_download_link(), unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-subheader">About</div>', unsafe_allow_html=True)
        st.markdown("""
        This dashboard analyzes website session data to identify issues related to:
        - High bounce rates
        - Low conversion rates
        - User journey problems
        - Device and location patterns
        
        The analysis pipeline uses advanced LLM techniques to process the data and generate actionable recommendations.
        """)

    # Main content
    st.markdown('<div class="main-header">Website Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">Analyze your website performance and get actionable recommendations to improve user experience and conversions.</div>', unsafe_allow_html=True)
    
    # Input Section
    st.markdown('<div class="section-header">Analysis Configuration</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        website_type = st.selectbox(
            "Website Type", 
            options=["e-commerce", "blog", "portfolio", "corporate", "educational", "news", "service"],
            index=0
        )
    
    with col2:
        default_issues = ["high bounce rate", "low conversion"]
        specific_issues = st.multiselect(
            "Specific Issues",
            options=["high bounce rate", "low conversion", "poor mobile experience", "high exit rate", "low engagement", "abandoned carts", "navigation problems", "slow loading time"],
            default=default_issues
        )
    
    uploaded_file = st.file_uploader("Upload your analytics data (JSON/CSV) or a report (MD)", type=["json", "csv", "md"])
    st.markdown('<div class="note">You can upload raw data for analysis or a pre-generated markdown report file.</div>', unsafe_allow_html=True)
    
    # Generate Analysis button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("Process Uploaded File")
    
    # If the Generate Analysis button is clicked
    if generate_button:
        if not specific_issues:
            st.warning("Please select at least one specific issue to analyze.")
        elif uploaded_file is None:
            st.warning("Please upload a file to process.")
        else:
            with st.spinner("Processing file... Please wait"):
                process_and_display_report(website_type, specific_issues, uploaded_file)
    
    # Display the analysis results if available
    if 'analysis_results' in st.session_state and st.session_state.analysis_results:
        analysis = st.session_state.analysis_results['analysis']
        visualizations = st.session_state.analysis_results['visualizations']
        markdown_report = st.session_state.analysis_results.get('markdown_report', '')
        
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown(f'<div class="main-header">Analysis Report: {analysis["website_type"].title()} Website</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="description">Analysis Date: {analysis["analysis_date"]}</div>', unsafe_allow_html=True)
        
        # Executive Summary
        st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(analysis.get("executive_summary", "No executive summary available."))
        
        # Key Metrics
        st.markdown('<div class="section-header">Key Metrics</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = analysis.get("metrics", {})
        
        with col1:
            st.markdown(f'<div class="metric-value">{metrics.get("total_visits", 0)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Total Visits</div>', unsafe_allow_html=True)
        
        with col2:
            bounce_rate = metrics.get("bounce_rate", 0)
            if isinstance(bounce_rate, float) and bounce_rate <= 1:
                bounce_rate = bounce_rate * 100
            st.markdown(f'<div class="metric-value">{bounce_rate:.1f}%</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Bounce Rate</div>', unsafe_allow_html=True)
        
        with col3:
            pageviews = metrics.get("average_pageviews_per_visit", 0)
            st.markdown(f'<div class="metric-value">{pageviews:.1f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Avg. Pageviews</div>', unsafe_allow_html=True)
        
        with col4:
            conversion_rate = metrics.get("conversion_rate", 0)
            if isinstance(conversion_rate, float) and conversion_rate <= 1:
                conversion_rate = conversion_rate * 100
            st.markdown(f'<div class="metric-value">{conversion_rate:.2f}%</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Conversion Rate</div>', unsafe_allow_html=True)
        
        # Key Visualizations
        st.markdown('<div class="section-header">Key Visualizations</div>', unsafe_allow_html=True)
        
        # Row 1: Bounce Rate and Conversion Rate Gauges
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(visualizations.get("bounce_rate_gauge"), use_container_width=True)
        with col2:
            st.plotly_chart(visualizations.get("conversion_rate_gauge"), use_container_width=True)
        
        # Row 2: Device Breakdown and Browser Stats
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(visualizations.get("device_breakdown"), use_container_width=True)
        with col2:
            st.plotly_chart(visualizations.get("browser_stats"), use_container_width=True)
        
        # Create tabs for detailed analysis sections
        tabs = st.tabs(["Traffic Analysis", "User Journey Analysis", "Device & Location Analysis", "Recommendations"])
        
        # Traffic Analysis Tab
        with tabs[0]:
            st.markdown('<div class="section-header">Traffic and Engagement Analysis</div>', unsafe_allow_html=True)
            st.markdown(analysis["traffic_analysis"].get("summary", "No traffic analysis available."))
            
            if analysis["traffic_analysis"].get("key_findings"):
                st.markdown('<br><div class="section-header">Key Findings</div>', unsafe_allow_html=True)
                for finding in analysis["traffic_analysis"]["key_findings"]:
                    st.markdown(f"• {finding}")
        
        # User Journey Analysis Tab
        with tabs[1]:
            st.markdown('<div class="section-header">User Journey Analysis</div>', unsafe_allow_html=True)
            st.markdown(analysis["journey_analysis"].get("summary", "No journey analysis available."))
            
            if analysis["journey_analysis"].get("journey_maps"):
                st.markdown('<br><div class="section-header">Top User Journeys</div>', unsafe_allow_html=True)
                for i, journey in enumerate(analysis["journey_analysis"]["journey_maps"][:5]):
                    st.markdown(f"**Journey {i+1}**: `{journey}`")
            
            if analysis["journey_analysis"].get("path_patterns"):
                st.markdown('<br><div class="section-header">Path Patterns</div>', unsafe_allow_html=True)
                for pattern in analysis["journey_analysis"]["path_patterns"]:
                    st.markdown(f"• {pattern}")
            
            if analysis["journey_analysis"].get("conversion_insights"):
                st.markdown('<br><div class="section-header">Conversion Insights</div>', unsafe_allow_html=True)
                for insight in analysis["journey_analysis"]["conversion_insights"]:
                    st.markdown(f"• {insight}")
        
        # Device & Location Analysis Tab
        with tabs[2]:
            st.markdown('<div class="section-header">Device and Location Analysis</div>', unsafe_allow_html=True)
            st.markdown(analysis["device_location_analysis"].get("summary", "No device analysis available."))
            
            st.markdown('<div class="section-header">Device Breakdown</div>', unsafe_allow_html=True)
            device_breakdown = analysis["device_location_analysis"]["device_breakdown"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Desktop", device_breakdown.get("desktop", "0%"))
            with col2:
                st.metric("Mobile", device_breakdown.get("mobile", "0%"))
            with col3:
                st.metric("Tablet", device_breakdown.get("tablet", "0%"))
            
            if analysis["device_location_analysis"].get("location_insights"):
                st.markdown('<br><div class="section-header">Location Insights</div>', unsafe_allow_html=True)
                for insight in analysis["device_location_analysis"]["location_insights"]:
                    st.markdown(f"• {insight}")
            
            st.markdown('<br><div class="section-header">Browser Statistics</div>', unsafe_allow_html=True)
            browser_stats = analysis["device_location_analysis"]["browser_stats"]
            for browser, percentage in browser_stats.items():
                # Try to extract a numeric value for the width
                try:
                    if isinstance(percentage, str):
                        col_width = float(percentage.replace('%', '').strip())
                    else:
                        col_width = float(percentage)
                except ValueError:
                    col_width = 0
                
                # Ensure the width is within bounds
                col_width = max(0, min(100, col_width))
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 100px; flex-shrink: 0;">{browser}</div>
                    <div style="flex-grow: 1; background-color: #e9ecef; border-radius: 5px; height: 25px;">
                        <div style="width: {col_width}%; height: 100%; background-color: #38BDF8; border-radius: 5px;"></div>
                    </div>
                    <div style="width: 60px; flex-shrink: 0; text-align: right; margin-left: 10px;">{percentage}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Recommendations Tab
        with tabs[3]:
            st.markdown('<div class="section-header">Recommendations</div>', unsafe_allow_html=True)
            
            if "recommendations" in visualizations:
                st.plotly_chart(visualizations["recommendations"], use_container_width=True)
            
            for rec in analysis["recommendations"]:
                priority = rec.get("priority", "medium").lower()
                priority_class = f"{priority}-priority"
                st.markdown(f'<div class="action-item {priority_class}">', unsafe_allow_html=True)
                st.markdown(f"### {rec['title']}")
                st.markdown(f"**Priority**: {priority.title()}")
                
                if rec.get("impact"):
                    st.markdown(f"**Expected Impact**: {rec['impact']}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Download Report Button
        st.markdown('<hr>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="Download Full Report",
                data=markdown_report,
                file_name=f"{analysis['website_type']}_analysis_report.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()
            