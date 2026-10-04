# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries for releases before this file existed were generated from commit subjects.

## [2.0.3] - 2026-09-28

- Maintenance release (dependency and metadata updates only).

## [2.0.2] - 2026-09-28

- Add IResettable.full_reset() override, moving cooling setup out of open()
- Add CLAUDE.md entry point pointing to specs/ conventions and tooling

## [2.0.1] - 2026-09-03

- Add DET-ID/DET-TBAS FITS headers; adopt FilterHeaderMixin (#872)
- Require stable pyobs-core>=2.0.0
- Remove stale poetry.lock; project now uses uv.lock
- Fix RTD build: mock flidriver instead of pip install .
- Fix filter wheel move timeout and late-result race
- Gate auto-merge on the PR author, not the event actor
- Enable Dependabot auto-merge for patch/minor updates
- Add standalone gui.py driving FliDriver directly (#85)
- Camera driver/GUI split: fix get_model buffer, _keep_alive reconnect, readout cleanup (#83)
- Add regression test for FLI-only kwargs reaching FliBaseMixin
- Convert FliCamera/FliFilterWheel to cooperative super() init chains
- tests: assert comm.set_state call shape in window/binning tests
- Add baseline test suite and CI (pytest, pyrefly), grouped Dependabot
- Disable uv cache in publish job (no deps installed there to cache)
- Pin cibuildwheel action to v4.2.0 (bare @v2 tag doesn't exist upstream)
- Build and publish manylinux wheels via cibuildwheel, drop Python 3.14 cap
- Mark nogil-libfli-calls plan as implemented
- Release the GIL around libfli calls
- Rename FliDriver.is_exposing to is_data_ready; use Binning in capabilities
- Run blocking FLI SDK calls off the event loop
- Upgrade uv.lock to clear open Dependabot alerts
- Require pyobs-core>=2.0.0.dev48
- Add dependabot.yml, targeting develop for PRs
- Raise AbortedError instead of bare InterruptedError on exposure abort
- Update to pyobs-core 2.0.0.dev10, apply FitsHeaderEntry to get_fits_header_before
- Fix docs heading and document FliFilterWheel
- Update README for uv-based install and pyobs 2.0 config style
- Update Ruff workflow to disable `--sync` during execution
- pypi workflow to uv, and added ruff workflow
- Remove DEVELOPMENT.md documentation for pyobs 2.0 migration
- Migrate to pyobs 2.0 API with scikit-build-core build system
- Add DEVELOPMENT.md documentation for pyobs 2.0 migration
- changing old-style type hints to new style
- back to poetry for building cython...
- github action
- migrated to uv
- datetime.utcnow() to datetime.utc(timezone.utc)
- fixed docs
- fixed bug
- fetching error
- filter wheel
- added get_filter_name
- filter wheel with multiple wheels
- added a few methods for filter wheels
- added 4x4 binning
- added _wait_exposure
- added list_binnings
- new build system
- implemented get_fits_header_before
- add device type

## [2.0.0] - 2026-08-26

- Require stable pyobs-core>=2.0.0
- Remove stale poetry.lock; project now uses uv.lock
- Fix RTD build: mock flidriver instead of pip install .
- Fix filter wheel move timeout and late-result race
- Gate auto-merge on the PR author, not the event actor
- Enable Dependabot auto-merge for patch/minor updates
- Add standalone gui.py driving FliDriver directly (#85)
- Camera driver/GUI split: fix get_model buffer, _keep_alive reconnect, readout cleanup (#83)
- Add regression test for FLI-only kwargs reaching FliBaseMixin
- Convert FliCamera/FliFilterWheel to cooperative super() init chains
- Publish ITemperatures placeholder state in open()
- tests: assert comm.set_state call shape in window/binning tests
- Add baseline test suite and CI (pytest, pyrefly), grouped Dependabot
- Disable uv cache in publish job (no deps installed there to cache)
- Pin cibuildwheel action to v4.2.0 (bare @v2 tag doesn't exist upstream)
- Build and publish manylinux wheels via cibuildwheel, drop Python 3.14 cap
- Mark nogil-libfli-calls plan as implemented
- Release the GIL around libfli calls
- Rename FliDriver.is_exposing to is_data_ready; use Binning in capabilities
- Run blocking FLI SDK calls off the event loop
- Upgrade uv.lock to clear open Dependabot alerts
- Require pyobs-core>=2.0.0.dev48
- Add dependabot.yml, targeting develop for PRs
- Raise AbortedError instead of bare InterruptedError on exposure abort
- Update to pyobs-core 2.0.0.dev10, apply FitsHeaderEntry to get_fits_header_before
- Fix docs heading and document FliFilterWheel
- Update README for uv-based install and pyobs 2.0 config style
- Update Ruff workflow to disable `--sync` during execution
- pypi workflow to uv, and added ruff workflow
- Remove DEVELOPMENT.md documentation for pyobs 2.0 migration
- Migrate to pyobs 2.0 API with scikit-build-core build system
- Add DEVELOPMENT.md documentation for pyobs 2.0 migration
- changing old-style type hints to new style

## [1.4.2] - 2025-07-09

- back to poetry for building cython...

## [1.4.1] - 2025-07-03

- github action

## [1.4.0] - 2025-07-03

- migrated to uv
- datetime.utcnow() to datetime.utc(timezone.utc)

## [1.3.10] - 2024-03-21

- fixed docs

## [1.3.9] - 2023-12-20

- fixed bug

## [1.3.8] - 2023-12-20

- fixed bug

## [1.3.7] - 2023-12-18

- fetching error

## [1.3.6] - 2023-12-18

- filter wheel

## [1.3.5] - 2023-12-18

- filter wheel

## [1.3.4] - 2023-12-18

- fixed bug

## [1.3.3] - 2023-12-18

- added get_filter_name

## [1.3.2] - 2023-12-18

- fixed bug

## [1.3.1] - 2023-12-18

- fixed bug

## [1.3.0] - 2023-12-18

- filter wheel with multiple wheels

## [1.2.1] - 2023-12-17

- fixed bug

## [1.2.0] - 2023-12-17

- added a few methods for filter wheels

## [1.1.5] - 2023-12-11

- Maintenance release (dependency and metadata updates only).

## [1.1.4] - 2023-12-10

- added 4x4 binning

## [1.1.3] - 2023-12-04

- added _wait_exposure

## [1.1.2] - 2023-11-30

- added list_binnings

## [1.1.1] - 2023-07-21

- new build system

## [1.1.0] - 2022-11-17

- implemented get_fits_header_before
- add device type
- set motion status
- set initial motion status
- added get_filter_pos/set_filter_pos
- init motionstatusmixin
- correct logging
- test
- added get_model
- fixed list_devices()
- added import
- first version for filterwheel

## [1.0.1] - 2022-11-14

- get serial number

## [1.0.0] - 2022-09-13

- added license

## [0.20.0] - 2022-06-27

- added IAbortable

## [0.18.2] - 2022-03-25

- send ping to keep connection to camera alive

## [0.18.1] - 2022-03-23

- dependencies

## [0.18.0] - 2022-03-23

- changed time.sleep to asyncio.sleep

## [0.16.1] - 2022-03-08

- core version
- example config
- moved import of flidriver into methods for RTD
- skip compilation if in RTD

## [0.16.0] - 2022-01-18

- fixed rtd
- basic docs
- set InterruptedError instead of AbortedError
- replaced AbortedError with builtin InterruptedError
- new exceptions for cameras
- added black and pre-commit to dev dependencies
- added .pre-commit-config.yaml
- running black
- added black config

## [0.15.0] - 2021-12-29

- changed used Python version to 3.9
- Pushed requirements to Python>=3.9 and astropy>=5.0, closes #55
- to asyncio for pyobs 0.15

## [0.14.2] - 2021-11-21

- github action
- poetry build seems to work
- working on poetry migration
- v0.14
- Added type hints
- renamed ICameraWindow to IWindow
- renamed ICameraBinning to IBinning
- using Image
- fixed exp_time
- v0.13
- documentation
- added __module__
- updated docstrings
- moved ExposureStatus to utils.enums
- changed to full imports instead of relative ones
- install numpy and cython and don't build wheel
- v0.12
- working on type hints
- GitHub workflow for publishing to PyPI
- v0.9
- removed pyobs-core from requirements
- - distutils -> setuptools - v0.8
- removed debug code
- flip
- fixed bug
- visible vs full frame
- image flip
- added get_visible_frame
- back
- setting trimsec from visible frame
- changed from FLIGetVisibleArea to FLIGetArrayArea in get_full_frame()
- flipping image
- flip x and y
- removed parameter from RUN command
- changed version number to 0.2
- new ITemperatures interface
- removed IStatus interface
- changed to match new interfaces
- new get_cooling_status()
- added new ExposureStatusChanged event
- no return value for open() any more
- renamed pytel to pyobs
- using Exceptions for error propagation
- fixed ENTRYPOINT
- new docker configs
- All working
- working on driver, exposure done except for readout
- initial commit
