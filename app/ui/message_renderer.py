"""
Module for enhanced rendering of chat messages in the UI.
Provides preprocessing and formatting for better display of markdown elements.
"""
import re
from nicegui import ui
from typing import Optional

def render_message(content: str, container=None) -> None:
    """
    Render a message with enhanced markdown and styling.
    
    Args:
        content: The message content to render
        container: Optional UI container to render into (if None, renders in current context)
    """
    # Pre-process the content
    enhanced_content = preprocess_markdown(content)
    
    # Use container if provided, otherwise render in current context
    if container:
        with container:
            ui.markdown(enhanced_content)
    else:
        ui.markdown(enhanced_content)

def preprocess_markdown(content: str) -> str:
    """
    Pre-process markdown to fix common rendering issues.
    Ensures lists, code blocks, and other elements render properly.
    
    Args:
        content: Raw markdown content
    
    Returns:
        Enhanced markdown content
    """
    # Fix starting lists that don't have proper newline before them
    content = fix_list_beginnings(content)
    
    # Fix numbered lists that don't have proper spacing
    content = fix_ordered_lists(content)
    
    # Fix unordered lists with improper spacing
    content = fix_unordered_lists(content)
    
    # Fix code blocks that might be malformed
    content = fix_code_blocks(content)
    
    # Fix headings without proper spacing
    content = fix_headings(content)
    
    return content

def fix_list_beginnings(content: str) -> str:
    """
    Specifically fix lists at the beginning of content or immediately after other elements.
    This ensures the first list element is properly formatted.
    """
    # Ensure any content starting with a list has proper newlines
    if re.match(r'^\s*(\d+\.\s|\*\s|\-\s|\+\s)', content):
        content = '\n\n' + content
    
    # Find any list that starts immediately after text without newline
    # Match pattern: text followed by newline, then immediately a list item without blank line
    patterns = [
        # For numbered lists (e.g., "Some text\n1. List item")
        (r'([^\n])\n(\d+\.\s)', r'\1\n\n\2'),
        
        # For bullet lists with *, -, + (e.g., "Some text\n* List item")
        (r'([^\n])\n([\*\-\+]\s)', r'\1\n\n\2')
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_ordered_lists(content: str) -> str:
    """Fix ordered lists that don't have proper spacing between number and content."""
    # Match numbered lists: digits followed by period with no or insufficient spacing
    pattern = r'(\n|^)(\d+)\.\s*([^\n])'
    replacement = r'\1\2. \3'
    
    # Apply multiple passes to catch nested lists
    result = content
    for _ in range(2):
        result = re.sub(pattern, replacement, result)
    
    # Ensure blank line before list starts for proper rendering
    list_start_pattern = r'(\n[^\n]+\n)(\d+\.\s)'
    result = re.sub(list_start_pattern, r'\1\n\2', result)
    
    # Fix continuations of numbered lists that might be broken
    broken_list_pattern = r'(\d+\.\s.*\n)([^\s\n\d\*\-\+])'
    result = re.sub(broken_list_pattern, r'\1\n\2', result)
    
    return result

def fix_unordered_lists(content: str) -> str:
    """Fix unordered lists that don't have proper spacing."""
    # Ensure proper spacing after bullet points (* - +)
    pattern = r'(\n|^)([\*\-\+])\s*([^\n\s])'
    replacement = r'\1\2 \3'
    
    # Apply multiple passes
    result = content
    for _ in range(2):
        result = re.sub(pattern, replacement, result)
    
    # Ensure blank line before list starts
    list_start_pattern = r'(\n[^\n]+\n)([\*\-\+]\s)'
    result = re.sub(list_start_pattern, r'\1\n\2', result)
    
    # Fix continuations of bullet lists that might be broken
    broken_list_pattern = r'([\*\-\+]\s.*\n)([^\s\n\d\*\-\+])'
    result = re.sub(broken_list_pattern, r'\1\n\2', result)
    
    return result

def fix_code_blocks(content: str) -> str:
    """Ensure code blocks have proper formatting and fencing."""
    # Ensure backtick code blocks have newlines before and after
    pattern = r'([^\n])```'
    replacement = r'\1\n```'
    result = re.sub(pattern, replacement, content)
    
    pattern = r'```([^\n])'
    replacement = r'```\n\1'
    result = re.sub(pattern, replacement, result)
    
    # Ensure inline code has proper spacing
    inline_pattern = r'([^\s`])`([^`]+)`([^\s`])'
    inline_replacement = r'\1 `\2` \3'
    result = re.sub(inline_pattern, inline_replacement, result)
    
    return result

def fix_headings(content: str) -> str:
    """Ensure markdown headings have proper spacing."""
    # Fix headings without space after #
    for i in range(6, 0, -1):  # Start with h6 to avoid double replacements
        hashes = '#' * i
        pattern = r'(\n|^)(' + hashes + r')([^\s#])'
        replacement = r'\1\2 \3'
        content = re.sub(pattern, replacement, content)
    
    # Ensure blank line before headings
    heading_pattern = r'(\n[^\n]+\n)(#{1,6}\s)'
    content = re.sub(heading_pattern, r'\1\n\2', content)
    
    return content
