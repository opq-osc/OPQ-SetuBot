from botoy import jconfig
from httpx_socks import SyncProxyTransport

if proxies_socks := jconfig.proxies_socks:
    transport = SyncProxyTransport.from_url(proxies_socks)
    proxies = None
else:
    transport = None
    proxies = jconfig.proxies_http
