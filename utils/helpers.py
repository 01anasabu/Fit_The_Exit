"""
Common utility functions for the Website Analyzer application.
"""

import json
from typing import Dict, List, Any

def show_progress(agent_name: str):
    """Display progress information in the terminal."""
    from config import TERMINAL_WIDTH
    print(f"\n{'='*TERMINAL_WIDTH}")
    print(f"🔄 Running: {agent_name}")
    print(f"{'='*TERMINAL_WIDTH}\n")

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract a JSON object from a text string."""
    try:
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        else:
            print("Warning: No JSON object found in the text")
            print(f"Text snippet: {text[:100]}...")
            return {}
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        print(f"Text snippet: {text[:100]}...")
        return {}

def filter_session_data(sessions: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
    """Filter session data to include only the specified columns."""
    filtered_sessions = []
    for session in sessions:
        filtered_session = {}
        for col in columns:
            # Handle nested columns like hits_data.pagePath
            if '.' in col:
                parent, child = col.split('.', 1)
                if parent in session and isinstance(session[parent], list):
                    filtered_session[parent] = []
                    for item in session[parent]:
                        if child in item:
                            if parent not in filtered_session:
                                filtered_session[parent] = []
                            filtered_session[parent].append({child: item[child]})
            elif col in session:
                filtered_session[col] = session[col]
        filtered_sessions.append(filtered_session)
    return filtered_sessions