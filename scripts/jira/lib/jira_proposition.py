"""
Proposition-first Jira distill tiers (no LLM).

Knowledge unit = 资格—分支—后果 命题簇, not one ticket.

distill_tier:
  proposition_core   — 须写入 Jira业务规则摘录 正文（代表票 + 分端索引）
  platform_variant   — 同命题分端实现，仅收录代表 KEY +  sibling 列表
  engineering_slice  — Gateway/埋点/映射；仅索引，不并入 _deliver
  cross_theme_ref    — 主命题在他域；本主题只留 KEY 引用
  index_only         — distill_queue 但薄/无 AC，仅遗漏扫描
"""

from __future__ import annotations

import re
from typing import Any, Mapping

# --- tier detection ---
_PLATFORM = re.compile(
    r"\[(ios|android|harmony|h5|iphone)\]|"
    r"\b(ios|android|harmony)\b.*\b(mall|hui)\b",
    re.I,
)
_ENGINEERING = re.compile(
    r"\bcngw\b|\[gw\]|\[gateway\]|data tracking|sensor|埋点|integration of us api|"
    r"plexus|ji guang|jiguang|oracle to sql",
    re.I,
)
_CROSS_THEME_HINTS: dict[str, re.Pattern[str]] = {
    "compensation-cbp": re.compile(
        r"notification|contest|growth trip|user title|registration address", re.I
    ),
    "checkout": re.compile(r"matching bonus|pacesetter|milestone widget|elite bonus", re.I),
    "contests": re.compile(r"matching bonus|promo widget|checkout", re.I),
    "messaging": re.compile(r"pacesetter|milestone|checkout|contest card", re.I),
    "compliance-identity": re.compile(r"promo widget|payment complete", re.I),
}

# Required proposition patterns per confirmed theme (slug, label, regex on normalized summary)
CORE_PROPOSITIONS: dict[str, list[tuple[str, str, re.Pattern[str]]]] = {
    "compensation-cbp": [
        ("matching", "Matching / 客户支持", re.compile(r"matching|客户支持|customer support", re.I)),
        ("pacesetter_home", "Pacesetter 首页", re.compile(r"pacesetter.*(home|widget|challenge)", re.I)),
        ("pacesetter_popup", "Pacesetter 弹窗", re.compile(r"pacesetter.*popup|弹窗", re.I)),
        ("milestone", "Milestone 详情", re.compile(r"milestone", re.I)),
        ("leadership", "Leadership Bonus", re.compile(r"leadership|\blb\b", re.I)),
        ("elite", "Elite Bonus", re.compile(r"elite bonus", re.I)),
        ("pacesetter_after", "达标后首页", re.compile(r"after achieving|pacesetter.*status|达标", re.I)),
        ("qualified_api", "Matching qualified 口径", re.compile(r"integration of us api|qualified", re.I)),
    ],
    "checkout": [
        ("cart_order", "Cart / Place Order", re.compile(r"cart order|place order|pending order", re.I)),
        ("fpv", "FPV 抵扣", re.compile(r"fpv|product coupon|voucher", re.I)),
        ("promo_widget", "Promotool 满赠", re.compile(r"promo widget|满赠|full gift|promotool", re.I)),
        ("alipay_apo", "支付宝 / APO", re.compile(r"alipay|auto payment|auto order|apo", re.I)),
        ("one_click", "一键结算", re.compile(r"一键|go-checkout|pre-sale", re.I)),
        ("payment", "支付完成 / 支付页", re.compile(r"payment complete|payment page|wechat pay", re.I)),
    ],
    "contests": [
        ("contest_card", "竞赛列表卡片", re.compile(r"contest.*card|contest ui", re.I)),
        ("cvp_api", "Contest CVP API", re.compile(r"contest.*cvp|cvp contest", re.I)),
        ("growth_trip", "Growth trip", re.compile(r"growth trip", re.I)),
        ("contest_138", "Contest 138 / health family", re.compile(r"138|health family", re.I)),
    ],
    "compliance-identity": [
        ("privacy_login", "登录隐私勾选", re.compile(r"privacy policy|checkbox.*login", re.I)),
        ("registration_address", "注册地址文案", re.compile(r"registration address|branch.*province", re.I)),
        ("title_display", "职称展示", re.compile(r"title information|user level|职级", re.I)),
        ("pc_enroll", "PC enroll / OE", re.compile(r"pc enroll|online enrollment|invite", re.I)),
        ("phone_login", "Native 登录", re.compile(r"native login|phone number login", re.I)),
    ],
    "messaging": [
        ("notification_center", "通知中心", re.compile(r"notification page|creation of notification", re.I)),
        ("push_deeplink", "推送外链", re.compile(r"notification card|external url|go to the link", re.I)),
        ("sms_bind", "换绑短信授权", re.compile(r"bound mobile|sms receiver|change the bound", re.I)),
        ("jiguang", "极光渠道", re.compile(r"jiguang|channel creation", re.I)),
    ],
    "content-mini-program": [
        ("cms_deps", "CMS / Dependencies", re.compile(r"cms|dependencies|content mini", re.I)),
        ("video_plugin", "视频插件", re.compile(r"video plugin|plugin", re.I)),
    ],
    "cpc-upgrade": [
        ("cpc_flow", "CPC 升级流程", re.compile(r"cpc|preferred customer|upgrade", re.I)),
    ],
    "profile-management": [
        ("profile_edit", "资料编辑", re.compile(r"profile|address|资料", re.I)),
    ],
    "health-evaluation": [
        ("health_quiz", "健康测评", re.compile(r"health evaluation|health quiz|questionnaire", re.I)),
    ],
    "international-wechat": [
        ("intl_poc", "国际微信 POC", re.compile(r"international wechat|oe|poc", re.I)),
    ],
}

