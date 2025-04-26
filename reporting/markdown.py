"""
Generate Markdown report from analysis results.
"""

import time
from typing import Dict, List, Any

def generate_markdown_report(final_report, website_type, specific_issues):
    """
    Generate a Markdown report from the analysis results using the new JSON structure.
    
    Args:
        final_report: The final report with the new structure
        website_type: The type of website analyzed
        specific_issues: The specific issues that were analyzed
        
    Returns:
        str: The Markdown report content
    """
    # Get current date and time
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Start building markdown
    markdown = f"#Agentic Analysis Report\n\n"
    
    # Overview section
    markdown += f"## Overview\n"
    # markdown += f"- **Website Type**: {website_type}\n"
    # markdown += f"- **Issues Analyzed**: {', '.join(specific_issues)}\n"
    markdown += f"- **Analysis Date**: {now}\n\n"
    
    
    
    
    
    markdown += "## Prioritized Action Plan\n"
    
    # Sort action items by priority (high, medium, low)
    def priority_sorter(item):
        priority_map = {"high": 0, "medium": 1, "low": 2}
        return priority_map.get(item.get("priority", "low"), 3)
    
    action_items = sorted(final_report.get("prioritized_action_plan", []), key=priority_sorter)
    
    for index, action in enumerate(action_items, 1):
        priority = action.get("priority", "medium").upper()
        problem = action.get("problem", "No problem defined")
        
        markdown += f"### {index}. {problem} [PRIORITY: {priority}]\n\n"
        
        # Supporting Data
        markdown += "#### Supporting Data:\n"
        for data in action.get("supporting_data", []):
            markdown += f"- {data}\n"
        markdown += "\n"
        
        # Corrective Measures
        markdown += "#### Corrective Measures:\n"
        for measure in action.get("corrective_measures", []):
            markdown += f"- {measure}\n"
        markdown += "\n"
    
    # Core Issues
    markdown += "## Core Issues\n"
    for issue in final_report.get("core_issues", []):
        markdown += f"- {issue}\n"
    markdown += "\n" 
   
        
    
    
    # User Behavior Insights
    markdown += "## User Behavior Insights\n"
    for insight in final_report.get("user_behavior_insights", []):
        markdown += f"- {insight}\n"
    markdown += "\n"
    
    # Device & Location Data
    markdown += "## Device & Location Data\n"
    for data in final_report.get("device_location_data", []):
        markdown += f"- **{data['category']}**: {data['data']}\n"
    markdown += "\n"
    
    # Key Performance Metrics
    markdown += "## Key Performance Metrics\n"
    for metric in final_report.get("key_performance_metrics", []):
        markdown += f"- **{metric['metric']}**: {metric['value']}\n"
    markdown += "\n"
    
    
    
    return markdown