# Weekly Efficiency View Design

**Date:** 2026-04-26

**Project:** Type Record

**Summary:** Add a weekly efficiency feature that helps the user see output efficiency changes over time without turning the app into a heavy analytics dashboard. The main view stays lightweight. A weekly summary strip appears on the home screen, and a dedicated weekly efficiency dialog provides the full analysis.

## Goal

Show whether the user's weekly output efficiency is improving or declining, using both total weekly output and active-session efficiency. Support two time scopes:

- Rolling 7 days
- Natural calendar week

Support three comparison frames:

- Versus previous week
- Versus trailing 4-week average
- Versus user-defined target

The feature should make weekly change obvious at a glance while keeping the current home screen uncluttered.

## Product Positioning

This is not a full analytics subsystem. The app should remain a focused desktop typing tracker with lightweight insight. The weekly efficiency feature should answer two questions:

1. How is this week going compared with last week?
2. Is the change caused by more output, better active efficiency, or more active time?

Home screen content should help the user detect change quickly. A detail dialog should explain the change.

## Approved Direction

Use the mixed layout approach:

- Add a lightweight weekly summary strip to the home screen
- Keep the existing global trend view on the home screen
- Add a separate weekly efficiency dialog for full weekly analysis

This avoids overloading the main view while still making weekly change visible.

## Definitions

### Primary Objective

Measure output efficiency, not typing-test speed and not a composite score.

### Weekly Output

Total weekly net characters.

Formula:

`sum(day.count)`

This is the main weekly result metric.

### Weekly Active Time

Total duration of all recorded sessions in the selected weekly window, converted to minutes.

Formula:

`sum(session.duration_seconds) / 60`

This is an activity measure, not full working time.

### Weekly Active Efficiency

Weekly net output divided by weekly active minutes.

Formula:

`weekly_output / weekly_active_minutes`

Display unit:

`net chars / minute`

If `weekly_active_minutes <= 0`, treat efficiency as unavailable rather than zero.

### Time Modes

#### Rolling 7 Days

Seven-day window ending today, inclusive.

#### Natural Week

Monday through Sunday. The current natural week can be shown as in progress before Sunday completes.

### Comparison Frames

#### Previous Week

- Rolling mode: current rolling 7-day window versus previous rolling 7-day window
- Natural week mode: current natural week versus previous natural week

Formula:

`(current - previous) / previous`

Special handling:

- If `previous == 0` and `current == 0`, show `0%`
- If `previous == 0` and `current > 0`, show `new`

#### 4-Week Average

Use the most recent four complete natural weeks as the baseline in the first version, even when the current display mode is rolling 7 days. This keeps interpretation stable and simple.

If fewer than four full weeks exist, average the available complete weeks. If no complete baseline week exists, show insufficient history.

#### Target

Use explicit user-configured targets in the first version:

- Weekly output target
- Weekly active efficiency target

Do not infer targets automatically in the first version.

## Home Screen Design

### Placement

Insert a weekly summary strip into the main window without replacing the primary daily workflow. It should sit between the current daily metrics and the explanatory status area, or directly above the larger trend area if that reads better in the final layout. It must not become a second hero block.

### Purpose

The summary strip answers one question:

`What is this week's efficiency state right now?`

### Content

The strip should include:

- Time mode toggle: `7D` and `Week`
- Weekly output
- Weekly active efficiency
- Primary comparison: versus previous week
- Secondary comparison text: versus 4-week average and versus target
- Entry point to the full weekly efficiency dialog

### Visual Behavior

The strip should stay compact and dense. It should feel like a status-summary band, not a card wall.

The most important values should be:

- Weekly active efficiency
- Versus previous week

Weekly output should remain visible but slightly less visually dominant than the efficiency change signal.

## Weekly Efficiency Dialog

### Purpose

The dialog explains why weekly efficiency changed.

### Structure

#### Top Summary

Show:

- Current mode: rolling 7 days or natural week
- Weekly output
- Weekly active time
- Weekly active efficiency

#### Middle Chart Area

Show a dual-series weekly view:

- Weekly output trend
- Weekly active efficiency trend

Also show:

- Previous-week context
- 4-week average reference
- Target line

The chart should prioritize readability over density. The user should immediately see whether output and efficiency moved together or diverged.

