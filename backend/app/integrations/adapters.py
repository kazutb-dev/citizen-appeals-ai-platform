"""Адаптеры опроса социальных источников.

Каждый адаптер возвращает list[FetchedPost] либо бросает AdapterError с
честным описанием причины (нет ключей, API недоступен). Заглушек и
синтетических данных здесь нет: если платформа не настроена — источник
получает статус not_configured.

Реализовано:
- instagram — Instagram Graph API (основной путь, см. instagram.py);
  публичный парсинг — только запасной вариант, без логина и sessionid.
- telegram  — публичное веб-превью t.me/s/<канал> (без API-ключей).
- youtube   — публичный RSS-фид канала (без API-ключей).
- vk        — VK API (нужен service token в credentials источника).

facebook, tiktok, x — требуют партнёрского доступа к API; адаптеры
сообщают not_configured, пока в credentials не заданы ключи.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from defusedxml import ElementTree  # стойкий к XXE/billion-laughs парсер

USER_AGENT = "Mozilla/5.0 (compatible; KUTB-AppealsBot/1.0)"


class AdapterError(RuntimeError):
    """Опрос невозможен: нет ключей или платформа недоступна."""


@dataclass
class FetchedPost:
    external_id: str
    text: str
    url: str | None
    posted_at: datetime
    author: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    extra: dict = field(default_factory=dict)


async def fetch_telegram_public(channel_url: str, limit: int = 20) -> list[FetchedPost]:
    """Публичное превью канала t.me/s/<имя> — без API-ключей."""
    match = re.search(r"t\.me/(?:s/)?([\w_]+)", channel_url)
    if not match:
        raise AdapterError(f"Не удалось извлечь имя канала из URL: {channel_url}")
    channel = match.group(1)

    async with httpx.AsyncClient(
        timeout=20, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        resp = await client.get(f"https://t.me/s/{channel}")
    if resp.status_code != 200:
        raise AdapterError(f"t.me/s/{channel} вернул HTTP {resp.status_code}")

    html = resp.text
    posts: list[FetchedPost] = []
    # Блоки сообщений в публичном превью
    for block in re.finditer(
        r'data-post="([^"]+)".*?js-message_text[^>]*>(.*?)</div>.*?datetime="([^"]+)"',
        html,
        re.DOTALL,
    ):
        post_id, raw_text, dt = block.group(1), block.group(2), block.group(3)
        text = re.sub(r"<br\s*/?>", "\n", raw_text)
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text:
            continue
        views_match = re.search(
            rf'data-post="{re.escape(post_id)}".*?tgme_widget_message_views[^>]*>([\d.,KM]+)',
            html,
            re.DOTALL,
        )
        posts.append(
            FetchedPost(
                external_id=post_id,
                text=text[:4000],
                url=f"https://t.me/{post_id}",
                posted_at=datetime.fromisoformat(dt.replace("Z", "+00:00")).replace(tzinfo=None),
                author=channel,
                views=_parse_count(views_match.group(1)) if views_match else 0,
            )
        )
    return posts[-limit:]


def _parse_count(value: str) -> int:
    value = value.strip().replace(",", ".")
    if value.endswith("K"):
        return int(float(value[:-1]) * 1000)
    if value.endswith("M"):
        return int(float(value[:-1]) * 1_000_000)
    try:
        return int(float(value))
    except ValueError:
        return 0


async def fetch_youtube_rss(channel_url: str, limit: int = 15) -> list[FetchedPost]:
    """Публичный RSS-фид канала YouTube — без API-ключей."""
    channel_id_match = re.search(r"channel/(UC[\w-]+)", channel_url)
    if channel_id_match:
        feed_url = (
            "https://www.youtube.com/feeds/videos.xml?channel_id="
            + channel_id_match.group(1)
        )
    else:
        handle_match = re.search(r"youtube\.com/(@[\w.-]+)", channel_url)
        if not handle_match:
            raise AdapterError(
                "Для YouTube укажите URL вида youtube.com/channel/UC… или youtube.com/@handle"
            )
        # Для @handle нужно получить channel_id со страницы канала
        async with httpx.AsyncClient(
            timeout=20, headers={"User-Agent": USER_AGENT}, follow_redirects=True
        ) as client:
            resp = await client.get(f"https://www.youtube.com/{handle_match.group(1)}")
        cid = re.search(r'"channelId":"(UC[\w-]+)"', resp.text)
        if not cid:
            raise AdapterError("Не удалось определить channel_id по @handle")
        feed_url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + cid.group(1)

    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": USER_AGENT}) as client:
        resp = await client.get(feed_url)
    if resp.status_code != 200:
        raise AdapterError(f"YouTube RSS вернул HTTP {resp.status_code}")

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "media": "http://search.yahoo.com/mrss/",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }
    root = ElementTree.fromstring(resp.text)
    author = root.findtext("atom:title", default="YouTube", namespaces=ns)
    posts: list[FetchedPost] = []
    for entry in root.findall("atom:entry", ns)[:limit]:
        video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
        title = entry.findtext("atom:title", default="", namespaces=ns)
        description = entry.findtext(
            "media:group/media:description", default="", namespaces=ns
        )
        published = entry.findtext("atom:published", default="", namespaces=ns)
        stats = entry.find("media:group/media:community/media:statistics", ns)
        posts.append(
            FetchedPost(
                external_id=f"yt:{video_id}",
                text=f"{title}\n\n{description}"[:4000],
                url=f"https://www.youtube.com/watch?v={video_id}",
                posted_at=datetime.fromisoformat(published).replace(tzinfo=None)
                if published
                else datetime.utcnow(),
                author=author,
                views=int(stats.get("views", 0)) if stats is not None else 0,
            )
        )
    return posts


async def fetch_vk_wall(source_url: str, credentials: dict, limit: int = 20) -> list[FetchedPost]:
    """Стена сообщества VK через VK API (нужен service/access token)."""
    token = credentials.get("access_token")
    if not token:
        raise AdapterError("Для VK укажите access_token в учётных данных источника")
    domain_match = re.search(r"vk\.com/([\w.]+)", source_url or "")
    if not domain_match:
        raise AdapterError("Укажите URL сообщества вида vk.com/<имя>")

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://api.vk.com/method/wall.get",
            params={
                "domain": domain_match.group(1),
                "count": limit,
                "access_token": token,
                "v": "5.199",
            },
        )
    data = resp.json()
    if "error" in data:
        raise AdapterError(f"VK API: {data['error'].get('error_msg', 'ошибка')}")

    posts: list[FetchedPost] = []
    for item in data.get("response", {}).get("items", []):
        text = (item.get("text") or "").strip()
        if not text:
            continue
        posts.append(
            FetchedPost(
                external_id=f"vk:{item['owner_id']}_{item['id']}",
                text=text[:4000],
                url=f"https://vk.com/wall{item['owner_id']}_{item['id']}",
                posted_at=datetime.utcfromtimestamp(item["date"]),
                author=domain_match.group(1),
                views=item.get("views", {}).get("count", 0),
                likes=item.get("likes", {}).get("count", 0),
                comments=item.get("comments", {}).get("count", 0),
                shares=item.get("reposts", {}).get("count", 0),
            )
        )
    return posts


async def fetch_instagram_public(profile_url: str, limit: int = 12) -> list[FetchedPost]:
    """ЗАПАСНОЙ вариант для Instagram: публичная страница профиля.

    Используется только когда Graph API не настроен. Без логина, без
    sessionid — только общедоступные данные; Instagram может ограничивать
    такие запросы, поэтому ошибки здесь ожидаемы и не критичны.
    """
    match = re.search(r"instagram\.com/([\w._]+)", profile_url or "")
    if not match:
        raise AdapterError("Укажите URL профиля вида instagram.com/<имя>")
    username = match.group(1)

    async with httpx.AsyncClient(
        timeout=20, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        resp = await client.get(
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
            headers={"x-ig-app-id": "936619743392459"},
        )
    if resp.status_code != 200:
        raise AdapterError(
            f"Публичный профиль Instagram недоступен (HTTP {resp.status_code}). "
            "Настройте Instagram Graph API в разделе Интеграции."
        )
    try:
        edges = (
            resp.json()["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
        )
    except (KeyError, ValueError) as exc:
        raise AdapterError("Не удалось разобрать ответ Instagram") from exc

    posts: list[FetchedPost] = []
    for edge in edges[:limit]:
        node = edge["node"]
        captions = node.get("edge_media_to_caption", {}).get("edges", [])
        text = captions[0]["node"]["text"] if captions else ""
        if not text:
            continue
        posts.append(
            FetchedPost(
                external_id=f"ig:{node['id']}",
                text=text[:4000],
                url=f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                posted_at=datetime.utcfromtimestamp(node.get("taken_at_timestamp", 0)),
                author=username,
                likes=node.get("edge_liked_by", {}).get("count", 0),
                comments=node.get("edge_media_to_comment", {}).get("count", 0),
            )
        )
    return posts
