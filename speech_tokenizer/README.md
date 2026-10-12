# Speech tokenizer audio comparisons

The page is served at `/speech_tokenizer/`. Comparison groups come from
`_data/speech_tokenizer.json`; adding a group does not require editing the page.

Every group must have these three audio roles, in this order:

| Role key | Page label | Purpose |
| --- | --- | --- |
| `timbre` | 提音色的音频 | Reference audio used to extract speaker timbre |
| `content` | 提内容的音频 | Source audio used to extract speech/content tokens |
| `synthesis` | 合成之后的音频 | Speech reconstructed from those two features |

All three original WAV files are required. Imported files are copied byte for
byte, and their SHA-256 hashes identify the specific audio being compared.

## Add a comparison group

Run from the repository root, using a new stable group ID:

```sh
python3 _scripts/add_speech_tokenizer_group.py \
  --id example-002 \
  --title "第二组：音色与内容组合" \
  --description "比较参考音色、内容源与重建语音。" \
  --method Kanade \
  --tag English \
  --timbre /path/to/timbre-reference.wav \
  --content /path/to/content-source.wav \
  --synthesis /path/to/synthesized.wav
python3 _scripts/validate_speech_tokenizer.py
```

The importer reads WAV metadata, copies the three files into
`assets/audio/speech_tokenizer/example-002/`, and atomically updates the manifest.
It refuses to overwrite an existing group ID or audio directory. Local input
paths are used only to read the files and are never written into the manifest.
Use one importer at a time and review the resulting changes before committing.

Optional flags include repeatable `--tag`, `--timbre-transcript`, and
`--content-transcript`. Transcripts default to empty strings and can be filled in
later. The three audio arguments are always mandatory. Use `--root` to target a
different checkout explicitly.

To edit an existing group, update its manifest entry and audio files deliberately,
then rerun the validator. Changing an audio file also requires updating its hash
and metadata; the validator rejects stale entries.

## Manifest contract

The document has `schemaVersion: 1` and a `groups` array. IDs use letters,
numbers, underscores, and hyphens and must be unique. Every group has:

```json
{
  "id": "example-002",
  "title": "第二组：音色与内容组合",
  "description": "比较参考音色、内容源与重建语音。",
  "method": "Kanade",
  "tags": ["English"],
  "audio": {
    "timbre": {
      "src": "assets/audio/speech_tokenizer/example-002/timbre.wav",
      "label": "提音色的音频",
      "duration": 22.72,
      "sampleRate": 24000,
      "channels": 1,
      "sha256": "<64 lowercase hexadecimal characters>"
    },
    "content": {
      "src": "assets/audio/speech_tokenizer/example-002/content.wav",
      "label": "提内容的音频",
      "duration": 30.0,
      "sampleRate": 24000,
      "channels": 1,
      "sha256": "<64 lowercase hexadecimal characters>"
    },
    "synthesis": {
      "src": "assets/audio/speech_tokenizer/example-002/synthesis.wav",
      "label": "合成之后的音频",
      "duration": 30.0,
      "sampleRate": 24000,
      "channels": 1,
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  },
  "transcripts": {
    "timbre": "",
    "content": ""
  },
  "notes": []
}
```

`notes` is optional; all other properties above are required. Duration is measured
in seconds, sample rate in Hz, and channels is an integer. The `audio` object
must have exactly `timbre`, `content`, and `synthesis`. Audio `src` values are
repository-relative paths without a leading slash. Workstation paths, URLs,
`..` path traversal, and symlinks escaping the repository are rejected.

## Validate

```sh
python3 _scripts/validate_speech_tokenizer.py
```

The validator uses only the Python standard library and exits with a nonzero
status for missing roles, duplicate IDs, invalid paths, missing files, malformed
WAV chunks, metadata mismatches, or hash mismatches. It supports PCM, IEEE float,
and supported PCM/float WAVE_FORMAT_EXTENSIBLE files, including extended headers
and odd-sized padded chunks. Validation preserves all original audio bytes.

For a separate manifest or checkout:

```sh
python3 _scripts/validate_speech_tokenizer.py \
  --root /path/to/checkout \
  --manifest /path/to/manifest.json
```

Header/hash validation confirms that the intended assets are present. Preview the
page and listen to each role when checking playback and the audible comparison.
