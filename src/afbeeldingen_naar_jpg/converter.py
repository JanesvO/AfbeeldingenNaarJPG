"""Afbeeldingen omzetten naar JPG.

De originele bestanden blijven altijd ongemoeid; de JPG's komen in een submap
'geconverteerd' van de gekozen map (met dezelfde mapstructuur bij submappen).
"""

from __future__ import annotations

import argparse
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageOps, UnidentifiedImageError, features

OUTPUT_FOLDER = "geconverteerd"
BASE_EXTENSIONS = {".png", ".bmp", ".gif", ".tif", ".tiff", ".webp", ".jpeg", ".jpg", ".jfif", ".ico"}

ON_EXISTING_NUMBER = "nummeren"
ON_EXISTING_OVERWRITE = "overschrijven"
ON_EXISTING_SKIP = "overslaan"

STATUS_DONE = "klaar"
STATUS_SKIPPED = "overgeslagen"
STATUS_FAILED = "fout"


def _register_optional_formats() -> set[str]:
    extensions = set(BASE_EXTENSIONS)
    try:
        # iPhone-foto's (HEIC/HEIF).
        from pillow_heif import register_heif_opener

        register_heif_opener()
        extensions |= {".heic", ".heif"}
    except ImportError:
        pass
    if features.check("avif"):
        extensions.add(".avif")
    return extensions


SUPPORTED_EXTENSIONS = _register_optional_formats()


class Cancelled(Exception):
    pass


@dataclass
class ConversionOptions:
    quality: int = 92
    on_existing: str = ON_EXISTING_NUMBER
    include_subfolders: bool = False
    max_size: int | None = None  # langste zijde in pixels; None = originele grootte
    keep_metadata: bool = True
    background: tuple[int, int, int] = (255, 255, 255)


@dataclass(frozen=True)
class ConversionResult:
    source_path: Path
    target_path: Path | None
    status: str
    message: str | None = None

    @property
    def success(self) -> bool:
        return self.status != STATUS_FAILED


ProgressCallback = Callable[[str, int, int, Path, ConversionResult | None], None]


def sanitize_stem(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value.strip())
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-.")
    return cleaned or "afbeelding"


def ensure_input_dir(input_dir: Path) -> Path:
    if not input_dir.exists():
        raise FileNotFoundError(f"Map niet gevonden: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Dit is geen map: {input_dir}")
    return input_dir


def find_images(input_dir: Path, include_subfolders: bool = False) -> list[Path]:
    ensure_input_dir(input_dir)
    candidates = input_dir.rglob("*") if include_subfolders else input_dir.iterdir()
    images = []
    for path in candidates:
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        # Eerder geconverteerde bestanden niet opnieuw meenemen.
        if OUTPUT_FOLDER in path.relative_to(input_dir).parts[:-1]:
            continue
        images.append(path)
    return sorted(images, key=lambda item: str(item.relative_to(input_dir)).lower())


def output_dir_for(input_dir: Path) -> Path:
    return input_dir / OUTPUT_FOLDER


def plan_target(source: Path, input_dir: Path, options: ConversionOptions, used: set[Path]) -> Path | None:
    """Bepaalt het doelbestand; None betekent overslaan."""
    relative_parent = source.parent.relative_to(input_dir)
    folder = output_dir_for(input_dir) / relative_parent
    stem = sanitize_stem(source.stem)
    target = folder / f"{stem}.jpg"

    if target.exists() and target not in used:
        if options.on_existing == ON_EXISTING_SKIP:
            return None
        if options.on_existing == ON_EXISTING_OVERWRITE:
            used.add(target)
            return target

    # Ook binnen dezelfde run kunnen namen botsen (foto.png en foto.webp worden allebei foto.jpg).
    counter = 2
    while target in used or (target.exists() and options.on_existing == ON_EXISTING_NUMBER):
        target = folder / f"{stem}-{counter}.jpg"
        counter += 1
    used.add(target)
    return target


def _to_rgb(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    if image.mode in ("I;16", "I;16B", "I;16L", "I"):
        image = image.point(lambda value: value * (1 / 256)).convert("L")
    has_alpha = image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info)
    if has_alpha:
        # Doorzichtige delen worden wit in plaats van zwart.
        rgba = image.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, background)
        canvas.paste(rgba, mask=rgba.getchannel("A"))
        return canvas
    return image.convert("RGB")


