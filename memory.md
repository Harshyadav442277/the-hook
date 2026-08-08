# THE HOOK — Project Memory

Purpose: durable handoff context for future implementation phases  
Last updated: 2026-08-08  
Current state: Phases 0–8 complete; submission-ready freeze

Next phase: participant submits the prepared Devpost entry; no feature development

## 1. North star

THE HOOK is an explainable MLB bullpen decision simulator for curated high-leverage historical situations.

Central question:

> Who should the manager bring in right now?

Winning product story:

> The real manager chose Pitcher A. THE HOOK recommends Pitcher B. Under the same assumptions, the model estimates a +X.X-percentage-point win-probability advantage, mainly because of the upcoming hitters' handedness/pitch profiles and the relievers' projected outcomes/workload.

The project optimizes for a polished 60–90 second hackathon demo, clear reasoning, compact validation, and on-time completion. It does not optimize for production architecture or research novelty.

## 2. Canonical documents

Read in this order before executing a phase:

1. `memory.md` — current state and durable decisions.
2. `phases.md` — active phase deliverables and exit gate.
3. `project_requirements.md` — product and acceptance requirements.
4. `rules.md` — mandatory guardrails.
5. `Architecture.md` — system/data/model contracts.
6. `design.md` — interaction and visual rules.

Original planning input was supplied as:

`C:\Users\hyada\Downloads\THE_HOOK_codex_improve_plan.md`

The repository documents are self-contained; future phases should not depend on the Downloads copy.

## 3. Frozen MVP decisions

| Area | Decision |
|---|---|
| Product | Curated bullpen decision replay, not universal browsing |
| Required scenarios | 3 minimum; 5 target only after MVP |
| Flagship | Exactly one default scenario |
| Candidate set | 3–5 plausible relievers including actual choice |
| Core interaction | Manager vs Model plus reliever what-if |
| Data | Offline MLB Statcast/Baseball Savant |
| Initial window | Start with 2025 + 2026 YTD; add 2024 only with evidence |
| Matchup model | Regularized four-outcome multinomial logistic regression |
| Outcome classes | OUT, FREE_PASS, SINGLE, EXTRA_BASE |
| Small samples | Shrink player/platoon rates to league priors |
| Validation | Chronological holdout, league baseline, log loss, on-base Brier/calibration |
| Simulation | Next three hitters, 1,000–5,000 vectorized runs; target 2,000 |
| Absolute WP | Fixed simple game-state win-expectancy model after short horizon |
| Explanations | Deterministic templates; no LLM |
| App | Single Streamlit app plus one How It Works page |
| Runtime | Local immutable artifacts; no network or training |
| Deployment | Streamlit-compatible; external deployment requires user authorization |

## 4. Mathematical simplification

The project deliberately avoids a six-class/full-game simulator.

1. Predict four PA outcome groups for each reliever against each of the next three hitters.
2. Split the extra-base group into 2B/3B/HR using a pooled conditional distribution.
3. Simulate base/out/run transitions for at most three hitters.
4. Feed resulting state to a simple win-expectancy estimator.
5. Compare candidates under identical assumptions.

This preserves the WOW factor—live Manager-vs-Model win-probability changes—while keeping the model explainable and implementation bounded.

## 5. Current repository state

The complete local MVP now includes:

- Restartable Statcast acquisition plus full cached 2025-03-27–2026-08-07 build.
- 324,435 modelable plate appearances, prior-only monthly profiles, workload, and state examples.
- Three official MLB feed-reviewed scenarios with one flagship.
- Regularized four-outcome matchup and game-state win-expectancy models.
- Deterministic vectorized three-hitter simulation and traceable explanations.
- Two-page Streamlit app, compact committed runtime artifacts, 26 passing tests, README, CI, and submission copy.
- Git repository initialized on `main` with remote `https://github.com/Harshyadav442277/the-hook.git`.

Raw/processed build data remains ignored; the public runtime bundle is only about 42 KB.

## 6. Phase status

