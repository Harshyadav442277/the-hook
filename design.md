# THE HOOK — Product and Visual Design

Status: MVP design specification  
Version: 1.0  
Last updated: 2026-08-08

## 1. Design objective

THE HOOK should feel like a focused baseball decision room: calm, analytical, and decisive under pressure.

The interface must communicate, in order:

1. What is happening in the game?
2. What did the manager do?
3. What does THE HOOK recommend?
4. How large is the estimated difference?
5. Why?
6. What changes if I choose someone else?

It should not look like a notebook, a generic admin dashboard, or a collection of unrelated charts.

## 2. Design principles

### Decision first

Place the answer and comparison before methodology. The user should not scroll through model details to find the recommendation.

### One visual story

Use one dominant story per screen: Manager vs Model on the main page; credibility and limitations on How It Works.

### Explainable, not theatrical

Use restrained emphasis, transparent labels, and sports-language explanations. Avoid glowing AI graphics, excessive gradients, or false precision.

### Stable for demos

Controls and results should not jump unpredictably. Use deterministic simulation seeds, fixed component order, and concise loading states.

### Honest comparison

Make actual choice, model recommendation, and user-selected what-if distinct. Never imply observed history is a controlled counterfactual.

## 3. Information architecture

Use two Streamlit pages only.

### Page 1 — Decision Room (`app.py`)

This is the landing page and full demo path.

Order:

1. Compact hero.
2. Scenario selector.
3. Situation card.
4. Manager vs Model.
5. Candidate ranking.
6. What-if reliever analysis.
7. Assumptions/limitations expander.

### Page 2 — How It Works (`pages/1_How_It_Works.py`)

Order:

1. One-paragraph method summary.
2. Data and point-in-time feature flow.
3. Four outcome classes.
4. Validation metric cards and baseline.
5. Calibration plot.
6. Three-batter simulation explanation.
7. Limitations and responsible interpretation.

Do not add a separate home page; it would add a click without advancing the demo.

## 4. Page 1 component specification

### 4.1 Hero

Content:

- Small eyebrow: `MLB BULLPEN DECISION LAB`
- Product name: `THE HOOK`
- Tagline: `Should the manager make the call?`
- One sentence: `Compare the real bullpen decision with statistically projected alternatives in a high-leverage moment.`

Keep the hero short enough that the situation and comparison begin near the first viewport.

### 4.2 Scenario selector

Use a single selectbox with narrative labels such as:

`7th inning · one-run lead · runners on 1st and 2nd`

The flagship is selected by default and may carry a `Flagship replay` badge in adjacent text.

On selection change:

- Reset the what-if candidate to THE HOOK recommendation.
- Recompute or load the new ranking.
- Update every component from the same scenario result object.
- Never retain explanation text from the previous scenario.

### 4.3 Situation card

Use one bounded card or container with two rows.

Top row:

- Inning/half.
- Score from fielding-team perspective.
- Outs.
- Base state rendered as a simple baseball diamond or labeled bases.

Bottom row:

- Current pitcher.
- Next three hitters with handedness.
- Fielding and batting teams.

Use labels and values, not paragraphs. Base occupancy must have a text alternative such as `Runners: 1B, 2B`.

### 4.4 Manager vs Model

This is the visual centerpiece and should fit within one laptop viewport when possible.

Use two equal cards:

#### Manager card

- Label: `ACTUAL DECISION`
- Actual reliever name.
- Estimated WP under the model.
- Small note: `What the manager chose`

#### THE HOOK card

- Label: `THE HOOK RECOMMENDS`
- Recommended reliever name.
- Estimated WP.
- Recommendation badge.

Between or directly below cards, show:

`Estimated advantage: +X.X percentage points`

If the model agrees with the manager:

`THE HOOK agrees with the call.`

If effectively tied:

`The top choices are effectively tied under this model.`

Below the delta, show at most three explanation bullets.

### 4.5 Candidate ranking

Primary visual: horizontal ranked bars or lollipop chart of estimated WP by candidate.

Requirements:

