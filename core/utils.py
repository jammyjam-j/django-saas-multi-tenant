import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.db.models.query import QuerySet
from django.utils.timezone import now


def generate_uuid() -> str:
    return str(uuid.uuid4())


def hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = uuid.uuid4().hex
    hashed = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_password(stored_hash: str, password_attempt: str) -> bool:
    try:
        salt, hash_value = stored_hash.split("$")
    except ValueError:
        return False
    attempt_hash = hashlib.sha256(f"{salt}{password_attempt}".encode("utf-8")).hexdigest()
    return attempt_hash == hash_value


def validate_email(email: str) -> None:
    django_validate_email(email)


def get_current_tenant(request) -> Any:
    return getattr(request, "tenant", None)


def serialize_object(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "__dict__"):
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    else:
        data = {}
    for key, value in list(data.items()):
        if isinstance(value, (datetime,)):
            data[key] = value.isoformat()
    return data


def serialize_queryset(queryset: QuerySet) -> List[Dict[str, Any]]:
    return [serialize_object(obj) for obj in queryset]


def paginate_queryset(
    qs: Iterable[Any], page_size: int, page_number: int
) -> Tuple[List[Any], Dict[str, int]]:
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    start = (page_number - 1) * page_size
    end = start + page_size
    items = list(qs)[start:end]
    total_items = len(list(qs))
    total_pages = (total_items + page_size - 1) // page_size
    return (
        items,
        {"total_items": total_items, "total_pages": total_pages, "current_page": page_number},
    )


def parse_date_range(
    start_str: Optional[str], end_str: Optional[str]
) -> Tuple[datetime, datetime]:
    today = now().date()
    if not start_str:
        start_date = today - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValidationError(f"Invalid start date: {start_str}") from exc
    if not end_str:
        end_date = today
    else:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValidationError(f"Invalid end date: {end_str}") from exc
    if start_date > end_date:
        raise ValidationError("start_date cannot be after end_date")
    return start_date, end_date


def get_setting(name: str, default: Any = None) -> Any:
    return getattr(settings, name, default)


def dict_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            target[key] = dict_merge(target[key], value)
        else:
            target[key] = value
    return target


def safe_int_convert(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_query_param(request, key: str, default: Any = None) -> Any:
    return request.GET.get(key, default)


def build_absolute_url(path: str, host: Optional[str] = None) -> str:
    if not host:
        host = settings.ALLOWED_HOSTS[0]
    scheme = "https" if getattr(settings, "SECURE_SSL_REDIRECT", False) else "http"
    return f"{scheme}://{host}{path}"


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(fmt)


def ensure_list(value: Any) -> List[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def parse_bool(val: Any) -> bool:
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    try:
        return dictionary[key]
    except KeyError:
        return default


def build_query_params(params: Dict[str, Any]) -> str:
    from urllib.parse import urlencode

    cleaned = clean_dict({k: v for k, v in params.items() if v is not None})
    return urlencode(cleaned)