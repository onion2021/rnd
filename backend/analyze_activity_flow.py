import pandas as pd
import os

# 读取Excel文件
EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'AI Use Case_Rev01.xlsx')

def analyze_activity_flow():
    """分析Activity Flow表的结构和内容"""
    try:
        # 读取Activity Flow表
        df = pd.read_excel(EXCEL_FILE, sheet_name='Activity Flow')
        
        print("Activity Flow表的详细分析:")
        print("=" * 80)
        
        # 显示所有列及其索引
        print("\n列索引和列名:")
        for i, col in enumerate(df.columns):
            print(f"Column {i}: {col}")
        
        # 显示前10行完整数据
        print("\n前10行完整数据:")
        print(df.head(10))
        
        # 分析数据结构，尝试理解表格的实际组织方式
        print("\n尝试理解表格结构:")
        print("=" * 80)
        
        # 检查每列的内容，寻找有意义的数据
        for i, col in enumerate(df.columns):
            print(f"\n列 {i} ({col}) 的非空值:")
            non_empty_values = df[col].dropna().tolist()
            for j, val in enumerate(non_empty_values[:10]):  # 显示前10个非空值
                print(f"  {j+1}. {val}")
            if len(non_empty_values) > 10:
                print(f"  ... 还有 {len(non_empty_values) - 10} 个值")
        
    except Exception as e:
        print(f"分析Excel文件时出错: {str(e)}")

if __name__ == "__main__":
    analyze_activity_flow()
