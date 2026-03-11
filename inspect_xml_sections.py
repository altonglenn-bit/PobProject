from __future__ import annotations

import xml.etree.ElementTree as ET

import pobapi


def load_build(source: str):
    if source.startswith("http://") or source.startswith("https://"):
        return pobapi.from_url(source)
    return pobapi.from_import_code(source)


def section_to_text(elem, max_len=4000):
    if elem is None:
        return "<missing>"
    text = ET.tostring(elem, encoding="unicode")
    if len(text) > max_len:
        return text[:max_len] + "\n... <truncated>"
    return text


def main():
    source = input("Paste PoB import code or pastebin URL: ").strip()
    build = load_build(source)

    root = ET.fromstring(ET.tostring(build.xml, encoding="unicode"))

    print("=" * 80)
    print("ROOT CHILDREN")
    print("=" * 80)
    for child in root:
        print(child.tag, child.attrib)
    print()

    for tag in ["Build", "Tree", "Skills", "Items", "Config", "Notes", "Calcs"]:
        elem = root.find(tag)
        print("=" * 80)
        print(tag)
        print("=" * 80)
        print(section_to_text(elem))
        print()

    with open("xml_dump.txt", "w", encoding="utf-8") as f:
        f.write("ROOT CHILDREN\n")
        for child in root:
            f.write(f"{child.tag} {child.attrib}\n")
        f.write("\n")

        for tag in ["Build", "Tree", "Skills", "Items", "Config", "Notes", "Calcs"]:
            elem = root.find(tag)
            f.write("=" * 80 + "\n")
            f.write(tag + "\n")
            f.write("=" * 80 + "\n")
            f.write(section_to_text(elem, max_len=20000))
            f.write("\n\n")

    print("Wrote xml_dump.txt")


if __name__ == "__main__":
    main()