import os
from dotenv import load_dotenv
from github import Github

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
# ⚠️ REPLACE 'YourUsername' WITH YOUR ACTUAL GITHUB USERNAME
TARGET_REPO = "Vinay1223/Automated_Testing_and_Code_Intelligence"


def test_connection():
    print("🌐 Authenticating with GitHub...")
    g = Github(GITHUB_TOKEN)
    
    try:
        # Check if the token is valid at all
        user = g.get_user()
        print(f"👤 Authenticated as: {user.login}")
        
        # Check if the token can see the repository
        print(f"🔍 Searching for repository: {TARGET_REPO}...")
        repo = g.get_repo(TARGET_REPO)
        print(f"✅ SUCCESS! Found repository: {repo.full_name}")
        
    except Exception as e:
        print(f"❌ Connection Failed: {str(e)}")
        print("\nFix: You need to generate a new Classic Token with 'repo' scope enabled.")

if __name__ == "__main__":
    test_connection()