| Phase | Status | Completion evidence |
|---|---|---|
| 0. Planning freeze | Complete | Six canonical planning files created and cross-checked |
| 1. Foundation and data probe | Complete | 6,803-row live probe; cache and schema gates passed |
| 2. Data artifacts and scenarios | Complete | 324,435 PAs; 3 scenarios pass official-feed review |
| 3. Models and validation | Complete | Matchup/state artifacts load; chronological metrics and sanity checks pass |
| 4. Simulation and explanations | Complete | 12 deterministic candidate runs in ~0.4 s; transition/ranking tests pass |
| 5. Core Streamlit MVP | Complete | Decision Room and How It Works pass AppTest and browser flow |
| 6. Scenario coverage and polish | Complete | All scenarios, tie/agreement language, what-if, navigation visually reviewed |
| 7. Submission package and deployment | Complete | Public repo and live Streamlit app verified in a clean browser session |
| 8. Buffer and freeze | Complete | 26 tests and artifact validator pass; scope frozen for submission |

## 7. Competition memory

- Event: AQX Sports Analytics Data Bowl 3.0.
- Official overview: <https://aqxanalyticsthree.devpost.com/>.
- Official rules: <https://aqxanalyticsthree.devpost.com/rules>.
- Required: sports-data project, working prototype, public source code, description/actionable impact.
- Student-only; teams/individuals allowed.
- Video optional.
- Previous AQX Data Bowl projects cannot be reused.
- Safe internal deadline is 2026-08-15 IST because official displayed and written deadline details differ slightly.
- Prior first-place projects favored understandable interactive tools over extreme modeling complexity.

## 8. Scope memory

Never add before MVP completion:

- FastAPI/React.
- Authentication or database.
- Live API dependency.
- Universal MLB history browser.
- LLM/agent explanations.
- Gradient boosting by default.
- Neural networks.
- Advanced causal or uncertainty claims.
- Production infrastructure.

Cut order if behind:

1. Fifth scenario.
2. Fourth scenario.
3. Optional workload control.
4. Secondary visualization.
5. Uncertainty display.
6. Video.
7. Any non-logistic model.
8. Decorative custom CSS.

Never cut Manager vs Model, what-if interaction, basic validation/limitations, offline runtime, or final smoke testing.

## 9. Known risks

| Risk | Current response |
|---|---|
| Full-window Statcast acquisition duration | Two one-day chunks succeeded; Phase 2 uses restartable seven-day chunks and local manifests |
| Data leakage in profiles | Enforce sorted prior-only features with `shift(1)` or monthly snapshots |
| Sparse player/platoon history | Shrink toward league or role priors |
| Matchup model adds little value | Use transparent pooled projection fallback and narrower claims |
| State WP estimator behaves implausibly | Remove interactions or use smoothed empirical lookup |
| Simulation latency | Vectorize, cache, and reduce count before changing architecture |
| Candidate availability uncertainty | Manually verify curated candidates and preserve sources |
| Rankings too close for dramatic claim | Use effective-tie language; do not manipulate output |
| Deployment artifact size | Commit scenario-specific inference artifacts if necessary |
| UI work overruns | Build correct unstyled flow before design polish |

## 10. Open decisions owned by future phases

These are intentionally unresolved; use the stated default unless evidence says otherwise.

| Decision | Owner | Default |
|---|---|---|
| Shrinkage constant `k` | Resolved | Fixed 200-PA league prior |
| Exact flagship historical game | Resolved | 2025 World Series Game 3, LAD vs TOR, top 12 bases loaded |
| State-WP interactions | Resolved | Score differential × inning retained; sanity checks pass |
| Simulation count | Resolved | 2,000 deterministic runs per candidate |
| Practical tie threshold | Resolved | 0.5 percentage point |
| Fourth/fifth scenarios | Phase 6 | Deferred unless MVP frozen |
| Hosting/public URL | Resolved | <https://the-hook.streamlit.app/> |

## 11. Decision log

### 2026-08-08 — Scope reduced to curated prototype

- Decision: build 3–5 curated historical situations rather than universal browsing.
- Reason: maximizes polish, data verification, and demo reliability in the hackathon window.
- Impact: scenario facts and candidate availability are manually reviewed.

