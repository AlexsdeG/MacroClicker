# Goals (what the plan delivers)

* Name MacroPosFlow
* A modular Python project that records & replays mouse/keyboard actions, with delays and a global emergency stop.
* Configurable action sequences saved as JSON/YAML.
* Fast pixel/area detection (mss + NumPy) and optional OCR (pytesseract).
* Multi-monitor-aware coordinates (monitor + relative coords).
* Pluggable CLI (console-menu first, easy swap to simple-term-menu or Textual).
* Tests, sample data, and a small codebase that's easy for an AI-agent to implement and extend.

---

# High-level phased roadmap

## Phase 0 — Project bootstrap (very small, prep)

**Goal:** create the repo skeleton, basic dev tooling and dependency list so coding starts smoothly.
**Sub-steps**

1. Create repo and top-level files: `README.md`, `LICENSE` (MIT recommended), `pyproject.toml` or `requirements.txt`. List dependencies: `pyautogui`, `pynput`, `mss`, `numpy`, `pytesseract` (optional), `console-menu` (or `simple-term-menu`), `pytest`.
2. Add a short CONTRIBUTING.md and coding style notes (PEP8).
3. Create skeleton package and example macro JSON folder: `/macros/sample.json`.
4. Create CI skeleton (optional): `github/workflows/python.yml` that runs tests.

**Acceptance criteria**

* Repo skeleton exists and dependencies listed.
* CI runs a placeholder test.

---

## Phase 1 — Minimal working prototype (MVP)

**Goal:** record single-point clicks, store them, replay sequence, global Esc stop; one CLI using `console-menu`. Keep everything synchronous and single-monitor (but store coords with monitor id for later).
**Sub-steps**

1. Implement `recorder` module

   * Listen for a hotkey (F3) using `pynput` to capture `mouse.position()` and append a step.
   * Each captured step: `{type:"click", monitor:<id>, rel_x:<float>, rel_y:<float>, button:"left", delay:0.1}` where `rel_x`/`rel_y` are ratios relative to monitor bounds (0..1).
2. Implement `executor` module

   * Simple loop that reads action sequence and performs `pyautogui.moveTo(abs_x, abs_y)` + `pyautogui.click()` with `time.sleep(delay)`.
   * Respect global `STOP` flag set by `pynput` Esc handler running in a separate thread.
3. Implement `cli_consolemenu` module

   * Menu items: `Record new point`, `List points`, `Run`, `Save`, `Load`, `Exit`.
   * Use `console-menu` for simple menu flows. Keep `cli.py` as an adapter so other CLI libs can be swapped.
4. Implement `config` module (JSON save/load).
5. Add simple logging and a small `main.py` that wires everything.

**Acceptance criteria**

* User can press F3 to record a point, see it in the menu, save the macro, load it, and run it.
* Pressing Esc at any time stops the runner immediately.

---

## Phase 2 — Robustness & reorder/edit actions

**Goal:** add editing of the sequence, action types (wait, keypress), insert/reorder, graceful failure handling and tests for core modules.
**Sub-steps**

1. Expand action types: `click`, `wait`, `keypress`, `type_text`.
2. CLI additions: reorder, insert action at index, delete action, edit action params (delay/button/key/text).
3. Add unit tests:

   * Mock `pyautogui` and `pynput` calls (use `unittest.mock`) to assert executor calls expected sequences.
   * Tests for `config.load/save` roundtrip.
4. Add input validation, error handling (invalid coordinates, missing monitor).
5. Add `--dry-run` mode: print actions without executing.

**Acceptance criteria**

* All action types are editable and covered by unit tests.
* Dry-run prints the absolute coordinates that will be used.

---

## Phase 3 — Multi-monitor & coordinate robustness

**Goal:** full support for two or more monitors; store monitor id + relative coordinates; add an interactive point selection flow that tells the user which monitor and relative coords were captured.
**Sub-steps**

1. Implement `display_manager` module:

   * Use `mss` to enumerate monitors and their bounding boxes.
   * Expose helper functions: `abs_from_monitor_rel(monitor_id, rel_x, rel_y)` and `monitor_rel_from_abs(x, y)`.
2. When recording (F3 flow), capture monitor id and rel coords; show textual confirmation in CLI.
3. Update executor to translate rel coords via `display_manager`.
4. Add tests for coordinate conversion functions (use synthetic monitor rectangles).

**Acceptance criteria**

* Actions saved show monitor + rel coords.
* Running a macro on a system with different monitor layout calculates absolute coordinates correctly.

---

## Phase 4 — Pixel & area detection (fast lightweight)

**Goal:** add triggers that wait for pixel or average-area thresholds using `mss` + `numpy` (no OpenCV yet).
**Sub-steps**

