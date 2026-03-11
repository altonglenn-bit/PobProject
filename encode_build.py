from __future__ import annotations

import argparse
import base64
import zlib
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Encode a PoB XML file into a PoB-style import string."
    )
    parser.add_argument(
        "--in",
        dest="input_path",
        default="build.xml",
        help="Input XML file. Default: build.xml",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        default=None,
        help="Output text file. Default: <input>_encoded.txt",
    )
    return parser


def ensure_out_path(input_path: str, output_path: str | None) -> str:
    if output_path:
        return output_path
    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_encoded.txt"))


def pob_base64_encode(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(data).decode("ascii")
    return encoded.rstrip("=")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    with open(args.input_path, "rb") as f:
        xml_bytes = f.read()

    compressed = zlib.compress(xml_bytes, level=9)
    encoded = pob_base64_encode(compressed)

    output_path = ensure_out_path(args.input_path, args.output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(encoded)

    print("=" * 60)
    print("ENCODE SUMMARY")
    print("=" * 60)
    print(f"Input:  {args.input_path}")
    print(f"Output: {output_path}")
    print(f"Encoded length: {len(encoded)}")
    print("=" * 60)
    print("First 120 chars:")
    print(encoded[:120])
    print("=" * 60)


if __name__ == "__main__":
    main()