### 2026-08-08 — Four-outcome model selected

- Decision: use regularized multinomial logistic regression for OUT, FREE_PASS, SINGLE, EXTRA_BASE.
- Reason: retains meaningful base transitions without a fragile six-class model.
- Impact: XBH subtype is sampled from a pooled conditional distribution.

### 2026-08-08 — Short-horizon WP approximation selected

- Decision: simulate the next three hitters, then evaluate the resulting state with a simple fixed win-expectancy model.
- Reason: preserves interactive win-probability comparison without full-game simulation.
- Impact: UI and README must disclose the approximation and relative interpretation.

### 2026-08-08 — Offline Streamlit architecture selected

- Decision: use local artifacts and a single Streamlit application; no runtime API calls.
- Reason: reliable, fast demos and minimal architecture.
- Impact: all acquisition/training happens in scripts before deployment.

### 2026-08-08 — Phase 1 Python stack verified

- Decision: use Python 3.12.2 with the direct versions pinned in `requirements.txt`.
- Evidence: all direct imports succeeded together and `pip check` reported no broken requirements.
- Key versions: NumPy 2.5.1, pandas 3.0.5, PyArrow 24.0.0, scikit-learn 1.9.0, pybaseball 2.2.7, Streamlit 1.61.1, Plotly 6.9.0, pytest 9.1.1.
- Impact: later phases should use `.venv\Scripts\python.exe` and must change pins only with compatibility evidence.

### 2026-08-08 — Statcast acquisition and cache contract verified

- Decision: acquire bounded inclusive ranges in seven-day Phase 2 chunks, writing each chunk to Parquet plus an adjacent JSON manifest before continuing.
- Evidence: the 2026-07-01 through 2026-07-02 probe downloaded 6,803 rows across two one-day chunks; a second run produced 2 cache hits and 0 downloads.
- Manifest contract: source, inclusive dates, row/column counts, columns, acquisition timestamp, pybaseball/pandas/PyArrow versions, file name, and SHA-256.
- Impact: interrupted Phase 2 downloads can safely resume and valid cached chunks are integrity-checked before reuse.

### 2026-08-08 — Phase 2 data window frozen

- Decision: acquire 2025-03-27 through 2026-08-07 in seven-day cached chunks.
- Reason: one recent complete main-season window plus 2026 YTD is sufficient for the hackathon model and chronological validation; adding 2024 now would add time without Phase 1 evidence of need.
- Fallback: add 2024 only if Phase 2 documents a cold-start or sample-coverage problem.

### 2026-08-08 — Terminal-event mapping verified

- Decision: keep the four canonical classes and explicitly exclude `catcher_interf`, `field_error`, `fielders_choice`, `runner_double_play`, and `truncated_pa` from model rows.
- Evidence: 1,780 terminal events contained 1,757 canonical mappings (98.71%) and 23 documented exclusions; accounted coverage is 100% with no unknown event.
- Workload evidence: `pitcher_days_since_prev_game` is directly available; recent pitch counts can be derived by pitcher/game/date from pitch rows.
- Impact: Phase 2 must report event counts/exclusions again across the full window and fail closed on any new unknown event.

## 12. Phase handoff template

Append a dated entry after each phase:

```markdown
### YYYY-MM-DD — Phase N handoff

- Status: Complete / Incomplete
- Exit criteria: [passed/failed summary]
- Created: [files and artifacts]
- Verified with: [commands and results]
- Decisions: [durable changes]
- Known issues: [specific remaining issues]
- Next phase: Phase N+1
- Next command/prompt: [exact starting point]
```

Also update the phase-status table near the top. Do not erase prior decision-log entries unless correcting a factual error; add a correction entry instead.

## 13. Next action

Submit the prepared Devpost entry using `submission/devpost_description.md`, `submission/demo_script.md`, and `submission/final_checklist.md`. The project is frozen; do not add features before judging.

### 2026-08-08 — Phase 1 handoff

