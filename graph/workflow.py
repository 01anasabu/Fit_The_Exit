"""
LangGraph workflow definition for the Website Analyzer application.
"""

from typing import Literal
from langgraph.graph import StateGraph, END, START
from models.state import AgentState

# Import agents
from agents.column_recommender import column_recommendation_agent
from agents.traffic_analyzer import traffic_engagement_agent
from agents.journey_analyzer import user_journey_agent
from agents.device_analyzer import device_location_agent
from agents.orchestrator import orchestrator_agent

def router(state: AgentState) -> Literal["column_recommendation_node", "traffic_engagement_node", "user_journey_node", "device_location_node", "orchestrator_node"]:
    """
    State router for the workflow. Determines the next node to execute based on the current state.
    """
    # First, run column recommendation if not done yet
    if state.get("column_recommendations") is None:
        return "column_recommendation_node"
    
    # Run each analysis agent if not done yet
    if state.get("traffic_engagement_analysis") is None:
        return "traffic_engagement_node"
    
    if state.get("user_journey_analysis") is None:
        return "user_journey_node"
    
    if state.get("device_location_analysis") is None:
        return "device_location_node"
    
    # Finally, run the orchestrator if not done yet
    if state.get("final_report") is None:
        return "orchestrator_node"
    
    # If everything is done, end the graph
    return END

def build_graph():
    """
    Build and return the LangGraph workflow.
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add the nodes
    workflow.add_node("column_recommendation_node", column_recommendation_agent)
    workflow.add_node("traffic_engagement_node", traffic_engagement_agent)
    workflow.add_node("user_journey_node", user_journey_agent)
    workflow.add_node("device_location_node", device_location_agent)
    workflow.add_node("orchestrator_node", orchestrator_agent)
    
    # Create a sequential flow
    workflow.add_edge(START, "column_recommendation_node")
    workflow.add_edge("column_recommendation_node", "traffic_engagement_node")
    workflow.add_edge("traffic_engagement_node", "user_journey_node")
    workflow.add_edge("user_journey_node", "device_location_node")
    workflow.add_edge("device_location_node", "orchestrator_node")
    workflow.add_edge("orchestrator_node", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app

def build_conditional_graph():
    """
    Build and return the LangGraph workflow with conditional routing.
    Use this if you want to skip steps that have already been completed.
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add the nodes
    workflow.add_node("column_recommendation_node", column_recommendation_agent)
    workflow.add_node("traffic_engagement_node", traffic_engagement_agent)
    workflow.add_node("user_journey_node", user_journey_agent)
    workflow.add_node("device_location_node", device_location_agent)
    workflow.add_node("orchestrator_node", orchestrator_agent)
    
    # Add the edges using the router
    workflow.add_conditional_edges(START, router)
    
    # Also add direct edges for the router to use
    workflow.add_edge("column_recommendation_node", "traffic_engagement_node")
    workflow.add_edge("traffic_engagement_node", "user_journey_node")
    workflow.add_edge("user_journey_node", "device_location_node")
    workflow.add_edge("device_location_node", "orchestrator_node")
    workflow.add_edge("orchestrator_node", END)
    
    # workflow.add_edge("device_location_node", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app