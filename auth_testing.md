# NaBaB Auth Testing Playbook
This file is created per the integration playbook for testing Emergent Google Auth.

## Step 1: Create Test User & Session
```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  credits: 1000,
  is_admin: true,
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API
```bash
# Test auth endpoint
curl -X GET "$REACT_APP_BACKEND_URL/api/auth/me" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Test protected endpoints
curl -X GET "$REACT_APP_BACKEND_URL/api/credits/balance" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Step 3: Browser Testing
Set session_token cookie before navigating to protected routes.

## Checklist
- [ ] User document has user_id field
- [ ] Session user_id matches user.user_id exactly
- [ ] All queries use {"_id": 0} projection
- [ ] /api/auth/me returns user data with cookie/header
- [ ] /chat, /dashboard, /buy, /admin routes work
