"""
MongoDB Client for Invoice Application
Handles connection to MongoDB Atlas and provides query functions for master data.
"""

import os
from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "invoice_app"

# Collection names (case-sensitive as per MongoDB)
COLLECTION_PARENT_COMPANIES = "Parent Companies"
COLLECTION_CLIENT_COMPANIES = "Client Companies"
COLLECTION_BANK_ACCOUNTS = "bank_accounts"
COLLECTION_TERMS_AND_CONDITIONS = "TermsAndConditions"

# Global client instance (singleton pattern)
_client: Optional[MongoClient] = None
_db = None


def get_mongodb_client():
    """
    Get or create MongoDB client instance (singleton pattern).
    Returns the database object.
    """
    global _client, _db
    
    if _client is None:
        if not MONGODB_URI:
            raise ValueError("MONGODB_URI not found in environment variables")
        
        try:
            _client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
            )
            # Test connection
            _client.admin.command('ping')
            _db = _client[DATABASE_NAME]
            print(f"✓ Connected to MongoDB: {DATABASE_NAME}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ MongoDB connection failed: {e}")
            raise
    
    return _db


def close_mongodb_connection():
    """Close MongoDB connection (call on application shutdown)."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        print("✓ MongoDB connection closed")


# ============================================================================
# Parent Companies
# ============================================================================

def get_all_parent_companies() -> List[Dict]:
    """
    Fetch all active parent companies from MongoDB.
    
    Returns:
        List of dicts with structure:
        [
            {
                "id": "_id value",
                "label": "display.label value",
                "document": { full MongoDB document without display field }
            },
            ...
        ]
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_PARENT_COMPANIES]
        
        # Query only active companies
        cursor = collection.find({"display.is_active": True})
        
        results = []
        for doc in cursor:
            # Extract display info for UI
            display = doc.get("display", {})
            label = display.get("label", doc.get("parent_company_title", "Unknown"))
            
            # Remove display field from document (don't map to invoice state)
            doc_copy = dict(doc)
            doc_copy.pop("display", None)
            
            results.append({
                "id": str(doc["_id"]),
                "label": label,
                "document": doc_copy
            })
        
        return results
    
    except Exception as e:
        print(f"Error fetching parent companies: {e}")
        return []


def get_parent_company_by_id(company_id: str) -> Optional[Dict]:
    """
    Fetch a specific parent company by ID.
    
    Args:
        company_id: The _id of the parent company
    
    Returns:
        MongoDB document without display field, or None if not found
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_PARENT_COMPANIES]
        
        doc = collection.find_one({"_id": company_id})
        
        if doc:
            # Remove display field
            doc.pop("display", None)
            return doc
        
        return None
    
    except Exception as e:
        print(f"Error fetching parent company {company_id}: {e}")
        return None


# ============================================================================
# Client Companies
# ============================================================================

def get_all_client_companies() -> List[Dict]:
    """
    Fetch all active client companies from MongoDB.
    
    Returns:
        List of dicts with structure:
        [
            {
                "id": "_id value",
                "label": "display.label value",
                "document": { full MongoDB document without display field }
            },
            ...
        ]
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_CLIENT_COMPANIES]
        
        # Query only active companies
        cursor = collection.find({"display.is_active": True})
        
        results = []
        for doc in cursor:
            # Extract display info for UI
            display = doc.get("display", {})
            label = display.get("label", doc.get("client_company_name", "Unknown"))
            
            # Remove display field from document
            doc_copy = dict(doc)
            doc_copy.pop("display", None)
            
            results.append({
                "id": str(doc["_id"]),
                "label": label,
                "document": doc_copy
            })
        
        return results
    
    except Exception as e:
        print(f"Error fetching client companies: {e}")
        return []


def get_client_company_by_id(company_id: str) -> Optional[Dict]:
    """
    Fetch a specific client company by ID.
    
    Args:
        company_id: The _id of the client company
    
    Returns:
        MongoDB document without display field, or None if not found
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_CLIENT_COMPANIES]
        
        doc = collection.find_one({"_id": company_id})
        
        if doc:
            # Remove display field
            doc.pop("display", None)
            return doc
        
        return None
    
    except Exception as e:
        print(f"Error fetching client company {company_id}: {e}")
        return None


# ============================================================================
# Bank Accounts
# ============================================================================

def get_all_bank_accounts() -> List[Dict]:
    """
    Fetch all active bank accounts from MongoDB.
    
    Returns:
        List of dicts with structure:
        [
            {
                "id": "_id value",
                "label": "display.label value",
                "document": { full MongoDB document without display field }
            },
            ...
        ]
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_BANK_ACCOUNTS]
        
        # Query only active bank accounts
        cursor = collection.find({"display.is_active": True})
        
        results = []
        for doc in cursor:
            # Extract display info for UI
            display = doc.get("display", {})
            label = display.get("label", f"{doc.get('bank_name', 'Unknown')} - {doc.get('branch', '')}")
            
            # Remove display field from document
            doc_copy = dict(doc)
            doc_copy.pop("display", None)
            
            results.append({
                "id": str(doc["_id"]),
                "label": label,
                "document": doc_copy
            })
        
        return results
    
    except Exception as e:
        print(f"Error fetching bank accounts: {e}")
        return []


