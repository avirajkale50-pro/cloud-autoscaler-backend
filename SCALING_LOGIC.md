# Scaling Decision Logic Documentation

## Overview
The autoscaler uses a **3-tier priority system** to make scaling decisions based on CPU, Memory, and Network metrics.

---

## Decision Priority Levels

| Priority | Condition | Action | Duration Required |
|----------|-----------|--------|-------------------|
| **1** | CPU < 10% **AND** Memory < 20% | Scale Down | 5 minutes sustained |
| **2** | CPU > 90% **OR** Memory > 90% | Scale Up | 5 minutes sustained |
| **3** | IQR-based outlier detection | Scale Up/Down/No Action | Based on last 5 minutes |

---

## Priority 1: Immediate Scale Down

### Conditions
```
Sustained Usage Check (5 minutes):
- CPU Utilization < 10%
- AND Memory Usage < 20%
- Sustained for ≥80% of time window
```

### Formula
```
matching_count = count of metrics where (CPU < 10% AND Memory < 20%)
total_count = total metrics in last 5 minutes
percentage = (matching_count / total_count) × 100

Decision: Scale Down if percentage ≥ 80%
```

### Outcome
- **Decision**: `scale_down`
- **Metric Flagged**: `is_outlier = True`, `outlier_type = scale_down`
- **Capacity Change**: CPU, Memory, Network capacity × 0.67 (33% reduction)
- **Scale Level**: Decremented by 1

---

## Priority 2: Immediate Scale Up

### Conditions (Either/Or)

#### Option A: High CPU
```
Sustained Usage Check (5 minutes):
- CPU Utilization > 90%
- Sustained for ≥80% of time window
```

#### Option B: High Memory
```
Sustained Usage Check (5 minutes):
- Memory Usage > 90%
- Sustained for ≥80% of time window
```

### Formula
```
matching_count = count of metrics where (CPU > 90% OR Memory > 90%)
total_count = total metrics in last 5 minutes
percentage = (matching_count / total_count) × 100

Decision: Scale Up if percentage ≥ 80%
```

### Outcome
- **Decision**: `scale_up`
- **Metric Flagged**: `is_outlier = True`, `outlier_type = scale_up`
- **Capacity Change**: CPU, Memory, Network capacity × 1.5 (50% increase)
- **Scale Level**: Incremented by 1

---

## Priority 3: IQR-Based Outlier Detection

### Prerequisites
- Minimum 4 non-outlier metrics in last 5 minutes
- If insufficient data → `no_action`

### IQR Formula (Applied to Each Metric)

```
Step 1: Sort metric values in ascending order
Step 2: Calculate quartiles
  Q1 = value at position (n / 4)
  Q3 = value at position (3n / 4)

Step 3: Calculate Interquartile Range
  IQR = Q3 - Q1

Step 4: Calculate bounds
  Lower Bound = Q1 - (1.5 × IQR)
  Upper Bound = Q3 + (1.5 × IQR)

Step 5: Compare current value
  If current_value > Upper Bound → Vote for Scale Up
  If current_value < Lower Bound → Vote for Scale Down
  Otherwise → No vote
```

---

## Metric Analysis & Voting System

| Metric | Weight | Scale Up Condition | Scale Down Condition |
|--------|--------|-------------------|---------------------|
| **CPU Utilization** | 2 votes | `current_cpu > (Q3 + 1.5×IQR)` | `current_cpu < (Q1 - 1.5×IQR)` |
| **Memory Usage** | 2 votes | `current_memory > (Q3 + 1.5×IQR)` | `current_memory < (Q1 - 1.5×IQR)` |
| **Network In** | 1 vote | `current_net_in > (Q3 + 1.5×IQR)` | `current_net_in < (Q1 - 1.5×IQR)` |
| **Network Out** | 1 vote | `current_net_out > (Q3 + 1.5×IQR)` | `current_net_out < (Q1 - 1.5×IQR)` |

### Decision Logic
```
Total Scale Up Votes = sum of all scale up votes
Total Scale Down Votes = sum of all scale down votes

If scale_up_votes ≥ 2:
  Decision = scale_up
  
Else If scale_down_votes ≥ 2:
  Decision = scale_down
  
Else:
  Decision = no_action
```

---

## Example Calculations

### Example 1: CPU-Based Scale Up (IQR)

**Historical CPU values (last 5 min):** `[45, 48, 50, 52, 55, 58, 60, 62]`

```
Step 1: Sort values (already sorted)
Step 2: Calculate quartiles
  n = 8
  Q1 = values[8/4] = values[2] = 50
  Q3 = values[3×8/4] = values[6] = 60

Step 3: IQR = 60 - 50 = 10

Step 4: Bounds
  Lower Bound = 50 - (1.5 × 10) = 35
  Upper Bound = 60 + (1.5 × 10) = 75

Step 5: Current CPU = 78%
  78 > 75 → Scale Up Vote (+2)
```

### Example 2: Network-Based Scale Down (IQR)

