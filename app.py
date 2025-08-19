import subprocess
import sys

def run_script(script_name):
    """运行指定的Python脚本，保持终端输出格式一致"""
    try:
        # 执行脚本，直接输出到终端
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"执行{script_name}时出错: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("===== 开始执行任务分解流程 =====")
    
    # 1. 运行主代理任务分解
    print("\n----- 执行主代理任务分解 -----")
    run_script("Ming_Agent.py")
    
    # 2. 运行细粒度任务分解
    print("\n----- 执行细粒度任务分解 -----")
    run_script("subagent2.py")
    
    # 3. 运行分解评估
    print("\n----- 执行任务分解评估 -----")
    run_script("evaluate_decomposition2.py")
    
    print("\n===== 所有任务分解流程执行完毕 =====")