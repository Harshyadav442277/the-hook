# THE HOOK — Project Requirements

Status: planning baseline  
Version: 1.0  
Last updated: 2026-08-08  
Safe internal submission target: 2026-08-15 (IST)

## 1. Product definition

THE HOOK is an explainable MLB bullpen decision simulator for curated, high-leverage historical situations.

Its central question is:

> Who should the manager bring in right now?

For each situation, the application compares the real manager's choice with 3–5 plausible relievers, estimates the effect of each choice under the same assumptions, recommends one option, and explains the main statistical reasons.

The product is a hackathon prototype. It is not a live coaching system, a causal estimator, a universal game browser, or production software.

## 2. Product objective

Build a polished and technically credible prototype that lets a judge understand the problem in 10 seconds, interact with it within 30 seconds, and complete the full Manager-vs-Model story in 60–90 seconds.

The target reaction is:

> “This tool tells an MLB manager which available reliever is statistically the strongest choice in a high-pressure situation, and it shows why.”

## 3. Target users

Primary:

- MLB manager or bench coach evaluating a pitching change.
- Baseball analyst preparing decision support or post-game review.

Secondary:

- Broadcasters and fans exploring counterfactual decisions.
- Hackathon judges with limited technical background.

## 4. User story

As a manager or analyst, I want to select a historical high-leverage situation, compare the actual decision with alternative relievers, and see a transparent estimate of each choice's win probability so that I can understand the trade-off without reading a technical report.

## 5. Required user journey

1. The application opens directly on a flagship situation.
2. The user immediately sees the inning, score, outs, base state, current pitcher, upcoming hitters, and actual managerial choice.
3. THE HOOK ranks 3–5 candidate relievers.
4. The recommended reliever and estimated difference from the actual choice are visually dominant.
5. The user selects any candidate as a what-if choice.
6. Estimated win probability, expected runs, and explanation update smoothly.
7. The user can open a short How It Works page containing the model, validation, and limitations.

## 6. MVP scope

### 6.1 Curated situations

Must include:

- At least 3 fully working historical MLB situations.
- A target of 5 situations if the first 3 pass all quality gates.
- Exactly one clearly marked flagship demo scenario.
- For each situation: inning half, inning number, score, outs, occupied bases, current pitcher, next 2–3 hitters, candidate relievers, actual choice, and as-of timestamp.
- 3–5 plausible candidate relievers per situation, including the actual choice and, where meaningful, leaving the current pitcher in.

The application must not depend on a universal historical game browser.

### 6.2 Candidate ranking

For every scenario, show a ranking with:

- Reliever name.
- Estimated win probability.
- Difference in estimated win probability from the actual manager's choice.
- Expected runs allowed over the simulated horizon.
- 1–3 concise reasons.
- Clear indication of the actual choice and THE HOOK recommendation.

All choices must be compared under identical state, horizon, simulation count, and random-seed policy.

### 6.3 Manager vs Model

The primary comparison must show:

- Actual manager choice.
- THE HOOK recommendation.
- Estimated win probability for each.
- Estimated delta in percentage points.
- Short explanation of why the recommendation differs or agrees.

Required language:

> “The model estimates…”

Prohibited language:

> “This proves…” or “Pitcher X definitely would have won.”

### 6.4 What-if interaction

The user must be able to choose any candidate reliever and immediately update:

- Estimated win probability.
- Estimated expected runs.
- Comparison with both the actual choice and recommendation.
- Explanation text.

### 6.5 How It Works

Must contain only the information needed to defend the project:

- Data source and temporal coverage.
- Leakage-safe chronological split.
- Matchup features.
- Model type.
- One baseline comparison.
- Multiclass log loss and/or on-base Brier score.
- One compact calibration graphic.
- Simulation description.
- Explicit limitations.

## 7. Analytical requirements

### 7.1 Matchup model

The default model is regularized multinomial logistic regression with four outcome groups:

1. `OUT`
2. `FREE_PASS` — walk or hit by pitch
3. `SINGLE`
4. `EXTRA_BASE` — double, triple, or home run

