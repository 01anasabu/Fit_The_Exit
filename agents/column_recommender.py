"""
Column Recommendation Agent for the Website Analyzer application.
"""

import json
from config import SAMPLE_SIZE
from models.state import AgentState, ColumnRecommendations
from utils.helpers import show_progress, extract_json_from_text
from utils.mistral_client import query_mistral
from langchain_core.messages import AIMessage

def column_recommendation_agent(state: AgentState) -> AgentState:
    """
    This agent analyzes sample rows from the session data and recommends
    which columns to use for each specialized analysis agent.
    
    Args:
        state: The current state
        
    Returns:
        Updated state with column recommendations
    """
    # Update and display current agent
    try:
        state["current_agent"] = "Column Recommendation Agent"
        show_progress(state["current_agent"])
        
        # Extract sample data
        sample_data = state["all_sessions"][:SAMPLE_SIZE]
        
        # Get all available columns (flattened)
        all_columns = set()
        for session in sample_data:
            for key in session.keys():
                all_columns.add(key)
                # Add nested columns for hits_data
                if key in ["navigationFlow", "pageTitleFlow"]:
                    all_columns.add(f"{key}")
        
        # Prepare prompt for Mistral
        system_prompt = """You are a Column Recommendation Agent. Your responsibility is to analyze sample data from website analytics and recommend which columns should be used by each specialized analysis agent.

    Based on the sample data provided, recommend columns for these analysis agents:

    1. Traffic and Engagement Analysis Agent: Focuses on sources of traffic, engagement metrics, and overall website activity.
    2. User Journey and Navigation Agent: Focuses on user navigation paths, conversion funnels, and user flow.
    3. Device and Location Analysis Agent: Focuses on device types, geographic locations, and technical aspects.

    Your output should be a JSON object with the following structure:
    {
    "traffic_engagement_columns": ["column1", "column2", ...],
    "user_journey_columns": ["column3", "column4", ...],
    "device_location_columns": ["column5", "column6", ...]
    }

    Ensure each agent gets all the columns it needs for effective analysis. Some columns may be used by multiple agents.
    """
        
        # Convert sample data to a pretty-printed JSON string
        sample_data_str = json.dumps(sample_data, indent=2)
        
        # Create the messages for Mistral
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Website Type: {state['website_info']['type']}\nSpecific Issues: {state['website_info']['specific_issues']}\n\nAvailable Columns: {sorted(list(all_columns))}\n\nSample Data:\n{sample_data_str}"}
        ]
        
        # Query Mistral
        response = query_mistral(messages)
        
        # Extract the JSON response
        column_data = extract_json_from_text(response)
        
        # If no valid columns were extracted, create default recommendations
        if not column_data or not column_data.get("traffic_engagement_columns"):
            print("Creating default column recommendations")
            column_data = {
                "traffic_engagement_columns": ["source", "medium", "channelGrouping", "timeOnSite", "bounces", "visits"],
                "user_journey_columns": ["navigationFlow", "pageTitleFlow", "landingScreenName", "exitScreenName", "pageviews"],
                "device_location_columns": ["deviceCategory", "isMobile", "browser", "country", "continent", "city"]
            }
        
        # Ensure we have all required keys with default empty lists
        column_recommendations = ColumnRecommendations(
            traffic_engagement_columns=column_data.get("traffic_engagement_columns", []),
            user_journey_columns=column_data.get("user_journey_columns", []),
            device_location_columns=column_data.get("device_location_columns", [])
        )
        
        # Update the state
        new_state = state.copy()
        new_state["column_recommendations"] = column_recommendations
        new_state["messages"].append(AIMessage(content=response))
        
        print(f"Column recommendations generated: {json.dumps(column_recommendations, indent=2)}")
        
        return new_state
    except Exception as e:
    # Add agent name to error message
        raise Exception(f"traffic_engagement agent error: {str(e)}")