**Historical Network In values (bytes):** `[5000, 5200, 5500, 5800, 6000, 6200, 6500]`

```
Step 1: Sort values (already sorted)
Step 2: Calculate quartiles
  n = 7
  Q1 = values[7/4] = values[1] = 5200
  Q3 = values[3×7/4] = values[5] = 6200

Step 3: IQR = 6200 - 5200 = 1000

Step 4: Bounds
  Lower Bound = 5200 - (1.5 × 1000) = 3700
  Upper Bound = 6200 + (1.5 × 1000) = 7700

Step 5: Current Network In = 3000 bytes
  3000 < 3700 → Scale Down Vote (+1)
```

### Example 3: Combined Decision

**Current Metrics:**
- CPU: 78% → Above upper bound → +2 scale up votes
- Memory: 45% → Within bounds → 0 votes
- Network In: 3000 bytes → Below lower bound → +1 scale down vote
- Network Out: 4500 bytes → Within bounds → 0 votes

**Vote Tally:**
- Scale Up Votes: 2
- Scale Down Votes: 1

**Decision:** `scale_up` (scale_up_votes ≥ 2)

---

## Capacity Adjustment Formulas

### Scale Up
```
new_cpu_capacity = current_cpu_capacity × 1.5
new_memory_capacity = current_memory_capacity × 1.5
new_network_capacity = current_network_capacity × 1.5
new_scale_level = current_scale_level + 1
```

### Scale Down
```
new_cpu_capacity = current_cpu_capacity × 0.67
new_memory_capacity = current_memory_capacity × 0.67
new_network_capacity = current_network_capacity × 0.67
new_scale_level = current_scale_level - 1
```

**Note:** 0.67 is approximately the inverse of 1.5, ensuring symmetric scaling.

---

## Outlier Flagging

Metrics are flagged as outliers when:
- Priority 1 condition met → `is_outlier = True`, `outlier_type = 'scale_down'`
- Priority 2 condition met → `is_outlier = True`, `outlier_type = 'scale_up'`

**Impact:** Flagged metrics are excluded from future mean calculations and IQR analysis to prevent skewing the baseline.

---

## Time Windows

| Parameter | Duration | Purpose |
|-----------|----------|---------|
| **Sustained Check** | 5 minutes | Verify high/low usage is persistent, not a spike |
| **IQR Historical Data** | 5 minutes | Calculate baseline behavior for outlier detection |
| **Minimum Data Points** | 3 (sustained), 4 (IQR) | Ensure statistical validity |
| **Decision Frequency** | Every 15 seconds | How often scaling decisions are evaluated |

---

## Decision Flow Chart

```
┌─────────────────────────────────────┐
│   Get Latest Metric for Instance    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Priority 1: Check Sustained Low    │
│  CPU < 10% AND Memory < 20%         │
│  (5 min, ≥80% of time)              │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │    Yes    │──────────────────► SCALE DOWN
         └───────────┘
               │ No
               ▼
┌─────────────────────────────────────┐
│  Priority 2: Check Sustained High   │
│  CPU > 90% OR Memory > 90%          │
│  (5 min, ≥80% of time)              │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │    Yes    │──────────────────► SCALE UP
         └───────────┘
               │ No
               ▼
┌─────────────────────────────────────┐
│  Priority 3: IQR Analysis           │
│  Calculate Q1, Q3, IQR for each     │
│  metric from last 5 min             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Compare Current vs Bounds          │
│  Count votes for each metric        │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │ Up ≥ 2?   │──────────────────► SCALE UP
         └───────────┘
               │ No
         ┌─────┴─────┐
         │ Down ≥ 2? │──────────────────► SCALE DOWN
         └───────────┘
               │ No
               ▼
          NO ACTION
```

---

## Summary Table

| Scenario | CPU | Memory | Network In | Network Out | Votes | Decision |
|----------|-----|--------|------------|-------------|-------|----------|
| Extreme Low | <10% | <20% | - | - | N/A | **Scale Down** (Priority 1) |
| Extreme High | >90% | - | - | - | N/A | **Scale Up** (Priority 2) |
| Extreme High | - | >90% | - | - | N/A | **Scale Up** (Priority 2) |
| High CPU Only | >Q3+1.5×IQR | Normal | Normal | Normal | 2 up | **Scale Up** (Priority 3) |
| Low CPU Only | <Q1-1.5×IQR | Normal | Normal | Normal | 2 down | **Scale Down** (Priority 3) |
| High CPU + Net | >Q3+1.5×IQR | Normal | >Q3+1.5×IQR | Normal | 3 up | **Scale Up** (Priority 3) |
| Low All Metrics | <Q1-1.5×IQR | <Q1-1.5×IQR | <Q1-1.5×IQR | <Q1-1.5×IQR | 6 down | **Scale Down** (Priority 3) |
| Mixed Signals | >Q3+1.5×IQR | Normal | <Q1-1.5×IQR | Normal | 2 up, 1 down | **Scale Up** (Priority 3) |
| All Normal | Normal | Normal | Normal | Normal | 0 | **No Action** |
