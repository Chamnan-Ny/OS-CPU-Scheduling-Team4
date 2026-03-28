"""
CPU Scheduling Simulator
Implements: FCFS, SJF (Non-preemptive), SRT (Preemptive), Round Robin, MLFQ
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from collections import deque
import copy


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0

    # Runtime tracking
    remaining_time: int = field(init=False)
    start_time: Optional[int] = field(default=None, init=False)
    finish_time: Optional[int] = field(default=None, init=False)
    waiting_time: int = field(default=0, init=False)
    turnaround_time: int = field(default=0, init=False)
    response_time: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        self.remaining_time = self.burst_time

    def reset(self):
        self.remaining_time = self.burst_time
        self.start_time = None
        self.finish_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None


GanttEntry = Tuple[str, int, int]  # (pid or "IDLE", start, end)


def clone_processes(processes: List[Process]) -> List[Process]:
    """Deep clone process list for simulation."""
    cloned = []
    for p in processes:
        c = Process(p.pid, p.arrival_time, p.burst_time, p.priority)
        cloned.append(c)
    return cloned


def compute_metrics(processes: List[Process]):
    """Compute WT, TAT, RT for all finished processes."""
    for p in processes:
        p.turnaround_time = p.finish_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        if p.response_time is None:
            p.response_time = p.start_time - p.arrival_time


# ─────────────────────────────────────────────
# 1. FCFS — First Come First Serve
# ─────────────────────────────────────────────
def fcfs(processes: List[Process]) -> Tuple[List[Process], List[GanttEntry]]:
    procs = clone_processes(processes)
    procs.sort(key=lambda p: (p.arrival_time, p.pid))
    gantt: List[GanttEntry] = []
    current_time = 0

    for p in procs:
        if current_time < p.arrival_time:
            gantt.append(("IDLE", current_time, p.arrival_time))
            current_time = p.arrival_time

        p.start_time = current_time
        p.response_time = current_time - p.arrival_time
        current_time += p.burst_time
        p.finish_time = current_time
        gantt.append((p.pid, p.start_time, p.finish_time))

    compute_metrics(procs)
    return procs, gantt


# ─────────────────────────────────────────────
# 2. SJF — Shortest Job First (Non-preemptive)
# ─────────────────────────────────────────────
def sjf(processes: List[Process]) -> Tuple[List[Process], List[GanttEntry]]:
    procs = clone_processes(processes)
    gantt: List[GanttEntry] = []
    current_time = 0
    remaining = list(procs)
    done = []

    while remaining:
        available = [p for p in remaining if p.arrival_time <= current_time]
        if not available:
            next_arrival = min(p.arrival_time for p in remaining)
            gantt.append(("IDLE", current_time, next_arrival))
            current_time = next_arrival
            continue

        # Pick shortest burst; tie-break by arrival then pid
        chosen = min(available, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        remaining.remove(chosen)

        chosen.start_time = current_time
        chosen.response_time = current_time - chosen.arrival_time
        current_time += chosen.burst_time
        chosen.finish_time = current_time
        gantt.append((chosen.pid, chosen.start_time, chosen.finish_time))
        done.append(chosen)

    compute_metrics(done)
    return done, gantt


# ─────────────────────────────────────────────
# 3. SRT — Shortest Remaining Time (Preemptive)
# ─────────────────────────────────────────────
def srt(processes: List[Process]) -> Tuple[List[Process], List[GanttEntry]]:
    procs = clone_processes(processes)
    gantt: List[GanttEntry] = []
    current_time = 0
    remaining = list(procs)
    done = []
    current_proc = None
    seg_start = 0

    all_times = sorted(set(
        [p.arrival_time for p in procs] +
        [p.arrival_time + p.burst_time for p in procs]
    ))

    time = 0
    max_time = sum(p.burst_time for p in procs) + max(p.arrival_time for p in procs) + 1

    while len(done) < len(procs) and time <= max_time:
        available = [p for p in remaining if p.arrival_time <= time and p not in done]

        if not available:
            if current_proc and current_proc.pid != "IDLE":
                gantt.append((current_proc.pid, seg_start, time))
                current_proc = None
            if remaining:
                next_t = min(p.arrival_time for p in remaining if p not in done) if [p for p in remaining if p not in done] else time + 1
                gantt.append(("IDLE", time, next_t))
                time = next_t
            continue

        best = min(available, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

        if current_proc != best:
            if current_proc is not None:
                gantt.append((current_proc.pid, seg_start, time))
            seg_start = time
            current_proc = best

        if best.start_time is None:
            best.start_time = time
            best.response_time = time - best.arrival_time

        best.remaining_time -= 1
        time += 1

        if best.remaining_time == 0:
            gantt.append((best.pid, seg_start, time))
            best.finish_time = time
            remaining.remove(best)
            done.append(best)
            current_proc = None
            seg_start = time

    # Merge consecutive same-pid gantt entries
    merged = []
    for entry in gantt:
        if merged and merged[-1][0] == entry[0] and merged[-1][2] == entry[1]:
            merged[-1] = (merged[-1][0], merged[-1][1], entry[2])
        else:
            merged.append(list(entry))
    gantt = [tuple(e) for e in merged]

    compute_metrics(done)
    return done, gantt


# ─────────────────────────────────────────────
# 4. Round Robin
# ─────────────────────────────────────────────
def round_robin(processes: List[Process], quantum: int = 2) -> Tuple[List[Process], List[GanttEntry]]:
    procs = clone_processes(processes)
    gantt: List[GanttEntry] = []
    queue: deque = deque()
    remaining = sorted(procs, key=lambda p: p.arrival_time)
    time = 0
    done = []
    in_queue = set()

    def enqueue_arrivals(t):
        for p in remaining:
            if p.pid not in in_queue and p.arrival_time <= t and p not in done:
                queue.append(p)
                in_queue.add(p.pid)

    enqueue_arrivals(0)

    while queue or any(p not in done for p in remaining):
        if not queue:
            next_arrival = min(p.arrival_time for p in remaining if p not in done)
            gantt.append(("IDLE", time, next_arrival))
            time = next_arrival
            enqueue_arrivals(time)
            continue

        p = queue.popleft()

        if p.start_time is None:
            p.start_time = time
            p.response_time = time - p.arrival_time

        run_time = min(quantum, p.remaining_time)
        gantt.append((p.pid, time, time + run_time))
        time += run_time
        p.remaining_time -= run_time

        enqueue_arrivals(time)

        if p.remaining_time == 0:
            p.finish_time = time
            done.append(p)
        else:
            queue.append(p)

    compute_metrics(done)
    return done, gantt


# ─────────────────────────────────────────────
# 5. MLFQ — Multilevel Feedback Queue
#    Queue 0: RR q=2  | Queue 1: RR q=4  | Queue 2: FCFS
#    Demotion: process uses full quantum → demoted
#    Aging:    process waits >AGING_THRESHOLD ticks → promoted
# ─────────────────────────────────────────────
AGING_THRESHOLD = 10


def mlfq(processes: List[Process], quantums: List[int] = None) -> Tuple[List[Process], List[GanttEntry]]:
    if quantums is None:
        quantums = [2, 4, float('inf')]  # inf = FCFS

    procs = clone_processes(processes)
    gantt: List[GanttEntry] = []

    # Each process tracks: queue level, time_in_queue (for aging), wait_since
    class MLFQProc:
        def __init__(self, proc):
            self.proc = proc
            self.level = 0
            self.wait_start = proc.arrival_time

    mprocs = [MLFQProc(p) for p in procs]
    queues = [deque() for _ in range(3)]
    remaining = sorted(mprocs, key=lambda m: m.proc.arrival_time)
    in_queue = set()
    done = []
    time = 0

    def enqueue_arrivals(t):
        for m in remaining:
            if m.proc.pid not in in_queue and m.proc.arrival_time <= t and m.proc not in done:
                queues[m.level].append(m)
                in_queue.add(m.proc.pid)
                m.wait_start = t

    def apply_aging(t):
        """Promote processes that have waited too long."""
        for level in range(1, 3):
            to_promote = []
            for m in list(queues[level]):
                if t - m.wait_start >= AGING_THRESHOLD:
                    to_promote.append(m)
            for m in to_promote:
                queues[level].remove(m)
                new_level = max(0, level - 1)
                m.level = new_level
                m.wait_start = t
                queues[new_level].appendleft(m)  # priority position

    enqueue_arrivals(0)

    max_time = sum(p.proc.burst_time for p in mprocs) + max(p.proc.arrival_time for p in mprocs) + 1

    while len(done) < len(procs) and time <= max_time:
        apply_aging(time)

        # Pick from highest-priority non-empty queue
        chosen_level = None
        chosen = None
        for lvl in range(3):
            if queues[lvl]:
                chosen_level = lvl
                chosen = queues[lvl].popleft()
                break

        if chosen is None:
            # CPU idle — advance to next arrival
            upcoming = [m for m in remaining if m.proc not in done and m.proc.pid not in in_queue]
            if not upcoming:
                break
            next_t = min(m.proc.arrival_time for m in upcoming)
            gantt.append(("IDLE", time, next_t))
            time = next_t
            enqueue_arrivals(time)
            continue

        p = chosen.proc
        q = quantums[chosen_level]

        if p.start_time is None:
            p.start_time = time
            p.response_time = time - p.arrival_time

        run_time = min(q, p.remaining_time) if q != float('inf') else p.remaining_time
        gantt.append((p.pid, time, time + run_time))
        time += run_time
        p.remaining_time -= run_time

        enqueue_arrivals(time)
        apply_aging(time)

        if p.remaining_time == 0:
            p.finish_time = time
            done.append(p)
        else:
            # Demote if used full quantum (not in bottom queue)
            used_full_quantum = (q != float('inf') and run_time == q)
            if used_full_quantum and chosen_level < 2:
                chosen.level = chosen_level + 1
            else:
                chosen.level = chosen_level  # stay same level (partial use or bottom)
            chosen.wait_start = time
            queues[chosen.level].append(chosen)

    compute_metrics(done)
    return done, gantt


# ─────────────────────────────────────────────
# Averages helper
# ─────────────────────────────────────────────
def averages(processes: List[Process]) -> dict:
    n = len(processes)
    return {
        "avg_waiting": sum(p.waiting_time for p in processes) / n,
        "avg_turnaround": sum(p.turnaround_time for p in processes) / n,
        "avg_response": sum(p.response_time for p in processes) / n,
    }
