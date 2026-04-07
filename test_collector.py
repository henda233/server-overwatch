"""测试 collector 模块 - 按用户区分CPU/内存/GPU使用率"""

from monitor.collector import Collector


def test_collect():
    c = Collector()
    result = c.collect()

    print("=== 测试结果 ===")
    for user, data in result.items():
        print(f"\n用户: {user}")
        print(f"  GPU使用率: {data['gpu_percent']}%")
        print(f"  显存使用: {data['gpu_memory_mb']} MB / {data['gpu_memory_total_mb']} MB")
        print(f"  CPU使用率: {data['cpu_percent']}%")
        print(f"  内存使用率: {data['memory_percent']}%")

    # 验证显存总和
    if result:
        total_mem = sum(d["gpu_memory_mb"] for d in result.values())
        global_mem = list(result.values())[0]["gpu_memory_total_mb"]
        print(f"\n=== 验证 ===")
        print(f"用户显存总和: {total_mem} MB")
        print(f"全局显存使用: {global_mem} MB")

        # 验证GPU使用率总和
        total_gpu = sum(d["gpu_percent"] for d in result.values())
        print(f"用户GPU使用率总和: {total_gpu}%")


if __name__ == "__main__":
    test_collect()
