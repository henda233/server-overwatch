"""诊断 collector 模块 - 按用户区分CPU/内存/GPU使用率"""

from monitor.collector import Collector


def debug_collector():
    c = Collector()

    # 1. 检查 get_process_info 返回值
    pid_to_user, pid_info = c.get_process_info()

    print("=== PID 2889417 (lgl的GPU进程) ===")
    print("pid_to_user[2889417]:", pid_to_user.get(2889417))
    print("pid_info[2889417]:", pid_info.get(2889417))

    # 2. 检查所有 lgl 的进程
    print("\n=== 所有 lgl 的进程 ===")
    for pid, user in pid_to_user.items():
        if user == "lgl":
            info = pid_info.get(pid, {})
            print(f"PID {pid}: CPU={info.get('cpu_percent', 0)}, MEM={info.get('mem_percent', 0)}")

    # 3. 检查所有 cxy 的进程
    print("\n=== 所有 cxy 的进程 ===")
    for pid, user in pid_to_user.items():
        if user == "cxy":
            info = pid_info.get(pid, {})
            print(f"PID {pid}: CPU={info.get('cpu_percent', 0)}, MEM={info.get('mem_percent', 0)}")

    # 4. 检查 who 返回的用户
    print("\n=== 在线用户 ===")
    users = c.collect_users()
    print(users)

    # 5. 完整采集结果
    print("\n=== 完整采集结果 ===")
    result = c.collect()
    for user, data in result.items():
        print(f"\n用户: {user}")
        print(f"  GPU使用率: {data['gpu_percent']}%")
        print(f"  显存使用: {data['gpu_memory_mb']} MB / {data['gpu_memory_total_mb']} MB")
        print(f"  CPU使用率: {data['cpu_percent']}%")
        print(f"  内存使用率: {data['memory_percent']}%")


if __name__ == "__main__":
    debug_collector()
