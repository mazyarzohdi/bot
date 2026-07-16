"""Template context processors for the panel app."""

from . import db as bot_db


def reseller_status(request):
    """Injects `nav_has_reseller` into every template's context, so the
    sidebar can show/hide the 'پنل نمایندگی' nav link regardless of which
    page is currently being rendered, without every single view needing
    to look this up and pass it along itself. Shown whenever the user has
    ANY reseller record — including an expired/disabled one — so they can
    still get to the page that explains why it's locked and what to do."""
    tg_user = request.session.get("tg_user")
    if not tg_user:
        return {"nav_has_reseller": False}
    try:
        db_user = bot_db.get_user_by_telegram_id(int(tg_user["id"]))
        reseller = bot_db.get_reseller_by_user(db_user["id"]) if db_user else None
    except Exception:
        # Never let a lookup failure here break page rendering — the nav
        # link just won't show, which is a safe default.
        return {"nav_has_reseller": False}
    return {"nav_has_reseller": bool(reseller)}
