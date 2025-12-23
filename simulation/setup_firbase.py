# This is a separate file to help you set up Firebase
import json

print("=== FIREBASE SETUP INSTRUCTIONS ===")
print("\n1. Go to: https://console.firebase.google.com/")
print("2. Create a new project")
print("3. Enable Realtime Database")
print("4. Go to Project Settings → Service Accounts")
print("5. Click 'Generate New Private Key'")
print("6. Save as 'serviceAccountKey.json' in the same folder")
print("\nYour database URL will be shown in Realtime Database section")
print("Example: https://your-project-id.firebaseio.com/")

# Create a sample config file
config = {
    "instructions": "Place your serviceAccountKey.json file in this folder",
    "databaseURL": "https://your-project-id.firebaseio.com/"
}

with open('firebase_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\nCreated firebase_config.json with instructions")