Within `EXTRA_BASE`, the simulator may sample double/triple/home-run type from a pooled conditional distribution. This keeps the model explainable while supporting realistic base-state transitions.

Candidate features may include:

- Pitcher and batter handedness.
- Shrunk strikeout and walk rates.
- Shrunk xwOBA or wOBA profiles.
- Pitcher pitch-family mix.
- Batter performance against broad pitch families.
- Average velocity.
- Recent pitcher workload and days of rest.
- Handedness interaction.
- Differences between pitcher and batter standardized profiles.

Direct pitcher-vs-batter history must not be a primary feature because samples are usually too small.

### 7.2 Small-sample control

Player and platoon rates must be pooled toward league averages. A documented empirical-Bayes-style shrinkage formula is sufficient:

`shrunk_rate = (n * observed_rate + k * league_rate) / (n + k)`

The constant `k` must be recorded in model metadata. Cold-start players must fall back to league-average or role-average profiles.

### 7.3 Chronology and leakage

- Training and validation must be split chronologically, never randomly across future and past plate appearances.
- Any rolling or expanding feature must use only events available before the target plate appearance (`shift(1)` or equivalent).
- A curated scenario's features must be computed using data available before that scenario.
- Final game outcome may be used only as the target for the state win-expectancy model, not as a feature.

### 7.4 Validation

Minimum validation package:

- Proper chronological holdout.
- League-rate baseline.
- Multiclass log loss for the four-outcome model.
- Brier score and a reliability plot for the derived on-base probability.
- Short written interpretation of whether performance is useful for relative ranking.

The model does not need to beat every baseline on every metric. If it does not add meaningful value, the team must simplify the claim and use the most stable defensible estimator.

### 7.5 Win probability

Estimated win probability is a comparative approximation, not an academically complete MLB win-probability product.

Preferred method:

1. Simulate the next three opposing batters for a selected reliever, ending earlier if the half-inning ends.
2. Update outs, bases, runs, inning state, and score.
3. Pass the resulting state to a simple fixed win-expectancy model trained on historical game states.
4. Average the resulting probabilities across simulations.

The three-batter horizon is both understandable and aligned with the practical reliever decision. Relative comparison between candidates matters more than exact absolute calibration.

### 7.6 Simulation

- Default target: 2,000 vectorized simulations per candidate.
- Allowed range: 1,000–5,000 after benchmarking.
- Use deterministic scenario/candidate seeds so repeated demos are stable.
- Do not call the predictive model once per simulation.
- Predict outcome probabilities once per matchup and sample with NumPy arrays.
- Do not perform live web requests.

### 7.7 Explanations

Use deterministic templates populated from model inputs and candidate-relative statistics.

Examples of valid reasons:

- More favorable handedness mix against the next three hitters.
- Stronger shrunk strikeout profile.
- Lower recent workload.
- Better projected outcome distribution against the upcoming hitters.

Do not use an LLM. Do not present feature contributions as causal effects.

## 8. Data requirements

Primary source: MLB Statcast/Baseball Savant, acquired offline through `pybaseball` or reproducible CSV queries.

Initial data window:

- Start with 2025 and 2026 year-to-date.
- Add 2024 only if Phase 1 shows insufficient player history or state coverage.
- Never expand the window merely to make the dataset sound larger.

Runtime artifacts should include:

- Clean plate-appearance table.
- Leakage-safe pitcher profiles.
- Leakage-safe batter profiles.
- State win-expectancy training or lookup artifact.
- Curated scenarios.
- Candidate matchup probabilities.
- Model artifacts and metadata.
- Validation metrics and calibration data.

Large raw downloads must not be required for the deployed application.

## 9. Exact MVP versus optional scope

### Required for submission

- 3 validated scenarios.
- Candidate ranking for every scenario.
- Manager-vs-Model comparison.
- Interactive reliever what-if.
- Four-outcome regularized model or documented simpler fallback.
- Lightweight vectorized simulation.
- Chronological validation and baseline.
- Template explanations.
- Polished Streamlit interface.
- Offline runtime data.
- Public README and reproducible build instructions.
- Reliable 60–90 second demo.

