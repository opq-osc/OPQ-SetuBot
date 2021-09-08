from botoy import jconfig
from httpx_socks import AsyncProxyTransport, SyncProxyTransport

if proxies_socks := jconfig.proxies_socks:
    transport = SyncProxyTransport.from_url(proxies_socks)
    async_transport = AsyncProxyTransport.from_url(proxies_socks)
    proxies = None
else:
    transport = None
    async_transport = None
    proxies = jconfig.proxies_http
