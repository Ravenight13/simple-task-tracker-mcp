#!/bin/bash

API_KEY="quJ5dpjJHfhuskKj3CGcTxn5Af6HZ-O9mPkaepvH7fo"
BASE_URL="http://127.0.0.1:8003"
PROJECT_ID="1e7be4ae"

echo "=== Test 1: Health Check (no auth) ==="
curl -s $BASE_URL/health | python3 -m json.tool | head -10

echo -e "\n\n=== Test 2: List Projects ==="
curl -s -H "X-API-Key: $API_KEY" $BASE_URL/api/projects | python3 -m json.tool | head -15

echo -e "\n\n=== Test 3: Get Project Info ==="
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/projects/$PROJECT_ID/info" | python3 -m json.tool | head -20

echo -e "\n\n=== Test 4: List Tasks ==="
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/tasks?project_id=$PROJECT_ID&limit=3" | python3 -m json.tool | head -30

echo -e "\n\n=== Test 5: Get Single Task ==="
TASK_ID=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/tasks?project_id=$PROJECT_ID&limit=1" | python3 -c "import sys, json; print(json.load(sys.stdin)['tasks'][0]['id'])" 2>/dev/null)
if [ -n "$TASK_ID" ]; then
  curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/tasks/$TASK_ID?project_id=$PROJECT_ID" | python3 -m json.tool | head -15
else
  echo "No tasks found"
fi

echo -e "\n\n=== Test 6: Search Tasks ==="
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/tasks/search?q=deployment&project_id=$PROJECT_ID&limit=2" | python3 -m json.tool | head -20

echo -e "\n\n=== Test 7: Get Next Tasks ==="
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/tasks/next?project_id=$PROJECT_ID&limit=2" | python3 -m json.tool | head -20

echo -e "\n\n=== Test 8: Get Blocked Tasks ==="
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/tasks/blocked?project_id=$PROJECT_ID" | python3 -m json.tool | head -10

echo -e "\n\n=== All Tests Complete ==="
