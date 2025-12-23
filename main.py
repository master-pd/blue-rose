#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Main Entry Point
Telegram Bot with Advanced Features
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from config import Config
from core.boot import BootManager
from core.kernel import Kernel
from core.event_loop import EventLoop
from core.shutdown import ShutdownManager
from failsafe.crash_handler import CrashHandler
from telegram_bot import TelegramBot
from analytics.system_health import SystemHealthMonitor
from payments.expiry_alert import ExpiryAlert
from intelligence.memory_decay import MemoryDecay

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOGGING['level']),
    format=Config.LOGGING['format'],
    handlers=[
        logging.FileHandler(Config.LOGGING['file'], encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BlueRoseBot:
    """Main Bot Class"""
    
    def __init__(self):
        self.config = Config
        self.boot_manager = BootManager()
        self.kernel = Kernel()
        self.event_loop = EventLoop()
        self.shutdown_manager = ShutdownManager()
        self.crash_handler = CrashHandler()
        self.telegram_bot = TelegramBot()
        self.system_monitor = SystemHealthMonitor()
        self.expiry_alert = ExpiryAlert()
        self.memory_decay = MemoryDecay()
        
        self.is_running = False
        self.start_time = None
        
        # Register crash handler
        self.crash_handler.register_bot(self)
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🚀 Starting Blue Rose Bot Initialization...")
            
            # Validate configuration
            issues = self.config.validate_config()
            if issues:
                logger.error("Configuration issues found:")
                for issue in issues:
                    logger.error(f"  - {issue}")
                return False
            
            # Boot sequence
            if not await self.boot_manager.boot():
                logger.error("Boot sequence failed!")
                return False
            
            # Initialize kernel
            if not await self.kernel.initialize():
                logger.error("Kernel initialization failed!")
                return False
            
            # Initialize event loop
            if not await self.event_loop.initialize():
                logger.error("Event loop initialization failed!")
                return False
            
            # Initialize system monitor
            await self.system_monitor.start()
            
            # Schedule background tasks
            await self._schedule_background_tasks()
            
            logger.info("✅ Initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            await self.crash_handler.handle_crash(e)
            return False
    
    async def _schedule_background_tasks(self):
        """Schedule background maintenance tasks"""
        # Schedule expiry checks
        await self.expiry_alert.schedule_expiry_checks(interval_hours=6)
        
        # Schedule memory decay
        await self.memory_decay.schedule_regular_decay(interval_hours=24)
        
        # Schedule system health monitoring
        await self.system_monitor.schedule_health_checks(interval_minutes=5)
        
        logger.info("✅ Background tasks scheduled")
    
    async def start(self):
        """Start the bot"""
        if self.is_running:
            logger.warning("Bot is already running!")
            return
        
        try:
            # Initialize
            if not await self.initialize():
                logger.error("Failed to initialize bot!")
                return
            
            self.is_running = True
            self.start_time = asyncio.get_event_loop().time()
            
            # Start kernel
            await self.kernel.start()
            
            # Start event loop
            await self.event_loop.start()
            
            logger.info("🤖 Blue Rose Bot is now running!")
            logger.info(f"📝 Bot Name: {self.config.BOT_NAME}")
            logger.info(f"👤 Developer: {self.config.DEVELOPER}")
            logger.info(f"🌐 Timezone: {self.config.TIMEZONE}")
            
            # Start Telegram bot
            await self._start_telegram_bot()
            
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal...")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
            await self.crash_handler.handle_crash(e)
        finally:
            await self.shutdown()
    
    async def _start_telegram_bot(self):
        """Start Telegram bot with polling"""
        try:
            logger.info("🤖 Starting Telegram bot polling...")
            
            # Start polling
            await self.telegram_bot.start_polling()
            
        except Exception as e:
            logger.error(f"Telegram bot failed: {e}")
            raise
    
    async def start_webhook(self, webhook_url: str, secret_token: Optional[str] = None):
        """Start bot with webhook"""
        if self.is_running:
            logger.warning("Bot is already running!")
            return
        
        try:
            # Initialize
            if not await self.initialize():
                logger.error("Failed to initialize bot!")
                return
            
            self.is_running = True
            self.start_time = asyncio.get_event_loop().time()
            
            # Start kernel
            await self.kernel.start()
            
            # Start event loop
            await self.event_loop.start()
            
            logger.info("🤖 Blue Rose Bot is now running with webhook!")
            
            # Set webhook
            await self.telegram_bot.set_webhook(webhook_url, secret_token)
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal...")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
            await self.crash_handler.handle_crash(e)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        if not self.is_running:
            return
        
        logger.info("🔴 Shutting down Blue Rose Bot...")
        self.is_running = False
        
        try:
            # Stop system monitor
            await self.system_monitor.stop()
            
            # Stop Telegram bot
            await self.telegram_bot.close()
            
            # Stop event loop
            await self.event_loop.stop()
            
            # Stop kernel
            await self.kernel.stop()
            
            # Shutdown boot manager
            await self.boot_manager.shutdown()
            
            # Execute graceful shutdown
            await self.shutdown_manager.graceful_shutdown()
            
            logger.info("✅ Blue Rose Bot shutdown complete!")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def run(self):
        """Run the bot (blocking)"""
        try:
            # Run async main function
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("👋 Goodbye!")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
    
    def run_webhook(self, webhook_url: str, secret_token: Optional[str] = None):
        """Run bot with webhook (blocking)"""
        try:
            asyncio.run(self.start_webhook(webhook_url, secret_token))
        except KeyboardInterrupt:
            logger.info("👋 Goodbye!")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)

def main():
    """Entry point"""
    print("""
    ╔═══════════════════════════════════════╗
    ║        🌹 BLUE ROSE BOT 🌹           ║
    ║      Advanced Telegram Bot System     ║
    ║        Version: 1.0.0                 ║
    ║      Developed by: RANA (MASTER)      ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Blue Rose Telegram Bot')
    parser.add_argument('--webhook', help='Webhook URL')
    parser.add_argument('--secret', help='Webhook secret token')
    parser.add_argument('--polling', action='store_true', help='Use polling (default)')
    
    args = parser.parse_args()
    
    # Create bot instance
    bot = BlueRoseBot()
    
    # Run based on arguments
    if args.webhook:
        print(f"🌐 Starting with webhook: {args.webhook}")
        bot.run_webhook(args.webhook, args.secret)
    else:
        print("🔄 Starting with polling...")
        bot.run()

if __name__ == "__main__":
    main()
