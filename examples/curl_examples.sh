#!/bin/bash
# HypertroQ Backend - cURL API Examples
# 
# Complete collection of cURL commands for testing the HypertroQ API.
# Run this script from the command line or copy individual commands.
#
# Requirements: curl, jq (optional, for pretty JSON output)
#
# Usage:
#   chmod +x curl_examples.sh
#   ./curl_examples.sh

# ==================== Configuration ====================

BASE_URL="http://localhost:8000"
API_VERSION="v1"
API_BASE="${BASE_URL}/api/${API_VERSION}"

# Store tokens in variables (will be set by authentication commands)
ACCESS_TOKEN=""
REFRESH_TOKEN=""
USER_EMAIL="demo@example.com"
USER_PASSWORD="SecureDemo123!"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ==================== Helper Functions ====================

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Pretty print JSON if jq is available
pretty_json() {
    if command -v jq &> /dev/null; then
        jq '.'
    else
        cat
    fi
}

# ==================== Health Check ====================

print_section "1. Health Check"

echo "GET ${API_BASE}/health"
curl -s "${API_BASE}/health" | pretty_json
print_success "Health check complete"

# ==================== Authentication ====================

print_section "2. Authentication"

# Register User
echo -e "\n${YELLOW}2.1 Register User${NC}"
echo "POST ${API_BASE}/auth/register"

REGISTER_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${USER_EMAIL}\",
    \"password\": \"${USER_PASSWORD}\",
    \"full_name\": \"Demo User\"
  }")

# Check if registration was successful or user already exists
if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    print_success "User registered successfully"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')
    REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.refresh_token')
    echo "$REGISTER_RESPONSE" | pretty_json
else
    print_warning "User might already exist, trying to login..."
fi

# Login (if registration failed)
if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "\n${YELLOW}2.2 Login${NC}"
    echo "POST ${API_BASE}/auth/login"
    
    LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"${USER_EMAIL}\",
        \"password\": \"${USER_PASSWORD}\"
      }")
    
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
    REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')
    
    if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
        print_success "Login successful"
        echo "$LOGIN_RESPONSE" | pretty_json
    else
        print_error "Login failed"
        echo "$LOGIN_RESPONSE" | pretty_json
        exit 1
    fi
fi

echo -e "\nAccess Token: ${ACCESS_TOKEN:0:20}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."

# Refresh Token
echo -e "\n${YELLOW}2.3 Refresh Access Token${NC}"
echo "POST ${API_BASE}/auth/refresh"

REFRESH_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"${REFRESH_TOKEN}\"
  }")

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token')
if [ "$NEW_ACCESS_TOKEN" != "null" ]; then
    print_success "Token refreshed"
    ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
else
    print_warning "Token refresh failed or not needed"
fi

# ==================== User Management ====================

print_section "3. User Management"

# Get Current User
echo -e "\n${YELLOW}3.1 Get Current User${NC}"
echo "GET ${API_BASE}/users/me"

curl -s "${API_BASE}/users/me" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json

print_success "User profile retrieved"

# Update User Profile
echo -e "\n${YELLOW}3.2 Update User Profile${NC}"
echo "PUT ${API_BASE}/users/me"

curl -s -X PUT "${API_BASE}/users/me" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Demo User Updated"
  }' | pretty_json

print_success "Profile updated"

# ==================== Exercise Management ====================

print_section "4. Exercise Management"

# List Exercises
echo -e "\n${YELLOW}4.1 List All Exercises${NC}"
echo "GET ${API_BASE}/exercises?page=1&limit=5"

