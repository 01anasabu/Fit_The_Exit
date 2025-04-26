#!/usr/bin/env python3
import json
import time
import concurrent.futures
from typing import Dict, List, Any, Tuple
 
from dotenv import load_dotenv
from models.state import WebsiteType, AgentState, FinalReport
from graph.workflow import build_graph
from reporting.markdown import generate_markdown_report
from langchain_core.messages import HumanMessage
from utils.helpers import show_progress
from agents.orchestrator import orchestrator_agent
 
from langgraph.graph import StateGraph, END, START
 
# Import agents
from agents.column_recommender import column_recommendation_agent
from agents.traffic_analyzer import traffic_engagement_agent
from agents.journey_analyzer import user_journey_agent
from agents.device_analyzer import device_location_agent
 
# Load environment variables from .env file
load_dotenv()
 
# Define chunk size and parallelism
CHUNK_SIZE = 20 # Adjust based on your needs
MAX_WORKERS = 4  # Limit concurrent workers to avoid rate limits
 
def analyze_chunk(website_type: str, specific_issues: List[str], chunk: List[Dict[str, Any]],
                 column_recommendations=None, chunk_id=None, start_from=None) -> AgentState:
    """
    Process a single chunk of session data through the agent pipeline.
   
    Args:
        website_type: Type of website
        specific_issues: List of specific issues to focus on
        chunk: A subset of session data to analyze
        column_recommendations: Optional pre-computed column recommendations
        chunk_id: Optional identifier for the chunk for logging
        start_from: Optional agent to start processing from (to resume after failure)
       
    Returns:
        The final state for this chunk
    """
    chunk_identifier = f"Chunk {chunk_id}" if chunk_id is not None else "Chunk"
    print(f"Processing {chunk_identifier} with {len(chunk)} sessions")
   
    # Process UTF-8 encoded strings
    processed_chunk = []
    for session in chunk:
        if "navigationFlow" in session:
            session["navigationFlow"] = session["navigationFlow"].replace("-\\u003e", "->").replace("-\\u002d\\u003e", "->")
        if "pageTitleFlow" in session:
            session["pageTitleFlow"] = session["pageTitleFlow"].replace("-\\u003e", "->").replace("-\\u002d\\u003e", "->")
        processed_chunk.append(session)
   
    # Create initial state
    initial_state = AgentState(
        website_info=WebsiteType(
            type=website_type,
            specific_issues=specific_issues
        ),
        all_sessions=processed_chunk,
        column_recommendations=column_recommendations,
        traffic_engagement_analysis=None,
        user_journey_analysis=None,
        device_location_analysis=None,
        final_report=None,
        current_agent=start_from,  # Set the starting agent if provided
        messages=[HumanMessage(content=f"Analyze this chunk of {website_type} website sessions")]
    )
   
    # Build a custom graph based on where to start from
    if start_from:
        app = build_custom_graph(start_from)
        print(f"Resuming from {start_from} agent")
    else:
        app = build_graph()
   
    # Run the graph
    chunk_state = app.invoke(initial_state)
   
    print(f"✅ {chunk_identifier} processing complete")
    return chunk_state
 
 
def build_custom_graph(start_from):
    """Build a custom graph that starts from a specific agent"""
    workflow = StateGraph(AgentState)
   
    # Add the nodes
    workflow.add_node("column_recommendation_node", column_recommendation_agent)
    workflow.add_node("traffic_engagement_node", traffic_engagement_agent)
    workflow.add_node("user_journey_node", user_journey_agent)
    workflow.add_node("device_location_node", device_location_agent)
    workflow.add_node("orchestrator_node", orchestrator_agent)
   
    # Create edges based on where to start from
    if start_from == "traffic_engagement":
        workflow.add_edge(START, "traffic_engagement_node")
        workflow.add_edge("traffic_engagement_node", "user_journey_node")
    elif start_from == "user_journey":
        workflow.add_edge(START, "user_journey_node")
    elif start_from == "device_location":
        workflow.add_edge(START, "device_location_node")
    elif start_from == "orchestrator":
        workflow.add_edge(START, "orchestrator_node")
    else:
        workflow.add_edge(START, "column_recommendation_node")
        workflow.add_edge("column_recommendation_node", "traffic_engagement_node")
   
    # Add remaining edges
    workflow.add_edge("user_journey_node", "device_location_node")
    workflow.add_edge("device_location_node", "orchestrator_node")
    workflow.add_edge("orchestrator_node", END)
   
    # Compile the graph
    return workflow.compile()
 
