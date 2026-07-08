"""AI Intelligence Center — предиктивная аналитика и раннее предупреждение.

Модуль реализует ядро системы поддержки управленческих решений MedHubHAQ:
никакой синтетики в рантайме — все показатели считаются по реальным данным
обращений (таблица appeals) и мониторинга соцсетей (social_posts).

Возможности:
* Национальный индекс риска здравоохранения (0–100) по республике и регионам;
* Прогноз потока обращений на 7 дней (линейный тренд + недельная сезонность
  + доверительный интервал по остаткам регрессии);
* Раннее предупреждение и детекция кризисов (всплески, дефицит лекарств,
  инфекционные очаги, нарушения SLA, перегрузка больниц, соц. резонанс);
* Рекомендации по каждому сигналу;
* Сравнение регионов (лучшие/худшие/динамика).

LLM используется только для «AI Executive Copilot» (текстовый брифинг);
все числовые показатели детерминированы и воспроизводимы.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.categories import CATEGORY_SLA_HOURS
from app.models.appeal import Appeal
from app.models.social import SocialPost
from app.models.tenant import Hospital

_CLOSED = ("resolved", "rejected")

# Веса компонентов индекса риска (в сумме = 1.0).
RISK_WEIGHTS: dict[str, float] = {
    "critical": 0.26,
    "growth": 0.18,
    "sla": 0.16,
    "medicine": 0.12,
    "campaign": 0.10,
    "social": 0.10,
    "duplicate": 0.08,
}

# Пороги нормализации компонентов (значение, при котором компонент = 1.0).
_NORM = {
    "critical": 0.15,   # доля критичных обращений
    "growth": 1.0,      # относительный рост потока (×2 к прошлой неделе)
    "sla": 0.40,        # доля нарушений SLA среди открытых
    "medicine": 0.35,   # доля обращений по лекарствам
    "campaign": 3.0,    # число активных кампаний
    "social": 0.70,     # доля негативных постов в соцсетях
    "duplicate": 0.30,  # доля дубликатов
}

RISK_COMPONENT_LABELS = {
    "critical": "Критические обращения",
    "growth": "Рост потока обращений",
    "sla": "Нарушения SLA",
    "medicine": "Дефицит лекарств",
    "campaign": "Скоординированные кампании",
    "social": "Негатив в соцсетях",
    "duplicate": "Дубликаты обращений",
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _cap_pct(value: float, ceiling: float = 300.0) -> float:
    """Ограничивает процент роста: при разреженной базе (почти ноль) относительные
    изменения раздуваются и вводят в заблуждение, поэтому показываем правдоподобный
    потолок."""
    return max(-100.0, min(ceiling, value))


def _risk_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "elevated"
    if score >= 20:
        return "moderate"
    return "low"


def _sla_hours_case():
    """SQL CASE: срок SLA (в часах) в зависимости от категории обращения."""
    whens = [(Appeal.category == cat, hours) for cat, hours in CATEGORY_SLA_HOURS.items()]
    return case(*whens, else_=72)


# ============================================================
# Временные ряды и статистика
# ============================================================


def _linreg(y: list[float]) -> tuple[float, float, float, float]:
    """Простая линейная регрессия по индексам 0..n-1.

    Возвращает (intercept, slope, r2, residual_std).
    """
    n = len(y)
    if n < 2:
        base = y[-1] if y else 0.0
        return base, 0.0, 0.0, 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(y) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((xs[i] - mx) * (y[i] - my) for i in range(n))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    ss_tot = sum((v - my) ** 2 for v in y)
    residuals = [y[i] - (intercept + slope * xs[i]) for i in range(n)]
    ss_res = sum(r ** 2 for r in residuals)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    resid_std = math.sqrt(ss_res / max(1, n - 2))
    return intercept, slope, _clamp(r2), resid_std


async def _daily_series(
    db: AsyncSession, since: datetime, *, critical_only: bool = False
) -> dict[date, int]:
    conds = [Appeal.submitted_at >= since]
    if critical_only:
        conds.append(Appeal.risk_level == "critical")
    day = func.date_trunc("day", Appeal.submitted_at).label("day")
    rows = (
        await db.execute(
            select(day, func.count(Appeal.id)).where(*conds).group_by(day).order_by(day)
        )
    ).all()
    return {row.day.date(): int(row[1]) for row in rows}


def _fill(series: dict[date, int], start: date, end: date) -> list[int]:
    out: list[int] = []
    cur = start
    while cur <= end:
        out.append(series.get(cur, 0))
        cur += timedelta(days=1)
    return out


# ============================================================
# Прогноз потока обращений
# ============================================================


@dataclass
class ForecastPoint:
    day: str
    predicted: float
    lower: float
    upper: float
    is_forecast: bool


@dataclass
class ForecastDriver:
    scope: str            # "region" | "category"
    key: str
    label: str
    region: str | None
    expected_next: int
    change_pct: float
    confidence: float
    direction: str        # up | down | stable


async def forecast(
    db: AsyncSession, horizon_days: int = 7, history_days: int = 60
) -> dict:
    now = datetime.utcnow()
    today = now.date()
    start = today - timedelta(days=history_days - 1)
    since = datetime.combine(start, datetime.min.time())

    series = await _daily_series(db, since)
    crit_series = await _daily_series(db, since, critical_only=True)
    y = [float(v) for v in _fill(series, start, today)]
    yc = [float(v) for v in _fill(crit_series, start, today)]

    intercept, slope, r2, resid_std = _linreg(y)
    n = len(y)

    # Недельная сезонность: коэффициент по дню недели.
    overall = sum(y) / n if n else 0.0
    wd_sum: dict[int, float] = {}
    wd_cnt: dict[int, int] = {}
    for i, val in enumerate(y):
        wd = (start + timedelta(days=i)).weekday()
        wd_sum[wd] = wd_sum.get(wd, 0.0) + val
        wd_cnt[wd] = wd_cnt.get(wd, 0) + 1
    wd_factor = {
        wd: (wd_sum[wd] / wd_cnt[wd] / overall if overall else 1.0)
        for wd in wd_sum
    }

    crit_ratio = (sum(yc) / sum(y)) if sum(y) else 0.0
    z = 1.28  # ~80% доверительный интервал

    points: list[ForecastPoint] = []
    # Исторические точки (для непрерывного графика).
    for i, val in enumerate(y):
        d = start + timedelta(days=i)
        points.append(ForecastPoint(d.isoformat(), round(val, 1), round(val, 1), round(val, 1), False))
    # Прогнозные точки.
    forecast_vals: list[float] = []
    for t in range(1, horizon_days + 1):
        d = today + timedelta(days=t)
        base = max(0.0, intercept + slope * (n - 1 + t))
        pred = base * wd_factor.get(d.weekday(), 1.0)
        margin = z * resid_std
        forecast_vals.append(pred)
        points.append(
            ForecastPoint(
                d.isoformat(),
                round(pred, 1),
                round(max(0.0, pred - margin), 1),
                round(pred + margin, 1),
                True,
            )
        )

    recent7 = sum(y[-7:])
    expected7 = sum(forecast_vals)
    total_change = ((expected7 - recent7) / recent7 * 100) if recent7 else 0.0
    volume_conf = _clamp(sum(y) / 120.0)
    confidence = round(_clamp(0.35 + 0.4 * r2 + 0.25 * volume_conf), 2)

    drivers = await _forecast_drivers(db, today, horizon_days)

    return {
        "generated_at": now,
        "horizon_days": horizon_days,
        "series": [p.__dict__ for p in points],
        "expected_total": round(expected7, 1),
        "expected_change_pct": round(total_change, 1),
        "expected_critical": round(expected7 * crit_ratio, 1),
        "confidence": confidence,
        "trend": "up" if slope > 0.05 else "down" if slope < -0.05 else "stable",
        "drivers": [d.__dict__ for d in drivers],
    }


async def _window_counts(
    db: AsyncSession, group, start: datetime, end: datetime
) -> dict:
    rows = (
        await db.execute(
            select(group, func.count(Appeal.id))
            .where(Appeal.submitted_at >= start, Appeal.submitted_at < end)
            .group_by(group)
        )
    ).all()
    return {row[0]: int(row[1]) for row in rows}


async def _forecast_drivers(
    db: AsyncSession, today: date, horizon: int
) -> list[ForecastDriver]:
    """Регионы и категории с наибольшим ожидаемым изменением потока.

    Базовый прогноз — персистентность последних 7 дней; тренд оценивается
    сравнением с предыдущими 7 днями (velocity).
    """
    now = datetime.combine(today, datetime.min.time()) + timedelta(days=1)
    recent_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)

    drivers: list[ForecastDriver] = []
    for scope, group, labeler in (
        ("region", Appeal.region, lambda k: k),
        ("category", Appeal.category, _category_label),
    ):
        recent = await _window_counts(db, group, recent_start, now)
        prev = await _window_counts(db, group, prev_start, recent_start)
        for key, rec in recent.items():
            if rec < 3:  # отсекаем шум малых объёмов
                continue
            base = prev.get(key, 0)
            # Если базовый период был почти пустым, сообщаем о новой активности
            # вместо экстремального процента, который вводит в заблуждение.
            if base == 0:
                change = 100.0  # "новая активность" — осторожная оценка
                direction = "up"
            else:
                change = (rec - base) / base * 100
                direction = "up" if change > 10 else "down" if change < -10 else "stable"
            confidence = round(_clamp(0.4 + 0.5 * _clamp(rec / 20.0)), 2)
            drivers.append(
                ForecastDriver(
                    scope=scope,
                    key=str(key),
                    label=labeler(key),
                    region=key if scope == "region" else None,
                    expected_next=rec,
                    change_pct=round(_cap_pct(change, 150.0), 1),
                    confidence=confidence,
                    direction=direction,
                )
            )
    drivers.sort(key=lambda d: abs(d.change_pct) * d.expected_next, reverse=True)
    return drivers[:8]


# ============================================================
# Индекс риска здравоохранения
# ============================================================


@dataclass
class RiskComponent:
    key: str
    label: str
    value: float          # нормализованный 0..1
    contribution: float   # вклад в итоговый балл


@dataclass
class RiskScore:
    scope: str
    key: str
    label: str
    score: float
    level: str
    total_appeals: int
    components: list[RiskComponent] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    growth_pct: float = 0.0


def _score_from_components(norms: dict[str, float]) -> tuple[float, list[RiskComponent]]:
    components: list[RiskComponent] = []
    score = 0.0
    for key, weight in RISK_WEIGHTS.items():
        value = _clamp(norms.get(key, 0.0))
        contribution = weight * value * 100
        score += contribution
        components.append(
            RiskComponent(key, RISK_COMPONENT_LABELS[key], round(value, 2), round(contribution, 1))
        )
    components.sort(key=lambda c: c.contribution, reverse=True)
    return round(score, 1), components


def _reasons_from(components: list[RiskComponent], growth_pct: float) -> list[str]:
    reasons: list[str] = []
    for c in components[:3]:
        if c.contribution < 3:
            continue
        if c.key == "critical":
            reasons.append(f"Высокая доля критических обращений")
        elif c.key == "growth":
            reasons.append(f"Рост потока обращений на {growth_pct:.0f}% за неделю")
        elif c.key == "sla":
            reasons.append("Значительная доля нарушений сроков (SLA)")
        elif c.key == "medicine":
            reasons.append("Повышенная нагрузка по лекарственному обеспечению")
        elif c.key == "campaign":
            reasons.append("Обнаружены скоординированные кампании обращений")
        elif c.key == "social":
            reasons.append("Негативный резонанс в социальных сетях")
        elif c.key == "duplicate":
            reasons.append("Высокая доля повторных/дублирующих обращений")
    return reasons


async def _social_negative_by_region(db: AsyncSession, since: datetime) -> dict:
    rows = (
        await db.execute(
            select(
                SocialPost.region,
                func.count(SocialPost.id),
                func.sum(
                    case((SocialPost.sentiment.in_(("negative", "alarming")), 1), else_=0)
                ),
            )
            .where(SocialPost.post_date >= since)
            .group_by(SocialPost.region)
        )
    ).all()
    return {row[0]: (int(row[1]), int(row[2] or 0)) for row in rows if row[0]}


async def risk_index(db: AsyncSession, window_days: int = 14) -> dict:
    now = datetime.utcnow()
    since = now - timedelta(days=window_days)
    recent_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)

    # Групповые агрегаты по регионам за окно.
    rows = (
        await db.execute(
            select(
                Appeal.region,
                func.count(Appeal.id).label("total"),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)).label("critical"),
                func.sum(case((Appeal.category == "medicines", 1), else_=0)).label("medicine"),
                func.sum(case((Appeal.status == "duplicate", 1), else_=0)).label("duplicate"),
                func.sum(case((Appeal.is_campaign.is_(True), 1), else_=0)).label("campaign"),
            )
            .where(Appeal.submitted_at >= since)
            .group_by(Appeal.region)
        )
    ).all()

    # Открытые обращения и нарушения SLA по регионам.
    age_hours = (func.extract("epoch", func.now()) - func.extract("epoch", Appeal.submitted_at)) / 3600.0
    open_rows = (
        await db.execute(
            select(
                Appeal.region,
                func.count(Appeal.id).label("open"),
                func.sum(case((age_hours > _sla_hours_case(), 1), else_=0)).label("sla"),
            )
            .where(Appeal.status.notin_(_CLOSED))
            .group_by(Appeal.region)
        )
    ).all()
    open_map = {r.region: (int(r.open), int(r.sla or 0)) for r in open_rows}

    recent = await _window_counts(db, Appeal.region, recent_start, now)
    prev = await _window_counts(db, Appeal.region, prev_start, recent_start)
    social = await _social_negative_by_region(db, since)

    regions: list[RiskScore] = []
    nat = {"total": 0, "critical": 0, "medicine": 0, "duplicate": 0, "campaign": 0,
           "open": 0, "sla": 0, "recent": 0, "prev": 0, "soc_total": 0, "soc_neg": 0}

    for row in rows:
        region = row.region
        total = int(row.total)
        openc, sla = open_map.get(region, (0, 0))
        rec, prv = recent.get(region, 0), prev.get(region, 0)
        soc_total, soc_neg = social.get(region, (0, 0))
        # При пустом базовом периоде (было загружено недавно) используем
        # консервативный рост (новая активность), а не экстремальный процент.
        if prv == 0:
            growth = 0.5 if rec > 0 else 0.0  # 50% — новая активность
        else:
            growth = (rec - prv) / prv

        norms = {
            "critical": int(row.critical) / total / _NORM["critical"] if total else 0.0,
            "growth": growth / _NORM["growth"],
            "sla": (sla / openc / _NORM["sla"]) if openc else 0.0,
            "medicine": int(row.medicine) / total / _NORM["medicine"] if total else 0.0,
            "campaign": int(row.campaign) / _NORM["campaign"],
            "social": (soc_neg / soc_total / _NORM["social"]) if soc_total else 0.0,
            "duplicate": int(row.duplicate) / total / _NORM["duplicate"] if total else 0.0,
        }
        score, components = _score_from_components(norms)
        regions.append(
            RiskScore(
                scope="region", key=region, label=region, score=score,
                level=_risk_level(score), total_appeals=total, components=components,
                reasons=_reasons_from(components, _cap_pct(growth * 100, 150.0)), growth_pct=round(_cap_pct(growth * 100, 150.0), 1),
            )
        )
        for k, v in (("total", total), ("critical", int(row.critical)), ("medicine", int(row.medicine)),
                     ("duplicate", int(row.duplicate)), ("campaign", int(row.campaign)),
                     ("open", openc), ("sla", sla), ("recent", rec), ("prev", prv),
                     ("soc_total", soc_total), ("soc_neg", soc_neg)):
            nat[k] += v

    regions.sort(key=lambda r: r.score, reverse=True)

    # Республиканский агрегат — та же логика.
    n_total = nat["total"] or 1
    if nat['prev'] == 0:
        n_growth = 0.5 if nat['recent'] > 0 else 0.0
    else:
        n_growth = (nat['recent'] - nat['prev']) / nat['prev']
    nat_norms = {
        "critical": nat["critical"] / n_total / _NORM["critical"],
        "growth": n_growth / _NORM["growth"],
        "sla": (nat["sla"] / nat["open"] / _NORM["sla"]) if nat["open"] else 0.0,
        "medicine": nat["medicine"] / n_total / _NORM["medicine"],
        "campaign": nat["campaign"] / (_NORM["campaign"] * 3),
        "social": (nat["soc_neg"] / nat["soc_total"] / _NORM["social"]) if nat["soc_total"] else 0.0,
        "duplicate": nat["duplicate"] / n_total / _NORM["duplicate"],
    }
    nat_score, nat_components = _score_from_components(nat_norms)
    national = RiskScore(
        scope="republic", key="KZ", label="Республика Казахстан", score=nat_score,
        level=_risk_level(nat_score), total_appeals=nat["total"], components=nat_components,
        reasons=_reasons_from(nat_components, _cap_pct(n_growth * 100, 150.0)), growth_pct=round(_cap_pct(n_growth * 100, 150.0), 1),
    )

    return {
        "generated_at": now,
        "national": _score_dict(national),
        "regions": [_score_dict(r) for r in regions],
    }


def _score_dict(rs: RiskScore) -> dict:
    return {
        "scope": rs.scope, "key": rs.key, "label": rs.label, "score": rs.score,
        "level": rs.level, "total_appeals": rs.total_appeals, "growth_pct": rs.growth_pct,
        "components": [c.__dict__ for c in rs.components], "reasons": rs.reasons,
    }


# ============================================================
# Раннее предупреждение и детекция кризисов
# ============================================================

RECOMMENDATIONS: dict[str, list[str]] = {
    "spike": [
        "Усилить дежурную смену в профильном подразделении",
        "Подготовить типовой ответ и FAQ для снижения нагрузки",
        "Проинформировать руководство региона о всплеске",
    ],
    "medicine": [
        "Проверить остатки на складе и в аптеках региона",
        "Инициировать экстренную поставку/перераспределение запасов",
        "Эскалировать в службу лекарственного обеспечения и закупки",
    ],
    "outbreak": [
        "Немедленно уведомить санитарно-эпидемиологическую службу",
        "Ввести противоэпидемические меры в затронутом учреждении",
        "Организовать проверку и лабораторный контроль",
    ],
    "sla": [
        "Перераспределить нагрузку между операторами",
        "Приоритизировать просроченные обращения",
        "Проверить причины задержек в ответственном подразделении",
    ],
    "hospital_overload": [
        "Рассмотреть перенаправление пациентопотока в соседние учреждения",
        "Усилить кадровый ресурс перегруженной больницы",
        "Проверить обеспеченность койками и оборудованием",
    ],
    "resonance": [
        "Подготовить официальную коммуникацию по проблеме",
        "Скоординировать ответ пресс-службы и профильного подразделения",
        "Отслеживать динамику соцсетей в реальном времени",
    ],
}

SIGNAL_TITLES = {
    "spike": "Всплеск обращений",
    "medicine": "Риск дефицита лекарств",
    "outbreak": "Санитарно-эпидемиологический риск",
    "sla": "Рост нарушений SLA",
    "hospital_overload": "Перегрузка больницы",
    "resonance": "Социальный резонанс",
}


def _severity(magnitude: float) -> str:
    if magnitude >= 3.0:
        return "critical"
    if magnitude >= 2.0:
        return "high"
    if magnitude >= 1.3:
        return "medium"
    return "low"


async def early_warnings(db: AsyncSession) -> list[dict]:
    now = datetime.utcnow()
    recent_start = now - timedelta(days=3)
    baseline_start = now - timedelta(days=17)
    signals: list[dict] = []

    # 1. Всплески по регион×категория (последние 3 дня vs дневная база за 14 дней).
    recent_rows = (
        await db.execute(
            select(Appeal.region, Appeal.category, func.count(Appeal.id))
            .where(Appeal.submitted_at >= recent_start)
            .group_by(Appeal.region, Appeal.category)
        )
    ).all()
    base_rows = (
        await db.execute(
            select(Appeal.region, Appeal.category, func.count(Appeal.id))
            .where(Appeal.submitted_at >= baseline_start, Appeal.submitted_at < recent_start)
            .group_by(Appeal.region, Appeal.category)
        )
    ).all()
    base_map = {(r[0], r[1]): int(r[2]) for r in base_rows}
    for region, category, cnt in recent_rows:
        cnt = int(cnt)
        if cnt < 3:
            continue
        base_daily = base_map.get((region, category), 0) / 14.0
        recent_daily = cnt / 3.0
        if base_daily <= 0:
            magnitude = 3.0 if cnt >= 4 else 1.5
        else:
            magnitude = recent_daily / base_daily
        if magnitude < 1.3:
            continue
        stype = "outbreak" if category == "sanitary" else "medicine" if category == "medicines" else "spike"
        severity = "critical" if stype == "outbreak" and magnitude >= 1.6 else _severity(magnitude)
        signals.append({
            "type": stype,
            "title": f"{SIGNAL_TITLES[stype]}: {_category_label(category)}",
            "scope": region,
            "category": category,
            "severity": severity,
            "confidence": round(_clamp(0.45 + 0.12 * cnt), 2),
            "magnitude": round(magnitude, 2),
            "predicted_impact": (
                f"Прогноз ~{round(recent_daily * 7)} обращений за неделю "
                f"(рост ×{magnitude:.1f} к базовому уровню)"
            ),
            "actions": RECOMMENDATIONS.get(stype, RECOMMENDATIONS["spike"]),
        })

    # 2. Рост нарушений SLA (национально).
    age_hours = (func.extract("epoch", func.now()) - func.extract("epoch", Appeal.submitted_at)) / 3600.0
    sla_open = (
        await db.execute(
            select(func.count(Appeal.id)).where(
                Appeal.status.notin_(_CLOSED), age_hours > _sla_hours_case()
            )
        )
    ).scalar_one()
    total_open = (
        await db.execute(select(func.count(Appeal.id)).where(Appeal.status.notin_(_CLOSED)))
    ).scalar_one()
    if total_open and sla_open / total_open > 0.25 and sla_open >= 5:
        ratio = sla_open / total_open
        signals.append({
            "type": "sla",
            "title": SIGNAL_TITLES["sla"],
            "scope": "Республика",
            "category": None,
            "severity": _severity(1.0 + ratio * 3),
            "confidence": round(_clamp(0.5 + ratio), 2),
            "magnitude": round(ratio, 2),
            "predicted_impact": f"{sla_open} просроченных обращений из {total_open} открытых ({ratio*100:.0f}%)",
            "actions": RECOMMENDATIONS["sla"],
        })

    # 3. Перегрузка больниц (объём + доля критичных).
    hosp_rows = (
        await db.execute(
            select(
                Hospital.name,
                func.count(Appeal.id).label("total"),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)).label("critical"),
            )
            .join(Appeal, Appeal.hospital_id == Hospital.id)
            .where(Appeal.submitted_at >= now - timedelta(days=14))
            .group_by(Hospital.name)
            .having(func.count(Appeal.id) >= 8)
            .order_by(func.count(Appeal.id).desc())
        )
    ).all()
    for name, total, critical in hosp_rows:
        total, critical = int(total), int(critical or 0)
        crit_ratio = critical / total if total else 0.0
        if crit_ratio < 0.12:
            continue
        signals.append({
            "type": "hospital_overload",
            "title": f"{SIGNAL_TITLES['hospital_overload']}: {name}",
            "scope": name,
            "category": None,
            "severity": _severity(1.0 + crit_ratio * 6),
            "confidence": round(_clamp(0.4 + total / 40.0), 2),
            "magnitude": round(crit_ratio, 2),
            "predicted_impact": f"{total} обращений за 14 дней, {critical} критических ({crit_ratio*100:.0f}%)",
            "actions": RECOMMENDATIONS["hospital_overload"],
        })

    # 4. Социальный резонанс (кампании + негатив в соцсетях).
    resonance = await _resonance_signals(db, now)
    signals.extend(resonance)

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    signals.sort(key=lambda s: (order.get(s["severity"], 9), -s["confidence"]))
    return signals


async def _resonance_signals(db: AsyncSession, now: datetime) -> list[dict]:
    rows = (
        await db.execute(
            select(
                SocialPost.region,
                func.count(SocialPost.id).label("total"),
                func.sum(case((SocialPost.sentiment.in_(("negative", "alarming")), 1), else_=0)).label("neg"),
                func.coalesce(func.sum(SocialPost.shares), 0).label("shares"),
            )
            .where(SocialPost.post_date >= now - timedelta(days=7))
            .group_by(SocialPost.region)
            .having(func.count(SocialPost.id) >= 3)
        )
    ).all()
    out: list[dict] = []
    for region, total, neg, shares in rows:
        total, neg, shares = int(total), int(neg or 0), int(shares or 0)
        neg_ratio = neg / total if total else 0.0
        if neg_ratio < 0.5:
            continue
        out.append({
            "type": "resonance",
            "title": f"{SIGNAL_TITLES['resonance']}: {region or 'соцсети'}",
            "scope": region or "Соцсети",
            "category": None,
            "severity": "high" if neg_ratio >= 0.7 and shares > 500 else "medium",
            "confidence": round(_clamp(0.4 + neg_ratio * 0.5), 2),
            "magnitude": round(neg_ratio, 2),
            "predicted_impact": f"{neg} негативных постов из {total}, {shares} репостов за неделю",
            "actions": RECOMMENDATIONS["resonance"],
        })
    return out


# ============================================================
# Сравнение регионов
# ============================================================


async def regional_comparison(db: AsyncSession) -> dict:
    ri = await risk_index(db)
    regions = ri["regions"]

    resolved_rows = (
        await db.execute(
            select(
                Appeal.region,
                func.count(Appeal.id).label("total"),
                func.sum(case((Appeal.status == "resolved", 1), else_=0)).label("resolved"),
            )
            .group_by(Appeal.region)
        )
    ).all()
    resolution = {
        r.region: round(int(r.resolved or 0) / int(r.total) * 100, 1) if r.total else 0.0
        for r in resolved_rows
    }

    ranking = []
    for r in regions:
        ranking.append({
            "region": r["label"],
            "score": r["score"],
            "level": r["level"],
            "total_appeals": r["total_appeals"],
            "growth_pct": r["growth_pct"],
            "resolution_rate": resolution.get(r["key"], 0.0),
        })

    scored = [r for r in ranking if r["total_appeals"] >= 3]
    best = sorted(scored, key=lambda r: r["score"])[:3]
    worst = sorted(scored, key=lambda r: r["score"], reverse=True)[:3]
    improving = sorted(scored, key=lambda r: r["growth_pct"])[:3]
    deteriorating = sorted(scored, key=lambda r: r["growth_pct"], reverse=True)[:3]

    return {
        "generated_at": ri["generated_at"],
        "ranking": ranking,
        "best": best,
        "worst": worst,
        "improving": improving,
        "deteriorating": deteriorating,
    }


# ============================================================
# Контекст для AI Executive Copilot
# ============================================================


async def copilot_context(db: AsyncSession, region: str | None) -> dict:
    ri = await risk_index(db)
    fc = await forecast(db)
    warnings = await early_warnings(db)

    if region:
        region_l = region.lower()
        risk = next((r for r in ri["regions"] if r["label"].lower() == region_l), None)
        warnings = [w for w in warnings if (w.get("scope") or "").lower() == region_l]
        drivers = [d for d in fc["drivers"] if (d.get("region") or "").lower() == region_l
                   or d["scope"] == "category"]
    else:
        risk = ri["national"]
        drivers = fc["drivers"]

    return {
        "region": region or "Республика Казахстан",
        "risk": risk,
        "national": ri["national"],
        "forecast": {
            "expected_total": fc["expected_total"],
            "expected_change_pct": fc["expected_change_pct"],
            "confidence": fc["confidence"],
            "trend": fc["trend"],
        },
        "drivers": drivers[:6],
        "warnings": warnings[:6],
    }


def _category_label(category: str) -> str:
    from app.data.categories import CATEGORY_GROUPS

    return CATEGORY_GROUPS.get(category, {}).get("label", category)
