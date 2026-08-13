from __future__ import annotations
import json
from yt_dlp.extractor.youtube.pot.provider import (
    PoTokenContext, PoTokenProvider, PoTokenProviderError,
    PoTokenProviderRejectedRequest, PoTokenResponse,
    register_preference, register_provider,
)
from yt_dlp.extractor.youtube.pot.utils import WEBPO_CLIENTS, get_webpo_content_binding
from yt_dlp.networking.common import Request

@register_provider
class InSavePTP(PoTokenProvider):
    PROVIDER_VERSION = '1.0.0'
    BUG_REPORT_LOCATION = 'local InSave provider'
    _SUPPORTED_CONTEXTS = (PoTokenContext.GVS, PoTokenContext.PLAYER, PoTokenContext.SUBS)
    _SUPPORTED_CLIENTS = WEBPO_CLIENTS
    _SUPPORTED_EXTERNAL_REQUEST_FEATURES = None

    def is_available(self):
        return True

    def _real_request_pot(self, request):
        binding, binding_type = get_webpo_content_binding(request)
        if not binding:
            raise PoTokenProviderRejectedRequest('InSave: no PO token content binding available')
        payload = json.dumps({
            'content_binding': binding,
            'binding_type': binding_type.value if binding_type else None,
            'context': request.context.value,
            'client': request.internal_client_name,
        }).encode()
        try:
            response = self._request_webpage(Request(
                'http://127.0.0.1:4417/get_pot', data=payload,
                headers={'Content-Type': 'application/json'},
                extensions={'timeout': 30.0}, proxies={'all': None}),
                note='Generando PO Token local de InSave')
            data = json.load(response)
        except Exception as e:
            raise PoTokenProviderError(f'InSave PO Token server error: {e!r}') from e
        token = data.get('poToken')
        if not token:
            raise PoTokenProviderError(data.get('error') or 'InSave PO Token server returned no token')
        return PoTokenResponse(po_token=token, expires_at=data.get('expiresAt'))

@register_preference(InSavePTP)
def insave_preference(provider, request):
    return 200
