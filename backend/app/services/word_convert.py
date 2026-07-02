"""Конвертация .doc → .docx для последующего разбора (LibreOffice или MS Word на Windows)."""
import shutil
import subprocess
import tempfile
from pathlib import Path


class WordConvertError(Exception):
    """Не удалось прочитать .doc — нужен .docx или установленный LibreOffice / Word."""


def _find_soffice() -> str | None:
    for path in (
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ):
        if path == "soffice" and shutil.which("soffice"):
            return "soffice"
        if Path(path).is_file():
            return path
    return None


def _convert_with_libreoffice(src: Path, out_dir: Path) -> Path:
    soffice = _find_soffice()
    if not soffice:
        raise WordConvertError("LibreOffice не найден")
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "docx", "--outdir", str(out_dir), str(src)],
        capture_output=True,
        timeout=90,
        check=False,
    )
    if result.returncode != 0:
        raise WordConvertError(result.stderr.decode(errors="replace") or "Ошибка конвертации LibreOffice")
    out = out_dir / f"{src.stem}.docx"
    if not out.is_file():
        raise WordConvertError("LibreOffice не создал .docx")
    return out


def _convert_with_ms_word(src: Path, out_dir: Path) -> Path:
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError as e:
        raise WordConvertError("pywin32 / MS Word недоступны") from e

    out = out_dir / f"{src.stem}.docx"
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = None
    try:
        doc = word.Documents.Open(str(src.resolve()))
        # 16 = wdFormatXMLDocument (.docx)
        doc.SaveAs2(str(out.resolve()), FileFormat=16)
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()
    if not out.is_file():
        raise WordConvertError("Word не сохранил .docx")
    return out


def ensure_docx_bytes(content: bytes, filename: str) -> bytes:
    """Возвращает байты .docx: для .docx — как есть, для .doc — конвертирует."""
    name = (filename or "file").lower()
    if name.endswith(".docx"):
        return content
    if not name.endswith(".doc"):
        raise WordConvertError("Поддерживаются только .doc и .docx")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / "upload.doc"
        src.write_bytes(content)
        errors: list[str] = []

        try:
            return _convert_with_libreoffice(src, tmp_path).read_bytes()
        except WordConvertError as e:
            errors.append(str(e))

        try:
            return _convert_with_ms_word(src, tmp_path).read_bytes()
        except WordConvertError as e:
            errors.append(str(e))

    raise WordConvertError(
        "Не удалось открыть файл .doc. Сохраните его в Word как .docx "
        "или установите LibreOffice (бесплатно) / Microsoft Word."
    )
