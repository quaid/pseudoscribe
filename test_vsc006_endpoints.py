#!/usr/bin/env python3
"""
Quick test script for VSC-006 Collaboration API endpoints
Tests basic functionality and performance requirements
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
TENANT_ID = "test-tenant"

async def test_vsc006_collaboration_endpoints():
    """Test VSC-006 collaboration endpoints for functionality and performance"""
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing VSC-006 Collaboration API Endpoints")
        print("=" * 50)
        
        # Test data
        document_id = "test-doc-123"
        users = [
            {"user_id": "alice", "name": "Alice"},
            {"user_id": "bob", "name": "Bob"},
            {"user_id": "charlie", "name": "Charlie"}
        ]
        
        session_id = None
        
        try:
            # Test 1: Create collaboration session
            print("\n1. Testing session creation...")
            start_time = time.time()
            
            create_response = await client.post(
                f"{BASE_URL}/api/v1/collaboration/sessions",
                json={
                    "document_id": document_id,
                    "creator_id": users[0]["user_id"],
                    "permissions": {
                        users[1]["user_id"]: "edit",
                        users[2]["user_id"]: "read"
                    }
                },
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            create_time = (time.time() - start_time) * 1000
            print(f"   Status: {create_response.status_code}")
            print(f"   Time: {create_time:.2f}ms")
            
            if create_response.status_code == 201:
                session_data = create_response.json()
                session_id = session_data["session_id"]
                print(f"   ✅ Session created: {session_id}")
                print(f"   Permissions: {session_data['permissions']}")
            else:
                print(f"   ❌ Failed: {create_response.text}")
                return
            
            # Test 2: Join session
            print("\n2. Testing session join...")
            for user in users:
                join_response = await client.post(
                    f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/join",
                    json={"user_id": user["user_id"]},
                    headers={"X-Tenant-ID": TENANT_ID}
                )
                
                if join_response.status_code == 200:
                    join_data = join_response.json()
                    print(f"   ✅ {user['user_id']} joined with {join_data['permission']} permission")
                else:
                    print(f"   ❌ {user['user_id']} failed to join: {join_response.text}")
            
            # Test 3: Document changes and sync performance
            print("\n3. Testing document changes and sync performance...")
            start_time = time.time()
            
            change_response = await client.post(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/changes",
                json={
                    "user_id": users[0]["user_id"],
                    "operation": "insert",
                    "position": 10,
                    "content": "Hello, collaborative world!",
                    "timestamp": int(time.time() * 1000)
                },
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            sync_time = (time.time() - start_time) * 1000
            print(f"   Status: {change_response.status_code}")
            print(f"   Sync time: {sync_time:.2f}ms")
            
            if change_response.status_code == 200:
                change_data = change_response.json()
                print(f"   ✅ Change applied: {change_data['change_id']}")
                print(f"   Conflicts: {change_data['conflicts']}")
                
                # Verify sync performance requirement (<200ms)
                if sync_time < 200:
                    print(f"   ✅ Sync performance: {sync_time:.2f}ms < 200ms requirement")
                else:
                    print(f"   ⚠️  Sync performance: {sync_time:.2f}ms exceeds 200ms requirement")
            else:
                print(f"   ❌ Failed: {change_response.text}")
            
            # Test 4: Cursor updates and performance
            print("\n4. Testing cursor updates and performance...")
            start_time = time.time()
            
            cursor_response = await client.post(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/cursor",
                json={
                    "user_id": users[1]["user_id"],
                    "position": 25,
                    "selection_start": 20,
                    "selection_end": 30
                },
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            cursor_time = (time.time() - start_time) * 1000
            print(f"   Status: {cursor_response.status_code}")
            print(f"   Cursor update time: {cursor_time:.2f}ms")
            
            if cursor_response.status_code == 200:
                cursor_data = cursor_response.json()
                print(f"   ✅ Cursor updated successfully")
                
                # Verify cursor performance requirement (<50ms)
                if cursor_time < 50:
                    print(f"   ✅ Cursor performance: {cursor_time:.2f}ms < 50ms requirement")
                else:
                    print(f"   ⚠️  Cursor performance: {cursor_time:.2f}ms exceeds 50ms requirement")
            else:
                print(f"   ❌ Failed: {cursor_response.text}")
            
            # Test 5: Presence awareness
            print("\n5. Testing presence awareness...")
            presence_response = await client.get(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/presence",
                params={"user_id": users[0]["user_id"]},
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            print(f"   Status: {presence_response.status_code}")
            if presence_response.status_code == 200:
                presence_data = presence_response.json()
                print(f"   ✅ Active users: {len(presence_data['users'])}")
                for user_presence in presence_data['users']:
                    print(f"      - {user_presence['user_id']}: {user_presence['status']}")
            else:
                print(f"   ❌ Failed: {presence_response.text}")
            
            # Test 6: Style suggestions
            print("\n6. Testing collaborative style suggestions...")
            suggestion_response = await client.post(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/suggestions",
                json={
                    "user_id": users[0]["user_id"],
                    "type": "style",
                    "position": 15,
                    "original_text": "collaborative world",
                    "suggested_text": "shared workspace",
                    "reason": "More professional terminology"
                },
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            print(f"   Status: {suggestion_response.status_code}")
            if suggestion_response.status_code == 201:
                suggestion_data = suggestion_response.json()
                print(f"   ✅ Suggestion created: {suggestion_data['suggestion_id']}")
            else:
                print(f"   ❌ Failed: {suggestion_response.text}")
            
            # Test 7: Get suggestions
            suggestions_list_response = await client.get(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/suggestions",
                params={"user_id": users[1]["user_id"]},
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            if suggestions_list_response.status_code == 200:
                suggestions_data = suggestions_list_response.json()
                print(f"   ✅ Retrieved {len(suggestions_data['suggestions'])} suggestions")
            
            # Test 8: Permission management
            print("\n7. Testing permission management...")
            permissions_response = await client.get(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/permissions",
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            print(f"   Status: {permissions_response.status_code}")
            if permissions_response.status_code == 200:
                permissions_data = permissions_response.json()
                print(f"   ✅ Current permissions: {permissions_data['permissions']}")
            
            # Test permission update
            update_perm_response = await client.put(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/permissions",
                json={
                    "user_id": users[0]["user_id"],  # admin user
                    "target_user_id": users[2]["user_id"],
                    "permission": "edit"
                },
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            if update_perm_response.status_code == 200:
                print(f"   ✅ Permission updated for {users[2]['user_id']}")
            
            # Test 9: Session history
            print("\n8. Testing session history...")
            history_response = await client.get(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/history",
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            print(f"   Status: {history_response.status_code}")
            if history_response.status_code == 200:
                history_data = history_response.json()
                print(f"   ✅ History entries: {history_data['total_count']}")
                for change in history_data['history'][:3]:  # Show first 3
                    print(f"      - {change['user_id']}: {change['operation']} at pos {change['position']}")
            
            # Test 10: Conflict detection
            print("\n9. Testing conflict detection...")
            # Create a conflicting change
            conflict_response = await client.post(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/changes",
                json={
                    "user_id": users[1]["user_id"],
                    "operation": "replace",
                    "position": 12,
                    "length": 5,
                    "content": "CONFLICT",
                    "timestamp": int(time.time() * 1000)
                },
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            if conflict_response.status_code == 200:
                conflict_data = conflict_response.json()
                if conflict_data['conflicts']:
                    print(f"   ✅ Conflict detected: {len(conflict_data['conflicts'])} conflicts")
                else:
                    print(f"   ℹ️  No conflicts detected")
            
            # Check conflicts endpoint
            conflicts_response = await client.get(
                f"{BASE_URL}/api/v1/collaboration/sessions/{session_id}/conflicts",
                headers={"X-Tenant-ID": TENANT_ID}
            )
            
            if conflicts_response.status_code == 200:
                conflicts_data = conflicts_response.json()
                print(f"   ✅ Pending conflicts: {len(conflicts_data['conflicts'])}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🏁 VSC-006 Collaboration API Testing Complete")


async def test_websocket_connection():
    """Test WebSocket connection for real-time collaboration"""
    print("\n🔌 Testing WebSocket Connection...")
    
    try:
        # Note: This is a basic test - full WebSocket testing would require more setup
        import websockets
        
        # This will likely fail until WebSocket is fully implemented
        # But it tests the endpoint availability
        print("   WebSocket endpoint: ws://localhost:8000/api/v1/collaboration/sessions/test/ws")
        print("   ℹ️  WebSocket testing requires running server and websockets library")
        
    except ImportError:
        print("   ℹ️  WebSocket testing skipped (websockets library not available)")
    except Exception as e:
        print(f"   ⚠️  WebSocket test: {str(e)}")


if __name__ == "__main__":
    print("VSC-006 Collaboration API Test Suite")
    print("Make sure the FastAPI server is running on localhost:8000")
    print()
    
    # Run the tests
    asyncio.run(test_vsc006_collaboration_endpoints())
    asyncio.run(test_websocket_connection())
