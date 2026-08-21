#!/usr/bin/env python3
"""Small dependency-free CPU and disk benchmark for sysops."""

import argparse
import multiprocessing as mp
import os
import tempfile
import time


def benchmark_disk(duration=0.33, block_size_mb=4):
    """Measure sequential temporary-file write/read throughput in MB/s."""
    block = os.urandom(block_size_mb * 1024 * 1024)
    fd, tmp_path = tempfile.mkstemp(prefix="sysops-bench-")
    os.close(fd)
    try:
        written_bytes = 0
        start = time.perf_counter()
        with open(tmp_path, "wb") as handle:
            while time.perf_counter() - start < duration:
                handle.write(block)
                written_bytes += len(block)
            handle.flush()
            os.fsync(handle.fileno())
        elapsed = max(time.perf_counter() - start, 1e-9)
        write_mb_s = written_bytes / (1024 * 1024) / elapsed

        read_bytes = 0
        start = time.perf_counter()
        with open(tmp_path, "rb") as handle:
            while time.perf_counter() - start < duration:
                chunk = handle.read(len(block))
                if not chunk:
                    handle.seek(0)
                    continue
                read_bytes += len(chunk)
        elapsed = max(time.perf_counter() - start, 1e-9)
        read_mb_s = read_bytes / (1024 * 1024) / elapsed
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return {"write_mb_s": round(write_mb_s, 1), "read_mb_s": round(read_mb_s, 1)}


def _cpu_worker(duration, result_queue=None):
    count = 0
    start = time.perf_counter()
    value = 0
    while time.perf_counter() - start < duration:
        value = (value * 1103515245 + 12345) & 0x7FFFFFFF
        count += 1
    if result_queue is not None:
        result_queue.put(count)
    return count


def benchmark_cpu_single(duration=0.33):
    ops = _cpu_worker(duration)
    return {"ops": ops, "ops_per_sec": int(ops / max(duration, 1e-9))}


def benchmark_cpu_multi(duration=0.33):
    cores = os.cpu_count() or 1
    queue = mp.Queue()
    processes = [mp.Process(target=_cpu_worker, args=(duration, queue)) for _ in range(cores)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    total_ops = sum(queue.get() for _ in processes)
    queue.close()
    queue.join_thread()
    return {"cores_used": cores, "ops": total_ops, "ops_per_sec": int(total_ops / max(duration, 1e-9))}


def run_benchmark(duration=0.33, include_multi_core=True):
    """Run disk, single-core, and optionally multi-core tests."""
    results = {
        "disk": benchmark_disk(duration=duration),
        "cpu_single": benchmark_cpu_single(duration=duration),
    }
    if include_multi_core:
        results["cpu_multi"] = benchmark_cpu_multi(duration=duration)
    return results


def print_results(results):
    disk = results.get("disk", {})
    single = results.get("cpu_single", {})
    print("=== SysOps Benchmark ===")
    print(f"Disk write       : {disk.get('write_mb_s', 'N/A')} MB/s")
    print(f"Disk read        : {disk.get('read_mb_s', 'N/A')} MB/s")
    print(f"CPU single-core  : {single.get('ops_per_sec', 'N/A'):,} ops/sec")
    if "cpu_multi" in results:
        multi = results["cpu_multi"]
        print(f"CPU multi-core   : {multi.get('ops_per_sec', 'N/A'):,} ops/sec ({multi.get('cores_used', '?')} cores)")


def main():
    parser = argparse.ArgumentParser(description="Run the SysOps CPU/disk benchmark.")
    parser.add_argument("--duration", type=float, default=0.33, help="Seconds per sub-test (default: 0.33)")
    parser.add_argument("--no-multi", action="store_true", help="Skip the multi-core test")
    args = parser.parse_args()
    if args.duration <= 0:
        parser.error("--duration must be greater than 0")

    started = time.perf_counter()
    print_results(run_benchmark(args.duration, include_multi_core=not args.no_multi))
    print(f"\nBenchmark time: {time.perf_counter() - started:.2f}s")


if __name__ == "__main__":
    main()
