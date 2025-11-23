"""
HypertroQ Backend - Python Client Example

Complete Python client for interacting with HypertroQ API.
Demonstrates authentication, exercise management, and program creation.

Requirements:
    pip install requests python-dotenv

Usage:
    # Set credentials via environment variables (recommended)
    export DEMO_EMAIL="your-email@example.com"
    export DEMO_PASSWORD="YourSecurePassword!"
    
    # Or on Windows PowerShell:
    $env:DEMO_EMAIL="your-email@example.com"
    $env:DEMO_PASSWORD="YourSecurePassword!"
    
    # Run the example
    python python_client.py

Security:
    ⚠️  NEVER hardcode credentials in production code!
    ⚠️  Always use environment variables or secure secret management
    ⚠️  The demo credentials in this file are for example purposes only
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import json


class HypertroQClient:
    """
    Python client for HypertroQ Backend API.
    
    Handles authentication, request retries, and error handling.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
        """
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()
        
    def _get_headers(self, authenticated: bool = True) -> Dict[str, str]:
        """Get request headers with optional authentication."""
        headers = {"Content-Type": "application/json"}
        
        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
            
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_data = response.json() if response.content else {}
            print(f"❌ API Error ({response.status_code}): {error_data.get('detail', str(e))}")
            raise
    
    # ==================== Authentication ====================
    
    def register(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            email: User email address
            password: User password (min 8 characters)
            full_name: User's full name
            
        Returns:
            Dict containing access_token, refresh_token, and user data
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            headers=self._get_headers(authenticated=False),
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        
        data = self._handle_response(response)
        
        # Store tokens
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        
        print(f"✅ Registered user: {data['user']['email']}")
        return data
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login with email and password.
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            Dict containing access_token, refresh_token, and user data
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            headers=self._get_headers(authenticated=False),
            json={
                "email": email,
                "password": password
            }
        )
        
        data = self._handle_response(response)
        
        # Store tokens
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        
        print(f"✅ Logged in as: {data['user']['email']}")
        return data
    
    def refresh_access_token(self) -> str:
        """
        Refresh the access token using refresh token.
        
        Returns:
            New access token
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/refresh",
            headers=self._get_headers(authenticated=False),
            json={"refresh_token": self.refresh_token}
        )
        
        data = self._handle_response(response)
        self.access_token = data.get("access_token")
        
        print("✅ Access token refreshed")
        return self.access_token
    
    def logout(self) -> None:
        """Logout and invalidate refresh token."""
        if not self.refresh_token:
            return
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/logout",
            headers=self._get_headers(),
            json={"refresh_token": self.refresh_token}
        )
        
        self._handle_response(response)
        
        # Clear tokens
        self.access_token = None
        self.refresh_token = None
        
        print("✅ Logged out successfully")
    
    # ==================== Users ====================
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user's profile."""
        response = self.session.get(
            f"{self.base_url}/api/v1/users/me",
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def update_profile(self, full_name: Optional[str] = None, 
                      email: Optional[str] = None) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            full_name: New full name (optional)
            email: New email (optional)
            
        Returns:
            Updated user data
        """
        data = {}
        if full_name:
            data["full_name"] = full_name
        if email:
            data["email"] = email
        
        response = self.session.put(
            f"{self.base_url}/api/v1/users/me",
            headers=self._get_headers(),
            json=data
        )
        
        return self._handle_response(response)
    
    # ==================== Exercises ====================
    
    def list_exercises(self, page: int = 1, limit: int = 20, 
                      search: Optional[str] = None,
                      equipment: Optional[str] = None,
                      muscle_group: Optional[str] = None) -> Dict[str, Any]:
        """
        List exercises with pagination and filters.
        
        Args:
            page: Page number (default: 1)
            limit: Results per page (default: 20, max: 100)
            search: Search by name (optional)
            equipment: Filter by equipment type (optional)
            muscle_group: Filter by muscle group (optional)
            
        Returns:
            Dict with 'data' (list of exercises) and 'meta' (pagination info)
        """
        params = {"page": page, "limit": limit}
        
        if search:
            params["search"] = search
        if equipment:
            params["equipment"] = equipment
        if muscle_group:
            params["muscle_group"] = muscle_group
        
        response = self.session.get(
            f"{self.base_url}/api/v1/exercises",
            headers=self._get_headers(),
            params=params
        )
        
        return self._handle_response(response)
    
    def get_exercise(self, exercise_id: str) -> Dict[str, Any]:
        """Get exercise by ID."""
        response = self.session.get(
            f"{self.base_url}/api/v1/exercises/{exercise_id}",
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def create_custom_exercise(self, name: str, equipment: str,
                              muscle_contributions: Dict[str, float],
                              description: Optional[str] = None,
                              difficulty: str = "INTERMEDIATE") -> Dict[str, Any]:
        """
        Create a custom exercise (requires Pro subscription).
        
        Args:
            name: Exercise name
            equipment: Equipment type (BARBELL, DUMBBELL, etc.)
            muscle_contributions: Dict of muscle groups to contribution (0.25-1.0)
            description: Exercise description (optional)
            difficulty: BEGINNER, INTERMEDIATE, or ADVANCED
            
        Returns:
            Created exercise data
        """
        data = {
            "name": name,
            "equipment": equipment,
            "muscle_contributions": muscle_contributions,
            "difficulty": difficulty
        }
        
        if description:
            data["description"] = description
        
        response = self.session.post(
            f"{self.base_url}/api/v1/exercises",
            headers=self._get_headers(),
            json=data
        )
        
        return self._handle_response(response)
    
    def search_exercises(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search for exercises using AI.
        
        Args:
            query: Natural language query
            limit: Max results
            
        Returns:
            List of semantically similar exercises
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/exercises/search",
            headers=self._get_headers(),
            json={"query": query, "limit": limit}
        )
        
        return self._handle_response(response)
    
    # ==================== Programs ====================
    
    def list_programs(self, page: int = 1, limit: int = 20,
                     structure_type: Optional[str] = None) -> Dict[str, Any]:
        """
        List training programs.
        
        Args:
            page: Page number
            limit: Results per page
            structure_type: WEEKLY or CYCLIC (optional)
            
        Returns:
            Dict with 'data' (list of programs) and 'meta' (pagination info)
        """
        params = {"page": page, "limit": limit}
        
        if structure_type:
            params["structure_type"] = structure_type
        
        response = self.session.get(
            f"{self.base_url}/api/v1/programs",
            headers=self._get_headers(),
            params=params
        )
        
        return self._handle_response(response)
    
    def get_program(self, program_id: str) -> Dict[str, Any]:
        """Get program by ID with sessions and exercises."""
        response = self.session.get(
            f"{self.base_url}/api/v1/programs/{program_id}",
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def create_program(self, name: str, description: str,
                      structure_type: str, frequency: int,
                      sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a training program.
        
        Args:
            name: Program name
            description: Program description
            structure_type: WEEKLY or CYCLIC
            frequency: Training days per week
            sessions: List of workout sessions with exercises
            
        Returns:
            Created program data
        """
        data = {
            "name": name,
            "description": description,
            "structure_type": structure_type,
            "frequency": frequency,
            "sessions": sessions
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/programs",
            headers=self._get_headers(),
            json=data
        )
        
        return self._handle_response(response)
    
    def calculate_program_volume(self, program_id: str) -> Dict[str, Any]:
        """
        Calculate volume per muscle group for a program.
        
        Returns:
            Dict with volume_per_muscle and warnings
        """
        response = self.session.get(
            f"{self.base_url}/api/v1/programs/{program_id}/volume",
            headers=self._get_headers()
        )
        
        return self._handle_response(response)
    
    def clone_program(self, program_id: str, new_name: str) -> Dict[str, Any]:
        """Clone an existing program with a new name."""
        response = self.session.post(
            f"{self.base_url}/api/v1/programs/{program_id}/clone",
            headers=self._get_headers(),
            json={"new_name": new_name}
        )
        
        return self._handle_response(response)
    
    # ==================== Health ====================
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(
            f"{self.base_url}/api/v1/health",
            headers=self._get_headers(authenticated=False)
        )
        
        return self._handle_response(response)


# ==================== Example Usage ====================

def main():
    """Example usage of the HypertroQ client."""
    
    # Initialize client
    client = HypertroQClient("http://localhost:8000")
    
    print("\n=== HypertroQ API Client Example ===\n")
    
    # Configuration - Use environment variables in production!
    import os
    from datetime import datetime
    
    # Generate unique email for demo to avoid conflicts
    demo_email = os.getenv("DEMO_EMAIL", f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com")
    demo_password = os.getenv("DEMO_PASSWORD", "ChangeMe123!")  # Change this!
    
    print(f"📧 Using demo email: {demo_email}")
    print("⚠️  For production, set DEMO_EMAIL and DEMO_PASSWORD environment variables\n")
    
    # 1. Check API health
    print("1️⃣ Checking API health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Database: {health['database']}")
    print(f"   Redis: {health['redis']}\n")
    
    # 2. Register or login
    print("2️⃣ Authenticating...")
    try:
        client.register(
            email=demo_email,
            password=demo_password,
            full_name="Demo User"
        )
    except requests.exceptions.HTTPError:
        # User already exists, login instead
        client.login(
            email=demo_email,
            password=demo_password
        )
    print()
    
    # 3. Get current user
    print("3️⃣ Getting user profile...")
    user = client.get_current_user()
    print(f"   User: {user['full_name']} ({user['email']})")
    print(f"   Tier: {user['subscription_tier']}")
    print(f"   AI Queries: {user['ai_queries_used']}/{user['ai_queries_limit'] or '∞'}\n")
    
    # 4. List exercises
    print("4️⃣ Listing chest exercises...")
    exercises = client.list_exercises(
        page=1,
        limit=5,
        muscle_group="CHEST"
    )
    print(f"   Found {exercises['meta']['total']} total exercises")
    for ex in exercises['data'][:3]:
        print(f"   - {ex['name']} ({ex['equipment']})")
    print()
    
    # 5. Search exercises semantically
    print("5️⃣ Searching for arm exercises...")
    results = client.search_exercises("exercises for building bigger arms", limit=3)
    for ex in results:
        print(f"   - {ex['name']}")
    print()
    
    # 6. Get first exercise ID for program creation
    exercise_id = exercises['data'][0]['id']
    
    # 7. Create a simple program
    print("6️⃣ Creating training program...")
    program = client.create_program(
        name="Demo Push/Pull Split",
        description="Simple 2-day push/pull program",
        structure_type="WEEKLY",
        frequency=2,
        sessions=[
            {
                "name": "Push Day",
                "day_of_week": 0,  # Monday
                "exercises": [
                    {
                        "exercise_id": exercise_id,
                        "sets": 4,
                        "reps": "8-12",
                        "rest_seconds": 90
                    }
                ]
            },
            {
                "name": "Pull Day",
                "day_of_week": 2,  # Wednesday
                "exercises": [
                    {
                        "exercise_id": exercise_id,
                        "sets": 4,
                        "reps": "8-12",
                        "rest_seconds": 90
                    }
                ]
            }
        ]
    )
    print(f"   Created: {program['name']}")
    print(f"   Sessions: {program['sessions_count']}\n")
    
    # 8. Calculate volume
    print("7️⃣ Calculating training volume...")
    volume = client.calculate_program_volume(program['id'])
    print("   Volume per muscle group:")
    for muscle, sets in volume['volume_per_muscle'].items():
        print(f"   - {muscle}: {sets} sets/week")
    
    if volume.get('warnings'):
        print("\n   ⚠️  Warnings:")
        for warning in volume['warnings']:
            print(f"   - {warning['muscle']}: {warning['recommendation']}")
    print()
    
    # 9. Logout
    print("8️⃣ Logging out...")
    client.logout()
    
    print("\n✅ Example completed successfully!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