def analyze_chunk_with_retry(website_type, specific_issues, chunk, column_recommendations, chunk_id, max_retries=3):
    """Process a chunk with retry logic that preserves progress."""
    agents_order = [None, "traffic_engagement", "user_journey", "device_location", "orchestrator"]
    current_agent_index = 0
   
    for attempt in range(max_retries + 1):
        try:
            return analyze_chunk(
                website_type,
                specific_issues,
                chunk,
                column_recommendations,
                chunk_id,
                start_from=agents_order[current_agent_index]
            )
        except Exception as e:
            error_msg = str(e)
            if "Requests rate limit exceeded" in error_msg and attempt < max_retries:
                # Determine which agent was running when the error occurred
                for i, agent in enumerate(agents_order):
                    if agent and agent in error_msg:
                        current_agent_index = i
                        break
               
                wait_time = 5 * (2 ** attempt)  # 5, 10, 20... seconds
                print(f"Error processing Chunk {chunk_id} at {agents_order[current_agent_index]} agent, retry {attempt+1}/{max_retries} in {wait_time}s")
                print(f"Error details: {error_msg}")
                time.sleep(wait_time)
            else:
                if attempt == max_retries:
                    print(f"Failed all {max_retries} retries for Chunk {chunk_id}")
                raise
 
def aggregate_with_llm(chunks_results, website_type, specific_issues, chunk_count):
    """
    Use LLM to aggregate results from multiple chunks.
   
    Args:
        chunks_results: List of results from each chunk
        website_type: Type of website
        specific_issues: Specific issues being analyzed
        chunk_count: Total number of chunks
       
    Returns:
        Aggregated analysis results
    """
    from utils.gemini_client import query_gemini
   
    print("Using Gemini to aggregate results from multiple chunks...")
   
    # Extract analyses from all chunks
    traffic_analyses = [result["traffic_engagement_analysis"] for result in chunks_results]
    journey_analyses = [result["user_journey_analysis"] for result in chunks_results]
    device_analyses = [result["device_location_analysis"] for result in chunks_results]
   
    # Prepare traffic analysis aggregation
    system_prompt = """You are an Analysis Aggregation Agent. Your task is to aggregate traffic and engagement analyses from multiple data chunks into a single coherent analysis.
 
Review the analyses from different chunks and create a unified analysis that:
1. Combines metrics into weighted averages
2. Removes duplicate findings
3. Identifies patterns across chunks
4. Creates a comprehensive summary
 
Your output should be in JSON format with this structure:
{
  "summary": "A comprehensive summary across all chunks",
  "key_metrics": {
    "metric1": "value1",
    "metric2": "value2"
  },
  "findings": [
    "Finding 1 (identified in multiple chunks)",
    "Finding 2 (specific to chunk X but significant)"
  ]
}
"""
   
    # Convert traffic analyses to a JSON string
    traffic_json = json.dumps(traffic_analyses, indent=2)
   
    # Create messages for the LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Website Type: {website_type}\nSpecific Issues: {specific_issues}\nNumber of Chunks: {chunk_count}\n\nTraffic Analyses from Multiple Chunks:\n{traffic_json}"}
    ]
   
    # Query Gemini
    response = query_gemini(messages)
   
    # Extract the aggregated traffic analysis
    from utils.helpers import extract_json_from_text
    traffic_agg = extract_json_from_text(response)
   
    if not traffic_agg:
        print("Warning: Failed to extract aggregated traffic analysis")
        traffic_agg = {
            "summary": "Failed to aggregate traffic analyses across chunks",
            "key_metrics": {},
            "findings": ["Aggregation failed"]
        }
   
    # Repeat for user journey analysis
    system_prompt = """You are an Analysis Aggregation Agent. Your task is to aggregate user journey analyses from multiple data chunks into a single coherent analysis.
 
Review the journey analyses from different chunks and create a unified analysis that:
1. Identifies the most representative journey maps
2. Combines path patterns without duplication
3. Aggregates conversion insights across all chunks
4. Creates a comprehensive summary
 
Your output should be in JSON format with this structure:
{
  "summary": "A comprehensive summary of user journeys across all chunks",
  "journey_maps": [
    "Most significant journey map 1",
    "Most significant journey map 2"
  ],
  "path_patterns": [
    "Pattern 1 (identified in multiple chunks)",
    "Pattern 2 (specific to chunk X but significant)"
  ],
  "conversion_insights": [
    "Insight 1 about conversion points",
    "Insight 2 about drop-off points"
  ]
}
"""
   
    # Convert journey analyses to a JSON string
    journey_json = json.dumps(journey_analyses, indent=2)
   
    # Create messages for the LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Website Type: {website_type}\nSpecific Issues: {specific_issues}\nNumber of Chunks: {chunk_count}\n\nJourney Analyses from Multiple Chunks:\n{journey_json}"}
    ]
   
    # Query Gemini
    response = query_gemini(messages)
   
    # Extract the aggregated journey analysis
    journey_agg = extract_json_from_text(response)
   
    if not journey_agg:
        print("Warning: Failed to extract aggregated journey analysis")
        journey_agg = {
            "summary": "Failed to aggregate journey analyses across chunks",
            "journey_maps": [],
            "path_patterns": [],
            "conversion_insights": ["Aggregation failed"]
        }
   
    # Repeat for device and location analysis
    system_prompt = """You are an Analysis Aggregation Agent. Your task is to aggregate device and location analyses from multiple data chunks into a single coherent analysis.
 
Review the device analyses from different chunks and create a unified analysis that:
1. Calculates weighted averages for device breakdown percentages
2. Combines location insights without duplication
3. Aggregates browser statistics across all chunks
4. Creates a comprehensive summary
 
Your output should be in JSON format with this structure:
{
  "summary": "A comprehensive summary of device and location patterns across all chunks",
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
"""
   
    # Convert device analyses to a JSON string
    device_json = json.dumps(device_analyses, indent=2)
   
    # Create messages for the LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Website Type: {website_type}\nSpecific Issues: {specific_issues}\nNumber of Chunks: {chunk_count}\n\nDevice Analyses from Multiple Chunks:\n{device_json}"}
    ]
   
    # Query Gemini
    response = query_gemini(messages)
   
    # Extract the aggregated device analysis
    device_agg = extract_json_from_text(response)
   
    if not device_agg:
        print("Warning: Failed to extract aggregated device analysis")
        device_agg = {
            "summary": "Failed to aggregate device analyses across chunks",
            "device_breakdown": {},
            "location_insights": [],
            "browser_stats": {}
        }
   
    # Return the aggregated analyses
    return {
        "traffic_engagement_analysis": traffic_agg,
        "user_journey_analysis": journey_agg,
        "device_location_analysis": device_agg
    }
   
 
