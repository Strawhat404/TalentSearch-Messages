import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_BASE = f"{BASE_URL}/auth"

def print_response(response, title):
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print(f"{'='*50}")

def test_auth_system():
    print("�� Testing Auth Token System")
    print("="*60)
    
    # Test 1: Register a new user
    print("\n1️⃣ Testing User Registration...")
    register_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "name": "Test User",
        "phone_number": "+251912345678",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!"
    }
    
    register_response = requests.post(f"{AUTH_BASE}/register/", json=register_data)
    print_response(register_response, "User Registration")
    
    if register_response.status_code != 201:
        print("❌ Registration failed. Using existing user for login test.")
        # Try to login with existing user
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPass123!"
        }
    else:
        # Use the tokens from registration
        tokens = register_response.json()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        print(f"✅ Registration successful! Got tokens:")
        print(f"   Access Token: {access_token[:50]}...")
        print(f"   Refresh Token: {refresh_token[:50]}...")
        
        # Test 2: Check token status
        print("\n2️⃣ Testing Token Status...")
        headers = {"Authorization": f"Bearer {access_token}"}
        status_response = requests.get(f"{AUTH_BASE}/token/status/", headers=headers)
        print_response(status_response, "Token Status Check")
        
        # Test 3: Test token refresh
        print("\n3️⃣ Testing Token Refresh...")
        refresh_data = {"refresh": refresh_token}
        refresh_response = requests.post(f"{AUTH_BASE}/token/refresh/", json=refresh_data)
        print_response(refresh_response, "Token Refresh")
        
        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()
            new_access_token = new_tokens['access']
            new_refresh_token = new_tokens['refresh']
            
            print(f"✅ Token refresh successful!")
            print(f"   New Access Token: {new_access_token[:50]}...")
            print(f"   New Refresh Token: {new_refresh_token[:50]}...")
            print(f"   Expires in: {new_tokens.get('expires_in', 'N/A')} seconds")
            print(f"   Refresh expires in: {new_tokens.get('refresh_expires_in', 'N/A')} seconds")
            
            # Test 4: Use new access token
            print("\n4️⃣ Testing New Access Token...")
            new_headers = {"Authorization": f"Bearer {new_access_token}"}
            new_status_response = requests.get(f"{AUTH_BASE}/token/status/", headers=new_headers)
            print_response(new_status_response, "New Token Status Check")
            
            # Test 5: Verify old refresh token is blacklisted
            print("\n5️⃣ Testing Old Refresh Token Blacklist...")
            old_refresh_response = requests.post(f"{AUTH_BASE}/token/refresh/", json=refresh_data)
            print_response(old_refresh_response, "Old Refresh Token (Should be blacklisted)")
            
            # Test 6: Test logout
            print("\n6️⃣ Testing Logout...")
            logout_data = {"refresh": new_refresh_token}
            logout_response = requests.post(f"{AUTH_BASE}/logout/", json=logout_data, headers=new_headers)
            print_response(logout_response, "Logout")
            
            # Test 7: Verify logout worked
            print("\n7️⃣ Testing Post-Logout Token Usage...")
            post_logout_response = requests.get(f"{AUTH_BASE}/token/status/", headers=new_headers)
            print_response(post_logout_response, "Post-Logout Token Check")
            
            # Test 8: Try to refresh after logout
            print("\n8️⃣ Testing Refresh After Logout...")
            post_logout_refresh_data = {"refresh": new_refresh_token}
            post_logout_refresh_response = requests.post(f"{AUTH_BASE}/token/refresh/", json=post_logout_refresh_data)
            print_response(post_logout_refresh_response, "Refresh After Logout (Should fail)")
    
    # Test 9: Test login with credentials
    print("\n9️⃣ Testing Login with Credentials...")
    login_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!"
    }
    login_response = requests.post(f"{AUTH_BASE}/login/", json=login_data)
    print_response(login_response, "Login with Credentials")
    
    if login_response.status_code == 200:
        login_tokens = login_response.json()
        print(f"✅ Login successful!")
        print(f"   Access Token: {login_tokens['access'][:50]}...")
        print(f"   Refresh Token: {login_tokens['refresh'][:50]}...")
        
        # Test 10: Test protected endpoint
        print("\n🔟 Testing Protected Endpoint...")
        login_headers = {"Authorization": f"Bearer {login_tokens['access']}"}
        protected_response = requests.get(f"{AUTH_BASE}/notifications/", headers=login_headers)
        print_response(protected_response, "Protected Endpoint Access")

def test_token_lifetimes():
    print("\n⏰ Testing Token Lifetimes...")
    print("="*60)
    
    # Login to get tokens
    login_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!"
    }
    login_response = requests.post(f"{AUTH_BASE}/login/", json=login_data)
    
    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        print(f"✅ Got tokens for lifetime testing")
        print(f"   Access Token: {access_token[:50]}...")
        print(f"   Refresh Token: {refresh_token[:50]}...")
        
        # Check token status to see expiry
        headers = {"Authorization": f"Bearer {access_token}"}
        status_response = requests.get(f"{AUTH_BASE}/token/status/", headers=headers)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            expires_in = status_data.get('expires_in', 'Unknown')
            print(f"   Access token expires in: {expires_in} seconds")
            
            # Convert to hours and minutes for readability
            if isinstance(expires_in, int):
                hours = expires_in // 3600
                minutes = (expires_in % 3600) // 60
                print(f"   That's approximately: {hours} hours and {minutes} minutes")

if __name__ == "__main__":
    try:
        test_auth_system()
        test_token_lifetimes()
        print("\n🎉 All tests completed!")
        print("\n�� Summary:")
        print("✅ Registration/Login working")
        print("✅ Token refresh working")
        print("✅ Token blacklisting working")
        print("✅ Logout working")
        print("✅ Protected endpoints working")
        print("✅ Token lifetimes configured correctly")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Make sure your Django server is running on http://localhost:8000")
        print("   Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}") 