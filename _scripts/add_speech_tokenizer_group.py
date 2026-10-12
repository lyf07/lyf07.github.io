#!/usr/bin/env python3
"""Import a complete audio comparison group without changing original WAV bytes."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from validate_speech_tokenizer import (
    ID_RE, LABELS, ROLES, ValidationError, inspect_wav, load_manifest, require, validate_data,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--id", required=True, dest="group_id")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--method", default="Kanade")
    parser.add_argument("--tag", action="append", default=[], dest="tags")
    for role in ROLES:
        parser.add_argument(f"--{role}", required=True, type=Path)
    parser.add_argument("--timbre-transcript", default="")
    parser.add_argument("--content-transcript", default="")
    return parser.parse_args(argv)


def import_group(args):
    root = args.root.resolve()
    require(ID_RE.fullmatch(args.group_id), "invalid group id: use letters, numbers, underscores, or hyphens")
    manifest_path = root / "_data/speech_tokenizer.json"
    require(manifest_path.parent.is_dir(), "repository _data directory is missing")
    require(manifest_path.parent.resolve().is_relative_to(root), "manifest directory escapes repository")
    lock_path = manifest_path.parent / ".speech_tokenizer-import.lock"
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise ValidationError("another import is in progress; check the import lock before retrying") from error
    os.close(lock_fd)
    staging_path = None
    manifest_temp = None
    created_destination = None
    committed = False
    try:
        original_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
        data = load_manifest(manifest_path) if original_manifest is not None else {
            "schemaVersion": 1, "groups": []
        }
        if original_manifest is not None:
            validate_data(data, root)
        require(not any(group["id"] == args.group_id for group in data["groups"]),
                f"group id already exists: {args.group_id}")
        audio_parent = root / "assets/audio/speech_tokenizer"
        require(audio_parent.resolve().is_relative_to(root), "audio directory escapes repository")
        audio_parent.mkdir(parents=True, exist_ok=True)
        destination = audio_parent / args.group_id
        require(not destination.exists() and not destination.is_symlink(),
                f"audio directory already exists: {args.group_id}")
        blobs = {}
        audio = {}
        for role in ROLES:
            source = getattr(args, role)
            require(source.is_file(), f"{role}: input WAV is missing")
            blobs[role] = source.read_bytes()
            metadata = inspect_wav(blobs[role], role)
            audio[role] = {
                "src": f"assets/audio/speech_tokenizer/{args.group_id}/{role}.wav",
                "label": LABELS[role],
                **{key: metadata[key] for key in ("duration", "sampleRate", "channels", "sha256")},
            }
        group = {
            "id": args.group_id,
            "title": args.title,
            "description": args.description,
            "method": args.method,
            "tags": args.tags,
            "audio": audio,
            "transcripts": {"timbre": args.timbre_transcript, "content": args.content_transcript},
        }
        data["groups"].append(group)
        staging_path = Path(tempfile.mkdtemp(prefix=f".{args.group_id}-", dir=audio_parent))
        for role, payload in blobs.items():
            (staging_path / f"{role}.wav").write_bytes(payload)
        require(not destination.exists(), "audio directory appeared during import; retry with a new id")
        staging_path.rename(destination)
        staging_path = None
        created_destination = destination
        validate_data(data, root)
        current_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
        require(current_manifest == original_manifest,
                "manifest changed during import; retry after reviewing concurrent changes")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".speech_tokenizer-",
                                         suffix=".tmp", dir=manifest_path.parent, delete=False) as handle:
            manifest_temp = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        current_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
        require(current_manifest == original_manifest,
                "manifest changed during import; retry after reviewing concurrent changes")
        os.replace(manifest_temp, manifest_path)
        manifest_temp = None
        committed = True
        return group
    finally:
        if staging_path is not None:
            shutil.rmtree(staging_path)
        if created_destination is not None and not committed:
            shutil.rmtree(created_destination)
        if manifest_temp is not None:
            manifest_temp.unlink(missing_ok=True)
        lock_path.unlink(missing_ok=True)


def main(argv=None):
    args = parse_args(argv)
    try:
        group = import_group(args)
    except (ValidationError, OSError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1
    print(f"Imported complete group {group['id']}: timbre, content, synthesis.")
    print("Original WAV bytes preserved; manifest and all audio hashes validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
