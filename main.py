"""
main.py — CPU Scheduling Simulator CLI
Run: python main.py
"""

from scheduler import Process, fcfs, sjf, srt, round_robin, mlfq, averages

# ─────────────────────────────────────────────
# Display Helpers
# ─────────────────────────────────────────────

def print_banner():
    print("\n" + "="*60)
    print("       CPU SCHEDULING ALGORITHM SIMULATOR")
    print("       Operating Systems Project")
    print("="*60 + "\n")

def print_gantt(gantt):
    print("\n  Gantt Chart:")
    print("  ", end="")
    for pid, start, end in gantt:
        width = max(len(pid), (end - start)) + 1
        print(f"| {pid:^{width}} ", end="")
    print("|")

    # Time labels
    print("  ", end="")
    for pid, start, end in gantt:
        width = max(len(pid), (end - start)) + 1
        print(f"  {start:<{width}} ", end="")
    # Print last end time
    print(gantt[-1][2])
    print()

def print_metrics(processes):
    print(f"\n  {'PID':<6} {'Arrival':>8} {'Burst':>7} {'Start':>7} {'Finish':>8} {'Wait':>6} {'TAT':>6} {'RT':>6}")
    print("  " + "-"*58)
    for p in sorted(processes, key=lambda x: x.pid):
        print(f"  {p.pid:<6} {p.arrival_time:>8} {p.burst_time:>7} {p.start_time:>7} {p.finish_time:>8} {p.waiting_time:>6} {p.turnaround_time:>6} {p.response_time:>6}")

    avgs = averages(processes)
    print("  " + "-"*58)
    print(f"  {'Average':<6} {'':>8} {'':>7} {'':>7} {'':>8} {avgs['avg_waiting']:>6.2f} {avgs['avg_turnaround']:>6.2f} {avgs['avg_response']:>6.2f}")

def print_comparison(results):
    print("\n" + "="*60)
    print("  COMPARISON TABLE")
    print("="*60)
    print(f"  {'Algorithm':<22} {'Avg Wait':>10} {'Avg TAT':>10} {'Avg RT':>10}")
    print("  " + "-"*52)

    best_wt  = min(v['avg_waiting']    for v in results.values())
    best_tat = min(v['avg_turnaround'] for v in results.values())
    best_rt  = min(v['avg_response']   for v in results.values())

    for name, avgs in results.items():
        wt_mark  = " ★" if avgs['avg_waiting']    == best_wt  else ""
        tat_mark = " ★" if avgs['avg_turnaround'] == best_tat else ""
        rt_mark  = " ★" if avgs['avg_response']   == best_rt  else ""
        print(f"  {name:<22} {avgs['avg_waiting']:>10.2f}{wt_mark:<3} {avgs['avg_turnaround']:>10.2f}{tat_mark:<3} {avgs['avg_response']:>10.2f}{rt_mark}")

    print("\n  ★ = best in that metric\n")

# ─────────────────────────────────────────────
# Input Helpers
# ─────────────────────────────────────────────

def get_int(prompt, default=None, min_val=None):
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
            if min_val is not None and val < min_val:
                print(f"  ✗ Must be at least {min_val}. Try again.")
                continue
            return val
        except ValueError:
            print("  ✗ Please enter a valid integer.")

def input_processes():
    print("\n── STEP 1: Enter Processes ──────────────────────────")
    print("  (Leave PID blank when done)\n")
    processes = []
    pid_counter = 1

    while True:
        default_pid = f"P{pid_counter}"
        pid = input(f"  Process ID [{default_pid}]: ").strip() or default_pid
        if pid == "" and processes:
            break

        if any(p.pid == pid for p in processes):
            print(f"  ✗ PID '{pid}' already used. Try another.")
            continue

        arrival = get_int(f"  Arrival Time  [0]: ", default=0, min_val=0)
        burst   = get_int(f"  Burst Time       : ", min_val=1)
        priority = get_int(f"  Priority      [0]: ", default=0, min_val=0)

        processes.append(Process(pid, arrival, burst, priority))
        print(f"  ✓ {pid} added (arrival={arrival}, burst={burst})\n")
        pid_counter += 1

        if input("  Add another process? [Y/n]: ").strip().lower() == 'n':
            break

    return processes

def load_sample():
    print("\n  Loading sample scenario from project spec...")
    return [
        Process("P1", arrival_time=0, burst_time=5),
        Process("P2", arrival_time=1, burst_time=3),
        Process("P3", arrival_time=2, burst_time=8),
        Process("P4", arrival_time=3, burst_time=6),
    ]

def choose_algorithm():
    print("\n── STEP 2: Choose Algorithm ─────────────────────────")
    print("  1) FCFS  — First Come First Serve")
    print("  2) SJF   — Shortest Job First (Non-preemptive)")
    print("  3) SRT   — Shortest Remaining Time (Preemptive)")
    print("  4) RR    — Round Robin")
    print("  5) MLFQ  — Multilevel Feedback Queue")
    print("  6) ALL   — Run all algorithms and compare")

    while True:
        choice = input("\n  Select [1-6]: ").strip()
        if choice in {'1','2','3','4','5','6'}:
            return choice
        print("  ✗ Enter a number between 1 and 6.")

def get_rr_quantum():
    return get_int("  Time Quantum [2]: ", default=2, min_val=1)

def get_mlfq_config():
    print("  MLFQ Queue config:")
    q0 = get_int("    Queue 0 quantum [2]: ", default=2, min_val=1)
    q1 = get_int("    Queue 1 quantum [4]: ", default=4, min_val=1)
    print("    Queue 2: FCFS (no preemption)")
    return [q0, q1, float('inf')]

# ─────────────────────────────────────────────
# Run One Algorithm
# ─────────────────────────────────────────────

def run_one(choice, processes, rq=2, mq=None):
    if mq is None:
        mq = [2, 4, float('inf')]

    algo_map = {
        '1': ('FCFS',                  lambda: fcfs(processes)),
        '2': ('SJF (Non-Preemptive)', lambda: sjf(processes)),
        '3': ('SRT (Preemptive)',      lambda: srt(processes)),
        '4': (f'Round Robin (q={rq})', lambda: round_robin(processes, rq)),
        '5': (f'MLFQ (q={mq[0]},{mq[1]},∞)', lambda: mlfq(processes, mq)),
    }

    name, fn = algo_map[choice]
    print(f"\n{'='*60}")
    print(f"  RESULT — {name}")
    print(f"{'='*60}")

    done, gantt = fn()
    print_gantt(gantt)
    print_metrics(done)
    return name, averages(done)

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print_banner()

    # Process input
    print("  1) Enter processes manually")
    print("  2) Load sample scenario (P1–P4 from spec)")
    src = input("\n  Choose [1/2]: ").strip()
    processes = load_sample() if src == '2' else input_processes()

    if not processes:
        print("  No processes entered. Exiting.")
        return

    print(f"\n  ✓ {len(processes)} process(es) loaded.")

    # Algorithm
    choice = choose_algorithm()

    rq = 2
    mq = [2, 4, float('inf')]

    if choice == '4':
        rq = get_rr_quantum()
    elif choice == '5':
        mq = get_mlfq_config()
    elif choice == '6':
        rq = get_rr_quantum()
        mq = get_mlfq_config()

    # Run
    if choice == '6':
        results = {}
        for c in ['1','2','3','4','5']:
            name, avgs = run_one(c, processes, rq, mq)
            results[name] = avgs
        print_comparison(results)
    else:
        run_one(choice, processes, rq, mq)

if __name__ == "__main__":
    main()
