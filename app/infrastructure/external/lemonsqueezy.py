"""LemonSqueezy payment service integration."""
import httpx
from app.core.config import settings


class LemonSqueezyService:
    """Service for interacting with LemonSqueezy payment API."""

    BASE_URL = "https://api.lemonsqueezy.com/v1"

    def __init__(self) -> None:
        """Initialize LemonSqueezy service."""
        self.api_key = settings.LEMONSQUEEZY_API_KEY
        self.store_id = settings.LEMONSQUEEZY_STORE_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    async def create_checkout(
        self,
        product_id: str,
        customer_email: str,
        custom_data: dict | None = None
    ) -> dict:
        """Create a checkout session."""
        async with httpx.AsyncClient() as client:
            data = {
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "email": customer_email,
                            "custom": custom_data or {},
                        }
                    },
                    "relationships": {
                        "store": {
                            "data": {
                                "type": "stores",
                                "id": self.store_id
                            }
                        },
                        "variant": {
                            "data": {
                                "type": "variants",
                                "id": product_id
                            }
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{self.BASE_URL}/checkouts",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_order(self, order_id: str) -> dict:
        """Get order details."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/orders/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify LemonSqueezy webhook signature."""
        # TODO: Implement webhook signature verification
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            settings.LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


# Global LemonSqueezy service instance
lemonsqueezy_service = LemonSqueezyService()
