from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection details
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'nice_chat_ai')

# Collections
CONVERSATIONS_COLLECTION = 'conversations'
CONFIG_COLLECTION = 'config'

# Global client and db variables
client = None
db = None

def connect_to_db():
    """Connect to MongoDB and return the database instance"""
    global client, db
    try:
        client = MongoClient(MONGO_URI)
        # Test connection
        client.admin.command('ping')
        db = client[DB_NAME]
        logger.info(f"Connected to MongoDB: {DB_NAME}")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

def get_db():
    """Get the database instance, connecting if necessary"""
    global db
    if db is None:
        db = connect_to_db()
    return db

def save_conversation(conversation_id, conversation_data):
    """Save conversation to MongoDB"""
    try:
        db = get_db()
        if db is None:
            logger.error("No database connection")
            return False
        
        # Use conversation_id as the key
        db[CONVERSATIONS_COLLECTION].update_one(
            {'_id': conversation_id},
            {'$set': conversation_data},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save conversation to MongoDB: {e}")
        return False

def get_all_conversations():
    """Get all conversations from MongoDB"""
    try:
        db = get_db()
        if db is None:
            logger.error("No database connection")
            return {}
        
        conversations = {}
        for doc in db[CONVERSATIONS_COLLECTION].find():
            conversation_id = doc.pop('_id')
            conversations[conversation_id] = doc
        return conversations
    except Exception as e:
        logger.error(f"Failed to get conversations from MongoDB: {e}")
        return {}

def delete_conversation(conversation_id):
    """Delete a conversation from MongoDB"""
    try:
        db = get_db()
        if db is None:
            logger.error("No database connection")
            return False
        
        db[CONVERSATIONS_COLLECTION].delete_one({'_id': conversation_id})
        return True
    except Exception as e:
        logger.error(f"Failed to delete conversation from MongoDB: {e}")
        return False

# Initialize connection when module is imported
connect_to_db()
