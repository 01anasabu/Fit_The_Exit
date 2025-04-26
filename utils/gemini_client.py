"""
Gemini API client module for interfacing with Google's Gemini API.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gemini_client")

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key. If not provided, will look for GEMINI_API_KEY environment variable.
        """
        self.api_key = "<YOUR_GOOGLE_API_KEY>"
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set the GEMINI_API_KEY environment variable or pass the key explicitly.")
        
        # Configure base API settings
        self.base_url = "https://generativelanguage.googleapis.com/v1"
        self.model = "models/gemini-2.0-flash-exp"  # Default model
        self.max_retries = 3
        self.retry_delay = 2  # Initial delay in seconds
        
    def get_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: int = 8192,
                       top_p: float = 0.95,
                       timeout: int = 120) -> str:
        """
        Get a completion from Gemini API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens in the response
            top_p: Nucleus sampling parameter
            timeout: Request timeout in seconds
            
        Returns:
            The text response from Gemini
        """
        # Convert LangChain-style messages to Gemini format
        gemini_messages = []
        
        # Map from LangChain/OpenAI format to Gemini format
        role_mapping = {
            "system": "user",  # Gemini doesn't have a system role - we'll prepend to the first user message
            "user": "user",
            "assistant": "model"
        }
        
        # Handle system message if present
        system_content = None
        for i, message in enumerate(messages):
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                system_content = content
                continue
                
            # If this is the first user message and we have a system message, combine them
            if role == "user" and system_content and not any(m.get("role") == "user" for m in messages[:i]):
                content = f"{system_content}\n\n{content}"
                system_content = None
            
            gemini_role = role_mapping.get(role, "user")
            gemini_messages.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        
        # If we have a system message but no user message to combine it with, add it as a user message
        if system_content:
            gemini_messages.append({
                "role": "user",
                "parts": [{"text": system_content}]
            })
        
        # Prepare request payload
        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": top_p
            }
        }
        
        # Add API key to URL
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        # Make API request with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Extract the generated text
                if "candidates" in response_data and response_data["candidates"]:
                    text_parts = []
                    for part in response_data["candidates"][0]["content"]["parts"]:
                        if "text" in part:
                            text_parts.append(part["text"])
                    return "".join(text_parts)
                else:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"No candidates returned: {error_msg}")
                    raise ValueError(f"No candidates returned: {error_msg}")
                    
            except requests.exceptions.RequestException as e:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {str(e)}. Retrying in {wait_time}s...")
                
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {self.max_retries} attempts: {str(e)}")
                    raise
        
        # This should never be reached due to the raise in the loop
        raise RuntimeError("Failed to get a response from Gemini API")


# Simplified function to query Gemini API
def query_gemini(messages: List[Dict[str, str]], 
                temperature: float = 0.2,
                max_tokens: int = 8192) -> str:
    """
    Query the Gemini API with the given messages.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        temperature: Controls randomness (0.0 to 1.0)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        The text response from Gemini
    """
    client = GeminiClient()
    
    try:
        response = client.get_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response
    except Exception as e:
        logger.error(f"Error querying Gemini: {str(e)}")
        # Return a friendly error message that can be handled by the calling code
        return f"ERROR: Failed to query Gemini API: {str(e)}. Please check your API key and connection."


if __name__ == "__main__":
    # Example usage
    sample_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain how to analyze website traffic data in 2-3 sentences."}
    ]
    
    print("Testing Gemini client...")
    result = query_gemini(sample_messages)
    print(f"Response: {result}")