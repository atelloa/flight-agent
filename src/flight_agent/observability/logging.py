from datetime import datetime
from time import perf_counter


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_node_start(state, node_name, message=None):
    start_time = perf_counter()

    print(f"\n[{now_ts()}] [RUN {state.run_id}] [NODE {node_name}] inicio")

    if message:
        print(f"  {message}")

    return start_time

def log_node_end(state, node_name, start_time):
    duration = perf_counter() - start_time
    print(
        f"[{now_ts()}] [RUN {state.run_id}] "
        f"[NODE {node_name}] fin | duration={duration:.2f}s"
    )