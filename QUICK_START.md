# Blue Rose Bot - Quick Start Guide

## 1. Installation

### Option A: Automatic Installation
```bash
# Clone or download the project
git clone <repository-url>
cd blue_rose

# Run installation script
python install.py
```
```
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/{bot,groups,users,payments,messages,schedules} logs backups

# Edit configuration
cp config.example.py config.py
# Edit config.py with your bot token and ID

```

# update repo 
```
git pull origin main
pip install -r requirements.txt --upgrade

```


## **সারসংক্ষেপ:**

এখন আপনার কাছে সম্পূর্ণ **Blue Rose Telegram Bot** সিস্টেম আছে:

### **কি কি করা হয়েছে:**
1. ✅ **Telegram Bot API Integration** - সম্পূর্ণ integration with polling/webhook
2. ✅ **SQLite Database** - Relational data storage
3. ✅ **Updated Main Application** - Improved with better error handling
4. ✅ **Installation Script** - Easy setup
5. ✅ **Quick Start Guide** - Step-by-step instructions
6. ✅ **All Core Modules** - Intelligence, Moderation, Payments, etc.

### **বাকি যা করতে হবে:**
1. **Webhook Server** - যদি production-এ webhook use করতে চান
2. **Docker Configuration** - Containerization
3. **Testing Suite** - Unit and integration tests
4. **Monitoring Dashboard** - Web-based admin panel
5. **Additional Features** - আপনার requirements অনুযায়ী

### **কিভাবে শুরু করবেন:**
```bash
# 1. Installation
python install.py

# 2. Edit config.py with your bot token
# 3. Run the bot
python main.py