"""
User Journey Analysis Agent for the Website Analyzer application.
"""

import json
from models.state import AgentState, UserJourneyAnalysis
from utils.helpers import show_progress, filter_session_data, extract_json_from_text
from utils.mistral_client import query_mistral
from langchain_core.messages import AIMessage

def user_journey_agent(state: AgentState) -> AgentState:
    """
    This agent analyzes user navigation paths, conversion funnels, and user flow.
    
    Args:
        state: The current state
        
    Returns:
        Updated state with user journey analysis
    """
    # Update and display current agent
    try:
      state["current_agent"] = "User Journey and Navigation Agent"
      show_progress(state["current_agent"])
      
      # Get recommended columns
      columns = state["column_recommendations"]["user_journey_columns"]
      print(f"Using columns: {columns}")
      
      # Filter session data to include only relevant columns
      filtered_data = filter_session_data(state["all_sessions"], columns)
      
      # Prepare prompt for Mistral
      system_prompt = """You are a User Journey and Navigation Agent. Your responsibility is to analyze user navigation paths, conversion funnels, and user flow through a website.

  Analyze the provided data and return a structured analysis with these components:
  1. A summary of user journey patterns
  2. Visual representations of journey maps (in text format)
  3. Common path patterns identified
  4. Insights about conversion points and drop-offs

  Your output should be in JSON format with this structure:
  {
    "summary": "A clear summary of user journey patterns",
    "journey_maps": [
      "Journey map 1: Path -> Path -> Exit",
      "Journey map 2: Path -> Path -> Path -> Exit"
    ],
    "path_patterns": [
      "Pattern 1: Users often return to the home page after viewing products",
      "Pattern 2: Quick view feature is frequently used before exit"
    ],
    "conversion_insights": [
      "Insight 1 about conversion points",
      "Insight 2 about drop-off points"
    ]
  }

  Focus on identifying problem areas in the user journey and potential improvements.
  """
      
      # Convert filtered data to a pretty-printed JSON string
      filtered_data_str = json.dumps(filtered_data, indent=2)
      
      # Create the messages for Mistral
      messages = [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": f"Website Type: {state['website_info']['type']}\nSpecific Issues: {state['website_info']['specific_issues']}\n\nUser Journey Data:\n{filtered_data_str}"}
      ]
      
      # Query Mistral
      response = query_mistral(messages)
      
      # Extract the JSON response
      analysis_data = extract_json_from_text(response)
      
      # Create the analysis with default values if keys are missing
      user_journey_analysis = UserJourneyAnalysis(
          summary=analysis_data.get("summary", "No summary provided"),
          journey_maps=analysis_data.get("journey_maps", []),
          path_patterns=analysis_data.get("path_patterns", []),
          conversion_insights=analysis_data.get("conversion_insights", [])
      )
      
      # Update the state
      new_state = state.copy()
      new_state["user_journey_analysis"] = user_journey_analysis
      new_state["messages"].append(AIMessage(content=response))
      
      return new_state
    
    except Exception as e:
        # Add agent name to error message
      raise Exception(f"traffic_engagement agent error: {str(e)}")