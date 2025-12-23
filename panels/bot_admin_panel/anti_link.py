#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Anti Link
Control link sharing in groups
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AntiLink:
    """Anti-Link Protection System"""
    
    def __init__(self):
        self.allowed_domains = [
            'telegram.org', 'github.com', 'wikipedia.org',
            'youtube.com', 'google.com', 'stackoverflow.com',
        ]
        self.url_pattern = r'https?://\S+|www\.\S+'
    
    async def check_links(self, message: Dict[str, Any], 
                         group_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Check for links in message"""
        text = message.get('text', '')
        if not text:
            return {'has_links': False}
        
        # Find all URLs
        urls = re.findall(self.url_pattern, text)
        
        if not urls:
            return {'has_links': False}
        
        # Check against allowed domains
        blocked_urls = []
        for url in urls:
            if not any(domain in url for domain in self.allowed_domains):
                blocked_urls.append(url)
        
        return {
            'has_links': True,
            'total_urls': len(urls),
            'blocked_urls': blocked_urls,
            'allowed_urls': [url for url in urls if url not in blocked_urls],
        }