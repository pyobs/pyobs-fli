# Plan: Release the GIL around libfli calls

Status: in progress

Tracks: https://github.com/pyobs/pyobs-fli/issues/75

## Problem

A hung FLI device freezes the whole module, including XMPP. `FliBaseMixin._run_blocking`
(`pyobs_fli/flibase.py`) already runs every libfli call in a daemon thread bounded by
`asyncio.wait_for(..., timeout=5.0)`, which is the fix that worked for the same blocking-call
shape in `pyobs-aravis`/`pyobs-asi` (see `pyobs-core/specs/steering/
blocking-sdk-calls-must-not-run-on-the-event-loop.md`). It doesn't work here, because
`libfli.pxd` declares `FLIOpen`, `FLIGetReadoutDimensions`, etc. without `nogil`. Cython calls
into a non-`nogil` C function while still holding the GIL, so when the call blocks (unresponsive
USB device), the daemon thread holds the GIL for the entire hang. The event loop thread cannot
run *anything* on that GIL, including the `asyncio.wait_for` timeout machinery meant to bound the
call. The timeout never fires; the module goes fully unresponsive (observed: `fli230` stopped
answering `disco#info`, every peer logged repeated capability-fetch timeouts).

## Decision

Mark the libfli C functions `nogil` in `libfli.pxd`, and wrap each call site in
`flidriver.pyx` in `with nogil:` so the GIL is actually released while the call runs. This
restores the daemon-thread timeout's ability to fire, since the event loop thread can run while
the SDK call blocks.

Considered and rejected: running FLI calls in a subprocess (the issue's "more robust, heavier"
alternative). Rejected for this pass because it's a much larger change (IPC, serialization of
buffers for `grab_row`, process lifecycle management) for the same practical outcome. Worth
reconsidering only if a `with nogil:` call turns out to still wedge somehow (e.g. libfli itself
deadlocks internally in a way that isn't a simple blocking wait).

## Design

### `libfli.pxd`

Change the whole `cdef extern from "../lib/libfli.h":` block to
`cdef extern from "../lib/libfli.h" nogil:`. This marks every declared function `nogil` at once,
including ones not yet called from `flidriver.pyx`, so new call sites added later don't silently
regress. Safe for the whole block: libfli is a pure hardware-I/O C library, none of its functions
take a Python object or call back into the interpreter.

### `flidriver.pyx`

`nogil` only changes what's *allowed* inside `with nogil:` — it does not by itself move existing
calls off the GIL. Every call site needs a `with nogil:` around the actual `FLI*(...)` call, and
anything inside that block that isn't a C primitive has to move outside it first:

- **Enum/typed-arg values** (`device_type.value`, `channel.value`, and `int`/`bool`-annotated
  Python parameters like `pos`, `wheel`, `x`, `y`, `left`, `exptime`, `open_shutter`): read into a
  local `cdef` C variable before the `with nogil:` block, since attribute access and Python->C
  unboxing both touch the GIL.
- **`self._device_info.filename` / `.domain`** (used in `open()`): same issue — read into local
  `cdef` variables (`bytes` for filename, kept alive as a local so the underlying buffer stays
  valid for the duration of the block; `flidomain_t` for domain) before entering `with nogil:`.
- **`self._device`**: no change needed. It's a C-typed (`cdef flidev_t`) field of a `cdef class`,
  so reading it inside `with nogil:` is a direct field access, not a Python attribute lookup.
- **`list_devices()`**: the `while` loop currently interleaves a C call (`FLIListNext`) with a
  Python-level `devices.append(...)`. Put just the C call in its own `with nogil:` per iteration
  (accepted GIL-flip overhead — this runs at most a few times per `open()`, not in a hot loop);
  the list bookkeeping stays under the GIL.
- **`grab_row()`**: `row_data` is already computed (as a raw pointer) before the call — just wrap
  the `FLIGrabRow` call itself; no reordering needed.

Cython raises a compile-time error for any Python-object touch inside a `with nogil:` block, so
this is self-checking: if an extraction is missed, `cython --cplus` on `flidriver.pyx` fails
before any build/link step.

### Verification

No existing test suite exercises the Cython extension (`pyobs-fli` has no `tests/` at all — a
hardware driver with no way to run libfli calls without real hardware). Verification is:

1. `cython --cplus` compiles `flidriver.pyx` clean (catches any missed nogil extraction as a hard
   error, not just a lint).
2. Full `cmake`/`scikit-build-core` build succeeds and the resulting `.so` imports.
3. Manual read-through confirming every `FLI*` call site in the diff is inside a `with nogil:`
   block, and that nothing added to `libfli.pxd`'s `nogil` block passes a Python object by
   reference to a C function that could retain/mutate it — none of the current API does.

No hardware-in-the-loop test is possible from here; actual freeze recovery on a hung `fli230` can
only be confirmed on-site.

## Out of scope (flagged, not fixed here)

- `get_model()` in `flidriver.pyx` (~line 320) passes `model` and `len` to `FLIGetModel`
  uninitialized (`cdef char *model` / `cdef size_t len`, never assigned before the call) — this
  writes through a garbage pointer with a garbage length. Pre-existing bug, unrelated to the GIL
  issue. Should be filed and fixed separately (needs a real fixed-size buffer, same shape as
  `get_serial_string()`/`get_filter_name()`).
- `pyobs-flipro` has the structurally identical bug (no `_run_blocking` wrapper at all yet, let
  alone `nogil`) — separate issue/PR in that repo, not touched here.

## Implementation checklist

- [x] `libfli.pxd`: add `nogil` to the `cdef extern from "../lib/libfli.h":` line.
- [x] `flidriver.pyx`: wrap every `FLI*` call site in `with nogil:`, hoisting Python-object/typed-arg
      reads above the block as described in Design.
- [x] `cython --cplus pyobs_fli/flidriver.pyx -I pyobs_fli` compiles with no errors (only the
      pre-existing, separately-flagged `get_model()` uninitialized-variable warning).
- [x] Full build (`uv sync`) succeeds; `import pyobs_fli.flidriver` works and
      `FliDriver.list_devices()` runs cleanly through the new `nogil` code path.
- [ ] Open a PR against `develop` (matches this repo's branch convention — dependabot/feature PRs
      land on `develop`, which then gets version-bumped into `main`).
- [ ] Update this doc's `Status:` to `implemented` once merged.
