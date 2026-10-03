/* Live GIPHY reactions. Keep provider URLs intact and load media directly. */
(function (global) {
  'use strict';

  const LIMIT = 12;
  const FIELDS = ['id', 'title', 'url', 'still', 'width', 'height', 'rating'];
  const RATINGS = ['g', 'pg', 'pg-13'];
  const ACTIONS = ['onload', 'onclick', 'onsent'];
  const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);

  function mediaURL(value) {
    if (typeof value !== 'string' || value.length > 4096 || /[\s\\]/.test(value)) return false;
    // Check the original authority too: URL.port hides an explicit default :443.
    if (!/^https:\/\/media\d*\.giphy\.com\/media\//i.test(value)) return false;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && /^media\d*\.giphy\.com$/i.test(url.hostname) &&
        !url.username && !url.password && !url.port && !url.hash &&
        /^\/media\/(?:[a-z0-9._~-]+\/)*[a-z0-9._~-]+\.(?:gif|webp|png|jpe?g)$/i.test(url.pathname);
    } catch (_) { return false; }
  }

  function dimension(value) {
    return typeof value === 'number' && Number.isInteger(value) && value >= 1 && value <= 4096;
  }

  function validate(packet) {
    if (!packet || typeof packet !== 'object' || Array.isArray(packet)) return false;
    if (Object.keys(packet).length !== FIELDS.length || !FIELDS.every(key => own(packet, key))) return false;
    return typeof packet.id === 'string' && /^[a-z0-9]{1,80}$/i.test(packet.id) &&
      typeof packet.title === 'string' && packet.title.length <= 160 &&
      mediaURL(packet.url) && mediaURL(packet.still) &&
      dimension(packet.width) && dimension(packet.height) &&
      typeof packet.rating === 'string' && RATINGS.includes(packet.rating);
  }

  function normalize(raw) {
    if (!raw || typeof raw !== 'object' || !raw.images || typeof raw.images !== 'object') return null;
    const images = raw.images;
    const still = [images.fixed_width_still, images.fixed_height_still, images.original_still]
      .map(image => image && image.url).find(mediaURL);
    if (!still) return null;
    const renditions = [images.fixed_width, images.fixed_height, images.downsized, images.original];
    for (const image of renditions) {
      if (!image || typeof image !== 'object') continue;
      const url = [image.webp, image.url].find(mediaURL);
      if (!url) continue;
      const numeric = value => typeof value === 'string' || typeof value === 'number' ? Number(value) : NaN;
      const packet = {
        id: raw.id,
        title: typeof raw.title === 'string' ? raw.title.slice(0, 160) : '',
        url,
        still,
        width: numeric(image.width),
        height: numeric(image.height),
        rating: raw.rating
      };
      if (validate(packet)) return packet;
    }
    return null;
  }

  function error(code, message, status) {
    const result = new Error(message);
    result.code = code;
    if (status) result.status = status;
    return result;
  }

  function responseError(status) {
    if (status === 401 || status === 403) {
      return error('INVALID_KEY', 'GIPHY rejected this API key. Check the Web API key in GIF settings.', status);
    }
    if (status === 429) {
      return error('RATE_LIMIT', 'GIPHY’s request limit has been reached. Try again later or upgrade the API key.', status);
    }
    return error('API_ERROR', 'GIPHY is unavailable right now. Try again in a moment.', status);
  }

  function aborted() {
    const result = error('ABORTED', 'GIF request cancelled.');
    result.name = 'AbortError';
    return result;
  }

  function analyticsURL(value) {
    if (typeof value !== 'string' || value.length > 12000 || /[\s\\]/.test(value) ||
        !value.startsWith('https://giphy-analytics.giphy.com/v2/pingback_simple?')) return false;
    try {
      const url = new URL(value);
      return url.origin === 'https://giphy-analytics.giphy.com' && !url.username && !url.password &&
        !url.port && !url.hash && url.pathname === '/v2/pingback_simple';
    } catch (_) { return false; }
  }

  function safeAnalytics(raw) {
    const result = {};
    if (raw && typeof raw === 'object') {
      for (const action of ACTIONS) {
        if (raw[action] && analyticsURL(raw[action].url)) result[action] = { url: raw[action].url };
      }
    }
    return result;
  }

  // Anonymous identifier lives only for this page load; no account or device data.
  const customerId = global.crypto && typeof global.crypto.randomUUID === 'function'
    ? global.crypto.randomUUID() : 'rtc-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);

  function createClient(key) {
    const apiKey = typeof key === 'string' ? key.trim() : '';

    async function list(options = {}) {
      const { query = '', offset = 0, signal } = options;
      if (!apiKey) throw error('MISSING_KEY', 'Add a GIPHY Web API key in GIF settings to load live GIFs.');
      if (typeof query !== 'string') throw error('INVALID_QUERY', 'Enter a text search for GIFs.');
      const search = query.slice(0, 50);
      const maxOffset = search ? 4999 : 499;
      if (!Number.isInteger(offset) || offset < 0 || offset > maxOffset) {
        throw error('INVALID_OFFSET', 'This GIF results page is unavailable. Start a new search.');
      }
      if (signal && signal.aborted) throw aborted();
      if (global.navigator && global.navigator.onLine === false) {
        throw error('OFFLINE', 'You’re offline. Reconnect to load live GIFs.');
      }
      const url = new URL('https://api.giphy.com/v1/gifs/' + (search ? 'search' : 'trending'));
      url.searchParams.set('api_key', apiKey);
      url.searchParams.set('limit', String(LIMIT));
      url.searchParams.set('rating', 'pg-13');
      url.searchParams.set('country_code', 'AU');
      url.searchParams.set('offset', String(offset));
      url.searchParams.set('customer_id', customerId);
      if (search) url.searchParams.set('q', search);

      const controller = new AbortController();
      let timedOut = false;
      const cancel = () => controller.abort();
      if (signal) signal.addEventListener('abort', cancel, { once: true });
      const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 10000);
      try {
        const response = await global.fetch(url.href, {
          signal: controller.signal, credentials: 'omit', cache: 'no-store', referrerPolicy: 'no-referrer'
        });
        if (!response.ok) throw responseError(response.status);
        let body;
        try { body = await response.json(); }
        catch (cause) {
          if (controller.signal.aborted) throw cause;
          throw error('INVALID_RESPONSE', 'GIPHY returned an unreadable response. Please try again.');
        }
        if (controller.signal.aborted) throw aborted();
        if (body && body.meta && Number.isInteger(body.meta.status) && body.meta.status >= 400) {
          throw responseError(body.meta.status);
        }
        if (!body || !Array.isArray(body.data)) {
          throw error('INVALID_RESPONSE', 'GIPHY returned an unreadable response. Please try again.');
        }
        const items = [];
        const analytics = Object.create(null);
        for (const raw of body.data) {
          const gif = normalize(raw);
          if (!gif) continue;
          items.push(gif);
          analytics[gif.id] = safeAnalytics(raw.analytics);
        }
        // Advance past every API result, including malformed packets rejected above.
        const next = offset + body.data.length;
        const total = body.pagination && body.pagination.total_count;
        const hasMore = body.data.length > 0 && (Number.isInteger(total) ? next < total : body.data.length >= LIMIT);
        return { items, nextOffset: hasMore && next <= maxOffset ? next : null, analytics };
      } catch (cause) {
        if (signal && signal.aborted) throw aborted();
        if (timedOut) throw error('TIMEOUT', 'GIPHY took too long to respond. Please try again.');
        if (cause && cause.code) throw cause;
        if (cause && cause.name === 'AbortError') throw aborted();
        throw error('NETWORK', 'Could not load GIFs. Check your connection and try again.');
      } finally {
        clearTimeout(timeout);
        if (signal) signal.removeEventListener('abort', cancel);
      }
    }

    async function track(rawOrAnalytics, action) {
      if (!ACTIONS.includes(action) || !rawOrAnalytics || typeof rawOrAnalytics !== 'object') return false;
      const analytics = safeAnalytics(rawOrAnalytics.analytics || rawOrAnalytics);
      if (!analytics[action]) return false;
      const url = new URL(analytics[action].url);
      url.searchParams.set('customer_id', customerId);
      url.searchParams.set('ts', String(Date.now()));
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      try {
        const response = await global.fetch(url.href, {
          method: 'GET', signal: controller.signal, credentials: 'omit', cache: 'no-store',
          referrerPolicy: 'no-referrer', keepalive: true
        });
        return response.ok;
      } catch (_) { return false; }
      finally { clearTimeout(timeout); }
    }

    return { list, track };
  }

  global.RTCGiphy = Object.freeze({ createClient, validate, normalize });
})(window);