# Baby Care root 46333957: 平台命题（非 CMA CBP/checkout 语义）
BC_CORE_PROPOSITIONS: dict[str, list[tuple[str, str, re.Pattern[str]]]] = {
    "china-payments": [
        ("cnps_callback", "CNPS 回调与真实渠道", re.compile(
            r"cnps|china.payment|payment.service|alipay.*placeholder|真实支付|callback", re.I
        )),
        ("unionpay", "银联", re.compile(r"unionpay|银联", re.I)),
        ("auto_alipay", "自动代扣 AO", re.compile(r"auto alipay|auto order|代扣|deduct", re.I)),
        ("inventory", "库存幂等", re.compile(r"inventory|idemkey|扣减|回滚", re.I)),
        ("citcon_pay", "Citcon 收银", re.compile(r"citcon|cbec.*pay|跨境购.*支付", re.I)),
    ],
    "cbec-fulfillment": [
        ("volume_roll", "业绩回卷", re.compile(r"volume roll|业绩回卷|roll.*volume", re.I)),
        ("declare_3pl", "报关与 3PL", re.compile(r"declare_number|3pl|customs|报关|清关", re.I)),
        ("sub_order", "子单策略", re.compile(r"sub.order|子单", re.I)),
    ],
    "cn-contest-service": [
        ("contest_list", "竞赛列表", re.compile(r"contest.*list|/api/contests", re.I)),
        ("contest_apply", "报名与目标级别", re.compile(r"apply|targetlevel|报名", re.I)),
        ("contest_card", "卡片字段", re.compile(r"cardfield|conteststatus|displaytype", re.I)),
    ],
    "convention-ticketing": [
        ("convention_hub", "HUB 分票", re.compile(r"convention|aventri|hub.*assign|大会|票务", re.I)),
        ("odyssey_ticket", "Odyssey 售票", re.compile(r"odyssey.*ticket|售票", re.I)),
    ],
}

# WeChat root 41975816: confirmed propositions differ from CMA (mini-program/Gateway/Hot Fix)
WC_CORE_PROPOSITIONS: dict[str, list[tuple[str, str, re.Pattern[str]]]] = {
    "checkout": [
        ("mini_order", "小程序订单/购物车", re.compile(
            r"cart|order|shopping|结账|place order|miniprogram|mini-program|static-shopping", re.I
        )),
        ("wechat_pay", "微信支付", re.compile(r"wechat pay|payment|收银|pay", re.I)),
        ("pcc_report", "PCC 报表", re.compile(r"pcc", re.I)),
        ("address", "地址/配送", re.compile(r"address|shipping|收货|placement", re.I)),
        ("fpv_coupon", "FPV/优惠", re.compile(r"fpv|coupon|voucher", re.I)),
        ("gateway", "Gateway/部署", re.compile(r"gateway|nested deployment|deploy", re.I)),
    ],
    "messaging": [
        ("hotfix", "Hot Fix", re.compile(r"hot\s*fix", re.I)),
        ("notification", "通知/消息", re.compile(r"notification|消息|notice", re.I)),
        ("subscribe", "订阅消息", re.compile(r"subscribe|订阅", re.I)),
        ("customer_service", "在线客服", re.compile(r"customer service|客服", re.I)),
    ],
    "content-mini-program": [
        ("cms_deps", "CMS / Dependencies", re.compile(r"cms|dependencies|content mini", re.I)),
        ("video_plugin", "视频/插件", re.compile(r"video|plugin|插件|调研", re.I)),
    ],
    "health-evaluation": [
        ("score_aggregate", "综合评分与五维得分", re.compile(
            r"part1|score|综合评分|total score|五部分|各维度总分", re.I
        )),
        ("weight_mgmt", "体重管理", re.compile(
            r"weight management|体重|bmi|体脂|腰围|part2", re.I
        )),
        ("meal_diet", "膳食情况", re.compile(
            r"meal situation|膳食|part3|主食|蔬菜|水果", re.I
        )),
        ("eating_habit", "饮食行为", re.compile(
            r"eating habit|饮食行为|高脂|高糖|高盐|part4", re.I
        )),
        ("lifestyle_sleep", "运动与睡眠压力", re.compile(
            r"life style|lifestyle|health situation|运动|睡眠|压力|part5|part6", re.I
        )),
        ("nutrition_recommend", "营养素与产品推荐", re.compile(
            r"nutrition summary|营养素|recommended|fetch product|part7|营养方案", re.I
        )),
        ("report_integrate", "报告整合与分享", re.compile(
            r"integrate|poster|homepage|报告详情|part8|分享", re.I
        )),
        ("privacy_phi", "隐私与草稿", re.compile(
            r"phi|privacy|隐私|草稿|do not save", re.I
        )),
    ],
}


