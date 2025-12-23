import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        # Try to find service account key
        service_account_paths = [
            'serviceAccountKey.json',
            'firebase-key.json',
            'config/serviceAccountKey.json',
            'water-monitoring-dashboard/serviceAccountKey.json'
        ]
        
        service_account_path = None
        for path in service_account_paths:
            if os.path.exists(path):
                service_account_path = path
                print(f"Found service account key: {path}")
                break
        
        if service_account_path:
            # Initialize with service account
            cred = credentials.Certificate(service_account_path)
            
            # Get database URL from environment or use default
            database_url = os.environ.get('FIREBASE_DB_URL', 
                                        'https://aterleak2-default-rtdb.firebaseio.com/')
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': database_url
                })
            
            print(f"Firebase initialized successfully with URL: {database_url}")
            return True
        else:
            print("No Firebase service account key found.")
            return False
            
    except Exception as e:
        print(f"Firebase setup error: {e}")
        return False

def get_firebase_ref():
    """Get Firebase database reference"""
    try:
        return db.reference('/water_system')
    except:
        return None

def get_system_data():
    """Fetch all system data from Firebase"""
    try:
        ref = get_firebase_ref()
        if ref:
            data = ref.get()
            return data if data else {}
    except Exception as e:
        print(f"Error fetching Firebase data: {e}")
    return {}
