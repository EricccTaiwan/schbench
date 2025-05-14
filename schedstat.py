#!/usr/bin/env python3

import sys
import time

# Domain fields by schedstat version
# read kernel/sched/stats.c:show_schedstat() to find the definitions
DOMAIN_FIELDS_V15 = [
    # CPU_IDLE
    "lb_count_idle",
    "lb_balance_idle",
    "lb_failed_idle",
    "lb_imbalance_idle",
    "lb_gained_idle",
    "lb_hot_gained_idle",
    "lb_nobusyq_idle",
    "lb_nobusyg_idle",

    # CPU_NOT_IDLE
    "lb_count_not_idle",
    "lb_balance_not_idle",
    "lb_failed_not_idle",
    "lb_imbalance_not_idle",
    "lb_gained_not_idle",
    "lb_hot_gained_not_idle",
    "lb_nobusyq_not_idle",
    "lb_nobusyg_not_idle",

    # CPU_NEWLY_IDLE
    "lb_count_newly_idle",
    "lb_balance_newly_idle",
    "lb_failed_newly_idle",
    "lb_imbalance_newly_idle",
    "lb_gained_newly_idle",
    "lb_hot_gained_newly_idle",
    "lb_nobusyq_newly_idle",
    "lb_nobusyg_newly_idle",

    "alb_count",
    "alb_failed",
    "alb_pushed",
    "sbe_cnt",
    "sbe_balanced",
    "sbe_pushed",
    "sbf_cnt",
    "sbf_balanced",
    "sbf_pushed",
    "ttwu_wake_remote",
    "ttwu_move_affine",
    "ttwu_move_balance"
]

# this is the same as v15, but the order of the idle type enum
# is different
DOMAIN_FIELDS_V16 = [
    # __CPU_NOT_IDLE
    "lb_count_not_idle",
    "lb_balance_not_idle",
    "lb_failed_not_idle",
    "lb_imbalance_not_idle",
    "lb_gained_not_idle",
    "lb_hot_gained_not_idle",
    "lb_nobusyq_not_idle",
    "lb_nobusyg_not_idle",

    # CPU_IDLE
    "lb_count_idle",
    "lb_balance_idle",
    "lb_failed_idle",
    "lb_imbalance_idle",
    "lb_gained_idle",
    "lb_hot_gained_idle",
    "lb_nobusyq_idle",
    "lb_nobusyg_idle",

    # CPU_NEWLY_IDLE
    "lb_count_newly_idle",
    "lb_balance_newly_idle",
    "lb_failed_newly_idle",
    "lb_imbalance_newly_idle",
    "lb_gained_newly_idle",
    "lb_hot_gained_newly_idle",
    "lb_nobusyq_newly_idle",
    "lb_nobusyg_newly_idle",

    "alb_count",
    "alb_failed",
    "alb_pushed",
    "sbe_cnt",
    "sbe_balanced",
    "sbe_pushed",
    "sbf_cnt",
    "sbf_balanced",
    "sbf_pushed",
    "ttwu_wake_remote",
    "ttwu_move_affine",
    "ttwu_move_balance"
]

DOMAIN_FIELDS_V17 = [
    # __CPU_NOT_IDLE
    "lb_count_not_idle",
    "lb_balance_not_idle",
    "lb_failed_not_idle",
    "lb_imbalance_load_not_idle",
    "lb_imbalance_util_not_idle",
    "lb_imbalance_task_not_idle",
    "lb_imbalance_misfit_not_idle",
    "lb_gained_not_idle",
    "lb_hot_gained_not_idle",
    "lb_nobusyq_not_idle",
    "lb_nobusyg_not_idle",

    # CPU_IDLE
    "lb_count_idle",
    "lb_balance_idle",
    "lb_failed_idle",
    "lb_imbalance_load_idle",
    "lb_imbalance_util_idle",
    "lb_imbalance_task_idle",
    "lb_imbalance_misfit_idle",
    "lb_gained_idle",
    "lb_hot_gained_idle",
    "lb_nobusyq_idle",
    "lb_nobusyg_idle",

    # CPU_NEWLY_IDLE
    "lb_count_newly_idle",
    "lb_balance_newly_idle",
    "lb_failed_newly_idle",
    "lb_imbalance_load_newly_idle",
    "lb_imbalance_util_newly_idle",
    "lb_imbalance_task_newly_idle",
    "lb_imbalance_misfit_newly_idle",
    "lb_gained_newly_idle",
    "lb_hot_gained_newly_idle",
    "lb_nobusyq_newly_idle",
    "lb_nobusyg_newly_idle",

    "alb_count",
    "alb_failed",
    "alb_pushed",
    "sbe_cnt",
    "sbe_balanced",
    "sbe_pushed",
    "sbf_cnt",
    "sbf_balanced",
    "sbf_pushed",
    "ttwu_wake_remote",
    "ttwu_move_affine",
    "ttwu_move_balance"
]

