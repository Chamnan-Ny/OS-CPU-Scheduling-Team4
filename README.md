# OS-CPU-Scheduling-Team4

> CPU Scheduling Algorithm Simulator — Operating Systems Project

Simulates **FCFS, SJF, SRT, Round Robin, and MLFQ** scheduling algorithms with Gantt chart output and performance metrics (Waiting Time, Turnaround Time, Response Time).

---

## Project Structure

```
OS-CPU-Scheduling-Team4/
├── scheduler.py          # Core algorithm engine (all 5 algorithms)
├── main.py               # CLI interface — run this
├── index.html            # Web UI — open in browser (no server needed)
└── README.md
```

---

## Setup & Installation

**Requirements:** Python 3.6 or higher. No external libraries needed.

```bash
# Check your Python version
python --version

---

## How to Run

### Option A — CLI (Terminal)

```bash
python main.py
```

You will be prompted to:
1. Enter processes manually **or** load the sample scenario
2. Choose an algorithm (1–5) or run **ALL** for comparison
3. Configure the time quantum for RR / MLFQ if selected

### Option B — Web UI (Browser)

Simply double-click `index.html` — it opens in your browser with no setup required.

Features:
- Add/remove processes interactively
- Live Gantt chart with color-coded bars
- Full metrics table (WT, TAT, RT, averages)
- "Run All & Compare" mode with bar charts across all 5 algorithms

---

## Algorithms Implemented

| # | Algorithm | Type | Description |
|---|-----------|------|-------------|
| 1 | **FCFS**| Non-preemptive | Executes in arrival order |
| 2 | **SJF** | Non-preemptive | Shortest burst runs first |
| 3 | **SRT** | Preemptive | Preempts if shorter job arrives |
| 4 | **Round Robin** | Preemptive | Equal time slices, configurable quantum |
| 5 | **MLFQ** | Preemptive | 3-level adaptive queue with aging |

**MLFQ Queue Structure:**
- Queue 0: Round Robin, quantum = 2 (default)
- Queue 1: Round Robin, quantum = 4 (default)
- Queue 2: FCFS (no preemption)
- Aging threshold: 10 ticks (prevents starvation)

---

## Sample Input / Output

**Input (sample scenario from spec):**

| Process | Arrival | Burst |
|---------|---------|-------|
| P1      |    0    |   5   |
| P2      |    1    |   3   |
| P3      |    2    |   8   |
| P4      |    3    |   6   |

**Output — FCFS:**
```
Gantt Chart:
| P1    | P2   | P3       | P4      |
  0       5      8          16      22

PID    Arrival  Burst  Start  Finish  Wait   TAT    RT
P1           0      5      0       5     0     5     0
P2           1      3      5       8     4     7     4
P3           2      8      8      16     6    14     6
P4           3      6     16      22    13    19    13
Average                                5.75 11.25  5.75
```

**Comparison — All Algorithms (sample scenario, RR q=2):**

| Algorithm | Avg Wait | Avg TAT | Avg RT |
|-----------|----------|---------|--------|
| FCFS      |   5.75   |  11.25  |  5.75  |
| SJF       |   5.25   |  10.75  |  5.25  |
| SRT ★WT ★TAT | **5.00** | **10.50** | 4.25 |
| RR        |   9.75   |  15.25  |  2.00  |
| MLFQ ★RT |   9.25    | 14.75   | **1.50** |

★ = best in that metric

---

## Using scheduler.py as a Module

```python
from scheduler import Process, fcfs, sjf, srt, round_robin, mlfq, averages

processes = [
    Process("P1", arrival_time=0, burst_time=5),
    Process("P2", arrival_time=1, burst_time=3),
]

done, gantt = round_robin(processes, quantum=2)
avgs = averages(done)
print(f"Avg Waiting Time: {avgs['avg_waiting']:.2f}")

# Gantt is a list of (pid, start, end) tuples
for pid, start, end in gantt:
    print(f"  {pid}: {start} → {end}")
```

