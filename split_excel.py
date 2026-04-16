import pandas as pd
import os

# 读取Excel文件
file_path = 'AI Use Case_Rev01.xlsx'
excel_file = pd.ExcelFile(file_path)

# 创建输出目录
output_dir = 'split_sheets'
os.makedirs(output_dir, exist_ok=True)

# 遍历每个工作表并保存为单独的文件
for sheet_name in excel_file.sheet_names:
    # 读取工作表数据
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 生成输出文件名
    output_file = os.path.join(output_dir, f'{sheet_name}.xlsx')
    
    # 保存为单独的Excel文件
    df.to_excel(output_file, index=False)
    print(f'已保存工作表 "{sheet_name}" 到 {output_file}')

print('所有工作表已成功保存为单独文件！')