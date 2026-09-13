// Node's native fetch (undici) ignores HTTP(S)_PROXY environment variables
// unless a proxy-aware global dispatcher is installed. Self-hosters behind a
// local gateway (Clash, sing-box, …) hit this hard: the browser reaches
// googleapis.com through the system proxy while every server-side call —
// places search, photo download — dies at TLS connect. Set HTTPS_PROXY (and
// optionally HTTP_PROXY/NO_PROXY) to route those requests through the
// gateway; with no proxy vars set this module does nothing and direct
// connections stay the default.
import { EnvHttpProxyAgent, setGlobalDispatcher } from 'undici';

const proxy =
  process.env.HTTPS_PROXY ??
  process.env.https_proxy ??
  process.env.HTTP_PROXY ??
  process.env.http_proxy;

if (proxy) {
  // EnvHttpProxyAgent only proxies what the env names; defaulting NO_PROXY
  // keeps loopback traffic (self-referencing calls, health checks) direct.
  if (!process.env.NO_PROXY && !process.env.no_proxy) {
    process.env.NO_PROXY = 'localhost,127.0.0.1,::1';
  }
  setGlobalDispatcher(new EnvHttpProxyAgent());
  console.log(`[trek:outbound-proxy] server-side fetch via ${proxy}`);
}