1. Add new action types:

   * `wait_for_pixel` — check that pixel at (monitor, relx,rely) matches color (with tolerance).
   * `wait_for_area` — sample rectangular area, compute mean brightness or channel difference, trigger when above/below threshold.
2. Implement `vision` module (mss + numpy):

   * Fast grab of required region.
   * Pixel compare with tolerance or area average calculation.
3. Add CLI flows for selecting an area: prompt user to press F3 for top-left, F4 for bottom-right; compute rel rect stored in action.
4. Add timeout parameter and polling interval for wait actions.
5. Add unit tests using synthetic images (save small PNGs and simulate mss grabs by monkeypatching the screenshot function).

**Acceptance criteria**

* Wait actions work reliably on test images and stop on Esc.
* CLI allows selecting regions via hotkeys and saves correctly.

---

## Phase 5 — OCR integration (pytesseract)

**Goal:** add `wait_for_text` action that runs OCR on a defined area and checks for text or regex.
**Sub-steps**

1. Add `ocr` submodule wrapper:

   * `ocr.read_text_from_region(monitor, rect)` returns text (postprocessing: strip, lower).
   * Document requirement: Tesseract binary must be installed and `TESSDATA_PREFIX` set (readme note).
2. Implement action type: `wait_for_text` with fields: `pattern` (string or regex), `match_type` (contains/exact/regex), `timeout`, `poll_interval`.
3. Add CLI flow to create `wait_for_text` actions (area selection + pattern).
4. Tests:

   * Provide PNG test images with known simple text.
   * Mock pytesseract to return known strings for unit tests.
5. Add retry/backoff and basic preprocessing options (grayscale, thresholding) as config flags.

**Acceptance criteria**

* `wait_for_text` works on test images with expected strings.
* README contains setup steps for Tesseract.

---

## Phase 6 — Advanced detection (OpenCV templates) + smoothing/randomness

**Goal:** Add template matching via OpenCV for robust image detection; add mouse-movement smoothing and click randomness to avoid identical clicks.
**Sub-steps**

1. Add optional dependency `opencv-python`.
2. Add `vision.template_match(image, region=None, threshold=0.85, multi_scale=False)` function with return of absolute center coords or None.
3. Add new actions: `click_on_template`, `wait_for_template`.
4. Implement movement smoothing & randomness:

   * `movement.smooth_move(start, end, duration)` using easing functions and many small `pyautogui.moveTo` calls.
   * `click_randomize(x,y, radius)` that chooses a random point within a radius.
   * Config options to enable/disable randomness and set jitter radius / speed variation.
5. Tests:

   * Template matching tests using small images.
   * Movement functions unit-tests for path samples (no real mouse movement — mock pyautogui).
6. Add fallback logic: if `pyautogui` doesn't register in some environments, provide guidance and placeholder for `pydirectinput` later.

**Acceptance criteria**

* Template matching works on provided test images.
* Movement smoothing function produces plausible intermediate steps and is mock-tested.

---

## Phase 7 — Richer CLI & extensibility (Textual optional) + plugin hooks

**Goal:** make CLI interchangeable, add plugin hooks for future GUI, and finalize docs and packaging.
**Sub-steps**

1. Create `cli_adapter` layer so `console-menu`, `simple-term-menu`, or `textual` implementations can be plugged without changing core modules.
2. Implement a `textual`-based demo (optional) for better UX. Keep it as separate CLI backend.
3. Add hooks and interfaces:

   * `before_action(action)`, `after_action(action)` — allow future plugins/loggers to register.
4. Add packaging: `setup.cfg`/`pyproject.toml`, entrypoint console script `clickflow` or chosen name.
5. Add final integration tests that run a test macro against sample images (can skip actual clicking by mocking `pyautogui`).
6. Documentation: user guide, developer guide, JSON schema reference, troubleshooting (DPI scaling, Tesseract, multi-monitor).

**Acceptance criteria**

* CLI adapter works; switching from `console-menu` to `simple-term-menu` requires only swapping the adapter implementation.
* Packaging installs a CLI entrypoint that runs `main.py`.

---

## Phase 8 — Polish & hardening

**Goal:** production-ready features, error resilience, optionally Windows-only improvements.
**Sub-steps**

1. Add logging levels and debug logs (file + console).
2. Add safe-run wrappers: confirm before executing destructive macros; add `max_runtime` guard.
3. Add configuration file (YAML) for global settings (randomness, default delays, polling intervals).
4. Optional: add `pywinauto` or `pydirectinput` support for specialized Windows/game scenarios (plugin).
5. Add E2E tests on CI that run core functions with mocks.