def convert_image(source: Path, target: Path, options: ConversionOptions) -> None:
    with Image.open(source) as original:
        original.seek(0)  # bij GIF/TIFF met meerdere beelden: het eerste beeld
        image = ImageOps.exif_transpose(original) or original
        icc_profile = original.info.get("icc_profile")
        exif = image.getexif() if options.keep_metadata else None

        rgb = _to_rgb(image, options.background)
        if options.max_size:
            rgb.thumbnail((options.max_size, options.max_size), Image.Resampling.LANCZOS)

        save_args: dict[str, object] = {"format": "JPEG", "quality": options.quality, "optimize": True}
        if options.keep_metadata:
            if exif:
                save_args["exif"] = exif.tobytes()
            if icc_profile:
                save_args["icc_profile"] = icc_profile

        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        try:
            rgb.save(temporary, **save_args)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def convert_files(
    files: list[Path],
    input_dir: Path,
    options: ConversionOptions,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> list[ConversionResult]:
    input_dir = ensure_input_dir(input_dir)
    used: set[Path] = set()
    results: list[ConversionResult] = []
    total = len(files)

    for index, source in enumerate(files, start=1):
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled()
        if progress_callback is not None:
            progress_callback("started", index, total, source, None)

        try:
            target = plan_target(source, input_dir, options, used)
            if target is None:
                result = ConversionResult(source, None, STATUS_SKIPPED, "bestaat al")
            else:
                convert_image(source, target, options)
                result = ConversionResult(source, target, STATUS_DONE)
        except UnidentifiedImageError:
            result = ConversionResult(source, None, STATUS_FAILED, "geen geldige afbeelding (beschadigd of onbekend formaat)")
        except PermissionError:
            result = ConversionResult(source, None, STATUS_FAILED, "geen toegang (bestand is in gebruik of alleen-lezen)")
        except Exception as exc:  # een kapot bestand mag de rest niet tegenhouden
            result = ConversionResult(source, None, STATUS_FAILED, str(exc) or exc.__class__.__name__)

        results.append(result)
        if progress_callback is not None:
            progress_callback("finished", index, total, source, result)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zet afbeeldingen uit een map om naar JPG (in de submap 'geconverteerd').")
    parser.add_argument("--input", required=True, help="Map met afbeeldingen.")
    parser.add_argument("--quality", type=int, default=92, help="JPG-kwaliteit 1-100, standaard 92.")
    parser.add_argument("--subfolders", action="store_true", help="Ook afbeeldingen in submappen omzetten.")
    parser.add_argument("--max-size", type=int, default=None, help="Maximale lengte van de langste zijde in pixels.")
    parser.add_argument(
        "--on-existing",
        choices=(ON_EXISTING_NUMBER, ON_EXISTING_OVERWRITE, ON_EXISTING_SKIP),
        default=ON_EXISTING_NUMBER,
        help="Wat te doen als de JPG al bestaat.",
    )
    parser.add_argument("--strip-metadata", action="store_true", help="Fotogegevens (EXIF) niet overnemen.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input).expanduser().resolve()
    options = ConversionOptions(
        quality=max(1, min(100, args.quality)),
        on_existing=args.on_existing,
        include_subfolders=args.subfolders,
        max_size=args.max_size,
        keep_metadata=not args.strip_metadata,
    )
    files = find_images(input_dir, options.include_subfolders)
    if not files:
        print("Geen ondersteunde afbeeldingen gevonden.")
        return 0

    results = convert_files(files, input_dir, options)
    for result in results:
        name = result.source_path.relative_to(input_dir)
        if result.status == STATUS_DONE:
            print(f"Omgezet:      {name} -> {result.target_path.relative_to(input_dir)}")
        elif result.status == STATUS_SKIPPED:
            print(f"Overgeslagen: {name} ({result.message})")
        else:
            print(f"Fout:         {name} -> {result.message}")
    done = sum(result.status == STATUS_DONE for result in results)
    skipped = sum(result.status == STATUS_SKIPPED for result in results)
    failed = sum(result.status == STATUS_FAILED for result in results)
    print(f"Klaar. {done} omgezet, {skipped} overgeslagen, {failed} mislukt.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
