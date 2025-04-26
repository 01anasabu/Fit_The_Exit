"""
Mistral API client functionality for the Website Analyzer application.
"""

import os
import time
import threading
from typing import List, Dict, Any

from mistralai import Mistral
from config import MISTRAL_MODEL

class RateLimiter:
    def __init__(self, max_calls_per_minute=10, tokens_per_minute=20000):
        self.max_calls_per_minute = max_calls_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.call_timestamps = []
        self.token_usage = []  # Track token usage with timestamps
        self.lock = threading.Lock()
        
    def wait_if_needed(self, estimated_tokens=1000):
        """
        Wait if we're exceeding the rate limit.
        
        Args:
            estimated_tokens: Estimated number of tokens in this request (prompt + completion)
        """
        with self.lock:
            now = time.time()
            
            # Clean up old timestamps and token usage (older than 1 minute)
            self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 60]
            self.token_usage = [(ts, tokens) for ts, tokens in self.token_usage if now - ts < 60]
            
            # Check request rate limit
            if len(self.call_timestamps) >= self.max_calls_per_minute:
                oldest_timestamp = min(self.call_timestamps)
                wait_time = 60 - (now - oldest_timestamp) + 1  # Add 1 second buffer
                
                print(f"Request rate limit approaching. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                
                # Update time and clean lists again after waiting
                now = time.time()
                self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 60]
                self.token_usage = [(ts, tokens) for ts, tokens in self.token_usage if now - ts < 60]
            
            # Check token rate limit
            total_tokens = sum(tokens for _, tokens in self.token_usage) + estimated_tokens
            if total_tokens > self.tokens_per_minute:
                # Calculate wait time needed based on token usage
                wait_time = 60  # Wait a full minute to reset token quota
                
                print(f"Token rate limit approaching. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                
                # Update time and clean lists again after waiting
                now = time.time()
                self.call_timestamps = []  # Reset after waiting
                self.token_usage = []  # Reset after waiting
            
            # Record this call
            self.call_timestamps.append(now)
            self.token_usage.append((now, estimated_tokens))

# Create a global rate limiter instance with free tier limits
# Mistral's free tier typically allows ~10 requests/minute and ~20K tokens/minute
rate_limiter = RateLimiter(max_calls_per_minute=10, tokens_per_minute=20000)

def get_mistral_client():
    """Initialize and return a Mistral API client."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")
    return Mistral(api_key=api_key)

def query_mistral(messages: List[Dict[str, str]], model: str = MISTRAL_MODEL):
    """
    Query the Mistral API with the given messages.
    
    Args:
        messages: List of message objects with 'role' and 'content'
        model: Mistral model name to use
        
    Returns:
        The content of the response message
    """
    client = get_mistral_client()
    
    # Estimate token count (rough estimate)
    estimated_tokens = 0
    for msg in messages:
        # Roughly 4 chars per token for English text
        estimated_tokens += len(msg.get('content', '')) // 4
    
    # Add expected completion tokens (conservative estimate)
    estimated_tokens += 1000
    
    # Wait if needed before making API call
    rate_limiter.wait_if_needed(estimated_tokens=estimated_tokens)
    
    print(f"🤖 Querying Mistral API... (est. {estimated_tokens} tokens)")
    try:
        response = client.chat.complete(
            model=model,
            messages=messages,
        )
        print("✅ Response received")
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
        # Re-raise the exception after logging
        raise