#### Bottom Interpretation Area

Show a short natural-language explanation derived from the computed values, for example:

`Output rose 9% versus last week, mainly from more active time; active efficiency fell 3%.`

This is a deterministic explanation template, not an AI feature.

## Data Model and Computation Boundaries

### Reuse Existing Data

Do not add new raw tracking fields. Reuse:

- `counts_by_date`
- `typed_by_date`
- `pasted_by_date`
- `backspace_by_date`
- `peak_wpm_by_date`
- `sessions_by_date`

The weekly feature is an interpretation layer on top of existing daily and session aggregates.

### Computation Layer

Weekly aggregation logic belongs in pure calculation helpers and storage queries, not in the UI layer.

## Codebase Integration

### `type_record/metrics.py`

Add pure computation helpers such as:

- weekly output calculation
- weekly active minute calculation
- weekly active efficiency calculation
- week-over-week change calculation
- 4-week average calculation

Add a dedicated structure for weekly results, for example `WeeklyEfficiencyMetrics`, containing:

- output
- active_minutes
- active_efficiency
- versus_previous_week
- versus_four_week_average
- versus_target

This module should not know anything about storage or Tkinter.

### `type_record/storage.py`

Add weekly data queries such as:

- rolling 7-day efficiency aggregation
- natural-week efficiency aggregation
- weekly efficiency history for charting

Also add internal helpers for:

- collecting day keys for rolling windows
- collecting day keys for natural weeks
- gathering matching session records

Storage is responsible for slicing and assembling source data. It should return already-aggregated weekly result objects or dictionaries suitable for the UI.

### `type_record/ui.py`

Add:

- a weekly summary strip on the main screen
- a `open_weekly_efficiency_dialog()` entry point
- a dedicated weekly detail dialog layout

The UI layer should not contain week-window math or comparison formulas.

### `type_record/i18n.py`

Add only the strings needed for the weekly feature, including labels for:

- weekly efficiency
- weekly output
- weekly active time
- weekly active efficiency
- rolling 7 days
- natural week
- versus last week
- versus 4-week average
- versus target
- insufficient history
- new baseline state

## Testing Strategy

### `tests/test_metrics.py`

Add tests for:

- active-time minute conversion
- efficiency calculation
- previous-week change calculation
- zero-baseline special cases
- 4-week average calculation

### `tests/test_storage.py`

Add tests for:

- rolling 7-day boundary correctness
- natural-week boundary correctness
- mixed daily and session aggregation
- insufficient-history behavior
- target comparison output shape

### UI Testing Scope

Do not attempt full UI automation in the first version. Keep UI verification focused on:

- data is shown in the correct widgets
- dialog opens without error
- mode switch refreshes displayed values

## Risks and Handling

### Active Time Is Not Full Working Time

Risk:

Session duration is an approximation of active typing work, not complete time spent thinking or drafting.

Handling:

Always label it as `Active Time`, never as total work time.

### Rolling and Natural Week Can Disagree

Risk:

The user may see different results in rolling and natural-week mode.

Handling:

This is expected. The UI must always show the currently selected mode clearly and compute comparisons only within that mode.

### Limited History

Risk:

New users may not have enough history for stable weekly comparison.

Handling:

Show partial baselines when possible and `insufficient history` when a stable baseline does not exist.

### Zero Previous Week

Risk:

Percentage change becomes misleading when the previous week is zero.

Handling:

Show `new` instead of an artificial percentage explosion.

### Settings Complexity

Risk:

Adding too many target settings makes configuration heavier than the feature deserves.

Handling:

Limit the first version to two user targets:

- weekly output target
- weekly active efficiency target

## First Version Scope

### In Scope

- Home screen weekly summary strip
- Weekly efficiency dialog
- Rolling 7-day and natural-week modes
- Weekly output, active time, active efficiency
- Previous-week comparison
- 4-week average comparison
- Target comparison

### Out of Scope

- Composite efficiency score
- AI-generated explanations
- Hour-of-day weekly decomposition
- Heatmaps or dashboard-style multi-chart analytics
- Automatic target recommendation
- Ranking or leaderboard-style tables

## Recommendation

Build the first version as a focused explanation layer:

- Home screen detects change
- Weekly dialog explains change

Do not turn the feature into a broad analytics module in the first release.
