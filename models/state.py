"""
Type definitions and state classes for the Website Analyzer application.
"""

from typing import Dict, List, Any, TypedDict, Optional, Union
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

class WebsiteType(TypedDict):
    """Information about the website being analyzed."""
    type: str
    specific_issues: Optional[List[str]]

class ColumnRecommendations(TypedDict):
    """Column recommendations for each analysis agent."""
    traffic_engagement_columns: List[str]
    user_journey_columns: List[str]
    device_location_columns: List[str]

class TrafficEngagementAnalysis(TypedDict):
    """Traffic and engagement analysis results."""
    summary: str
    key_metrics: Dict[str, Any]
    findings: List[str]

class UserJourneyAnalysis(TypedDict):
    """User journey analysis results."""
    summary: str
    journey_maps: List[str]
    path_patterns: List[str]
    conversion_insights: List[str]

class DeviceLocationAnalysis(TypedDict):
    """Device and location analysis results."""
    summary: str
    device_breakdown: Dict[str, Any]
    location_insights: List[str]
    browser_stats: Dict[str, Any]

class FinalReport(TypedDict):
    """Final consolidated report with updated structure."""
    key_performance_metrics: List[Dict[str, str]]
    core_issues: List[str]
    user_behavior_insights: List[str]
    device_location_data: List[Dict[str, str]]
    prioritized_action_plan: List[Dict[str, Any]]

class AgentState(TypedDict):
    """The shared state that's passed between agents."""
    website_info: WebsiteType
    all_sessions: List[Dict[str, Any]]
    column_recommendations: Optional[ColumnRecommendations]
    traffic_engagement_analysis: Optional[TrafficEngagementAnalysis]
    user_journey_analysis: Optional[UserJourneyAnalysis]
    device_location_analysis: Optional[DeviceLocationAnalysis]
    final_report: Optional[FinalReport]
    current_agent: Optional[str]
    messages: List[Union[HumanMessage, AIMessage, ToolMessage]]