#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Anti-Ban Guard
Protect bot from getting banned
"""

import asyncio
import logging
import random
from typing import Dict, Any, Optional

from config import Config

logger = logging.getLogger(__name__)

class AntiBanGuard:
    """Anti-Ban Protection System"""
    
    def __init__(self):
        self.config = Config
        self.safety_level = "high"  # high, medium, low
        self.ban_risk = 0
        self.consecutive_actions = 0
        self.last_action_time = 0
        self.cooldown_multiplier = 1.0
        
        # Action history
        self.action_history = []
        self.max_history = 100
        
        # Risk factors
        self.risk_factors = {
            'mass_message': 10,
            'rapid_commands': 5,
            'frequent_kicks': 15,
            'spam_detection': 20,
            'user_reports': 25,
            'admin_actions': 8,
        }
    
    async def check_action_safety(self, action_type: str, 
                                chat_id: Optional[int] = None,
                                user_id: Optional[int] = None) -> Dict[str, Any]:
        """Check if an action is safe to perform"""
        try:
            current_time = asyncio.get_event_loop().time()
            
            # Calculate risk for this action
            action_risk = self.risk_factors.get(action_type, 5)
            
            # Adjust based on safety level
            if self.safety_level == "high":
                action_risk *= 1.5
            elif self.safety_level == "low":
                action_risk *= 0.5
            
            # Check consecutive actions
            time_since_last = current_time - self.last_action_time
            if time_since_last < 1.0:  # Less than 1 second
                self.consecutive_actions += 1
                action_risk *= (1 + self.consecutive_actions * 0.2)
            else:
                self.consecutive_actions = max(0, self.consecutive_actions - 1)
            
            # Update ban risk
            self.ban_risk = min(100, self.ban_risk + action_risk)
            
            # Check if action should be blocked
            should_block = False
            block_reason = ""
            
            if self.ban_risk > 80:
                should_block = True
                block_reason = "high_ban_risk"
            elif action_risk > 50:
                should_block = True
                block_reason = "high_action_risk"
            elif self.consecutive_actions > 10:
                should_block = True
                block_reason = "too_many_consecutive_actions"
            
            # Calculate delay if action is allowed
            delay = 0
            if not should_block:
                # Base delay
                delay = random.uniform(0.5, 2.0) * self.cooldown_multiplier
                
                # Add risk-based delay
                risk_delay = (self.ban_risk / 100) * 3.0
                delay += risk_delay
                
                # Humanize delay if enabled
                if self.config.HUMANIZE_DELAY:
                    delay = random.uniform(
                        max(self.config.MIN_DELAY, delay * 0.8),
                        min(self.config.MAX_DELAY, delay * 1.2)
                    )
            
            # Record action
            action_record = {
                'timestamp': current_time,
                'type': action_type,
                'risk': action_risk,
                'allowed': not should_block,
                'delay': delay,
                'chat_id': chat_id,
                'user_id': user_id,
            }
            
            self.action_history.append(action_record)
            if len(self.action_history) > self.max_history:
                self.action_history.pop(0)
            
            self.last_action_time = current_time
            
            # Gradual risk decay
            self._decay_risk()
            
            return {
                'allowed': not should_block,
                'delay': delay,
                'risk_level': self.ban_risk,
                'block_reason': block_reason if should_block else None,
                'suggested_action': 'proceed' if not should_block else 'wait',
            }
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {
                'allowed': True,  # Allow by default if check fails
                'delay': 1.0,
                'risk_level': 50,
                'block_reason': None,
                'suggested_action': 'proceed',
            }
    
    def _decay_risk(self):
        """Gradually reduce ban risk over time"""
        decay_rate = 0.1  # 10% decay
        self.ban_risk = max(0, self.ban_risk * (1 - decay_rate))
        
        # Also reduce consecutive actions counter
        if self.consecutive_actions > 0:
            self.consecutive_actions = max(0, self.consecutive_actions - 1)
    
    async def adjust_safety_level(self, level: str):
        """Adjust safety level"""
        valid_levels = ["high", "medium", "low"]
        
        if level in valid_levels:
            self.safety_level = level
            
            # Adjust cooldown multiplier based on safety level
            if level == "high":
                self.cooldown_multiplier = 1.5
            elif level == "medium":
                self.cooldown_multiplier = 1.0
            else:  # low
                self.cooldown_multiplier = 0.5
            
            logger.info(f"Safety level changed to: {level}")
            return True
        
        logger.error(f"Invalid safety level: {level}")
        return False
    
    async def report_user_action(self, user_id: int, action_type: str,
                               severity: int = 1):
        """Report user action for risk assessment"""
        # Increase risk if user is performing suspicious actions
        if severity > 5:
            self.ban_risk = min(100, self.ban_risk + severity * 2)
            logger.warning(f"High severity action from user {user_id}: {action_type}")
    
    async def report_admin_action(self, admin_id: int, action_type: str,
                                target_id: Optional[int] = None):
        """Report admin action for monitoring"""
        # Monitor admin actions for potential abuse
        risky_admin_actions = ['ban', 'kick', 'mute', 'restrict']
        
        if action_type in risky_admin_actions:
            self.ban_risk = min(100, self.ban_risk + 5)
            logger.info(f"Admin action recorded: {admin_id} performed {action_type}")
    
    async def get_safety_report(self) -> Dict[str, Any]:
        """Get safety report"""
        current_time = asyncio.get_event_loop().time()
        
        # Analyze recent actions
        recent_actions = [
            action for action in self.action_history
            if current_time - action['timestamp'] < 300  # Last 5 minutes
        ]
        
        high_risk_actions = sum(1 for action in recent_actions if action['risk'] > 30)
        blocked_actions = sum(1 for action in recent_actions if not action['allowed'])
        
        return {
            'safety_level': self.safety_level,
            'ban_risk': round(self.ban_risk, 1),
            'consecutive_actions': self.consecutive_actions,
            'cooldown_multiplier': round(self.cooldown_multiplier, 2),
            'recent_actions': len(recent_actions),
            'high_risk_actions': high_risk_actions,
            'blocked_actions': blocked_actions,
            'action_history_size': len(self.action_history),
        }
    
    async def emergency_cooldown(self, duration: int = 60):
        """Enter emergency cooldown mode"""
        logger.warning(f"Entering emergency cooldown for {duration} seconds")
        
        # Drastically increase cooldown
        old_multiplier = self.cooldown_multiplier
        self.cooldown_multiplier = 5.0
        
        # Reset after duration
        async def reset_cooldown():
            await asyncio.sleep(duration)
            self.cooldown_multiplier = old_multiplier
            logger.info("Emergency cooldown ended")
        
        asyncio.create_task(reset_cooldown())
    
    async def reset_risk(self):
        """Reset ban risk to zero"""
        self.ban_risk = 0
        self.consecutive_actions = 0
        logger.info("Ban risk reset to zero")
    
    async def simulate_human_behavior(self) -> float:
        """Simulate human-like delays and behavior"""
        if not self.config.HUMANIZE_DELAY:
            return 0.0
        
        # Random thinking time
        thinking_time = random.uniform(0.3, 1.5)
        
        # Typing simulation (for longer responses)
        typing_delay = random.uniform(0.1, 0.5)
        
        # Network latency simulation
        network_delay = random.uniform(0.05, 0.2)
        
        total_delay = thinking_time + typing_delay + network_delay
        
        # Add to current ban risk
        self.ban_risk = min(100, self.ban_risk + 0.1)
        
        return total_delay