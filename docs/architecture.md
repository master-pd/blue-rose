# Blue Rose Bot - Architecture Documentation

## Overview
Blue Rose Bot is an advanced Telegram bot with modular architecture, designed for scalability and maintainability.

## System Architecture

### Core Components
1. **Kernel System** - Central brain of the bot
2. **Permission Engine** - Hierarchical role-based permissions
3. **Feature Switch** - Feature flag management
4. **Rate Limiter** - Anti-abuse protection
5. **Anti-Ban Guard** - Telegram ToS compliance

### Storage System
- **JSON Engine** - Atomic JSON file operations
- **File Lock** - Thread-safe file locking
- **Backup Manager** - Automatic backups
- **Restore Manager** - Data recovery

### Intelligence System
1. **Message Collector** - Message analysis
2. **Question Detector** - Question identification
3. **Keyword Extractor** - Topic extraction
4. **Similarity Engine** - Text comparison
5. **Confidence Engine** - Response scoring
6. **Memory Builder** - Conversation memory
7. **Memory Decay** - Gradual forgetting

### Moderation System
- Anti-Spam, Anti-Flood, Anti-Link, Anti-Forward
- Auto-Warn, Auto-Mute, Auto-Ban
- Bot detection and management

### Payment System
- Plan management
- Payment requests
- Approval workflow
- Service unlocking
- Expiry alerts

## Data Structure

### JSON Files

```json
data/
├── bot/ # Bot configuration
├── groups/ # Group data
├── users/ # User data
├── payments/ # Payment data
├── messages/ # Message templates
└── schedules/ # Scheduling data

```


### Database
- SQLite for relational data
- JSON files for configuration
- In-memory caching for performance

## Security Features
- Rate limiting per user/group
- Permission-based access control
- Anti-ban protection
- Data encryption
- Backup and recovery

## Deployment
- Cross-platform (Termux, VPS, Windows, Linux)
- Docker support
- Python 3.12+
- No external API dependencies