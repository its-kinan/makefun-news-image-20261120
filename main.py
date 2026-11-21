#!/usr/bin/env python3
"""news-image-20261120 entry: copy the built front page to /output/entry.png.

The image (entry.png beside this file) is the agent-built front page for
20 November 2026: masthead with the date plus four stories — Russia's
overnight barrage on Kyiv, the AI stock sell-off, Cyclone Akvan's
landfall in Odisha, and the 6.7 quake in Peru. The program only copies
bytes, so both grader runs write identical output. Outside the grader,
MAKEFUN_OUTPUT_DIR stands in for /output:
  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import hashlib
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576
MAX_SIDE = 1024


def fail(msg):
    raise SystemExit("entry.png: " + msg)


def check_magic(head):
    if head[:8] != PNG_MAGIC:
        fail("not a PNG file")


def check_ihdr(head):
    """The first chunk must be IHDR; width/height live at fixed offsets
    inside it, so reading them without this check would misread a file
    whose first chunk is something else."""
    if head[12:16] != b"IHDR":
        fail("first chunk is not IHDR")
    width, height = struct.unpack(">II", head[16:24])
    if width > MAX_SIDE or height > MAX_SIDE:
        fail("%dx%d, over 1024 px a side" % (width, height))
    if width == 0 or height == 0:
        fail("zero dimension in IHDR")
    return width, height


def check_trailer(path):
    with open(path, "rb") as f:
        f.seek(-12, os.SEEK_END)
        tail = f.read(12)
    if tail[4:8] != b"IEND":
        fail("truncated, no IEND trailer")


def check_size(path):
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        fail("%d bytes, over the 1 MiB cap" % size)
    return size


def check_png(path):
    """Refuse to ship a file the gate would reject: bad magic, a first
    chunk that is not IHDR, oversize, over 1024 px a side, or a
    truncated file with no IEND trailer. A corrupt copy fails loudly
    here, before anything is written, instead of failing silently
    downstream."""
    with open(path, "rb") as f:
        head = f.read(33)
    check_magic(head)
    width, height = check_ihdr(head)
    check_trailer(path)
    size = check_size(path)
    return width, height, size


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    src = os.path.join(HERE, "entry.png")
    width, height, size = check_png(src)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    if sha256_file(dst) != sha256_file(src):
        fail("copy mismatch, destination differs from source")
    print("entry.png %dx%d %d bytes -> %s"
          % (width, height, size, out_dir))


if __name__ == "__main__":
    main()
