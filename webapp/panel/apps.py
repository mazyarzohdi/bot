import logging
import sys

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class PanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "panel"

    def ready(self):
        # db_schema.py lives in the bot's project root (one level up from
        # this webapp/ dir), outside any package that would drag in
        # aiogram/aiosqlite (not installed in this separate venv). Adding
        # the bot root to sys.path lets us reuse the exact same schema
        # reconciler the bot itself runs at startup, so restoring an old
        # DB backup and restarting only the web panel (not the bot) is
        # just as safe — missing tables/columns get added automatically
        # instead of the panel crashing on the first query that needs them.
        bot_root = str(settings.BOT_DIR)
        if bot_root not in sys.path:
            sys.path.insert(0, bot_root)
        try:
            from db_schema import reconcile
            report = reconcile(settings.BOT_DB_PATH)
            if report["tables_created"] or report["columns_added"]:
                logger.info(
                    "Database schema updated — tables created: %s, columns added: %s",
                    report["tables_created"], report["columns_added"],
                )
        except Exception:
            # Never let a schema-check failure block the panel from
            # starting — worst case it behaves as it did before this
            # existed (crashing lazily on whatever query hits a missing
            # column), which is still recoverable from the DB backup menu.
            logger.exception("Database schema reconciliation failed at startup")
