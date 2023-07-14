import httpx
import json


async def verify_email(email: str, api_key: str):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        response_json = json.loads(response.text)
        if "status" not in response_json["data"] or response_json["data"]["status"] is None:
            return None
        else:
            return response_json["data"]["status"]


async def enrich_email(email: str, api_key: str):
    url = f"https://person.clearbit.com/v2/combined/find?email={email}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("person", {})
    except Exception:
        return None
