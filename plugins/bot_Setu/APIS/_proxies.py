from botoy import jconfig
from httpx_socks import AsyncProxyTransport

if proxies_socks := jconfig.proxies_socks:
    transport = AsyncProxyTransport.from_url(proxies_socks)
    proxies = None
else:
    transport = None
    proxies = jconfig.proxies_http