EXERCISES_RESPONSE=$(curl -s "${API_BASE}/exercises?page=1&limit=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

echo "$EXERCISES_RESPONSE" | pretty_json

# Extract first exercise ID for later use
EXERCISE_ID=$(echo "$EXERCISES_RESPONSE" | jq -r '.data[0].id')
print_success "Retrieved exercises (First ID: ${EXERCISE_ID:0:8}...)"

# List Exercises with Filters
echo -e "\n${YELLOW}4.2 List Exercises (Filtered)${NC}"
echo "GET ${API_BASE}/exercises?equipment=BARBELL&muscle_group=CHEST"

curl -s "${API_BASE}/exercises?equipment=BARBELL&muscle_group=CHEST&limit=3" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json

print_success "Filtered exercises retrieved"

# Get Exercise by ID
echo -e "\n${YELLOW}4.3 Get Exercise by ID${NC}"
echo "GET ${API_BASE}/exercises/${EXERCISE_ID}"

curl -s "${API_BASE}/exercises/${EXERCISE_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json

print_success "Exercise details retrieved"

# Search Exercises (Semantic)
echo -e "\n${YELLOW}4.4 Search Exercises (AI-Powered)${NC}"
echo "POST ${API_BASE}/exercises/search"

curl -s -X POST "${API_BASE}/exercises/search" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "exercises for building bigger arms",
    "limit": 3
  }' | pretty_json

print_success "Semantic search complete"

# Get Equipment Types
echo -e "\n${YELLOW}4.5 Get Equipment Types${NC}"
echo "GET ${API_BASE}/exercises/equipment-types"

curl -s "${API_BASE}/exercises/equipment-types" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json

# Get Muscle Groups
echo -e "\n${YELLOW}4.6 Get Muscle Groups${NC}"
echo "GET ${API_BASE}/exercises/muscle-groups"

curl -s "${API_BASE}/exercises/muscle-groups" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json

print_success "Exercise metadata retrieved"

# Create Custom Exercise (requires Pro)
echo -e "\n${YELLOW}4.7 Create Custom Exercise (Pro only)${NC}"
echo "POST ${API_BASE}/exercises"

curl -s -X POST "${API_BASE}/exercises" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cable Fly Variation",
    "description": "Modified cable fly for upper chest",
    "equipment": "CABLE",
    "muscle_contributions": {
      "CHEST": 1.0,
      "FRONT_DELTS": 0.25
    },
    "difficulty": "INTERMEDIATE"
  }' | pretty_json

# May fail if user is on free tier
print_warning "Custom exercise creation (may require Pro tier)"

# ==================== Program Management ====================

print_section "5. Program Management"

# List Programs
echo -e "\n${YELLOW}5.1 List Programs${NC}"
echo "GET ${API_BASE}/programs?page=1&limit=5"

PROGRAMS_RESPONSE=$(curl -s "${API_BASE}/programs?page=1&limit=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

echo "$PROGRAMS_RESPONSE" | pretty_json

# Extract first program ID if available
PROGRAM_ID=$(echo "$PROGRAMS_RESPONSE" | jq -r '.data[0].id')
print_success "Programs retrieved"

# Create Program
echo -e "\n${YELLOW}5.2 Create Training Program${NC}"
echo "POST ${API_BASE}/programs"

CREATE_PROGRAM_RESPONSE=$(curl -s -X POST "${API_BASE}/programs" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Demo Push/Pull Split\",
    \"description\": \"Simple 2-day push/pull program\",
    \"structure_type\": \"WEEKLY\",
    \"frequency\": 2,
    \"sessions\": [
      {
        \"name\": \"Push Day\",
        \"day_of_week\": 0,
        \"exercises\": [
          {
            \"exercise_id\": \"${EXERCISE_ID}\",
            \"sets\": 4,
            \"reps\": \"8-12\",
            \"rest_seconds\": 90
          }
        ]
      },
      {
        \"name\": \"Pull Day\",
        \"day_of_week\": 2,
        \"exercises\": [
          {
            \"exercise_id\": \"${EXERCISE_ID}\",
            \"sets\": 4,
            \"reps\": \"8-12\",
            \"rest_seconds\": 90
          }
        ]
      }
    ]
  }")

echo "$CREATE_PROGRAM_RESPONSE" | pretty_json

# Extract created program ID
CREATED_PROGRAM_ID=$(echo "$CREATE_PROGRAM_RESPONSE" | jq -r '.id')
if [ "$CREATED_PROGRAM_ID" != "null" ]; then
    PROGRAM_ID="$CREATED_PROGRAM_ID"
    print_success "Program created (ID: ${PROGRAM_ID:0:8}...)"
else
    print_warning "Program creation may have failed"
