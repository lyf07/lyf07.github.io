# Speech tokenizer comparison page

These instructions apply to the speech tokenizer page and its supporting files:
`_pages/speech_tokenizer.html`, `_data/speech_tokenizer.json`,
`assets/css/speech_tokenizer.css`, `assets/js/speech_tokenizer.js`,
`assets/audio/speech_tokenizer/`, `_scripts/*speech_tokenizer*.py`, and
`speech_tokenizer/README.md`. They do not change other pages on this site.

This is a standalone, intentionally unlisted listening page. Keep `layout: null`,
`nav: false`, and `sitemap: false`, with its own complete HTML document and styles.
Do not add links to it in the main site's navigation, homepage, or search index.
Keep a `noindex` robots meta tag. Preserve the direct URL `/speech_tokenizer/`.
Its design must remain independent of the academic homepage; do not inherit the
homepage header, footer, theme styles, or theme scripts.

The user requires **every comparison group to contain all three audio roles**:

1. `timbre`: 提音色的音频 — the reference from which speaker timbre is extracted.
2. `content`: 提取音频token — the source from which speech tokens are extracted.
3. `synthesis`: 合成之后的音频 — the reconstruction combining those features.

Keep these stable role keys and display order when adding or editing groups. Never
publish an incomplete group or silently substitute a different audio file.

Show each group's actual speech tokenizer (`group.method`) prominently beside
its comparison number. The opening section must state the number and names of
available tokenizers, derived from the manifest's unique `method` values. Use
speech token terminology for the token source throughout the page. The
voice-generation model is secondary and should not
dominate titles, tags, or audio labels. Keep body text around 16px and secondary
labels at least 14px on desktop and mobile; never shrink text to fit a narrow card.

Use `_data/speech_tokenizer.json` as the single group manifest. Each audio entry
must specify `src`, `label`, `duration`, `sampleRate`, `channels`, and `sha256`.
Store the three files at `assets/audio/speech_tokenizer/<group-id>/<role>.wav`.
Preserve the complete original WAV bytes when importing; do not normalize,
resample, trim, or transcode an audio comparison without an explicit request.

Public data and page text must not contain workstation absolute paths. Keep audio
URLs repository relative, without a leading slash, and render them with Jekyll's
`relative_url` filter. Describe which audio provides timbre, speech tokens, and the
result; do not present unverified voice or accent claims as established results.

Prefer `_scripts/add_speech_tokenizer_group.py` for new groups. Run
`python3 _scripts/validate_speech_tokenizer.py` after any manifest/audio update
and before publishing. Check actual browser playback when changing audio formats
or player behavior. See `speech_tokenizer/README.md` for the data contract and
import command.
