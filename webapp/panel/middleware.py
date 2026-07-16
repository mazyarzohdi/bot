"""Middleware needed for the panel to work as a Telegram Mini App.

Django's default XFrameOptionsMiddleware sends `X-Frame-Options: DENY`,
which blocks the page from being embedded in *any* frame. Telegram Desktop
(and some other Telegram clients) render Mini Apps inside an embedded
webview that behaves like an iframe, so DENY silently breaks the Mini App
there (blank/white screen, page "refuses to connect"). Mobile clients are
less strict, which is why this can look like it "mostly works" until
someone opens it on desktop.

We replace the blanket DENY with a Content-Security-Policy that only
allows framing from Telegram's own domains, which keeps the page safe from
being embedded on arbitrary third-party sites while still letting Telegram
itself display it.
"""

TELEGRAM_FRAME_ANCESTORS = (
    "'self' https://web.telegram.org https://webk.telegram.org "
    "https://webz.telegram.org https://*.web.telegram.org"
)


class TelegramEmbedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Remove the blanket X-Frame-Options: DENY set by
        # XFrameOptionsMiddleware and rely on CSP frame-ancestors instead,
        # which supports an allow-list instead of an all-or-nothing switch.
        if "X-Frame-Options" in response:
            del response["X-Frame-Options"]
        response["Content-Security-Policy"] = f"frame-ancestors {TELEGRAM_FRAME_ANCESTORS}"
        return response
