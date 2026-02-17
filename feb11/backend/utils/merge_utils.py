def deep_merge(dst: dict, src: dict) -> dict:
    """
    Canonical deep merge: merge src into dst.
    - Dicts: recursively merged.
    - Lists: merged element-by-element by index, preserving extras in dst.
    - Scalars: src overwrites dst.
    """
    if not isinstance(src, dict):
        return src
    if not isinstance(dst, dict):
        return src

    result = dst.copy()
    for key, src_val in src.items():
        if key not in result:
            result[key] = src_val
        elif isinstance(src_val, dict) and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], src_val)
        elif isinstance(src_val, list) and isinstance(result[key], list):
            merged_list = result[key].copy()
            for i, src_elem in enumerate(src_val):
                if i < len(merged_list):
                    if isinstance(src_elem, dict) and isinstance(merged_list[i], dict):
                        merged_list[i] = deep_merge(merged_list[i], src_elem)
                    else:
                        merged_list[i] = src_elem
                else:
                    merged_list.append(src_elem)
            result[key] = merged_list
        else:
            result[key] = src_val
    return result