def analyze_website_session_parallel(website_type: str, specific_issues: List[str], sessions_json: List[Dict[str, Any]], sample=False):
    """
    Analyze sessions for a website with parallel processing of chunks and LLM-based aggregation.
   
    Args:
        website_type: Type of website (e.g., "e-commerce")
        specific_issues: List of specific issues to focus on
        sessions_json: List of session data objects
        sample: If True, use smaller chunks and more parallelism for sample runs
   
    Returns:
        The final state after analysis and markdown report
    """
    chunk_size = CHUNK_SIZE
    max_workers = MAX_WORKERS
    
    if sample:
        chunk_size = 2
        max_workers = 3
        
    print(f"\n{'='*60}")
    print(f"🚀 Starting analysis for {website_type} website with parallel processing")
    print(f"{'='*60}")
   
    try:
        # Define chunks
        total_sessions = len(sessions_json)
        chunks = [sessions_json[i:i + chunk_size] for i in range(0, total_sessions, chunk_size)]
        num_chunks = len(chunks)
       
        print(f"Processing {total_sessions} sessions in {num_chunks} chunks (size: {chunk_size}) using {max_workers} parallel workers")
       
        # Process first chunk to get column recommendations (this must be done sequentially)
        print(f"\n{'='*60}")
        print(f"🔍 Processing primary chunk (1/{num_chunks}) to get column recommendations")
        print(f"{'='*60}")
       
        first_chunk_state = analyze_chunk(website_type, specific_issues, chunks[0], chunk_id=1)
        column_recommendations = first_chunk_state["column_recommendations"]
        all_chunk_results = [first_chunk_state]  # Store the first result
       
        # Process remaining chunks in parallel
        if num_chunks > 1:
            print(f"\n{'='*60}")
            print(f"⚡ Processing remaining {num_chunks-1} chunks in parallel")
            print(f"{'='*60}")
           
            remaining_chunks = chunks[1:]
            chunk_ids = list(range(2, num_chunks + 1))
           
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks with retry
                future_to_chunk_id = {
                    executor.submit(
                        analyze_chunk_with_retry,
                        website_type,
                        specific_issues,
                        chunk,
                        column_recommendations,
                        chunk_id
                    ): chunk_id
                    for chunk_id, chunk in zip(chunk_ids, remaining_chunks)
                }
               
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_chunk_id):
                    chunk_id = future_to_chunk_id[future]
                    try:
                        chunk_result = future.result()
                        all_chunk_results.append(chunk_result)
                        print(f"✅ Chunk {chunk_id}/{num_chunks} completed and results collected")
                    except Exception as e:
                        print(f"❌ Chunk {chunk_id}/{num_chunks} generated an exception: {e}")
                        # For critical failures, you might want to stop processing
                        # raise RuntimeError(f"Critical failure processing chunk {chunk_id}: {e}")
           
        # Use LLM to aggregate results from all chunks
        print(f"\n{'='*60}")
        print(f"🧠 Aggregating results across all {len(all_chunk_results)} successful chunks using Gemini")
        print(f"{'='*60}")
       
        aggregated_results = aggregate_with_llm(
            all_chunk_results,
            website_type,
            specific_issues,
            num_chunks
        )
       
        # Run the orchestrator agent with the aggregated results
        print(f"\n{'='*60}")
        print("🔄 Running: Final Orchestration on Gemini-aggregated results")
        print(f"{'='*60}\n")
       
        # Create a state with aggregated results for the orchestrator
        orchestrator_state = AgentState(
            website_info=all_chunk_results[0]["website_info"],
            all_sessions=[],  # Not needed for orchestrator
            column_recommendations=all_chunk_results[0]["column_recommendations"],
            traffic_engagement_analysis=aggregated_results["traffic_engagement_analysis"],
            user_journey_analysis=aggregated_results["user_journey_analysis"],
            device_location_analysis=aggregated_results["device_location_analysis"],
            final_report=None,
            current_agent="Orchestrator Agent",
            messages=[HumanMessage(content=f"Create final report for {website_type} website")]
        )
       
        # Run orchestrator
        final_state = orchestrator_agent(orchestrator_state)
       
        # Generate markdown report from new structure
        markdown_report = generate_markdown_report(
            final_state["final_report"],
            website_type,
            specific_issues
        )
       
        # Save markdown report to file
        report_filename = f"{website_type.replace(' ', '_')}_analysis_report.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(markdown_report)
       
        print(f"\n{'='*60}")
        print(f"✅ Analysis complete! Report saved to {report_filename}")
        print(f"{'='*60}\n")
       
        return final_state, markdown_report
       
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
       
        # Create a minimal emergency report
        emergency_report = f"""# Website Analysis Report - Error
 
## Error Information
An error occurred during the parallel analysis: {str(e)}
 
## Overview
- **Analysis Date**: {time.strftime("%Y-%m-%d %H:%M:%S")}
 
## Recommendations
- Check the input data format
- Ensure all required environment variables are set
- Check API connectivity
- Review the logs for more details
"""
       
        # Save emergency report
        emergency_filename = f"{website_type.replace(' ', '_')}_error_report.md"
        with open(emergency_filename, "w", encoding="utf-8") as f:
            f.write(emergency_report)
           
        print(f"\n{'='*60}")
        print(f"❌ Analysis failed! Error report saved to {emergency_filename}")
        print(f"{'='*60}\n")
       
        # Create minimal state and return emergency report
        minimal_state = AgentState(
            website_info=WebsiteType(
                type=website_type,
                specific_issues=specific_issues
            ),
            all_sessions=[],
            column_recommendations=None,
            traffic_engagement_analysis=None,
            user_journey_analysis=None,
            device_location_analysis=None,
            final_report=None,
            current_agent=None,
            messages=[HumanMessage(content=f"Analysis failed with error: {str(e)}")]
        )
       
        return minimal_state, emergency_report
 
 
# Original sequential processing function (kept for compatibility)
def analyze_website_session(website_type: str, specific_issues: List[str], sessions_json: List[Dict[str, Any]]):
    """
    Analyze sessions for a website with chunking and LLM-based aggregation (sequential processing).
   
    Args:
        website_type: Type of website (e.g., "e-commerce")
        specific_issues: List of specific issues to focus on
        sessions_json: List of session data objects
   
    Returns:
        The final state after analysis and markdown report
    """
    print("Running sequential analysis. For better performance, use analyze_website_session_parallel() instead.")
    return analyze_website_session_parallel(website_type, specific_issues, sessions_json, sample=False)
 
 
if __name__ == "__main__":
    website_type = "e-commerce"
    specific_issues = ["high bounce rate", "low conversion"]
   
    # Example session data (you would load your JSON here)
    with open("session_test.json", "r") as f:
        sessions_json = json.load(f)
   
    # Run the analysis with parallel processing
    result, markdown_report = analyze_website_session_parallel(website_type, specific_issues, sessions_json, sample=False)
   
    # Print markdown report to console
    print("\nMarkdown Report Preview:")
    print(f"\n{'-'*40}\n")
    print(markdown_report[:1000] + "...\n(Report truncated)")