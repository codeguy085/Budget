"""Compile Django .po files to .mo without needing GNU gettext.

Run from the project root:
    python scripts/compile_po.py

Walks every locale/*/LC_MESSAGES/*.po and writes a matching .mo next to it.
"""
import ast
import re
import struct
import sys
from pathlib import Path


def _to_bytes(x, encoding):
    return x if isinstance(x, bytes) else x.encode(encoding)


def parse_po(path):
    """Parse a .po file. Returns {key_bytes: value_bytes}."""
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8")

    messages = {}
    lines = text.splitlines()
    i = 0
    encoding = "utf-8"

    def read_string(idx):
        """Read a msgid/msgstr string starting at line idx (which begins with the keyword).
        Returns (string_value_str, next_idx).
        """
        line = lines[idx].strip()
        # Extract the part after the keyword up to the first "
        first_quote = line.find('"')
        result = ""
        if first_quote >= 0:
            result += ast.literal_eval(line[first_quote:])
        idx += 1
        while idx < len(lines):
            l = lines[idx].strip()
            if l.startswith('"'):
                result += ast.literal_eval(l)
                idx += 1
            else:
                break
        return result, idx

    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        msgctxt = None
        msgid = None
        msgid_plural = None
        msgstr = None
        msgstr_plurals = {}

        if line.startswith("msgctxt"):
            msgctxt, i = read_string(i)
            line = lines[i].strip() if i < len(lines) else ""

        if line.startswith("msgid_plural"):
            i += 1  # shouldn't happen without msgid
            continue

        if line.startswith("msgid"):
            msgid, i = read_string(i)
        else:
            i += 1
            continue

        line = lines[i].strip() if i < len(lines) else ""
        if line.startswith("msgid_plural"):
            msgid_plural, i = read_string(i)
            # Read msgstr[0], msgstr[1], ...
            while i < len(lines):
                l = lines[i].strip()
                m = re.match(r"msgstr\[(\d+)\]", l)
                if not m:
                    break
                idx_n = int(m.group(1))
                s, i = read_string(i)
                msgstr_plurals[idx_n] = s
        elif line.startswith("msgstr"):
            msgstr, i = read_string(i)

        # Detect encoding from empty msgid header
        if msgid == "" and msgstr:
            m = re.search(r"charset=([^\s\\]+)", msgstr)
            if m:
                encoding = m.group(1)

        if msgid_plural is not None:
            key = msgid.encode(encoding) + b"\0" + msgid_plural.encode(encoding)
            plural_bytes = []
            for n in sorted(msgstr_plurals.keys()):
                plural_bytes.append(msgstr_plurals[n].encode(encoding))
            if plural_bytes and any(plural_bytes):
                messages[key] = b"\0".join(plural_bytes)
        elif msgid and msgstr:
            key_bytes = msgid.encode(encoding)
            if msgctxt is not None:
                key_bytes = msgctxt.encode(encoding) + b"\x04" + key_bytes
            messages[key_bytes] = msgstr.encode(encoding)
        elif msgid == "" and msgstr:
            # Header entry
            messages[b""] = msgstr.encode(encoding)

    return messages


def generate_mo(messages):
    keys = sorted(messages.keys())
    offsets = []
    ids = strs = b""
    for key in keys:
        offsets.append((len(ids), len(key), len(strs), len(messages[key])))
        ids += key + b"\0"
        strs += messages[key] + b"\0"

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)

    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    offsets = koffsets + voffsets

    output = struct.pack(
        "Iiiiiii",
        0x950412de,
        0,
        len(keys),
        7 * 4,
        7 * 4 + len(keys) * 8,
        0,
        0,
    )
    output += struct.pack("i" * len(offsets), *offsets)
    output += ids
    output += strs
    return output


def main():
    root = Path(__file__).resolve().parent.parent
    locale = root / "locale"
    if not locale.exists():
        print(f"No locale directory at {locale}")
        sys.exit(1)
    count = 0
    for po in locale.rglob("*.po"):
        mo = po.with_suffix(".mo")
        messages = parse_po(po)
        with open(mo, "wb") as f:
            f.write(generate_mo(messages))
        print(f"Compiled {po.relative_to(root)} -> {mo.relative_to(root)} ({len(messages)} entries)")
        count += 1
    if count == 0:
        print("No .po files found.")
    else:
        print(f"Done. {count} file(s) compiled.")


if __name__ == "__main__":
    main()
