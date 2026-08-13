from __future__ import annotations
import json
import time
from yt_dlp.extractor.youtube.pot.provider import (
    PoTokenContext, PoTokenProvider, PoTokenProviderError,
    PoTokenProviderRejectedRequest, PoTokenResponse,
    register_preference, register_provider,
)
from yt_dlp.extractor.youtube.pot.utils import WEBPO_CLIENTS, get_webpo_content_binding
from yt_dlp.networking.common import Request

@register_provider
class InSavePTP(PoTokenProvider):
    PROVIDER_VERSION = '1.1.0'
    BUG_REPORT_LOCATION = 'local InSave provider'
    _SUPPORTED_CONTEXTS = (PoTokenContext.GVS, PoTokenContext.PLAYER, PoTokenContext.SUBS)
    _SUPPORTED_CLIENTS = WEBPO_CLIENTS
    _SUPPORTED_EXTERNAL_REQUEST_FEATURES = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._primed = {}

    def is_available(self):
        return True

    def _request_local(self, binding, binding_type=None, context=None, client=None, note=None):
        payload = json.dumps({
            'content_binding': binding,
            'binding_type': binding_type,
            'context': context,
            'client': client,
        }).encode()
        try:
            response = self._request_webpage(Request(
                'http://127.0.0.1:4417/get_pot', data=payload,
                headers={'Content-Type': 'application/json'},
                extensions={'timeout': 30.0}, proxies={'all': None}),
                note=note or 'Generando PO Token local de InSave')
            data = json.load(response)
        except Exception as e:
            raise PoTokenProviderError(f'InSave PO Token server error: {e!r}') from e
        token = data.get('poToken')
        if not token:
            raise PoTokenProviderError(data.get('error') or 'InSave PO Token server returned no token')
        return PoTokenResponse(po_token=token, expires_at=data.get('expiresAt'))

    @staticmethod
    def _valid_cached(response):
        return response is not None and (response.expires_at is None or response.expires_at > int(time.time()) + 30)

    def _real_request_pot(self, request):
        binding, binding_type = get_webpo_content_binding(request)
        if not binding:
            raise PoTokenProviderRejectedRequest('InSave: no PO token content binding available')

        # WebPo/BotGuard expects the streaming token bound to visitorData to be minted
        # before player/video tokens. yt-dlp requests PLAYER before GVS, so prime it here
        # and cache it for the later GVS request.
        if not request.is_authenticated and request.visitor_data:
            cached = self._primed.get(request.visitor_data)
            if request.context == PoTokenContext.GVS and binding == request.visitor_data and self._valid_cached(cached):
                return cached
            if request.context in (PoTokenContext.PLAYER, PoTokenContext.SUBS) and not self._valid_cached(cached):
                cached = self._request_local(
                    request.visitor_data,
                    binding_type='visitor_data',
                    context='gvs-prime',
                    client=request.internal_client_name,
                    note='Preparando PO Token de visitante de InSave')
                self._primed[request.visitor_data] = cached

        return self._request_local(
            binding,
            binding_type=binding_type.value if binding_type else None,
            context=request.context.value,
            client=request.internal_client_name)

@register_preference(InSavePTP)
def insave_preference(provider, request):
    return 200
