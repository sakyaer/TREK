import { Injectable } from '@nestjs/common';
import { readEnv } from '../../app-config';

interface Attempt { count: number; first: number }

/**
 * In-memory per-IP rate limiter, ported 1:1 from the legacy auth route's
 * `rateLimiter`. Each named bucket keeps its own attempt map; `check` returns
 * false once a key exceeds `max` within `windowMs` (the caller answers 429).
 *
 * The legacy route ran a setInterval to garbage-collect expired records. There
 * is no timer here — a dangling one leaks in tests — but the housekeeping is
 * back as a lazy sweep driven by the `now` the caller already passes: keys are
 * per-IP and proxy-header derived, so without it a bucket grows for every
 * address that ever knocked and never shrinks again. An expired record is
 * treated as fresh by the window check below, so dropping it changes nothing
 * about who gets a 429.
 */
@Injectable()
export class RateLimitService {
  private readonly buckets = new Map<string, Map<string, Attempt>>();
  /** Last sweep per bucket, so a busy bucket doesn't keep a quiet one from being cleaned. */
  private readonly lastSweep = new Map<string, number>();

  private store(bucket: string): Map<string, Attempt> {
    let s = this.buckets.get(bucket);
    if (!s) { s = new Map(); this.buckets.set(bucket, s); }
    return s;
  }

  /** Returns true when the request is allowed, false when it should be rejected (429). */
  check(bucket: string, key: string, max: number, windowMs: number, now: number): boolean {
    // RATE_LIMIT_MAX_OVERRIDE is a development escape hatch rather than a tuning
    // knob: a local instance keys every bucket on one address, so the operator
    // and their scripts share a single attempt budget and trip here on limits
    // meant for strangers. Read per call, because readEnv() is documented as
    // never caching across requests and the tests mutate process.env at runtime.
    const { maxOverride } = readEnv().rateLimit;
    const ceiling = maxOverride > 0 && max < maxOverride ? maxOverride : max;
    const store = this.store(bucket);
    this.sweep(bucket, store, windowMs, now);
    const record = store.get(key);
    if (record && record.count >= ceiling && now - record.first < windowMs) {
      return false;
    }
    if (!record || now - record.first >= windowMs) {
      store.set(key, { count: 1, first: now });
    } else {
      record.count++;
    }
    return true;
  }

  /** Drops records whose window has elapsed, at most once per window per bucket. */
  private sweep(bucket: string, store: Map<string, Attempt>, windowMs: number, now: number): void {
    if (now - (this.lastSweep.get(bucket) ?? 0) < windowMs) return;
    for (const [k, record] of store) {
      if (now - record.first >= windowMs) store.delete(k);
    }
    this.lastSweep.set(bucket, now);
  }

  /** Test helper: clear a bucket (mirrors the legacy exported maps used for resets). */
  reset(bucket?: string): void {
    if (bucket) this.buckets.get(bucket)?.clear();
    else { this.buckets.clear(); this.lastSweep.clear(); }
  }
}
