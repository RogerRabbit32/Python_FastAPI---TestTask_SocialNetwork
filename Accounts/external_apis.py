import httpx
import json

from fastapi import HTTPException


async def verify_email(email: str, api_key: str):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to verify email. {e}")


async def enrich_email(email: str, api_key: str):
    try:
        url = f"https://person.clearbit.com/v2/combined/find?email={email}"
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None
