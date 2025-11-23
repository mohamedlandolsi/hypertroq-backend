# API Examples

This folder contains practical examples for interacting with the HypertroQ Backend API.

## Contents

### 1. Postman Collection (`postman_collection.json`)

Complete Postman collection with all API endpoints organized by category.

**Features**:
- ✅ Pre-configured environment variables
- ✅ Automatic token management (extracts tokens from responses)
- ✅ All 49 API endpoints
- ✅ Example request bodies
- ✅ Test scripts for assertions

**How to use**:

1. **Import into Postman**:
   - Open Postman
   - Click "Import" → Choose file
   - Select `postman_collection.json`

2. **Set base URL**:
   - Click collection → Variables tab
   - Set `base_url` to `http://localhost:8000` (or your server)

3. **Run requests**:
   - Start with "Authentication → Register User"
   - Tokens are automatically saved to variables
   - Subsequent requests will use the saved `access_token`

4. **Run entire collection**:
   - Collection → Run
   - Configure iterations and data
   - View test results

---

### 2. Python Client (`python_client.py`)

Complete Python client library for programmatic API access.

**Features**:
- ✅ Clean OOP interface
- ✅ Automatic token management
- ✅ Error handling and retries
- ✅ Type hints
- ✅ Comprehensive docstrings
- ✅ Example usage in `main()` function

**Installation**:

```bash
pip install requests python-dotenv
```

**Basic usage**:

```python
from python_client import HypertroQClient

# Initialize client
client = HypertroQClient("http://localhost:8000")

# Login
client.login("user@example.com", "password")

# List exercises
exercises = client.list_exercises(page=1, limit=20)

# Create program
program = client.create_program(
    name="My Program",
    description="Custom training program",
    structure_type="WEEKLY",
    frequency=3,
    sessions=[...]
)

# Logout
client.logout()
```

**Run the example**:

```bash
# Make sure the API server is running
python python_client.py
```

This will:
1. Check API health
2. Register/login a demo user
3. Fetch user profile
4. List and search exercises
5. Create a sample program
6. Calculate training volume
7. Logout

---

### 3. cURL Examples (`curl_examples.sh`)

Bash script with comprehensive cURL commands for all API endpoints.

**Features**:
- ✅ Complete API workflow
- ✅ Automatic token extraction
- ✅ Pretty JSON output (with jq)
- ✅ Color-coded output
- ✅ Individual command reference
- ✅ Works on Linux, macOS, Git Bash (Windows)

**Requirements**:

```bash
# curl (usually pre-installed)
curl --version

# jq for JSON formatting (optional but recommended)
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq

# Windows (Git Bash)
# Download from: https://stedolan.github.io/jq/download/
```

**Usage**:

```bash
# Make script executable
chmod +x curl_examples.sh

# Run entire script
./curl_examples.sh

# Or copy individual commands from the script
```

**Individual command examples**:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!","full_name":"User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!"}'

# Get current user (replace TOKEN)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"

# List exercises with filters
curl "http://localhost:8000/api/v1/exercises?equipment=BARBELL&muscle_group=CHEST" \
  -H "Authorization: Bearer TOKEN"
```

---

## Quick Start

### Option 1: Postman (Visual, GUI-based)

Best for: Manual testing, exploration, team collaboration

1. Import `postman_collection.json`
2. Set `base_url` variable
3. Run "Authentication → Register User"
4. Explore other endpoints

### Option 2: Python Client (Programmatic)

Best for: Integration, automation, scripting

```bash
pip install requests
python python_client.py
```

### Option 3: cURL (Command line)

Best for: Quick tests, CI/CD, shell scripting

```bash
chmod +x curl_examples.sh
./curl_examples.sh
```

---

## Common Workflows

### Workflow 1: Register and Create First Program

**Postman**:
1. Auth → Register User
2. Exercises → List Global Exercises (note an exercise ID)
3. Programs → Create Program (use the exercise ID)
4. Programs → Calculate Program Volume

**Python**:
```python
client = HypertroQClient()
client.register("user@example.com", "Pass123!", "User Name")
exercises = client.list_exercises(limit=5)
exercise_id = exercises['data'][0]['id']

program = client.create_program(
    name="Push/Pull Split",
    description="2-day split",
    structure_type="WEEKLY",
    frequency=2,
    sessions=[
        {
            "name": "Push Day",
            "day_of_week": 0,
            "exercises": [{"exercise_id": exercise_id, "sets": 4, "reps": "8-12"}]
        }
    ]
)

volume = client.calculate_program_volume(program['id'])
print(volume)
```

**cURL**:
```bash
# 1. Register
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!","full_name":"User"}' \
  | jq -r '.access_token')

# 2. List exercises
EXERCISE_ID=$(curl -s "http://localhost:8000/api/v1/exercises?limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.data[0].id')

# 3. Create program
curl -X POST http://localhost:8000/api/v1/programs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"My Program\",\"description\":\"Test\",\"structure_type\":\"WEEKLY\",\"frequency\":2,\"sessions\":[{\"name\":\"Day 1\",\"day_of_week\":0,\"exercises\":[{\"exercise_id\":\"$EXERCISE_ID\",\"sets\":4,\"reps\":\"8-12\"}]}]}"
```

---

### Workflow 2: Search Exercises and Clone Program

**Postman**:
1. Auth → Login
2. Exercises → Search Exercises (semantic query: "arm exercises")
3. Programs → List Programs
4. Programs → Clone Program

**Python**:
```python
client = HypertroQClient()
client.login("user@example.com", "Pass123!")

# Semantic search
arm_exercises = client.search_exercises("exercises for bigger arms", limit=5)

# Clone existing program
programs = client.list_programs(limit=1)
program_id = programs['data'][0]['id']
cloned = client.clone_program(program_id, "My Modified Program")
```

---

## Testing Tips

### 1. Use Variables

**Postman**: Use `{{variable_name}}` in requests
**Python**: Store IDs in variables
**cURL**: Use shell variables `$VARIABLE_NAME`

### 2. Check Response Status

**Postman**: Check status code in response (200, 201, 401, etc.)
**Python**: Use try/except for error handling
**cURL**: Add `-w "\nStatus: %{http_code}\n"` to see status

### 3. Debug Requests

**Postman**: Use Console (View → Show Postman Console)
**Python**: Add `print()` statements or use debugger
**cURL**: Add `-v` flag for verbose output

---

## Troubleshooting

### Problem: "Connection refused"

**Solution**: Make sure the API server is running
```bash
# Start server
cd ../
poetry run uvicorn app.main:app --reload
```

### Problem: "401 Unauthorized"

**Solution**: Check if token is valid
- Token might have expired (default: 15 minutes)
- Use refresh token endpoint
- Or login again

### Problem: "403 Forbidden (Pro tier required)"

**Solution**: Custom exercises require Pro subscription
- Use global exercises instead
- Or upgrade account tier (via admin or payment)

### Problem: "404 Not Found"

**Solution**: Verify the resource ID exists
- Check if exercise/program ID is correct
- Resource might have been deleted
- Ensure proper UUID format

---

## Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Reference**: See `docs/API.md`
- **Development Guide**: See `docs/DEVELOPMENT.md`

---

## Contributing Examples

Have a useful example? Please contribute!

1. Add your example to this folder
2. Update this README
3. Submit a pull request

Example ideas:
- TypeScript/JavaScript client
- Go client
- Integration with specific frameworks
- CI/CD pipeline examples
- Automated testing scripts

---

**Happy coding! 🚀**
