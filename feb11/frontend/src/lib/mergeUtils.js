/**
 * Canonical deep merge: merge src into dst.
 * - Objects: recursively merged.
 * - Arrays: merged element-by-element by index, preserving extras in dst.
 * - Scalars: src overwrites dst.
 */
export function deepMergeObjects(dst, src) {
  if (!src || typeof src !== 'object') return dst;
  if (!dst || typeof dst !== 'object') return src;

  const result = Array.isArray(dst) ? [...dst] : { ...dst };

  if (Array.isArray(src) && Array.isArray(dst)) {
    for (let i = 0; i < src.length; i++) {
      if (i < result.length) {
        if (src[i] && typeof src[i] === 'object' && !Array.isArray(src[i]) &&
            result[i] && typeof result[i] === 'object' && !Array.isArray(result[i])) {
          result[i] = deepMergeObjects(result[i], src[i]);
        } else {
          result[i] = src[i];
        }
      } else {
        result.push(src[i]);
      }
    }
    return result;
  }

  for (const [key, value] of Object.entries(src)) {
    if (value && typeof value === 'object' && !Array.isArray(value) &&
        result[key] && typeof result[key] === 'object' && !Array.isArray(result[key])) {
      result[key] = deepMergeObjects(result[key], value);
    } else if (Array.isArray(value) && Array.isArray(result[key])) {
      result[key] = deepMergeObjects(result[key], value);
    } else {
      result[key] = value;
    }
  }
  return result;
}