### Optional only after the MVP is frozen

- Fourth and fifth scenario.
- Small workload-assumption control.
- Scenario-specific annotated pitch-mix chart.
- Downloadable comparison card.
- One uncertainty note based on simulation standard error, clearly distinguished from full model uncertainty.
- Short optional demo video.

### Explicitly out of scope

- Universal MLB game browser.
- Live game support or live Baseball Savant calls.
- Full roster/availability inference.
- FastAPI, React, authentication, or databases.
- Cloud data pipeline or scheduled ingestion.
- Gradient boosting unless logistic regression demonstrably fails.
- Neural networks, LLMs, agents, or generated explanations.
- Causal claims.
- Complete season strategy optimization.
- Full research dashboard.
- Production observability, MLOps, microservices, or container orchestration.

## 10. Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-01 | Load a flagship scenario by default | Fresh app launch shows a complete situation without user setup |
| FR-02 | Switch among at least 3 scenarios | Every selector option loads valid data and recomputes views |
| FR-03 | Rank 3–5 candidates | Ranking is sorted, labeled, and includes actual and recommended choices |
| FR-04 | Compare Manager vs Model | Side-by-side cards show choices, WP estimates, delta, and explanation |
| FR-05 | Run a what-if choice | Selecting a reliever updates all dependent outputs consistently |
| FR-06 | Explain recommendation | 1–3 data-grounded reasons match the displayed player profiles |
| FR-07 | Show methodology | How It Works contains source, model, metrics, calibration, and limitations |
| FR-08 | Run offline | Disconnecting network access does not break normal app use |
| FR-09 | Preserve scenario provenance | Scenario metadata records source game, date, state, and cutoff |
| FR-10 | Avoid statistical overclaiming | UI and README use estimate/association language |

## 11. Non-functional requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Reliability | All required scenarios complete the demo path without error |
| NFR-02 | Warm interaction speed | Scenario/candidate update should normally complete in under 2 seconds |
| NFR-03 | Cold start | Deployed app should become usable in roughly 10 seconds or less |
| NFR-04 | Reproducibility | Fixed artifacts, feature schema, model metadata, and random seeds |
| NFR-05 | Clarity | A nontechnical reviewer understands the recommendation without documentation |
| NFR-06 | Accessibility | Color is not the sole carrier of meaning; adequate contrast and text labels |
| NFR-07 | Portability | Python 3.11-compatible Streamlit project with pinned direct dependencies |
| NFR-08 | Maintainability | Runtime logic lives in `src/`; notebooks are not imported by the app |

## 12. Success criteria

The MVP is complete only when:

- The application runs reliably from a clean environment.
- At least 3 scenarios satisfy the schema and pass smoke tests.
- Candidate rankings are plausible and reviewed manually.
- Changing relievers updates results without inconsistent cards or charts.
- Manager vs Model is the most visually prominent interaction.
- Validation artifacts exist and claims match the evidence.
- The app makes no obviously false or causal statistical claims.
- No runtime network request is required.
- The README explains the method and limitations.
- The complete demo can be delivered smoothly in 60–90 seconds.

## 13. Submission deliverables

- Public GitHub repository.
- Working deployed Streamlit prototype.
- Project description focused on the decision problem and actionable impact.
- README with method, validation, limitations, setup, and data attribution.
- 3–5 screenshots suitable for Devpost.
- Final 60–90 second demo script.
- Optional video only if it can be created without risking the core submission.

## 14. Assumptions to verify early

- Statcast acquisition for the selected period is stable enough to cache offline.
- Required fields are present for terminal plate appearances and game state reconstruction.
- Candidate workload can be derived or manually recorded accurately enough for curated cases.
- A simple state win-expectancy estimator produces sensible monotonic outputs.
- Streamlit Community Cloud can load the committed artifacts within repository limits.

If an assumption fails, use the fallback in `Architecture.md` and preserve the user-facing story.
