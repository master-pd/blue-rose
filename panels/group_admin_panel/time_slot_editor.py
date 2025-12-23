#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Time Slot Editor
Group admin time slot management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class TimeSlotEditor:
    """Time Slot Editor for Group Admin"""
    
    def __init__(self):
        self.config = Config
        
    async def get_time_slots(self, group_id: int) -> Dict[str, Any]:
        """Get time slots for a group"""
        try:
            slots_path = self.config.DATA_DIR / "schedules" / "slots.json"
            slots_data = JSONEngine.load_json(slots_path, {})
            
            group_key = str(group_id)
            
            # Get group-specific slots if exists
            group_slots = slots_data.get('group_slots', {}).get(group_key, {})
            
            if group_slots:
                return group_slots
            
            # Return default slots
            return slots_data.get('default_slots', {})
        
        except Exception as e:
            logger.error(f"Failed to get time slots: {e}")
            return {}
    
    async def update_time_slot(self, group_id: int, 
                             slot_name: str,
                             time_str: str,
                             message: str,
                             enabled: bool,
                             admin_id: int) -> bool:
        """Update a time slot"""
        try:
            # Validate time format
            if not self._validate_time(time_str):
                return False
            
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            slots_path = self.config.DATA_DIR / "schedules" / "slots.json"
            slots_data = JSONEngine.load_json(slots_path, {})
            
            group_key = str(group_id)
            
            # Initialize structures if not exists
            if 'group_slots' not in slots_data:
                slots_data['group_slots'] = {}
            
            if group_key not in slots_data['group_slots']:
                slots_data['group_slots'][group_key] = {}
            
            # Update slot
            slots_data['group_slots'][group_key][slot_name] = {
                'time': time_str,
                'message': message,
                'enabled': enabled,
                'updated_by': admin_id,
                'updated_at': self._get_timestamp()
            }
            
            # Save changes
            JSONEngine.save_json(slots_path, slots_data)
            
            logger.info(
                f"Time slot {slot_name} updated "
                f"for group {group_id} by admin {admin_id}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update time slot: {e}")
            return False
    
    async def add_custom_slot(self, group_id: int,
                            slot_name: str,
                            time_str: str,
                            message: str,
                            enabled: bool,
                            admin_id: int) -> bool:
        """Add a custom time slot"""
        try:
            # Validate time format
            if not self._validate_time(time_str):
                return False
            
            # Check if slot name already exists
            existing_slots = await self.get_time_slots(group_id)
            if slot_name in existing_slots:
                logger.error(f"Slot {slot_name} already exists")
                return False
            
            return await self.update_time_slot(
                group_id, slot_name, time_str, message, enabled, admin_id
            )
        
        except Exception as e:
            logger.error(f"Failed to add custom slot: {e}")
            return False
    
    async def delete_slot(self, group_id: int, 
                         slot_name: str,
                         admin_id: int) -> bool:
        """Delete a time slot"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            slots_path = self.config.DATA_DIR / "schedules" / "slots.json"
            slots_data = JSONEngine.load_json(slots_path, {})
            
            group_key = str(group_id)
            
            # Check if slot exists in group slots
            if (group_key in slots_data.get('group_slots', {}) and 
                slot_name in slots_data['group_slots'][group_key]):
                
                # Delete slot
                del slots_data['group_slots'][group_key][slot_name]
                
                # If no slots left, remove group entry
                if not slots_data['group_slots'][group_key]:
                    del slots_data['group_slots'][group_key]
                
                # Save changes
                JSONEngine.save_json(slots_path, slots_data)
                
                logger.info(
                    f"Time slot {slot_name} deleted "
                    f"for group {group_id} by admin {admin_id}"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete slot: {e}")
            return False
    
    async def toggle_slot(self, group_id: int,
                         slot_name: str,
                         enabled: bool,
                         admin_id: int) -> bool:
        """Toggle a time slot"""
        try:
            slots = await self.get_time_slots(group_id)
            
            if slot_name not in slots:
                logger.error(f"Slot {slot_name} not found")
                return False
            
            slot_data = slots[slot_name]
            
            return await self.update_time_slot(
                group_id,
                slot_name,
                slot_data.get('time', '00:00'),
                slot_data.get('message', ''),
                enabled,
                admin_id
            )
        
        except Exception as e:
            logger.error(f"Failed to toggle slot: {e}")
            return False
    
    def _validate_time(self, time_str: str) -> bool:
        """Validate time string format (HH:MM)"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    async def _validate_group_admin(self, group_id: int, user_id: int) -> bool:
        """Validate group admin permissions"""
        try:
            # Bot owner and admins can always edit
            if (user_id == self.config.BOT_OWNER_ID or 
                user_id in self.config.BOT_ADMIN_IDS):
                return True
            
            # Check group admins
            group_admins_path = self.config.DATA_DIR / "groups" / "group_admins.json"
            group_admins = JSONEngine.load_json(group_admins_path, {})
            
            group_key = str(group_id)
            admins = group_admins.get('groups', {}).get(group_key, {}).get('admins', [])
            
            return user_id in admins
        
        except Exception as e:
            logger.error(f"Failed to validate group admin: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    async def get_next_scheduled_time(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get next scheduled message time"""
        try:
            slots = await self.get_time_slots(group_id)
            now = datetime.now()
            
            next_slot = None
            min_difference = float('inf')
            
            for slot_name, slot_data in slots.items():
                if not slot_data.get('enabled', False):
                    continue
                
                slot_time_str = slot_data.get('time', '00:00')
                slot_time = datetime.strptime(slot_time_str, '%H:%M').time()
                
                # Create datetime for today with slot time
                slot_datetime = datetime.combine(now.date(), slot_time)
                
                # If slot time has passed today, schedule for tomorrow
                if slot_datetime < now:
                    slot_datetime = datetime.combine(
                        now.date(), slot_time
                    )  # This needs to be fixed to add a day
                    # Let me fix this:
                    from datetime import timedelta
                    slot_datetime = slot_datetime + timedelta(days=1)
                
                difference = (slot_datetime - now).total_seconds()
                
                if difference < min_difference:
                    min_difference = difference
                    next_slot = {
                        'name': slot_name,
                        'time': slot_datetime,
                        'message': slot_data.get('message', ''),
                        'time_remaining': int(difference)
                    }
            
            return next_slot
        
        except Exception as e:
            logger.error(f"Failed to get next scheduled time: {e}")
            return None
    
    async def create_schedule_report(self, group_id: int) -> str:
        """Create schedule report for group"""
        try:
            slots = await self.get_time_slots(group_id)
            next_slot = await self.get_next_scheduled_time(group_id)
            
            if not slots:
                return "No time slots configured for this group."
            
            report_lines = ["⏰ **Time Slot Schedule Report**\n"]
            report_lines.append(f"**Group ID:** `{group_id}`\n")
            
            enabled_count = 0
            for slot_name, slot_data in slots.items():
                status = "✅" if slot_data.get('enabled', False) else "❌"
                time = slot_data.get('time', '00:00')
                message = slot_data.get('message', '')[:50] + "..." if len(slot_data.get('message', '')) > 50 else slot_data.get('message', '')
                
                report_lines.append(
                    f"{status} **{slot_name}** - {time}\n"
                    f"   {message}\n"
                )
                
                if slot_data.get('enabled', False):
                    enabled_count += 1
            
            report_lines.append(f"\n**Total Slots:** {len(slots)} ({enabled_count} enabled)")
            
            if next_slot:
                hours = next_slot['time_remaining'] // 3600
                minutes = (next_slot['time_remaining'] % 3600) // 60
                report_lines.append(
                    f"\n**Next Scheduled Message:**\n"
                    f"• **Time:** {next_slot['time'].strftime('%H:%M')}\n"
                    f"• **Slot:** {next_slot['name']}\n"
                    f"• **In:** {hours}h {minutes}m"
                )
            
            return "\n".join(report_lines)
        
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return f"Error generating report: {e}"