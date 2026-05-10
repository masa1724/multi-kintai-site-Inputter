import os


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"環境変数が設定されていません: {name}")
    return value


def masking(value: str) -> str:
    """ログに認証情報をそのまま出さないため、先頭と末尾以外を伏せる。"""
    if not value:
        return ""

    if len(value) <= 2:
        return "*" * len(value)

    return value[0] + "*" * (len(value) - 2) + value[-1]


def has_time_range(start: str | None, end: str | None) -> bool:
    return bool(start and end)
