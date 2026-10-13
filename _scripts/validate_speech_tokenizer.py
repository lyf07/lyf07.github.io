#!/usr/bin/env python3
"""Validate the complete three-audio-group manifest using Python stdlib only."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys


ROLES = ("timbre", "content", "synthesis")
LABELS = {
    "timbre": "提音色的音频",
    "content": "提取音频token",
    "synthesis": "合成之后的音频",
}
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
WORKSTATION_PATH_RE = re.compile(
    r"(?:^|[\s\"'=:(])(?:/(?:proj|home|Users|tmp|u|mnt|workspace|var|private)/|[A-Za-z]:[\\/])"
)


class ValidationError(ValueError):
    """An actionable manifest or WAV validation failure."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def inspect_wav(payload, name="audio"):
    """Read RIFF WAV metadata; support PCM, float, and extensible fmt chunks."""
    require(len(payload) >= 12, f"{name}: truncated WAV header")
    require(payload[:4] == b"RIFF" and payload[8:12] == b"WAVE",
            f"{name}: expected a RIFF/WAVE file")
    riff_size = struct.unpack_from("<I", payload, 4)[0]
    require(riff_size + 8 == len(payload), f"{name}: RIFF size does not match file length")
    chunks = {}
    offset = 12
    while offset < len(payload):
        require(offset + 8 <= len(payload), f"{name}: truncated chunk header")
        chunk_id = payload[offset:offset + 4]
        size = struct.unpack_from("<I", payload, offset + 4)[0]
        start = offset + 8
        end = start + size
        padded_end = end + (size % 2)
        require(padded_end <= len(payload), f"{name}: truncated {chunk_id!r} chunk")
        if chunk_id in (b"fmt ", b"data", b"fact"):
            require(chunk_id not in chunks, f"{name}: duplicate {chunk_id!r} chunk")
            chunks[chunk_id] = (start, size)
        offset = padded_end
    require(b"fmt " in chunks and b"data" in chunks, f"{name}: missing fmt or data chunk")
    fmt_start, fmt_size = chunks[b"fmt "]
    require(fmt_size >= 16, f"{name}: truncated fmt chunk")
    audio_format, channels, sample_rate, byte_rate, block_align, bits = struct.unpack_from(
        "<HHIIHH", payload, fmt_start
    )
    require(fmt_size != 17, f"{name}: incomplete fmt extension length")
    if fmt_size >= 18:
        extension_size = struct.unpack_from("<H", payload, fmt_start + 16)[0]
        require(extension_size <= fmt_size - 18, f"{name}: truncated fmt extension")
    if audio_format == 0xFFFE:
        require(fmt_size >= 40 and extension_size >= 22,
                f"{name}: truncated WAVE_FORMAT_EXTENSIBLE header")
        valid_bits = struct.unpack_from("<H", payload, fmt_start + 18)[0]
        guid = payload[fmt_start + 24:fmt_start + 40]
        require(guid[4:] == bytes.fromhex("00001000800000aa00389b71"),
                f"{name}: unsupported extensible format GUID")
        audio_format = struct.unpack_from("<I", guid)[0]
        require(0 < valid_bits <= bits, f"{name}: invalid valid-bits value")
    require(audio_format in (1, 3), f"{name}: unsupported WAV format {audio_format}")
    require(channels > 0 and sample_rate > 0, f"{name}: invalid channels or sample rate")
    allowed_bits = (8, 16, 24, 32) if audio_format == 1 else (32, 64)
    require(bits in allowed_bits, f"{name}: unsupported sample width {bits}")
    require(block_align == channels * (bits // 8), f"{name}: invalid block alignment")
    require(byte_rate == sample_rate * block_align, f"{name}: invalid byte rate")
    _, data_size = chunks[b"data"]
    require(data_size > 0 and data_size % block_align == 0,
            f"{name}: empty or misaligned audio data")
    frames = data_size // block_align
    if b"fact" in chunks:
        fact_start, fact_size = chunks[b"fact"]
        require(fact_size >= 4, f"{name}: truncated fact chunk")
        fact_frames = struct.unpack_from("<I", payload, fact_start)[0]
        require(fact_frames == frames, f"{name}: fact frame count does not match audio data")
    return {
        "duration": frames / sample_rate,
        "sampleRate": sample_rate,
        "channels": channels,
        "frames": frames,
        "format": "PCM" if audio_format == 1 else "FLOAT",
        "bits": bits,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _check_public_strings(value, location="manifest"):
    if isinstance(value, str):
        require(not WORKSTATION_PATH_RE.search(value),
                f"{location}: contains a workstation absolute path")
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_public_strings(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_public_strings(item, f"{location}[{index}]")


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_data(data, root):
    """Validate manifest data and every audio asset, returning role summaries."""
    root = Path(root).resolve()
    require(isinstance(data, dict), "manifest must be a JSON object")
    require(type(data.get("schemaVersion")) is int and data["schemaVersion"] == 1,
            "schemaVersion must be 1")
    groups = data.get("groups")
    require(isinstance(groups, list) and groups, "groups must be a nonempty array")
    _check_public_strings(data)
    seen_ids = set()
    summaries = []
    for index, group in enumerate(groups):
        context = f"groups[{index}]"
        require(isinstance(group, dict), f"{context}: group must be an object")
        group_id = group.get("id")
        require(isinstance(group_id, str) and ID_RE.fullmatch(group_id),
                f"{context}: invalid group id")
        require(group_id not in seen_ids, f"{context}: duplicate group id {group_id}")
        seen_ids.add(group_id)
        context = group_id
        for key in ("title", "description", "method"):
            require(_nonempty_string(group.get(key)), f"{context}: {key} must be a nonempty string")
        tags = group.get("tags")
        require(isinstance(tags, list) and all(_nonempty_string(tag) for tag in tags),
                f"{context}: tags must be an array of nonempty strings")
        audio = group.get("audio")
        require(isinstance(audio, dict) and set(audio) == set(ROLES),
                f"{context}: audio must contain exactly timbre, content, synthesis")
        transcripts = group.get("transcripts")
        require(isinstance(transcripts, dict) and set(transcripts) == {"timbre", "content"}
                and all(isinstance(text, str) for text in transcripts.values()),
                f"{context}: transcripts must contain timbre and content strings")
        notes = group.get("notes", [])
        require(isinstance(notes, list) and all(_nonempty_string(note) for note in notes),
                f"{context}: notes must be an array of nonempty strings")
        for role in ROLES:
            entry = audio[role]
            name = f"{context}/{role}"
            require(isinstance(entry, dict), f"{name}: audio entry must be an object")
            expected_src = f"assets/audio/speech_tokenizer/{group_id}/{role}.wav"
            require(entry.get("src") == expected_src,
                    f"{name}: src must be {expected_src}")
            require(_nonempty_string(entry.get("label")), f"{name}: label must be a nonempty string")
            require(isinstance(entry.get("sha256"), str) and SHA_RE.fullmatch(entry["sha256"]),
                    f"{name}: sha256 must contain 64 lowercase hexadecimal characters")
            duration = entry.get("duration")
            require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
                    f"{name}: duration must be a finite positive number")
            for key in ("sampleRate", "channels"):
                require(type(entry.get(key)) is int and entry[key] > 0,
                        f"{name}: {key} must be a positive integer")
            path = (root / expected_src).resolve()
            require(path.is_relative_to(root), f"{name}: audio path escapes repository")
            require(path.is_file(), f"{name}: audio file is missing")
            actual = inspect_wav(path.read_bytes(), name)
            require(entry["sha256"] == actual["sha256"], f"{name}: SHA-256 mismatch")
            for key in ("sampleRate", "channels"):
                require(entry[key] == actual[key], f"{name}: {key} does not match WAV header")
            require(math.isclose(duration, actual["duration"], rel_tol=0, abs_tol=1e-6),
                    f"{name}: duration does not match WAV frame count")
            summaries.append({"group": group_id, "role": role, **actual})
    return summaries


def load_manifest(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"cannot read manifest: {error}") from error


def validate_manifest(manifest_path, root):
    return validate_data(load_manifest(manifest_path), root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    manifest = args.manifest or args.root / "_data/speech_tokenizer.json"
    try:
        summaries = validate_manifest(manifest, args.root)
    except (ValidationError, OSError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(summaries) // len(ROLES)} complete group(s), {len(summaries)} WAV files.")
    for item in summaries:
        print(f"  {item['group']}/{item['role']}: {item['duration']:.2f}s, "
              f"{item['sampleRate']} Hz, {item['channels']} channel(s), "
              f"{item['format']} {item['bits']}-bit, SHA-256 verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
