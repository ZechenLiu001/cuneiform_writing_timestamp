# cuneiform_writing_timestamp

Phase-1 implementation scaffold for the handwriting + voice timeline matching project.

## What is implemented now
- Portable core data models (`core/models.py`)
- V1 processing pipeline (`core/processor.py`):
  - hard-delete erase policy
  - retained-stroke filtering
  - stroke clustering by space+time
  - cluster-level aggregated time range
- ASR enrichment adapter (`core/asr.py`)
  - use provided `transcript_segments` directly when available
  - `mock` provider from `asr_input.mock_segments`
  - `qwen` provider via configurable HTTP endpoint
- Lightweight session log store (`core/session_log.py`)
- CLI runner (`scripts/run_processor.py`)
- Minimal HTTP API (`scripts/run_api.py`)
  - `GET /health`
  - `POST /process`
  - `GET /sessions/{session_id}`
- Example input (`examples/session_example.json`)
- Unit tests (`tests/test_processor.py`, `tests/test_api.py`, `tests/test_asr.py`)

## API behavior (`POST /process`)
- If request already has `transcript_segments`, API uses them directly.
- Otherwise it attempts ASR enrichment using `asr_input` with current provider.

## ASR configuration
```bash
# default
export ASR_PROVIDER=mock

# for qwen http adapter
export ASR_PROVIDER=qwen
export QWEN_ASR_ENDPOINT="https://your-asr-service/process"
export ASR_TIMEOUT_S=8.0
```

### `mock` provider input example
```json
{
  "asr_input": {
    "mock_segments": [
      {
        "start_ts_ms": 1710000122500,
        "end_ts_ms": 1710000125000,
        "start_offset_ms": 2500,
        "end_offset_ms": 5000,
        "text": "mock asr text"
      }
    ]
  }
}
```

## Run
```bash
python scripts/run_processor.py examples/session_example.json
python scripts/run_api.py
python -m unittest discover -s tests -p 'test_*.py' -v
```
