"""Instagram Graph API (Instagram Business API) — основная интеграция.

Поток:
1. Админ задаёт App ID / App Secret / Business Account ID в админ-панели.
2. OAuth: GET oauth_url → пользователь логинится на facebook.com →
   callback с code → exchange_code() меняет на long-lived token (60 дней).
3. refresh_long_lived_token() продлевает токен до истечения.
4. health_check() проверяет доступность API.

Playwright/логин-пароль/sessionid НЕ используются. Запасной вариант —
публичный парсинг (см. adapters.py), только если Graph API недоступен.
"""
import hmac
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

GRAPH_BASE = "https://graph.facebook.com/v19.0"
OAUTH_DIALOG = "https://www.facebook.com/v19.0/dialog/oauth"

# Минимальный набор прав для комментариев, упоминаний, сообщений и статистики
OAUTH_SCOPES = [
    "instagram_basic",
    "instagram_manage_comments",
    "instagram_manage_messages",
    "instagram_manage_insights",
    "pages_show_list",
    "pages_read_engagement",
]


@dataclass
class TokenResult:
    access_token: str
    expires_at: datetime | None


class InstagramGraphError(RuntimeError):
    pass


def build_oauth_url(app_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": ",".join(OAUTH_SCOPES),
        "response_type": "code",
    }
    return f"{OAUTH_DIALOG}?{urlencode(params)}"


def generate_state() -> str:
    return secrets.token_urlsafe(24)


def appsecret_proof(access_token: str, app_secret: str) -> str:
    return hmac.new(
        app_secret.encode(), access_token.encode(), hashlib.sha256
    ).hexdigest()


async def _get(url: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
    data = resp.json()
    if resp.status_code != 200 or "error" in data:
        message = data.get("error", {}).get("message", resp.text[:200])
        raise InstagramGraphError(f"Instagram Graph API: {message}")
    return data


async def exchange_code(
    app_id: str, app_secret: str, redirect_uri: str, code: str
) -> TokenResult:
    """Код OAuth → краткосрочный токен → долгосрочный токен (60 дней)."""
    short = await _get(
        f"{GRAPH_BASE}/oauth/access_token",
        {
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )
    long_lived = await _get(
        f"{GRAPH_BASE}/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short["access_token"],
        },
    )
    expires_in = int(long_lived.get("expires_in", 60 * 24 * 3600))
    return TokenResult(
        access_token=long_lived["access_token"],
        expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
    )


async def refresh_long_lived_token(
    app_id: str, app_secret: str, access_token: str
) -> TokenResult:
    data = await _get(
        f"{GRAPH_BASE}/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": access_token,
        },
    )
    expires_in = int(data.get("expires_in", 60 * 24 * 3600))
    return TokenResult(
        access_token=data["access_token"],
        expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
    )


async def health_check(access_token: str, app_secret: str, business_account_id: str) -> dict:
    """Проверка: токен валиден и бизнес-аккаунт доступен."""
    data = await _get(
        f"{GRAPH_BASE}/{business_account_id}",
        {
            "fields": "id,username,followers_count,media_count",
            "access_token": access_token,
            "appsecret_proof": appsecret_proof(access_token, app_secret),
        },
    )
    return data


async def fetch_recent_media(
    access_token: str, app_secret: str, business_account_id: str, limit: int = 25
) -> list[dict]:
    """Последние публикации бизнес-аккаунта с метриками."""
    data = await _get(
        f"{GRAPH_BASE}/{business_account_id}/media",
        {
            "fields": "id,caption,permalink,timestamp,like_count,comments_count,media_type",
            "limit": limit,
            "access_token": access_token,
            "appsecret_proof": appsecret_proof(access_token, app_secret),
        },
    )
    return data.get("data", [])


async def fetch_comments(
    access_token: str, app_secret: str, media_id: str, limit: int = 50
) -> list[dict]:
    data = await _get(
        f"{GRAPH_BASE}/{media_id}/comments",
        {
            "fields": "id,text,username,timestamp,like_count",
            "limit": limit,
            "access_token": access_token,
            "appsecret_proof": appsecret_proof(access_token, app_secret),
        },
    )
    return data.get("data", [])


async def fetch_mentions(
    access_token: str, app_secret: str, business_account_id: str, limit: int = 25
) -> list[dict]:
    """Публикации, в которых упомянут аккаунт организации."""
    data = await _get(
        f"{GRAPH_BASE}/{business_account_id}/tags",
        {
            "fields": "id,caption,permalink,timestamp,like_count,comments_count,username",
            "limit": limit,
            "access_token": access_token,
            "appsecret_proof": appsecret_proof(access_token, app_secret),
        },
    )
    return data.get("data", [])


async def fetch_insights(
    access_token: str, app_secret: str, business_account_id: str
) -> dict:
    """Базовая статистика профиля (за последние 30 дней)."""
    data = await _get(
        f"{GRAPH_BASE}/{business_account_id}/insights",
        {
            "metric": "reach,profile_views,accounts_engaged",
            "period": "day",
            "metric_type": "total_value",
            "access_token": access_token,
            "appsecret_proof": appsecret_proof(access_token, app_secret),
        },
    )
    return data
