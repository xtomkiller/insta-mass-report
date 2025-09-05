import os
import json
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def list_active_accounts():
    files = [f for f in os.listdir(SESSIONS_DIR) if f.startswith("session_") and f.endswith(".json")]
    if not files:
        print("❌ No active accounts found.")
        return

    print("\n📌 Active Accounts:")
    for file in files:
        try:
            cl = Client()
            cl.load_settings(os.path.join(SESSIONS_DIR, file))

            try:
                cl.get_timeline_feed()  # Check if still logged in
                username = cl.account_info().username
                print(f"✅ {username} -> Active")
            except LoginRequired:
                print(f"❌ {file.replace('session_', '').replace('.json', '')} -> Expired")

        except json.JSONDecodeError:
            print(f"⚠️ {file} -> Corrupted JSON")
        except Exception as e:
            print(f"⚠️ Error loading {file}: {e}")

def login_new_account():
    username = input("📥 Enter Instagram username: ").strip()
    password = input("🔑 Enter Instagram password: ").strip()

    cl = Client()
    try:
        cl.login(username, password)
        session_file = os.path.join(SESSIONS_DIR, f"session_{username}.json")
        cl.dump_settings(session_file)
        print(f"✅ Login successful! Session saved as {session_file}")

        next_action = input("\n[1] Login another account\n[2] Show active accounts\n[3] Exit\n👉 Enter choice: ").strip()
        if next_action == "1":
            login_new_account()
        elif next_action == "2":
            list_active_accounts()

    except Exception as e:
        print(f"❌ Login failed: {e}")

def main():
    while True:
        print("\n====== Instagram Login Manager ======")
        print("[1] Login new account")
        print("[2] Show active accounts")
        print("[3] Exit")
        choice = input("👉 Enter choice: ").strip()

        if choice == "1":
            login_new_account()
        elif choice == "2":
            list_active_accounts()
        elif choice == "3":
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()
