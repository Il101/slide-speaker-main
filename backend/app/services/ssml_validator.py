"""
SSML Validator - validates SSML before sending to Google TTS
"""
import xml.etree.ElementTree as ET
import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


def validate_ssml(ssml_text: str) -> Tuple[bool, List[str]]:
    """
    Validate SSML before sending to Google TTS
    
    Args:
        ssml_text: SSML text to validate
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # 1. Basic XML validation
    try:
        # Remove <?xml?> declaration if present
        if ssml_text.startswith('<?xml'):
            ssml_text = ssml_text.split('?>', 1)[1]
        
        root = ET.fromstring(ssml_text)
        
        # 2. Check root element
        if root.tag != 'speak':
            errors.append("Root element must be <speak>")
        
    except ET.ParseError as e:
        errors.append(f"Invalid XML: {e}")
        return False, errors
    
    # 3. Check for allowed tags
    allowed_tags = {
        'speak', 'prosody', 'emphasis', 'break', 'mark',
        'sub', 'lang', 'phoneme', 'say-as', 'voice', 'audio'
    }
    
    def check_tags(element):
        if element.tag not in allowed_tags:
            errors.append(f"Unknown tag: <{element.tag}>")
        
        # Check attributes for specific tags
        if element.tag == 'mark':
            if 'name' not in element.attrib:
                errors.append("<mark> must have 'name' attribute")
            else:
                # Validate marker name
                name = element.attrib['name']
                if len(name) > 64:
                    errors.append(f"<mark> name too long: {name[:20]}... (max 64 chars)")
                if not re.match(r'^[a-zA-Z0-9_-]+$', name):
                    errors.append(f"<mark> name contains invalid chars: {name}")
        
        elif element.tag == 'break':
            if 'time' in element.attrib:
                time_val = element.attrib['time']
                # Validate time format: XXXms or XXXs
                if not re.match(r'^\d+(?:ms|s)$', time_val):
                    errors.append(f"<break> time invalid format: {time_val}")
        
        elif element.tag == 'prosody':
            # Check prosody attributes
            if 'rate' in element.attrib:
                rate = element.attrib['rate']
                # Should be like "medium", "fast", "slow" or "X%"
                valid_rates = ['x-slow', 'slow', 'medium', 'fast', 'x-fast']
                if rate not in valid_rates and not re.match(r'^\d+%$', rate):
                    errors.append(f"<prosody> rate invalid: {rate}")
        
        # Recursively check children
        for child in element:
            check_tags(child)
    
    check_tags(root)
    
    # 4. Check SSML size
    if len(ssml_text) > 5000:
        errors.append(f"SSML too long: {len(ssml_text)} chars (max 5000)")
    
    # 5. Check number of marks
    mark_count = ssml_text.count('<mark')
    if mark_count > 200:
        errors.append(f"Too many <mark> tags: {mark_count} (recommended max: 200)")
    
    # 6. Check for unescaped special characters in text
    # Find text content between tags
    text_pattern = r'>([^<]+)<'
    for match in re.finditer(text_pattern, ssml_text):
        text_content = match.group(1)
        # Check for unescaped & (should be &amp;)
        if '&' in text_content and not re.search(r'&(?:amp|lt|gt|quot|apos);', text_content):
            errors.append(f"Unescaped '&' character found in text: '{text_content[:30]}...'")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def fix_common_ssml_issues(ssml_text: str) -> str:
    """
    Automatically fix common SSML issues
    
    Args:
        ssml_text: SSML text with potential issues
        
    Returns:
        Fixed SSML text
    """
    # 1. Fix self-closing <mark> tags
    # <mark name="x"> should be <mark name="x"/>
    ssml_text = re.sub(r'<mark\s+name="([^"]+)"\s*>', r'<mark name="\1"/>', ssml_text)
    
    # 2. Escape unescaped ampersands in text
    # This is tricky because we don't want to double-escape
    def escape_ampersand(text):
        # Only escape & that are not already part of an entity
        return re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', text)
    
    # Find text content and escape
    parts = []
    last_end = 0
    for match in re.finditer(r'>([^<]+)<', ssml_text):
        parts.append(ssml_text[last_end:match.start(1)])
        parts.append(escape_ampersand(match.group(1)))
        last_end = match.end(1)
    parts.append(ssml_text[last_end:])
    ssml_text = ''.join(parts)
    
    # 3. Remove empty prosody tags
    ssml_text = re.sub(r'<prosody[^>]*>\s*</prosody>', '', ssml_text)
    ssml_text = re.sub(r'<emphasis[^>]*>\s*</emphasis>', '', ssml_text)
    
    # 4. Remove double spaces
    ssml_text = re.sub(r'\s+', ' ', ssml_text)
    
    # 5. Ensure proper nesting (basic check)
    # Remove nested empty tags
    ssml_text = re.sub(r'<([a-z]+)[^>]*>\s*</\1>', '', ssml_text)
    
    return ssml_text


def sanitize_marker_name(name: str) -> str:
    """
    Sanitize marker name for SSML
    
    Args:
        name: Original marker name
        
    Returns:
        Sanitized marker name (only alphanumeric, underscore, hyphen)
    """
    # Replace invalid characters with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Limit length
    return sanitized[:64]
