#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Webhook Server
Production-ready webhook server with SSL support
"""

import asyncio
import logging
import ssl
from typing import Optional, Dict, Any
from pathlib import Path

from aiohttp import web
import telebot
from telebot.async_telebot import AsyncTeleBot

from config import Config
from telegram_bot import TelegramBot

logger = logging.getLogger(__name__)

class WebhookServer:
    """Production Webhook Server"""
    
    def __init__(self):
        self.config = Config
        self.telegram_bot = TelegramBot()
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Webhook settings
        self.webhook_path = '/webhook'
        self.secret_token = self.config.SECURITY.get('webhook_secret')
        
        # SSL settings
        self.ssl_cert_path = Path('ssl/cert.pem')
        self.ssl_key_path = Path('ssl/key.pem')
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        # Webhook endpoint
        self.app.router.add_post(self.webhook_path, self.handle_webhook)
        
        # Health check endpoint
        self.app.router.add_get('/health', self.handle_health)
        
        # Status endpoint
        self.app.router.add_get('/status', self.handle_status)
        
        # Admin endpoints (protected)
        self.app.router.add_get('/admin/restart', self.handle_admin_restart)
        self.app.router.add_get('/admin/backup', self.handle_admin_backup)
        
        # Static files (for dashboard)
        self.app.router.add_static('/static/', Path('static'))
    
    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook updates"""
        try:
            # Verify secret token if set
            if self.secret_token:
                token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
                if token != self.secret_token:
                    logger.warning(f"Invalid secret token: {token}")
                    return web.Response(status=403, text='Forbidden')
            
            # Parse update
            update_data = await request.json()
            update = telebot.types.Update.de_json(update_data)
            
            # Process update
            await self.telegram_bot.bot.process_new_updates([update])
            
            logger.debug(f"Webhook processed: {update.update_id}")
            return web.Response(text='OK')
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.Response(status=500, text='Internal Server Error')
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        health_status = {
            'status': 'healthy',
            'timestamp': asyncio.get_event_loop().time(),
            'service': 'blue_rose_bot',
            'version': self.config.BOT_VERSION,
        }
        
        return web.json_response(health_status)
    
    async def handle_status(self, request: web.Request) -> web.Response:
        """Status endpoint with bot information"""
        try:
            # Get bot info
            bot_info = await self.telegram_bot.bot.get_me()
            
            # Get system status
            import psutil
            import datetime
            
            status = {
                'bot': {
                    'id': bot_info.id,
                    'username': bot_info.username,
                    'first_name': bot_info.first_name,
                    'is_active': True,
                },
                'system': {
                    'uptime': datetime.datetime.now().isoformat(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                },
                'webhook': {
                    'url': self.config.SECURITY.get('webhook_url'),
                    'is_active': True,
                    'path': self.webhook_path,
                },
                'timestamp': datetime.datetime.now().isoformat(),
            }
            
            return web.json_response(status)
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_admin_restart(self, request: web.Request) -> web.Response:
        """Admin endpoint to restart bot (protected)"""
        # Verify admin key
        admin_key = request.query.get('key')
        if admin_key != self.config.SECURITY.get('admin_key'):
            return web.Response(status=403, text='Forbidden')
        
        # Restart logic
        logger.info("Admin requested restart via webhook")
        
        response = {
            'status': 'restarting',
            'message': 'Bot restart initiated',
            'timestamp': asyncio.get_event_loop().time(),
        }
        
        # Schedule restart
        asyncio.create_task(self._schedule_restart())
        
        return web.json_response(response)
    
    async def handle_admin_backup(self, request: web.Request) -> web.Response:
        """Admin endpoint to create backup"""
        # Verify admin key
        admin_key = request.query.get('key')
        if admin_key != self.config.SECURITY.get('admin_key'):
            return web.Response(status=403, text='Forbidden')
        
        try:
            from storage.backup import BackupManager
            backup_manager = BackupManager()
            
            backup_file = await backup_manager.create_backup(
                backup_type="admin_request",
                description="Admin requested via webhook"
            )
            
            response = {
                'status': 'backup_created',
                'backup_file': str(backup_file) if backup_file else None,
                'timestamp': asyncio.get_event_loop().time(),
            }
            
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _schedule_restart(self, delay: int = 5):
        """Schedule bot restart"""
        logger.info(f"Scheduling restart in {delay} seconds...")
        await asyncio.sleep(delay)
        
        # In production, this would use systemd or supervisor to restart
        logger.info("Restart signal sent")
    
    def setup_ssl(self) -> Optional[ssl.SSLContext]:
        """Setup SSL context"""
        if self.ssl_cert_path.exists() and self.ssl_key_path.exists():
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(
                str(self.ssl_cert_path),
                str(self.ssl_key_path)
            )
            logger.info("SSL certificate loaded")
            return ssl_context
        else:
            logger.warning("SSL certificates not found, running without SSL")
            return None
    
    async def start(self, host: str = '0.0.0.0', port: int = 8443):
        """Start webhook server"""
        try:
            # Setup SSL if available
            ssl_context = self.setup_ssl()
            
            # Set webhook
            webhook_url = f"https://{self.config.SECURITY.get('webhook_domain')}:{port}{self.webhook_path}"
            
            await self.telegram_bot.set_webhook(
                webhook_url=webhook_url,
                secret_token=self.secret_token
            )
            
            # Create runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Start site
            self.site = web.TCPSite(
                self.runner,
                host=host,
                port=port,
                ssl_context=ssl_context
            )
            
            await self.site.start()
            
            logger.info(f"Webhook server started on {host}:{port}")
            logger.info(f"Webhook URL: {webhook_url}")
            
            # Keep server running
            await self._keep_alive()
            
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            raise
    
    async def _keep_alive(self):
        """Keep server alive"""
        try:
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except asyncio.CancelledError:
            pass
    
    async def stop(self):
        """Stop webhook server"""
        try:
            # Remove webhook
            await self.telegram_bot.remove_webhook()
            
            # Stop server
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            logger.info("Webhook server stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop webhook server: {e}")

async def main():
    """Main function for webhook server"""
    server = WebhookServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server...")
    finally:
        await server.stop()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run server
    asyncio.run(main())