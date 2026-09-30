# LIVE SARVAM TTS VERIFICATION

## Configuration
- **API key configured:** YES (Loaded strictly from server `.env`)
- **Key exposed:** NO (Zero frontend exposure, zero logging)
- **Provider:** Sarvam
- **Model:** Bulbul v3 (`bulbul:v3`)

---

## Language Verification

The following live requests were executed against the active Sarvam Bulbul v3 neural endpoint (`https://api.sarvam.ai/text-to-speech` via `POST /api/v1/tts/synthesize`):

### 1. Hardened Reference Test Sentences

| Language | Code | Speaker | Provider | Model | TTS Mode | HTTP | Bytes | SHA-256 | Duration | Human Listening |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| **English** | `en-IN` | `ratan` | `sarvam` | `bulbul:v3` | `live_sarvam` | `200` | `139,282` | `cbc9b7d8a03efad5a1b0f46a1c5756f946bb17433bb4fc1d9fdb5b59f731ecdd` | `3.157s` | Clear, natural English Indian pronunciation with natural pitch |
| **Hindi** | `hi-IN` | `priya` | `sarvam` | `bulbul:v3` | `live_sarvam` | `200` | `278,520` | `aee6d205034213ffc77414a3cd37f5ce9647f0522a3f7b8b41064fb0be1215e6` | `6.315s` | Clear Devanagari Hindi phonetics, correct numerical/percentage articulation |
| **Kannada** | `kn-IN` | `ishita` | `sarvam` | `bulbul:v3` | `live_sarvam` | `200` | `222,072` | `7ee446b75ad75946aacc8abb250490566aa9584a6648903cef7e0ef8aa7cb506` | `5.035s` | Authentic Kannada cadence, native vowel duration and consonant clusters |
| **Telugu** | `te-IN` | `neha` | `sarvam` | `bulbul:v3` | `live_sarvam` | `200` | `222,072` | `fa325d8efdd791a4878252a55fe3dcf1236bede228a14a50667616b21f9235f8` | `5.035s` | Authentic Telugu cadence, natural inflection on question ending |

*Sample Rate for all live Sarvam Bulbul v3 streams: 22,050 Hz (Mono PCM WAV).*

---

### 2. Real RAG Grounded Answer Spoken Responses

Real document queries evaluated through `embed -> ChromaDB + BM25 -> RRF -> LLM -> Sarvam TTS`:

| Language | RAG Query | RAG State | Speaker | TTS Mode | Audio Bytes | SHA-256 | Duration |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :---: |
| **English** | *"What is the minimum attendance required?"* | `GROUNDED` | `ratan` | `live_sarvam` | `1,825,314` | `c29c082d3c14b57dfb2e150fd935b0eb577f498f61d83629fa879403a415dd7c` | `41.389s` |
| **Hindi** | *"परीक्षा में शामिल होने के लिए न्यूनतम उपस्थिति कितनी होनी चाहिए?"* | `GROUNDED` | `priya` | `live_sarvam` | `666,130` | `07fa758611a8ec32ccb310749fb68dba3032b43a64a7b65d043e57fcb4510ecf` | `15.104s` |
| **Kannada** | *"ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಇರಬೇಕು?"* | `GROUNDED` | `ishita` | `live_sarvam` | `643,552` | `8e13d5edb8d2de86f4afa79574cb227347ef8bcfd7a176d1ae6e215c08f54849` | `14.592s` |
| **Telugu** | *"పరీక్షకు హాజరు కావడానికి కనీస హాజరు ఎంత ఉండాలి?"* | `GROUNDED` | `neha` | `live_sarvam` | `831,712` | `0475135ce1d94b94236d36219d1909880b64761a75cc5941464466d68651703c` | `18.859s` |

---

### 3. Cross-Language Target Mode Speech

| Source Query | Target Selection | Response Language | Speaker | TTS Mode | Audio Bytes | Status |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| English Attendance Query | हिन्दी (`hi`) | `hi` | `priya` | `live_sarvam` | `291,080` | Verified |
| English Attendance Query | ಕನ್ನಡ (`kn`) | `kn` | `ishita` | `live_sarvam` | `541,960` | Verified |
| English Attendance Query | తెలుగు (`te`) | `te` | `neha` | `live_sarvam` | `707,544` | Verified |

---

## Security Verification
- **API key backend-only:** `SARVAM_API_KEY` is accessed exclusively in `app/services/tts/sarvam.py` on the FastAPI backend.
- **No secret logged:** Loggers sanitize error messages and replace any credentials with `***`.
- **No secret returned to frontend:** API responses return only `audio`, `language`, `provider`, `model`, `speaker`, `voice`, and `tts_mode`.
- **.env excluded from git:** `.env` is listed in `.gitignore` and has zero git tracking.

---

## Synthetic vs Live Separation
- **`live_sarvam`:** Activated automatically when `SARVAM_API_KEY` is present. Connects to `https://api.sarvam.ai/text-to-speech` with `bulbul:v3`. Produces unique, high-fidelity neural audio streams with 22,050 Hz sampling rate.
- **`synthetic_test`:** Strictly reserved for offline CI test environments (`settings.APP_ENV == "testing"` or explicit mock tests). Returns deterministic synthetic WAV sine tones (25,644 bytes, 16,000 Hz).
- **Production Guard:** Normal production requests without an API key reject the request with HTTP 503 instead of silently presenting synthetic audio as real speech.

---

## Real Chrome Browser Verification
- Executed via Playwright on `/Applications/Google Chrome.app`:
  - English, Hindi, Kannada, Telugu answers dynamically trigger `POST /api/v1/tts/synthesize`.
  - Frontend `SpeakButton` creates `new Audio("data:audio/wav;base64,...").play()` and plays the live Sarvam neural audio cleanly.
  - Active audio stops immediately when Stop is clicked or a new language turn begins.
  - Voice Response mode automatically plays live neural audio when enabled.

---

## Final Status

**LIVE SARVAM TTS VERIFIED**