- Sort highest to lowest.
- Label actual choice and recommendation directly.
- Display one decimal percentage precision.
- Use a 0–100% axis unless a clearly labeled focused inset is necessary; default to the honest full scale.
- Provide accessible table values below or in an expander if the chart alone is insufficient.

Secondary columns/table fields:

- Estimated WP.
- Delta versus actual in percentage points.
- Expected runs.
- Status badge.

Do not show more than 5 candidates.

### 4.6 What-if panel

Control:

- Selectbox or horizontal radio for candidate reliever.

Default:

- THE HOOK recommendation.

Output:

- Candidate name and hand.
- Estimated WP.
- Delta versus actual.
- Expected runs over modeled horizon.
- Next-three-hitter matchup strip.
- 1–3 reasons.

Avoid controls for every model feature. The MVP interaction is choosing a pitcher, not editing the model.

### 4.7 Assumptions expander

Collapsed by default. Include:

- Three-batter horizon.
- Simplified base advancement.
- State win-expectancy approximation.
- Relative, not causal, interpretation.
- Data cutoff.

Link or direct users to How It Works for details.

## 5. Page 2 component specification

### 5.1 Method summary

Use a three-step strip:

1. `Profile` — construct prior-only player and workload features.
2. `Project` — estimate four plate-appearance outcome probabilities.
3. `Simulate` — simulate the next three hitters and evaluate resulting game states.

### 5.2 Outcome model

Show four compact outcome chips/cards:

- Out.
- Walk/HBP.
- Single.
- Extra-base hit.

State that XBH subtype is sampled from pooled historical rates.

### 5.3 Validation

Show no more than three metric cards:

- Multiclass log loss.
- Baseline log loss.
- On-base Brier score.

Add one reliability chart. Accompany every metric with a short plain-language interpretation; do not rely on numbers alone.

### 5.4 Limitations

Use a visible, calm section rather than fine print:

- Counterfactual estimates are not observed outcomes.
- Player form and availability are simplified.
- Base advancement and reliever horizon are simplified.
- Absolute WP is approximate; candidate comparisons share assumptions.
- Small samples are shrunk toward league averages.

## 6. Visual tokens

### 6.1 Color palette

| Token | Hex | Use |
|---|---|---|
| `navy-900` | `#0B1F33` | Headers, Manager card, primary text |
| `navy-700` | `#183B56` | Secondary dark elements |
| `cream-050` | `#F7F4ED` | App background |
| `white` | `#FFFFFF` | Cards |
| `field-600` | `#176B4D` | Recommendation and positive state |
| `field-100` | `#DCEDE6` | Recommendation card tint |
| `hook-600` | `#C74755` | Product accent, warnings, actual-decision marker where appropriate |
| `gold-500` | `#D9A928` | Estimated delta and attention accent |
| `slate-600` | `#5D6B78` | Secondary text |
| `slate-200` | `#D9E0E6` | Dividers and neutral bars |

Color semantics must be reinforced with text labels or icons. Do not depend on green/red alone.

### 6.2 Typography

Use a local system sans-serif stack to avoid runtime font downloads:

`Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

Suggested hierarchy:

- Product title: 2.4–3.0rem, 750 weight.
- Section heading: 1.35–1.65rem, 700 weight.
- Card value: 1.6–2.1rem, 700 weight.
- Body: 0.95–1.05rem.
- Labels: 0.72–0.82rem, uppercase with moderate tracking.

Avoid more than three distinct text sizes in a single card.

### 6.3 Spacing and shape

- Base spacing unit: 4px.
- Major section gap: 28–36px.
- Card padding: 16–24px.
- Card radius: 12–16px.
- Border: 1px neutral slate.
- Shadow: subtle or none; use one consistent style.

Avoid excessive pill shapes. Reserve badges for `Actual`, `Recommended`, `Selected`, and `Flagship`.

## 7. Plotly design

Create one shared Plotly template:

- Transparent/white plot background matching its card.
- Navy text.
- Minimal gridlines.
- No mode bar in judged views unless useful.
- Consistent hover template with one decimal percentage point.
- Direct labels when there are five or fewer marks.
- Recommendation green; actual choice navy or hook accent; other candidates slate.

Charts must not use 3D effects, gauges, radar charts, or pie charts.

Preferred charts:

- Horizontal WP ranking.
- Small matchup probability stacked bar if optional.
- Reliability diagram on How It Works.

## 8. Copy system

### Approved terminology

- `Estimated win probability`
- `Estimated advantage`
- `percentage points`
- `Model recommendation`
- `Actual managerial decision`
- `Upcoming hitters`
- `Recent workload`
- `Under the same assumptions`

### Avoid

- `Guaranteed win`
- `Optimal` without qualification.
- `Manager mistake` as a headline.
- `Confidence` when showing only Monte Carlo sampling variability.
- Dense acronyms without a tooltip or expansion.

### Explanation template

Preferred form:

> `THE HOOK prefers {pitcher} because the model projects {reason_1}, {reason_2}, and {reason_3} against the next three hitters.`

If only one reason clears threshold, use one reason. Do not pad with weak claims.

## 9. State behavior

### Loading

- Show a short message such as `Running the matchup simulation…` only when uncached work is noticeable.
- Do not expose training or data-acquisition language at runtime.

### Missing artifact

Show:

> `THE HOOK could not load its analysis artifacts. Rebuild them with the documented artifact command.`

Log technical details for development, but do not show a raw stack trace in the main page.

### Invalid scenario

Fail closed. Do not render partial or mismatched candidate results. Show a short error and preserve navigation to a working scenario if possible.

### Tie

Use the same practical tie threshold everywhere. The recommendation card may show `Co-leader` or `Effectively tied`; it must not manufacture a decisive narrative.

### Model agrees

Agreement is a strong story too. State:

> `THE HOOK agrees with the manager's call.`

Then explain why the actual choice ranks first.

## 10. Responsive behavior

Target desktop/laptop judging first, but avoid failure on narrow screens.

- Two Manager-vs-Model cards may stack vertically below tablet width.
- Candidate chart labels must remain readable without horizontal scrolling.
- Situation metrics may wrap into two rows.
- Tables should use compact columns and avoid long explanation text inside cells.
- Keep essential comparison above long detail sections.

Do not spend MVP time on elaborate mobile-only navigation.

## 11. Accessibility checklist

- Contrast meets reasonable WCAG AA targets for text.
- Actual/recommended status includes text, not color alone.
- Base occupancy has a text representation.
- Plotly marks have hover/labels and adjacent text/table where needed.
- Controls have explicit labels.
- Heading order is logical.
- No flashing or autoplay animation.
- Use icons only with adjacent words.

## 12. 10/30/90-second design test

### In 10 seconds

The reviewer can answer:

- What sport is this?
- What decision is being made?
- Which choice does the model recommend?

### In 30 seconds

The reviewer can:

- Read the game situation.
- Compare actual and recommended choices.
- Understand the size of the estimated difference.

### In 90 seconds

The reviewer can:

- Change the selected reliever.
- See the result update.
- Hear two evidence-based reasons.
- Understand the model/data at a high level.
- Hear one honest limitation.

If the design cannot pass this test, remove content before adding new components.

## 13. Screenshot plan

After MVP freeze, capture:

1. Full flagship Decision Room with Manager vs Model.
2. Candidate ranking and recommendation reasons.
3. What-if choice showing a changed result.
4. How It Works metrics/calibration.
5. Optional second scenario demonstrating breadth.

Screenshots must use real validated values, no mock data, and a consistent viewport.

## 14. Design definition of done

- The flagship decision is visible with minimal scrolling.
- Hierarchy makes recommendation and delta unmistakable.
- Three scenarios share the same stable layout.
- All numbers and statuses are synchronized.
- The palette and chart template are consistent.
- Copy is concise and statistically responsible.
- Core path works at a laptop viewport.
- Loading/error/tie/agreement states are deliberate.
- The app passes the 10/30/90-second test.
