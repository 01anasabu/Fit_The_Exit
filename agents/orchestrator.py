"""
Orchestrator Agent for the Website Analyzer application.
"""

import json
from models.state import AgentState, FinalReport
from utils.helpers import show_progress, extract_json_from_text
from utils.mistral_client import query_mistral
from langchain_core.messages import AIMessage

def orchestrator_agent(state: AgentState) -> AgentState:
    """
    This agent combines all analyses and generates a final comprehensive report.
    
    Args:
        state: The current state
        
    Returns:
        Updated state with final report
    """
    # Update and display current agent
    try:
        state["current_agent"] = "Orchestrator Agent"
        show_progress(state["current_agent"])
        
        # Get all analyses
        traffic_analysis = state["traffic_engagement_analysis"]
        user_journey_analysis = state["user_journey_analysis"]
        device_location_analysis = state["device_location_analysis"]
        
        # Prepare prompt for Mistral
        system_prompt = """You are an Orchestrator Agent. Your responsibility is to synthesize analyses from multiple specialized agents and create a highly concise, actionable report that does not exceed 3 pages when printed.

Review the analyses provided and create a focused report in JSON format with this structure:

{
  "key_performance_metrics": [
    {"metric": "Metric name", "value": "Value"}
    // Include only 4-5 most essential metrics
  ],
  "core_issues": [
    "Brief bullet point of critical problem 1",
    "Brief bullet point of critical problem 2"
    // Include only 3-5 most critical issues
  ],
  "user_behavior_insights": [
    "Short bullet point about key user journey pattern 1",
    "Short bullet point about key user journey pattern 2"
    // Include only 3-5 most important patterns
  ],
  "device_location_data": [
    {"category": "Category name", "data": "Key statistic"}
    // Include only 3-4 most relevant statistics
  ],
  "prioritized_action_plan": [
    {
      "problem": "One-sentence definition of the identified issue",
      "supporting_data": [
        "Key data point 1",
        "Key data point 2"
        // Include only 2-3 most relevant data points
      ],
      "corrective_measures": [
        "Specific action 1",
        "Specific action 2"
        // Include only 2-3 highest-impact actions
      ],
      "priority": "high | medium | low"
    }
    // Include only 3-4 most important issues
  ]
}

Use extreme brevity throughout. Focus only on the most critical insights and highest-impact action items. Eliminate all redundancies to ensure the entire report content would fit within 3 pages when formatted for printing."""
        
        # Convert analyses to JSON strings
        traffic_str = json.dumps(traffic_analysis, indent=2)
        journey_str = json.dumps(user_journey_analysis, indent=2)
        device_str = json.dumps(device_location_analysis, indent=2)
        
        # Create the messages for Mistral
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Website Type: {state['website_info']['type']}\nSpecific Issues: {state['website_info']['specific_issues']}\n\nTraffic and Engagement Analysis:\n{traffic_str}\n\nUser Journey Analysis:\n{journey_str}\n\nDevice and Location Analysis:\n{device_str}"}
        ]
        
        # Query Mistral
        response = query_mistral(messages)
        
        # Extract the JSON response
        try:
            # Find JSON in the response
            response_json = extract_json_from_text(response)
            
            if not response_json:
                print("Warning: Failed to extract JSON from orchestrator response")
                print("Response snippet:", response[:100])
                
                # Create default structure using the FinalReport TypedDict
                final_report = FinalReport(
                    key_performance_metrics=[{"metric": "Error", "value": "Failed to generate metrics"}],
                    core_issues=["Analysis incomplete due to technical issues"],
                    user_behavior_insights=["Unable to analyze user behavior"],
                    device_location_data=[{"category": "Error", "data": "Data unavailable"}],
                    prioritized_action_plan=[]
                )
            else:
                # Create the final report with default values if keys are missing
                final_report = FinalReport(
                    key_performance_metrics=response_json.get("key_performance_metrics", []),
                    core_issues=response_json.get("core_issues", []),
                    user_behavior_insights=response_json.get("user_behavior_insights", []),
                    device_location_data=response_json.get("device_location_data", []),
                    prioritized_action_plan=response_json.get("prioritized_action_plan", [])
                )
        except Exception as e:
            print(f"Error in orchestrator: {e}")
            
            # Create a minimal report in case of errors using the FinalReport TypedDict
            final_report = FinalReport(
                key_performance_metrics=[{"metric": "Error", "value": f"Error: {str(e)}"}],
                core_issues=["Error occurred during analysis"],
                user_behavior_insights=[],
                device_location_data=[{"category": "Status", "data": "Analysis failed"}],
                prioritized_action_plan=[{
                    "problem": f"Error generating report: {str(e)}",
                    "supporting_data": ["Technical error occurred"],
                    "corrective_measures": ["Please try again or contact support"],
                    "priority": "high"
                }]
            )
        
        # Update the state
        new_state = state.copy()
        new_state["final_report"] = final_report
        new_state["messages"].append(AIMessage(content=response))
        
        return new_state
    except Exception as e:
        # Add agent name to error message
        raise Exception(f"orchestrator agent error: {str(e)}")