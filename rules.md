# THE HOOK — Rules and Guardrails

Status: mandatory execution rules  
Version: 1.0  
Last updated: 2026-08-08

These rules apply to every implementation phase unless the user explicitly changes them. They exist to keep the project credible, focused, and finishable.

## 1. Instruction precedence

When documents conflict, use this order:

1. The user's latest explicit instruction.
2. Official hackathon requirements.
3. `project_requirements.md`.
4. This file.
5. `Architecture.md` and `design.md` within their respective domains.
6. `phases.md`.
7. `memory.md`.

Record any durable change of direction in `memory.md`.

## 2. Competition rules

Verified from the AQX Sports Analytics Data Bowl 3.0 overview/rules during planning:

- Participants must be students; teams and individuals are allowed.
- The project must concern sports analytics and use sports data.
- Submission requires a working prototype, public source code, and a short description of solution, features, and actionable impact.
- A video is optional.
- Projects from previous AQX Sports Analytics Data Bowls cannot be resubmitted.
- The official Devpost deadline display and written rules contain a small timezone/minute discrepancy; treat 2026-08-15 IST as the safe internal deadline.

Official pages:

- <https://aqxanalyticsthree.devpost.com/>
- <https://aqxanalyticsthree.devpost.com/rules>

Do not transmit a submission, publish a repository, or deploy externally without the user's authorization in the relevant phase.

## 3. Product rules

1. The product answers one question: **Who should the manager bring in right now?**
2. Manager vs Model is the centerpiece, not a supporting feature.
3. The app starts on a working flagship scenario.
4. Curated depth beats universal coverage.
5. Three excellent scenarios are complete; five mediocre scenarios are not.
6. The demo path takes at most 90 seconds.
7. A feature that does not improve credibility, interaction, or story is not MVP work.
8. Once all MVP gates pass, stop adding architecture.

## 4. Scope rules

### Mandatory MVP

- 3 curated scenarios.
- 3–5 candidates per scenario.
- Actual choice and model recommendation.
- What-if selection.
- Candidate ranking.
- Lightweight simulation.
- Compact validation.
- Clear limitations.
- Offline runtime.
- Polished Streamlit UI.

### Forbidden before MVP freeze

- React or another frontend.
- FastAPI or another API layer.
- Authentication, accounts, or persistent user storage.
- Live data ingestion.
- Cloud databases.
- LLM features.
- Neural networks.
- Full historical game browsing.
- Advanced bullpen availability inference.
- Production MLOps, logging, Docker orchestration, or microservices.
- Additional sports.
- More than two Streamlit pages.

### Optional features

Optional work may begin only when every required acceptance gate in `project_requirements.md` passes. Implement at most one optional feature at a time and keep it only if it improves the demo without harming reliability.

## 5. Data rules

1. Data acquisition occurs offline through a script, never during app startup.
2. Every raw pull is cached before transformation.
3. Every processed artifact has a known source window and build timestamp.
4. A curated scenario records game ID, game date, state, actual choice, source, and point-in-time cutoff.
5. Future events must never enter a player profile used for an earlier prediction.
6. Training/validation splits are chronological.
7. Do not silently drop or impute important fields; record counts and policy.
8. Do not commit unnecessary large raw data.
9. Runtime artifacts must contain only required columns.
10. Baseball Savant/Statcast must be attributed in the README and app methodology.

## 6. Statistical rules

1. Prefer transparent regularized models over complex models.
2. Compare against a league-rate or similarly simple baseline.
3. Use proper scoring metrics; accuracy alone is insufficient.
4. Pool small player and handedness samples toward league averages.
5. Do not use raw pitcher-vs-batter history as a primary signal.
6. Do not tune on the chronological holdout and then report it as untouched.
7. The same situation, horizon, transition rules, and seed policy apply to all candidate comparisons.
8. Display percentage-point deltas correctly. A change from 60% to 65% is `+5.0 pp`, not `+5%` unless explicitly described as a relative change.
9. Do not imply Monte Carlo sampling error captures model uncertainty.
10. Do not hand-edit model outputs to create a better story.
11. If two candidates differ by less than the configured practical threshold, describe them as effectively tied.
12. If a model fails a sanity check, simplify it before replacing it with a more complex model.

## 7. Claims and language rules

Use:

- “The model estimates…”
- “Under the same assumptions…”
- “Projected advantage…”
- “In this simulation…”
- “Associated with…”

Avoid:

