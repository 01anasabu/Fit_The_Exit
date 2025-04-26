"""
Traffic Engagement Analysis Agent for the Website Analyzer application.
"""

import json
from models.state import AgentState, TrafficEngagementAnalysis
from utils.helpers import show_progress, filter_session_data, extract_json_from_text
from utils.mistral_client import query_mistral
from langchain_core.messages import AIMessage

def traffic_engagement_agent(state: AgentState) -> AgentState:
    """
    This agent analyzes traffic sources, engagement metrics, and overall website activity.
    
    Args:
        state: The current state
        
    Returns:
        Updated state with traffic and engagement analysis
    """
    # Update and display current agent
    try:
      state["current_agent"] = "Traffic and Engagement Analysis Agent"
      show_progress(state["current_agent"])
      
      # Get recommended columns
      columns = state["column_recommendations"]["traffic_engagement_columns"]
      print(f"Using columns: {columns}")
      
      # Filter session data to include only relevant columns
      filtered_data = filter_session_data(state["all_sessions"], columns)
      print(filtered_data)
      
      # Prepare prompt for Mistral
      system_prompt = """You are a Traffic and Engagement Analysis Agent. Your responsibility is to analyze website traffic sources, engagement metrics, and overall website activity.

  Analyze the provided data and return a structured analysis with these components:
  1. A summary of overall traffic and engagement patterns
  2. Key metrics for traffic and engagement
  3. Specific findings and insights

  Your output should be in JSON format with this structure:
  {
    "summary": "A clear summary of traffic and engagement patterns",
    "key_metrics": {
      "metric1": "value1",
      "metric2": "value2"
    },
    "findings": [
      "Finding 1 about traffic patterns",
      "Finding 2 about engagement issues",
      "Finding 3 about potential improvements"
    ]
  }

  Focus on actionable insights that could help improve website performance.
  """
      
      # Convert filtered data to a pretty-printed JSON string
      filtered_data_str = json.dumps(filtered_data, indent=2)
      
      # Create the messages for Mistral
      messages = [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": f"Website Type: {state['website_info']['type']}\nSpecific Issues: {state['website_info']['specific_issues']}\n\nTraffic and Engagement Data:\n{filtered_data_str}"}
      ]
      
      # Query Mistral
      response = query_mistral(messages)
      print("response from traffic analyzer",response)
      
      # Extract the JSON response
      analysis_data = extract_json_from_text(response)
      
      # Create the analysis with default values if keys are missing
      traffic_engagement_analysis = TrafficEngagementAnalysis(
          summary=analysis_data.get("summary", "No summary provided"),
          key_metrics=analysis_data.get("key_metrics", {}),
          findings=analysis_data.get("findings", [])
      )
      
      # Update the state
      new_state = state.copy()
      new_state["traffic_engagement_analysis"] = traffic_engagement_analysis
      new_state["messages"].append(AIMessage(content=response))
      
      return new_state
    except Exception as e:
      # Add agent name to error message
      raise Exception(f"traffic_engagement agent error: {str(e)}")