from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image


SUPPORTED_EXTENSIONS = {".png", ".bmp", ".gif", ".tif", ".tiff", ".webp", ".jpeg", ".jpg"}


@dataclass(frozen=True)
class ConversionResult:
    source_path: Path
    target_path: Path | None
    success: bool
    error_message: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zet afbeeldingen uit een map om naar JPG.")
    parser.add_argument("--input", required=True, help="Map met bronafbeeldingen.")
    parser.add_argument("--quality", type=int, default=92, help="JPG-kwaliteit, standaard 92.")
    return parser.parse_args()


def sanitize_stem(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value.strip())
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-.")
    return cleaned or "afbeelding"


def ensure_input_dir(input_dir: Path) -> Path:
    if not input_dir.exists():
        raise FileNotFoundError(f"Invoermap niet gevonden: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Invoerpad is geen map: {input_dir}")
    return input_dir


def iter_source_images(input_dir: Path) -> list[Path]:
    ensure_input_dir(input_dir)
    return sorted(
        path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def create_output_dir(input_dir: Path, folder_name: str = "geconverteerd") -> Path:
    output_dir = input_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_target_path(source_path: Path, output_dir: Path) -> Path:
    base_name = sanitize_stem(source_path.stem)
    target_path = output_dir / f"{base_name}.jpg"
    counter = 2

    while target_path.exists():
        target_path = output_dir / f"{base_name}-{counter}.jpg"
        counter += 1

    return target_path


def convert_image(source_path: Path, output_dir: Path, quality: int) -> Path:
    target_path = build_target_path(source_path, output_dir)

    with Image.open(source_path) as image:
        rgb_image = image.convert("RGB")
        rgb_image.save(target_path, format="JPEG", quality=quality)

    return target_path


def convert_directory(
    input_dir: Path,
    quality: int = 92,
    progress_callback: Callable[[str, int, int, ConversionResult | None], None] | None = None,
) -> list[ConversionResult]:
    input_dir = ensure_input_dir(input_dir)
    output_dir = create_output_dir(input_dir)
    source_images = iter_source_images(input_dir)
    results: list[ConversionResult] = []

    for index, source_image in enumerate(source_images, start=1):
        if progress_callback is not None:
            progress_callback("started", index, len(source_images), None)

        try:
            target_path = convert_image(source_image, output_dir, quality)
            result = ConversionResult(source_image, target_path, True)
        except Exception as exc:
            result = ConversionResult(source_image, None, False, str(exc))

        results.append(result)
        if progress_callback is not None:
            progress_callback("finished", index, len(source_images), result)

    return results


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input).expanduser().resolve()
    source_images = iter_source_images(input_dir)

    if not source_images:
        print("Geen ondersteunde afbeeldingen gevonden.")
        return 0

    results = convert_directory(input_dir, quality=args.quality)
    success_count = sum(1 for result in results if result.success)
    failed_count = len(results) - success_count

    for result in results:
        if result.success and result.target_path is not None:
            print(f"Omgezet: {result.source_path.name} -> {result.target_path.name}")
        else:
            print(f"Fout: {result.source_path.name} -> {result.error_message}")

    print(f"Klaar. {success_count} gelukt, {failed_count} mislukt.")
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
