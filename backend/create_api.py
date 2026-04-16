# Script to create api.py

api_content = '''from flask import Blueprint, request, jsonify
import pandas as pd
import os
import json
import re
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

api = Blueprint('api', __name__)

CSV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_project_data.csv')
STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'project_status.json')

# LLM配置
LLM_BASE_URL = os.getenv('LLM_BASE_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')

def load_status_map():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_status_map(status_map):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_map, f, ensure_ascii=False, indent=2)

def read_data():
    df = pd.read_csv(CSV_FILE)
    status_map = load_status_map()
    df['project status'] = df.index.map(lambda x: status_map.get(str(x), 'Active'))
    return df

def save_data(df):
    status_map = {}
    for idx, row in df.iterrows():
        status_map[str(idx)] = row.get('project status', 'Active')
    save_status_map(status_map)

def call_llm(prompt, context):
    """调用LLM进行分析"""
    if not all([LLM_BASE_URL, LLM_API_KEY, LLM_MODEL]):
        return "LLM配置不完整，无法进行深度分析"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        
        data = {
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位在半导体封装领域深耕20年的资深研发专家，精通各类主流封装技术、材料特性、失效模式及DOE实验设计。请基于提供的历史数据和用户问题，提供专业、可落地的技术反馈。"
                },
                {
                    "role": "user",
                    "content": f"历史数据:\n{context}\n\n用户问题:\n{prompt}\n\n请按照以下结构输出：\n1. 相似历史案例\n2. 推荐工艺参数\n3. 核心实战经验\n4. 潜在风险及失效预警\n5. 理论建议（如需）"
                }
            ],
            "temperature": 0.3
        }
        
        response = requests.post(f"{LLM_BASE_URL}/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        return f"LLM调用失败: {str(e)}"

@api.route('/projects', methods=['GET'])
def get_projects():
    df = read_data()
    return jsonify(df.to_dict('records'))

@api.route('/projects/<int:index>', methods=['GET'])
def get_project(index):
    df = read_data()
    if 0 <= index < len(df):
        return jsonify(df.iloc[index].to_dict())
    return jsonify({'error': 'Project not found'}), 404

@api.route('/projects', methods=['POST'])
def create_project():
    data = request.json
    df = pd.read_csv(CSV_FILE)
    
    new_row = {
        'project name': data.get('project name'),
        'package type': data.get('package type'),
        'purpose': data.get('purpose'),
        'new technology': data.get('new technology'),
        'DOE factor': data.get('DOE factor'),
        'DOE result': data.get('DOE result'),
        'best pecipe setting': data.get('best pecipe setting'),
        'engineer insight(lesson learned)': data.get('engineer insight(lesson learned)')
    }
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    
    status_map = load_status_map()
    status_map[str(len(df) - 1)] = 'Active'
    save_status_map(status_map)
    
    result = new_row.copy()
    result['project status'] = 'Active'
    
    return jsonify(result), 201

@api.route('/projects/<int:index>/status', methods=['PUT'])
def update_status(index):
    data = request.json
    df = read_data()
    
    if 0 <= index < len(df):
        status_map = load_status_map()
        status_map[str(index)] = data.get('status', 'Active')
        save_status_map(status_map)
        return jsonify({'status': 'success', 'message': 'Status updated'})
    return jsonify({'error': 'Project not found'}), 404

# AI助手相关API

@api.route('/ai/query', methods=['POST'])
def ai_query():
    """AI助手查询接口"""
    data = request.json
    query = data.get('query', '')
    
    # 解析查询内容
    analysis = analyze_query(query)
    
    # 检索相似案例
    similar_cases = find_similar_cases(analysis)
    
    # 生成规则匹配响应
    rule_based_response = generate_ai_response(analysis, similar_cases)
    
    # 准备LLM上下文
    context = ""
    for case in similar_cases:
        project = case['project']
        context += f"项目: {project['project name']}\n"
        context += f"封装类型: {project['package type']}\n"
        context += f"技术: {project['new technology']}\n"
        context += f"目的: {project['purpose']}\n"
        context += f"最优参数: {project['best pecipe setting']}\n"
        context += f"工程师洞见: {project['engineer insight(lesson learned)']}\n\n"
    
    # 调用LLM进行深度分析
    llm_response = call_llm(query, context)
    
    # 组合响应
    response = {
        'rule_based': rule_based_response,
        'llm_analysis': llm_response,
        'similar_cases': [case['project'] for case in similar_cases]
    }
    
    return jsonify(response)

def analyze_query(query):
    """分析用户查询"""
    analysis = {
        'package_type': None,
        'technology': None,
        'keywords': [],
        'parameters': {}
    }
    
    # 提取封装类型
    package_types = ['FC-BGA', 'FC-CSP', 'QFN', 'WLCSP', '2.5D SiP', 'FO-WLP', 'BGA', 'Automotive QFN', '3D Stack']
    for pt in package_types:
        if pt.lower() in query.lower():
            analysis['package_type'] = pt
            break
    
    # 提取技术关键词
    technologies = ['low cte', 'underfill', 'silver sinter', 'cu pillar', 'thermo-compression', 'polyimide', 'vacuum reflow', 'plasma']
    for tech in technologies:
        if tech.lower() in query.lower():
            analysis['technology'] = tech
            break
    
    # 提取关键词
    keywords = ['warpage', 'crack', 'delamination', 'void', 'reliability', 'thermal', 'bonding', 'flow']
    for keyword in keywords:
        if keyword in query.lower():
            analysis['keywords'].append(keyword)
    
    # 提取参数
    temp_pattern = r'(\\d+)\\s*C'
    temp_matches = re.findall(temp_pattern, query)
    if temp_matches:
        analysis['parameters']['temperature'] = temp_matches
    
    return analysis

def find_similar_cases(analysis):
    """查找相似案例"""
    df = read_data()
    similar_cases = []
    
    for idx, row in df.iterrows():
        score = 0
        
        # 封装类型匹配
        if analysis['package_type'] and analysis['package_type'] in row['package type']