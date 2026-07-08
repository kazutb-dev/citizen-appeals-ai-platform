"""AI Intelligence Center — эндпоинты предиктивной аналитики и раннего
предупреждения. Все числовые показатели считаются по реальным данным
(app.agents.intelligence); LLM применяется только для текстового брифинга
Executive Copilot и уважает выбранный язык интерфейса.
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import intelligence
from app.agents.llm_client import complete
from app.core.i18n import language_directive, resolve_language
from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/risk-index")
async def risk_index(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> dict:
    return await intelligence.risk_index(db)


@router.get("/forecast")
async def forecast(
    days: int = Query(7, ge=3, le=30),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> dict:
    return await intelligence.forecast(db, horizon_days=days)


@router.get("/early-warning")
async def early_warning(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> dict:
    signals = await intelligence.early_warnings(db)
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for s in signals:
        counts[s["severity"]] = counts.get(s["severity"], 0) + 1
    return {"signals": signals, "counts": counts, "total": len(signals)}


@router.get("/regional-comparison")
async def regional_comparison(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> dict:
    return await intelligence.regional_comparison(db)


COPILOT_SYSTEM = (
    "Ты — AI-советник руководителя системы здравоохранения Республики Казахстан "
    "(MedHubHAQ). Отвечай кратко, структурированно и по-деловому, СТРОГО на основе "
    "приведённых данных, ничего не выдумывая."
)

COPILOT_PROMPT = """Подготовь управленческий брифинг по запросу руководителя.

ОБЛАСТЬ: {region}

ИНДЕКС РИСКА: {risk_score}/100 (уровень: {risk_level}); рост потока {growth_pct}% за неделю.
ГЛАВНЫЕ ФАКТОРЫ РИСКА: {reasons}

ПРОГНОЗ НА НЕДЕЛЮ: ожидается ~{expected_total} обращений ({expected_change_pct}% к прошлой неделе), тренд: {trend}.
ДРАЙВЕРЫ РОСТА: {drivers}

СИГНАЛЫ РАННЕГО ПРЕДУПРЕЖДЕНИЯ:
{warnings}

Сформируй брифинг из 4 блоков (обычный текст, без markdown):
1. Ситуация — что происходит сейчас.
2. Вероятные причины.
3. Прогноз и риски на ближайшую неделю.
4. Рекомендованные действия (3–4 конкретных пункта).
"""


def _fmt_drivers(drivers: list[dict]) -> str:
    if not drivers:
        return "нет значимых драйверов"
    return "; ".join(
        f"{d['label']} {'+' if d['change_pct'] >= 0 else ''}{d['change_pct']:.0f}%"
        for d in drivers[:5]
    )


def _fmt_warnings(warnings: list[dict]) -> str:
    if not warnings:
        return "- активных сигналов нет"
    return "\n".join(
        f"- [{w['severity']}] {w['title']} ({w['scope']}): {w['predicted_impact']}"
        for w in warnings[:6]
    )


@router.get("/copilot")
async def copilot(
    request: Request,
    region: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> dict:
    ctx = await intelligence.copilot_context(db, region)
    risk = ctx["risk"] or {}
    prompt = COPILOT_PROMPT.format(
        region=ctx["region"],
        risk_score=risk.get("score", 0),
        risk_level=risk.get("level", "—"),
        growth_pct=risk.get("growth_pct", 0),
        reasons="; ".join(risk.get("reasons", []) or ["—"]),
        expected_total=ctx["forecast"]["expected_total"],
        expected_change_pct=ctx["forecast"]["expected_change_pct"],
        trend=ctx["forecast"]["trend"],
        drivers=_fmt_drivers(ctx["drivers"]),
        warnings=_fmt_warnings(ctx["warnings"]),
    )
    lang = resolve_language(request)
    briefing: str | None = None
    ai_available = True
    try:
        system = f"{COPILOT_SYSTEM} {language_directive(lang)}"
        briefing = (await complete(prompt, max_tokens=650, system=system)).strip()
    except Exception:  # noqa: BLE001 — LLM недоступен: возвращаем структурный контекст
        ai_available = False

    return {
        "region": ctx["region"],
        "ai_available": ai_available,
        "briefing": briefing,
        "risk": ctx["risk"],
        "forecast": ctx["forecast"],
        "drivers": ctx["drivers"],
        "warnings": ctx["warnings"],
    }