- Status: Complete.
- Exit criteria: cached sample exists; data feasibility is proven; the Phase 2 window/chunk size is frozen; schema, mapping, cache, and environment evidence are recorded.
- Created: environment/dependency files, minimal `src/data` package, acquisition CLI, two test modules, two raw cache chunks/manifests, and JSON/Markdown probe reports.
- Verified with: `.venv\Scripts\python.exe -m pytest -q` (`6 passed`); `.venv\Scripts\python.exe scripts\download_data.py` (`PASS`, 2 cache hits, 0 misses); `.venv\Scripts\python.exe -m pip check` (`No broken requirements found`).
- Decisions: Python 3.12.2 stack; 2025-03-27–2026-08-07 Phase 2 range; seven-day chunks; canonical event mapping and documented exclusions.
- Known issues: full-window acquisition time remains unmeasured; manifests make it restartable. The workspace is not yet a Git repository, which is not a Phase 2 analytical blocker but must be addressed before publication.
- Next phase: Phase 2 — Data artifacts and curated scenarios.
- Next command/prompt: execute the Phase 2 prompt above and do not train models.

### 2026-08-08 — Phase 2 handoff

- Status: Complete.
- Exit criteria: full bounded cache reconciles; profiles are prior-only; exactly three scenarios pass official MLB feed checks; one is flagship; actual choices and 4-player pools validate.
- Created: processed PA/profile/workload/state Parquets, `scenarios.json`, build report, and reproducible scenario verifier.
- Verified with: 1,274,390 pitches → 327,756 terminal events → 324,435 modelable PAs; 3,321 documented exclusions; official-feed review `all_passed: true`.
- Decisions: normalize Statcast `Bot` to `BOTTOM`; accept and cache legitimate off-season empty chunks; flagship is 2025 World Series Game 3 LAD–TOR, top 12, bases loaded.
- Known issues: plausible bullpen availability is approximated from recent usage, not an official status feed.

### 2026-08-08 — Phase 3 handoff

- Status: Complete.
- Exit criteria: both pipelines persist/load, probabilities sum to one, chronological metrics/calibration persist, and state sanity checks pass.
- Verified with: matchup holdout log loss 0.9645 vs 0.9700 baseline; on-base Brier 0.2174; state log loss 0.4743 vs 0.6927 baseline.
- Decisions: retain regularized logistic models; keep the score-difference × inning interaction; use modest comparative claims.

### 2026-08-08 — Phase 4 handoff

- Status: Complete.
- Exit criteria: deterministic rankings for all three scenarios, pure transitions, effective ties, evidence-backed reasons, and performance budget pass.
- Verified with: 2,000 simulations per candidate; all 12 candidates built in ~0.4 seconds; strictly prior scenario profiles; targeted transition/simulation tests pass.
- Decisions: fixed XBH conditional mix 58% double / 3% triple / 39% home run; practical tie threshold 0.5 pp.

### 2026-08-08 — Phases 5–6 handoff

- Status: Complete.
- Exit criteria: flagship default, all three scenario paths, synchronized what-if, honest tie copy, real methodology metrics, offline runtime, responsive design, and browser QA pass.
- Created: `app.py`, How It Works page, shared UI components/charts/theme, Streamlit config, and smoke tests.
- Verified with: Streamlit AppTest plus in-app-browser selection, what-if, navigation, DOM, and visual review; no runtime network client imports.
- Decisions: use compact custom sidebar navigation; retain one ranking chart and one calibration chart; freeze feature scope.

### 2026-08-08 — Phases 7–8 handoff

- Status: Complete; submission-ready freeze.
- Completed: public GitHub repository, MIT license, Streamlit deployment, README/screenshots, CI, Devpost description, demo script, judge Q&A, and final checklist.
- Live URLs: <https://the-hook.streamlit.app/> and <https://github.com/Harshyadav442277/the-hook>.
- Verified with: clean-session checks of the Decision Room and How It Works routes; flagship values 44.0% vs 47.6% (+3.6 pp); no browser console errors; `scripts/validate_artifacts.py` passes; `pytest -q` reports 26 passed.
- Decisions: freeze all feature work; only correctness or deployment fixes are allowed before judging.
- Known issues: Devpost submission itself requires the participant's account and remains the only human action.