def get_bank_account_by_id(account_id: str) -> Optional[Dict]:
    """
    Fetch a specific bank account by ID.
    
    Args:
        account_id: The _id of the bank account
    
    Returns:
        MongoDB document without display field, or None if not found
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_BANK_ACCOUNTS]
        
        doc = collection.find_one({"_id": account_id})
        
        if doc:
            # Remove display field
            doc.pop("display", None)
            return doc
        
        return None
    
    except Exception as e:
        print(f"Error fetching bank account {account_id}: {e}")
        return None


# ============================================================================
# Terms and Conditions
# ============================================================================

def get_all_terms_and_conditions() -> List[Dict]:
    """
    Fetch all active terms and conditions sets from MongoDB.
    
    Returns:
        List of dicts with structure:
        [
            {
                "id": "_id value",
                "label": "display.label value",
                "document": { full MongoDB document without display field }
            },
            ...
        ]
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_TERMS_AND_CONDITIONS]
        
        # Query only active T&C sets
        cursor = collection.find({"display.is_active": True})
        
        results = []
        for doc in cursor:
            doc_copy = dict(doc)
            display_info = doc_copy.pop("display", {})
            
            results.append({
                "id": str(doc["_id"]),
                "label": display_info.get("label", str(doc["_id"])),
                "document": doc_copy
            })
        
        return results
    
    except Exception as e:
        print(f"Error fetching terms and conditions: {e}")
        return []


def get_terms_and_conditions_by_id(tnc_id: str) -> Optional[Dict]:
    """
    Fetch a specific terms and conditions set by ID.
    
    Args:
        tnc_id: The _id of the T&C document
    
    Returns:
        MongoDB document without display field, or None if not found
    """
    try:
        db = get_mongodb_client()
        collection = db[COLLECTION_TERMS_AND_CONDITIONS]
        
        doc = collection.find_one({"_id": tnc_id})
        
        if doc:
            # Extract label from display before removing it
            display = doc.pop("display", {})
            doc["label"] = display.get("label", str(doc.get("_id", "Unknown")))
            return doc
        
        return None
    
    except Exception as e:
        print(f"Error fetching terms and conditions {tnc_id}: {e}")
        return None


# ============================================================================
# Utility Functions
# ============================================================================

def test_connection() -> bool:
    """
    Test MongoDB connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        db = get_mongodb_client()
        # Ping the database
        db.command('ping')
        print("✓ MongoDB connection test successful")
        return True
    except Exception as e:
        print(f"✗ MongoDB connection test failed: {e}")
        return False


def get_collection_stats() -> Dict:
    """
    Get statistics about the collections.
    
    Returns:
        Dict with collection counts
    """
    try:
        db = get_mongodb_client()
        
        stats = {
            "parent_companies": {
                "total": db[COLLECTION_PARENT_COMPANIES].count_documents({}),
                "active": db[COLLECTION_PARENT_COMPANIES].count_documents({"display.is_active": True})
            },
            "client_companies": {
                "total": db[COLLECTION_CLIENT_COMPANIES].count_documents({}),
                "active": db[COLLECTION_CLIENT_COMPANIES].count_documents({"display.is_active": True})
            },
            "bank_accounts": {
                "total": db[COLLECTION_BANK_ACCOUNTS].count_documents({}),
                "active": db[COLLECTION_BANK_ACCOUNTS].count_documents({"display.is_active": True})
            }
        }
        
        return stats
    
    except Exception as e:
        print(f"Error getting collection stats: {e}")
        return {}


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("MongoDB Client Test")
    print("=" * 80)
    
    # Test connection
    if test_connection():
        print("\n✓ Connection successful!")
        
        # Get stats
        print("\n📊 Collection Statistics:")
        stats = get_collection_stats()
        for collection, counts in stats.items():
            print(f"  {collection}: {counts['active']} active / {counts['total']} total")
        
        # Test parent companies
        print("\n🏢 Parent Companies:")
        parent_companies = get_all_parent_companies()
        for pc in parent_companies:
            print(f"  - {pc['label']} (ID: {pc['id']})")
        
        # Test client companies
        print("\n👥 Client Companies:")
        client_companies = get_all_client_companies()
        for cc in client_companies:
            print(f"  - {cc['label']} (ID: {cc['id']})")
        
        # Test bank accounts
        print("\n🏦 Bank Accounts:")
        bank_accounts = get_all_bank_accounts()
        for ba in bank_accounts:
            print(f"  - {ba['label']} (ID: {ba['id']})")
        
        # Close connection
        close_mongodb_connection()
    else:
        print("\n✗ Connection failed!")
