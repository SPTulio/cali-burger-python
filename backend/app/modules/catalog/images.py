"""Imagens dos itens do cardápio: confere o conteúdo real do arquivo e grava com nome aleatório."""

import logging
import secrets
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.core.errors import InvalidInput

logger = logging.getLogger("caliburger.images")

ALLOWED_FORMATS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}
MAX_PIXELS = 25_000_000  # evita imagens gigantes (decompression bomb)


def _invalid(message: str) -> InvalidInput:
    return InvalidInput(message, fields={"image": message})


def save_menu_image(content: bytes) -> str:
    """Valida e grava a imagem.

    Retorna o caminho relativo à pasta de mídia (ex.: menu/ab12.webp)."""
    settings = get_settings()
    if not content:
        raise _invalid("Selecione uma imagem.")
    if len(content) > settings.max_image_bytes:
        raise _invalid("A imagem deve ter no máximo 2 MB.")
    try:
        with Image.open(BytesIO(content)) as image:
            image_format = image.format or ""
            width, height = image.size
            image.verify()
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise _invalid("Envie uma imagem PNG, JPG ou WebP.") from exc
    if image_format not in ALLOWED_FORMATS:
        raise _invalid("Envie uma imagem PNG, JPG ou WebP.")
    if width * height > MAX_PIXELS:
        raise _invalid("A imagem é grande demais. Use até 5000 × 5000 pixels.")

    folder = settings.menu_media_dir
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{secrets.token_hex(12)}.{ALLOWED_FORMATS[image_format]}"
    (folder / filename).write_bytes(content)
    return f"menu/{filename}"


def delete_media_file(relative_path: str | None) -> None:
    """Apaga o arquivo antigo. Só aceita arquivos dentro da pasta de mídia."""
    if not relative_path:
        return
    media_dir = get_settings().media_dir.resolve()
    path = (media_dir / relative_path).resolve()
    if not path.is_relative_to(media_dir):
        logger.warning("Caminho de imagem fora da pasta de mídia ignorado: %s", relative_path)
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        logger.warning("Não foi possível apagar a imagem %s", relative_path, exc_info=True)


def media_url(relative_path: str | None) -> str | None:
    return f"/media/{relative_path}" if relative_path else None
