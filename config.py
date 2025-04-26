"""
Configuration settings for the Website Analyzer application.
"""

# Mistral API settings
MISTRAL_MODEL = "mistral-large-latest"

# UI settings
TERMINAL_WIDTH = 60

# Data processing settings
SAMPLE_SIZE = 2  # Number of rows to use for column recommendations
DEFAULT_CHUNK_SIZE = 50  # Default number of sessions to process at once

# Application settings
DEFAULT_REPORT_FORMAT = "markdown"