def propositions_for_theme(theme: str, root_id: str | None = None) -> list[tuple[str, str, re.Pattern[str]]]:
    """Theme → proposition patterns; table selected by team key from team-roots.json."""
    table = CORE_PROPOSITIONS
    team_key: str | None = None
    if root_id:
        try:
            from teams.registry import team_key_for_root_id

            team_key = team_key_for_root_id(str(root_id))
        except ImportError:
            team_key = None
    if team_key == "bc":
        table = BC_CORE_PROPOSITIONS
        if theme in table and table[theme]:
            return table[theme]
        try:
            from teams.registry import jira_theme_to_proposition_slug

            prop = jira_theme_to_proposition_slug(team_key, theme)
            if prop in table and table[prop]:
                return table[prop]
        except ImportError:
            pass
        return []
    if team_key == "wc":
        return WC_CORE_PROPOSITIONS.get(theme, [])
    return CORE_PROPOSITIONS.get(theme, [])


def normalize_summary(summary: str) -> str:
    s = (summary or "").strip()
    s = re.sub(r"\[[^\]]+\]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s[:100]


def proposition_cluster_id(
    primary: str,
    summary: str,
    parent_key: str | None,
    *,
    theme: str | None = None,
    root_id: str | None = None,
) -> str:
    """Stable cluster id for grouping platform duplicates."""
    norm = normalize_summary(summary)
    # match theme core pattern slug if any
    props = propositions_for_theme(theme, root_id) if theme else []
    if props:
        for slug, _, pat in props:
            if pat.search(norm) or pat.search(summary or ""):
                return f"{theme}:{slug}"
    base = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", norm)[:50].strip("-") or "misc"
    pk = parent_key or "orphan"
    return f"{primary}:{pk}:{base}"


def classify_distill_tier(
    raw: Mapping[str, Any],
    *,
    primary: str,
    themes: list[str],
    material_kind: str,
    distill_queue: bool,
    substance_tier: str,
    rule_like: bool,
) -> str:
    if not distill_queue:
        return "index_only"
    summary = raw.get("summary") or ""
    norm = normalize_summary(summary)
    blob = f"{summary}\n{raw.get('description_text') or ''}"

    # CBP 接口票：标题像工程，但评论含 qualified 口径 → 命题核心
    if material_kind == "normative_business" and (
        "compensation-cbp" in themes or primary == "compensation-cbp"
    ):
        if re.search(
            r"integration of us api|qualifiedfor|matching bonus detail|94875",
            blob,
            re.I,
        ):
            return "proposition_core"

    if material_kind == "mapping_engineering" or _ENGINEERING.search(summary):
        return "engineering_slice"

    # cross-theme: primary not in theme slug but ticket tagged with theme
    for th in themes:
        if th == primary:
            continue
        pat = _CROSS_THEME_HINTS.get(th)
        if pat and pat.search(summary) and primary in (
            "compensation-cbp",
            "checkout",
            "contests",
            "messaging",
            "compliance-identity",
        ):
            return "cross_theme_ref"

    if _PLATFORM.search(summary) and substance_tier != "rich":
        return "platform_variant"
    if _PLATFORM.search(summary):
        return "platform_variant"

    if substance_tier == "thin" and not rule_like:
        return "index_only"

    return "proposition_core"


def proposition_extract(tier: str) -> bool:
    return tier == "proposition_core"


def match_core_proposition(theme: str, summary: str, *, root_id: str | None = None) -> str | None:
    norm = normalize_summary(summary)
    for slug, _, pat in propositions_for_theme(theme, root_id):
        if pat.search(norm) or pat.search(summary or ""):
            return slug
    return None


def core_proposition_labels(theme: str, *, root_id: str | None = None) -> list[tuple[str, str]]:
    return [(s, label) for s, label, _ in propositions_for_theme(theme, root_id)]
