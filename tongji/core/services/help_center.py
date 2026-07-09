"""Help centre / support page services.

Ref: Browser scan of /helpCenter page, 2026-07-09.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def find_user_group_list(client: RawOneClient) -> Any:
    """Query the user-group lookup list used on the help-centre page.

    Returns a flat list of 230+ user-group entries (college admins, etc.).

    Ref: POST /api/userservice/userGroup/findUserGroupList
    """
    return await client.request(
        "POST",
        "/api/userservice/userGroup/findUserGroupList",
        data={},
    )


async def list_all_help(client: RawOneClient) -> Any:
    """Query the full help-centre article listing.

    Returns a paginated dict with ``list`` of help articles.

    Ref: POST /api/commonservice/helpCenter/listAllHelp
    """
    return await client.request(
        "POST",
        "/api/commonservice/helpCenter/listAllHelp",
        data={},
    )
