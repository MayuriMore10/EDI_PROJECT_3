# EDI 810 Validator

## Run

1. Create venv and install deps
2. Start API

```bash
./venv/Scripts/uvicorn backend.app.main:app --reload
```

3. Open frontend by a simple server or open `frontend/index.html` directly.

## Notes
- Prototype includes placeholder parsing and comparison.
- Extend parsers in `backend/app` to produce real XML and validation.