# Common CPU fields (adjust if your kernel differs)
# these are the same in 15 and 17
CPU_FIELDS = [
    "yld_count", "sched_count", "sched_goidle", "ttwu_count",
    "ttwu_local", "rq_cpu_time", "rq_run_delay", "rq_pcount"
]


def detect_schedstat_version():
    with open("/proc/schedstat", "r") as f:
        for line in f:
            if line.startswith("version"):
                return int(line.strip().split()[1])
    return 15  # Default to v15 if not specified


def parse_domains(lines, version):
    domains = []
    for line in lines:
        if line.startswith("domain"):
            parts = line.split()
            if version == 17:
                values = list(map(int, parts[3:]))
                fields = DOMAIN_FIELDS_V17
            elif version == 16:
                values = list(map(int, parts[2:]))
                fields = DOMAIN_FIELDS_V16
            elif version == 15:
                values = list(map(int, parts[2:]))
                fields = DOMAIN_FIELDS_V15
            else:
                sys.stderr.write("Unsupported schedstat version %d" % version)
                sys.exit(1)
            domain = dict(zip(fields, values))
            domains.append(domain)
    return domains


def parse_cpus(lines):
    cpus = {}
    for line in lines:
        if line.startswith("cpu") and not line.startswith("cpufreq"):
            parts = line.split()
            cpu_id = parts[0]
            values = list(map(int, parts[1:]))
            cpus[cpu_id] = values
    return cpus


def read_schedstat():
    version = detect_schedstat_version()
    with open("/proc/schedstat", "r") as f:
        lines = [line.strip() for line in f if line.strip() and
                 not line.startswith("version")]
    domains = parse_domains(lines, version)
    cpus = parse_cpus(lines)
    return version, domains, cpus


def sum_domains(domains):
    if not domains:
        return {}
    summed = {}
    for field in domains[0].keys():
        summed[field] = sum(domain.get(field, 0) for domain in domains)
    return summed


def print_delta(delta, label):
    print(f"\nSystem-wide domain counter deltas ({label}):")
    for field, value in delta.items():
        print(f"{field}: {value}")


def cpu_delta(start_cpus, end_cpus):
    if not start_cpus or not end_cpus:
        return []
    num_fields = min(len(list(start_cpus.values())[0]),
                     len(list(end_cpus.values())[0]))
    combined = [0] * num_fields
    for cpu in start_cpus:
        if cpu in end_cpus:
            start_vals = start_cpus[cpu]
            end_vals = end_cpus[cpu]
            for i in range(num_fields):
                combined[i] += end_vals[i] - start_vals[i]
    return combined


def print_cpu_deltas(deltas, field_names=None):

    print("\nCombined CPU field deltas (all CPUs):")
    if field_names is None:
        for idx, val in enumerate(deltas):
            print(f"field_{idx}: {val}")
    else:
        for name, val in zip(field_names, deltas):
            print(f"{name}: {val}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <interval_seconds>")
        sys.exit(1)
    try:
        interval = float(sys.argv[1])
    except Exception:
        print("Interval must be a number (seconds).")
        sys.exit(1)

    version, start_domains, start_cpus = read_schedstat()
    start_sum = sum_domains(start_domains)

    time.sleep(interval)

    _, end_domains, end_cpus = read_schedstat()
    end_sum = sum_domains(end_domains)

    # Print domain deltas
    delta = {field: end_sum.get(field, 0) - start_sum.get(field, 0)
             for field in start_sum.keys()}
    print_delta(delta, f"interval {interval}s")

    # Print combined CPU field deltas
    cpu_field_names = CPU_FIELDS
    deltas = cpu_delta(start_cpus, end_cpus)
    print_cpu_deltas(deltas, cpu_field_names)


if __name__ == "__main__":
    main()