**Acceptance criteria**

* Clear docs and tested critical functions.
* Project can be installed and used by an end-user with minimal setup.

---

# Folder & file structure (simple, modular)

```
clickflow/                 # package root
├─ clickflow/__init__.py
├─ main.py                 # entry point that wires CLI + modules
├─ cli/                    # CLI adapters
│  ├─ __init__.py
│  ├─ consolemenu_cli.py   # default implementation using console-menu
│  └─ textual_cli.py       # optional: Textual adapter
├─ recorder.py             # record hotkeys (F3) & build actions
├─ executor.py             # main executor loop (interprets actions)
├─ input_control.py        # wrappers around pyautogui / pynput (move, click, press)
├─ vision.py               # mss + numpy helpers (pixel/area), optional OpenCV wrappers
├─ ocr_wrapper.py          # pytesseract wrapper + preprocessing helpers
├─ display_manager.py      # monitor enumeration and conversion helpers
├─ config.py               # load/save macros (JSON), global config
├─ movement.py             # smoothing & randomization helpers
├─ tests/                  # test folder
│  ├─ test_executor.py
│  ├─ test_config.py
│  ├─ test_vision.py
│  └─ assets/              # sample images for vision/ocr tests
├─ macros/                 # sample macros
│  └─ sample_download.json
└─ README.md
```

Keep modules concise — each ~200–400 lines at first. Don't prematurely split into subpackages until complexity demands it.

---

# Core data model (JSON schema — simplified)

Use JSON for macros (human-editable). Example:

```json
{
  "meta": {"name": "sample-macro", "author": "you", "created": "2025-09-20"},
  "actions": [
    {"type":"click","monitor":1,"rel_x":0.5,"rel_y":0.6,"button":"left","delay":0.2},
    {"type":"wait","seconds":0.5},
    {"type":"wait_for_area","monitor":1,"rel_rect":[0.45,0.55,0.1,0.05],"metric":"avg_brightness","operator":"<","threshold":120,"timeout":30,"poll":0.5},
    {"type":"click_on_template","image":"assets/download_btn.png","threshold":0.88},
    {"type":"type_text","text":"done","enter":true}
  ]
}
```

* `monitor` is 1-based index matching `mss` monitor list.
* `rel_rect`: `[rel_left, rel_top, rel_width, rel_height]` all 0..1 values.

---

# Testing strategy (important for AI agent)

1. **Unit tests**:

   * Mock `pyautogui` and `pynput` so no real input occurs. Validate `executor` calls expected functions.
   * Test coordinate computations (monitor rel ↔ abs).
   * Test config load/save roundtrip.
2. **Vision tests**:

   * Use small PNG images in `tests/assets/` and monkeypatch `vision.screenshot()` to return those images. Check pixel/area and OCR functions.
3. **Integration tests (mocked)**:

   * Use a small macro and assert executor flows (click → wait_for_area → click_on_template) call the correct helpers in sequence.
4. **Manual end-to-end smoke tests**:

   * Document a manual checklist so a human can run on their machine: "press F3 on the desired point; save macro; run; press Esc to kill."

---

# Implementation notes & gotchas (for the AI implementer)

* **DPI scaling / Windows scaling**: tests must consider that absolute coords vary with DPI; store rel coords and convert via `mss` monitor boxes.
* **Hotkey listener**: run `pynput.keyboard.Listener` in a dedicated thread and use a `threading.Event` or `multiprocessing.Value` boolean as `STOP` flag.
* **Mocking hardware**: always mock `pyautogui` in unit tests to avoid moving the tester's mouse.
* **Tesseract**: pytesseract requires the Tesseract binary installed separately — document this in README with sample install commands.
* **Performance**: use `mss` for repeated pixel grabs (fast) and avoid full-screen grabs when only small regions needed.
* **Safety**: always keep an emergency stop; log actions and have `dry-run` mode.
* **Extensibility**: design `executor` as a finite-state machine reading typed actions; keep action handlers as small functions registered in a handler map: `ACTION_HANDLERS = {"click": handle_click, "wait_for_area": handle_wait_for_area, ...}`.

---

# Example Phase-by-Phase acceptance checklist (concise)

* Phase 1: record F3 → saved JSON → run executes actions → Esc cancels.
* Phase 2: reorder/insert actions + unit tests pass.
* Phase 3: multi-monitor coordinate conversions tested.
* Phase 4: area/pixel wait actions detect changes on test images.
* Phase 5: OCR reads test images as expected (with Tesseract installed for manual tests).
* Phase 6: template matching + movement smoothing + randomness options.
* Phase 7/8: CLI adapter, packaging, docs, CI tests.