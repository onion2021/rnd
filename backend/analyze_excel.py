import pandas as pd
import os

# 读取Excel文件
EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'AI Use Case_Rev01.xlsx')

def analyze_activity_flow():
    """分析activity flow表的结构和内容"""
    try:
        # 读取Excel文件中的所有工作表
        xl = pd.ExcelFile(EXCEL_FILE)
        print("Excel文件中的工作表:")
        for sheet_name in xl.sheet_names:
            print(f"- {sheet_name}")
        
        # 读取Activity Flow表
        if 'Activity Flow' in xl.sheet_names:
            df = pd.read_excel(EXCEL_FILE, sheet_name='Activity Flow')
            print("\nActivity Flow表的列名:")
            for col in df.columns:
                print(f"- {col}")
            
            print("\nActivity Flow表的前5行数据:")
            print(df.head())
            
            print("\nActivity Flow表的基本信息:")
            print(f"总行数: {len(df)}")
            print(f"总列数: {len(df.columns)}")
            
            # 分析每列的数据类型和唯一值
            print("\n各列的数据分析:")
            for col in df.columns:
                print(f"\n列名: {col}")
                print(f"数据类型: {df[col].dtype}")
                print(f"非空值数量: {df[col].count()}")
                print(f"唯一值数量: {df[col].nunique()}")
                if df[col].nunique() < 20:
                    print(f"唯一值: {df[col].unique()}")
        else:
            print("\n未找到'activity flow'工作表")
            
    except Exception as e:
        print(f"分析Excel文件时出错: {str(e)}")

if __name__ == "__main__":
    analyze_activity_flow()