- “Proves…”
- “Would definitely have…”
- “Guarantees…”
- “The manager was wrong” without qualification.
- “AI-powered” unless it adds necessary clarity; “statistical model” is preferred.

Every explanation must be traceable to displayed or stored features. Do not fabricate qualitative baseball reasoning after seeing the result.

## 8. Architecture rules

1. The runtime is a single Streamlit app reading local artifacts.
2. UI modules never train models or acquire data.
3. Data/model code never imports Streamlit.
4. Notebooks are exploratory and cannot be runtime dependencies.
5. Business logic lives in `src/` and is callable without Streamlit.
6. Model preprocessing and inference are persisted as one pipeline where practical.
7. File paths are centralized; do not scatter magic paths.
8. Random seeds and artifact versions are explicit.
9. Add a dependency only when a current phase requires it.
10. Prefer deleting complexity over adding abstractions.

## 9. Code rules

1. Implement only the active phase.
2. Preserve unrelated user changes.
3. Use small functions with explicit inputs and outputs for transitions, simulation, and ranking.
4. Add type hints to public business-logic functions where they improve clarity.
5. Validate external/artifact data at module boundaries.
6. Do not hide data problems behind broad exception handling.
7. Error messages shown in Streamlit must be understandable and actionable.
8. Keep configuration out of layout code.
9. Avoid premature class hierarchies; functions and small dataclasses are sufficient.
10. Do not optimize before measuring a demo-relevant slowdown.

## 10. Testing rules

Testing is targeted to decision-critical logic:

- Scenario schemas.
- Outcome mapping.
- Base/out transitions.
- Simulation determinism and bounds.
- Candidate ranking.
- Artifact compatibility.
- Required-scenario app smoke path.

Every bug in these areas gets a regression test. Pixel-perfect snapshot suites, exhaustive mocks, and broad infrastructure testing are out of scope.

A phase is not complete when tests cannot run or when its acceptance checks are undocumented.

## 11. UI rules

1. Manager vs Model must appear above detailed methodology.
2. Actual choice and recommendation must be distinguishable by both text and color/icon.
3. Positive/negative meaning cannot rely on red/green alone.
4. Win-probability charts must label their scale and avoid misleading truncation.
5. Show at most one primary and one secondary chart in the core decision view.
6. Prefer compact cards and plain language over dense tables.
7. Do not add animated loaders, custom navigation, or decorative motion unless core work is complete.
8. The interface must remain usable at common laptop widths.
9. No raw stack trace may appear in the judged demo.
10. Every displayed decimal must have justified precision; use one decimal percentage point by default.

## 12. Phase execution protocol

At the start of each implementation phase:

1. Read `memory.md`.
2. Read the active phase in `phases.md`.
3. Read relevant sections of requirements, architecture, rules, and design.
4. Inspect existing code/data without overwriting unrelated work.
5. State the phase objective and current assumptions.

During a phase:

1. Implement the smallest path to the exit gate.
2. Verify continuously with targeted checks.
3. Defer work owned by later phases.
4. Log durable decisions and unexpected constraints.

At the end of a phase:

1. Run its required tests/checks.
2. Compare results with explicit exit criteria.
3. Update the status table and decision log in `memory.md`.
4. List artifacts created and commands needed by the next phase.
5. Mark the phase complete only when all exit criteria pass.

## 13. Change-control rules

A change to a frozen decision is allowed only when one of these is true:

- Required data is unavailable.
- A correctness or leakage problem is found.
- Performance blocks the 90-second demo.
- The user explicitly changes the objective.
- A simpler design preserves the story and increases completion probability.

For each change, record:

- Previous decision.
- New decision.
- Evidence/reason.
- Impact on later phases.

Do not change architecture because another approach seems more impressive.

## 14. Cut order if behind

Cut in this order, stopping as soon as the schedule recovers:

1. Fifth scenario.
2. Fourth scenario.
3. Workload assumption control.
4. Secondary pitch-mix visualization.
5. Uncertainty display.
6. Optional video.
7. Any model beyond regularized logistic/pooled fallback.
8. Any nonessential custom CSS.

Never cut:

- Flagship scenario.
- Three-scenario minimum unless the user explicitly accepts the risk.
- Manager vs Model.
- What-if interaction.
- Basic validation and limitations.
- Offline runtime.
- Final smoke test and submission buffer.

## 15. Definition of done

“Done” means the prototype is stable, understandable, honest, and demonstrable—not that every attractive feature was built. The project is finished when the MVP success criteria pass and the submission package is ready.
