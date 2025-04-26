"""
Device Location Analysis Agent for the Website Analyzer application.
"""

import json
from models.state import AgentState, DeviceLocationAnalysis
from utils.helpers import show_progress, filter_session_data, extract_json_from_text
from utils.mistral_client import query_mistral
from langchain_core.messages import AIMessage

def device_location_agent(state: AgentState) -> AgentState:
    """
    This agent analyzes device types, geographic locations, and technical aspects.
    
    Args:
        state: The current state
        
    Returns:
        Updated state with device and location analysis
    """
    # Update and display current agent
    try:
      state["current_agent"] = "Device and Location Analysis Agent"
      show_progress(state["current_agent"])
      
      # Get recommended columns
      columns = state["column_recommendations"]["device_location_columns"]
      print(f"Using columns: {columns}")
      
      # Filter session data to include only relevant columns
      filtered_data = filter_session_data(state["all_sessions"], columns)
      
      # Prepare prompt for Mistral
      system_prompt = """You are a Device and Location Analysis Agent. Your responsibility is to analyze device types, geographic locations, and technical aspects of website visits.

  Analyze the provided data and return a structured analysis with these components:
  1. A summary of device and location patterns
  2. Breakdown of device usage
  3. Geographic insights
  4. Browser and technical statistics

  Your output should be in JSON format with this structure:
  {
    "summary": "A clear summary of device and location patterns",
    "device_breakdown": {
      "desktop": "percentage%",
      "mobile": "percentage%",
      "tablet": "percentage%"
    },
    "location_insights": [
      "Insight 1 about geographic distribution",
      "Insight 2 about location-based patterns"
    ],
    "browser_stats": {
      "Chrome": "percentage%",
      "Firefox": "percentage%",
      "Safari": "percentage%"
    }
  }

  Focus on identifying how device and location factors influence user behavior and technical requirements.
  """
      
      # Convert filtered data to a pretty-printed JSON string
      filtered_data_str = json.dumps(filtered_data, indent=2)
      
      # Create the messages for Mistral
      messages = [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": f"Website Type: {state['website_info']['type']}\nSpecific Issues: {state['website_info']['specific_issues']}\n\nDevice and Location Data:\n{filtered_data_str}"}
      ]
      
      # Query Mistral
      response = query_mistral(messages)
      
      # Extract the JSON response
      analysis_data = extract_json_from_text(response)
      
      # Create the analysis with default values if keys are missing
      device_location_analysis = DeviceLocationAnalysis(
          summary=analysis_data.get("summary", "No summary provided"),
          device_breakdown=analysis_data.get("device_breakdown", {}),
          location_insights=analysis_data.get("location_insights", []),
          browser_stats=analysis_data.get("browser_stats", {})
      )
      
      # Update the state
      new_state = state.copy()
      new_state["device_location_analysis"] = device_location_analysis
      new_state["messages"].append(AIMessage(content=response))
      
      return new_state
    except Exception as e:
      # Add agent name to error message
      raise Exception(f"traffic_engagement agent error: {str(e)}")