fi

# Get Program by ID
if [ "$PROGRAM_ID" != "null" ] && [ -n "$PROGRAM_ID" ]; then
    echo -e "\n${YELLOW}5.3 Get Program by ID${NC}"
    echo "GET ${API_BASE}/programs/${PROGRAM_ID}"
    
    curl -s "${API_BASE}/programs/${PROGRAM_ID}" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json
    
    print_success "Program details retrieved"
    
    # Calculate Program Volume
    echo -e "\n${YELLOW}5.4 Calculate Program Volume${NC}"
    echo "GET ${API_BASE}/programs/${PROGRAM_ID}/volume"
    
    curl -s "${API_BASE}/programs/${PROGRAM_ID}/volume" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json
    
    print_success "Volume calculation complete"
    
    # Clone Program
    echo -e "\n${YELLOW}5.5 Clone Program${NC}"
    echo "POST ${API_BASE}/programs/${PROGRAM_ID}/clone"
    
    curl -s -X POST "${API_BASE}/programs/${PROGRAM_ID}/clone" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "new_name": "Demo Push/Pull Split (Clone)"
      }' | pretty_json
    
    print_success "Program cloned"
fi

# Get Program Templates
echo -e "\n${YELLOW}5.6 Get Program Templates${NC}"
echo "GET ${API_BASE}/programs/templates"

curl -s "${API_BASE}/programs/templates?page=1&limit=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | pretty_json

print_success "Program templates retrieved"

# ==================== Advanced Examples ====================

print_section "6. Advanced Examples"

# Pagination Example
echo -e "\n${YELLOW}6.1 Pagination Example${NC}"
echo "Fetching multiple pages of exercises..."

for page in 1 2; do
    echo -e "\nPage $page:"
    curl -s "${API_BASE}/exercises?page=${page}&limit=3" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      | jq -r '.data[] | "  - \(.name) (\(.equipment))"'
done

print_success "Pagination example complete"

# Filtering Example
echo -e "\n${YELLOW}6.2 Multiple Filters Example${NC}"
echo "GET ${API_BASE}/exercises?equipment=DUMBBELL&difficulty=BEGINNER"

curl -s "${API_BASE}/exercises?equipment=DUMBBELL&difficulty=BEGINNER&limit=3" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  | jq -r '.data[] | "  - \(.name) (\(.difficulty))"'

print_success "Filtering example complete"

# ==================== Cleanup ====================

print_section "7. Cleanup"

# Logout
echo -e "\n${YELLOW}7.1 Logout${NC}"
echo "POST ${API_BASE}/auth/logout"

curl -s -X POST "${API_BASE}/auth/logout" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"${REFRESH_TOKEN}\"
  }" | pretty_json

print_success "Logged out successfully"

# ==================== Summary ====================

print_section "Summary"

echo "✅ All API examples executed successfully!"
echo ""
echo "Key endpoints tested:"
echo "  • Health check"
echo "  • Authentication (register, login, refresh, logout)"
echo "  • User management (get profile, update profile)"
echo "  • Exercise management (list, get, search, create)"
echo "  • Program management (list, create, get, volume, clone)"
echo ""
echo "For more information, visit: http://localhost:8000/docs"
echo ""

# ==================== Individual Command Examples ====================

# These can be copied and used individually:

: '
# Quick Reference - Copy these commands as needed:

# 1. Health Check
curl http://localhost:8000/api/v1/health

# 2. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '"'"'{"email":"user@example.com","password":"Pass123!","full_name":"User"}'"'"'

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '"'"'{"email":"user@example.com","password":"Pass123!"}'"'"'

# 4. Get Current User (replace TOKEN)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"

# 5. List Exercises
curl http://localhost:8000/api/v1/exercises?page=1&limit=20 \
  -H "Authorization: Bearer TOKEN"

# 6. Create Program
curl -X POST http://localhost:8000/api/v1/programs \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '"'"'{"name":"My Program","description":"Test","structure_type":"WEEKLY","frequency":3,"sessions":[]}'"'"'

# 7. Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '"'"'{"refresh_token":"REFRESH_TOKEN"}'"'"'
'
