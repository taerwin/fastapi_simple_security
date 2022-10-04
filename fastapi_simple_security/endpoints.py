from typing import List, Optional
import os

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from fastapi_simple_security._security_secret import secret_based_security
from fastapi_simple_security._sqlite_access import sqlite_access

api_key_router = APIRouter()

show_endpoints = False if "FASTAPI_SIMPLE_SECURITY_HIDE_DOCS" in os.environ else True

@api_key_router.get("/new", dependencies=[Depends(secret_based_security)], include_in_schema=show_endpoints)
def get_new_api_key(
    never_expires: bool = Query(False, description="if set, the created API key will never be considered expired"), 
    account_name: Optional[str] = Query(default="Not Provided", description="if set, creates a field in the database table that corresponds to the account/client who utilizes the API Key.")
    ) -> str:
    """
    Args:
        never_expires: if set, the created API key will never be considered expired
        account_name: if set, creates a field in the database table that corresponds to the account/client who utilizes the API Key.
    Returns:
        api_key: a newly generated API key
    """
    return sqlite_access.create_key(never_expires, account_name)


@api_key_router.get("/revoke", dependencies=[Depends(secret_based_security)], include_in_schema=show_endpoints)
def revoke_api_key(api_key: str = Query(..., description="the api_key to revoke")):
    """
    Revokes the usage of the given API key

    """
    return sqlite_access.revoke_key(api_key)


@api_key_router.get("/renew", dependencies=[Depends(secret_based_security)], include_in_schema=show_endpoints)
def renew_api_key(api_key: str=Query(..., description="the API key to renew"),
                  expiration_date: str = Query(None, description="the new expiration date in ISO format")):
    """
    Renews the chosen API key, reactivating it if it was revoked.

    """
    return sqlite_access.renew_key(api_key, expiration_date)


class UsageLog(BaseModel):
    api_key: str
    is_active: bool
    never_expire: bool
    account_name: str
    expiration_date: str
    latest_query_date: Optional[str]
    total_queries: int


class UsageLogs(BaseModel):
    logs: List[UsageLog]


@api_key_router.get(
    "/logs", dependencies=[Depends(secret_based_security)], response_model=UsageLogs, include_in_schema=show_endpoints
)
def get_api_key_usage_logs():
    """
    Returns usage information for all API keys
    """
    # TODO Add some sort of filtering on older keys/unused keys?

    return UsageLogs(
        logs=[
            UsageLog(
                api_key=row[0],
                is_active=row[1],
                never_expire=row[2],
                account_name=row[3],
                expiration_date=row[4],
                latest_query_date=row[5],
                total_queries=row[6],
            )
            for row in sqlite_access.get_usage_stats()
        ]
    )
