import pandas as pd
import os
import json
import re
import requests
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

# 加载环境变量
load_dotenv()

api = Blueprint('api', __name__)

CSV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_project_data.csv')
STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'project_status.json')

# 数据库连接参数
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'rnd')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1233')

# LLM配置
LLM_BASE_URL = os.getenv('LLM_BASE_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')

# 数据库连接函数
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def read_data():
    """读取CSV数据"""
    if not os.path.exists(CSV_FILE):
        # 创建示例数据
        data = {
            'project name': ['Project A', 'Project B', 'Project C'],
            'package type': ['FC-BGA', 'WLCSP', 'QFN'],
            'purpose': ['Improve reliability', 'Reduce cost', 'Enhance performance'],
            'new technology': ['Cu pillar', 'Fan-out', 'Silver sinter'],
            'DOE factor': ['Temperature', 'Pressure', 'Time'],
            'DOE result': ['Pass', 'Pass', 'Fail'],
            'best pecipe setting': ['250C, 10s', '300C, 5s', '200C, 15s'],
            'engineer insight(lesson learned)': ['Need better thermal management', 'Optimize material selection', 'Improve process control']
        }
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
    else:
        df = pd.read_csv(CSV_FILE)
    
    # 确保状态文件存在
    if not os.path.exists(STATUS_FILE):
        status_map = {}
        for idx, row in df.iterrows():
            status_map[str(idx)] = 'Active'
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_map, f)
    
    return df

def load_status_map():
    """加载状态映射"""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_status_map(status_map):
    """保存状态映射"""
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_map, f)

def call_llm(prompt, context, language='zh'):
    """调用LLM进行分析"""
    if not all([LLM_BASE_URL, LLM_API_KEY, LLM_MODEL]):
        return "LLM配置不完整，无法进行深度分析"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        
        # 根据语言设置系统提示词
        if language == 'zh':
            system_prompt = """# Role
你是一位半导体封装领域的资深研发专家，拥有深厚的物理失效分析（FA）功底和丰富的先进封装（如 Fan-out, Chiplet, Substrate-based packaging）量产经验。

# Context
你正在查阅一份关于\"面板级封装工艺优化\"的项目历史记录数据库。该数据库以表格形式存储，记录了针对特定工艺问题（如起泡 Blister、除胶渣 Desmear）的实验迭代过程。

# Knowledge Base Column Definition (表的列定义说明)
在处理用户查询时，请参考以下列定义的逻辑：
1. **Main Activity / Background of Main activity**: 描述当前阶段的核心任务及其发生的背景。
2. **Order / DOE #**: 实验的先后顺序和编号，用于追踪工艺改进的迭代路径。
3. **Background of Sub activity**: 针对具体实验（Sub activity）的假设或前提条件。
4. **Sub activity**: 具体实施的动作、测试条件或验证的假设。
5. **Result / Learnings**: 实验的核心产出。包含具体的量测结果、观察到的现象以及通过数据得出的结论。
6. **Summary**: 对该阶段工作的定性总结，包含对设备性能、工艺窗口或成本效益的最终评价。

# Response Guidelines
1. **精准检索**：回答必须严格基于提供的历史数据中的实验数据，不得虚构或创造不存在的DOE编号、实验数据或结果。
2. **Engineer Insight (实战经验)**：在回答基础事实后，必须提供一个名为"Engineer Insight"的板块。
   - 分享实际生产中的避坑指南。
   - 解释现象背后的物理机制。
3. **理论推导**：如果提供的数据中无直接答案，请基于封装原理给出推论，并明确标注"[理论推导]"。
4. **简洁专业**：使用行业标准术语（如 POR, CCL, ABF, Via Cleaning）。

# Output Format
## [问题核心摘要]
- **实验结论**：直接回答问题。
- **关键参数/路径**：引用提供的历史数据中的 DOE 数据。
- **Engineer Insight**：提供深度行业见解。

## [本次回答采纳的Main Activity]
- 请列出本次回答中参考的所有Main Activity名称，每行一个。"""
            user_prompt = f"历史数据:\n{context}\n\n用户问题:\n{prompt}\n\n请严格按照上述Output Format输出，确保包含实验结论、关键参数/路径和Engineer Insight板块。回答必须基于提供的历史数据，不得虚构任何DOE编号或实验数据。"
        else:
            system_prompt = """# Role
You are a senior R&D expert in the field of semiconductor packaging, with deep physical failure analysis (FA) expertise and extensive mass production experience in advanced packaging (such as Fan-out, Chiplet, Substrate-based packaging).

# Context
You are reviewing a project history database on "panel-level packaging process optimization". This database is stored in tabular form and records the experimental iteration process for specific process issues (such as Blister, Desmear).

# Knowledge Base Column Definition
When processing user queries, please refer to the logic of the following column definitions:
1. **Main Activity / Background of Main activity**: Describes the core task of the current phase and its background.
2. **Order / DOE #**: The sequence and numbering of experiments, used to track the iterative path of process improvements.
3. **Background of Sub activity**: Hypotheses or prerequisites for specific experiments (Sub activity).
4. **Sub activity**: Specific actions implemented, test conditions, or hypotheses verified.
5. **Result / Learnings**: The core output of the experiment. Contains specific measurement results, observed phenomena, and conclusions drawn from the data.
6. **Summary**: A qualitative summary of the work in this phase, including final evaluations of equipment performance, process window, or cost-effectiveness.

# Response Guidelines
1. **Precise Retrieval**: Answers must be strictly based on the experimental data provided in the historical data, and you must not fabricate or create non-existent DOE numbers, experimental data, or results.
2. **Engineer Insight**: After answering the basic facts, you must provide a section called "Engineer Insight".
   - Share practical production pitfalls.
   - Explain the physical mechanisms behind phenomena.
3. **Theoretical Derivation**: If there is no direct answer in the provided data, please provide inferences based on packaging principles and clearly mark "[Theoretical Derivation]".
4. **Concise and Professional**: Use industry standard terminology (e.g., POR, CCL, ABF, Via Cleaning).

# Output Format
## [Core Question Summary]
- **Experimental Conclusion**: Directly answer the question.
- **Key Parameters/Path**: Reference DOE data from the provided historical data.
- **Engineer Insight**: Provide deep industry insights.

## [Main Activity References]
- Please list all Main Activity names referenced in this answer, one per line."""
            user_prompt = f"Historical data:\n{context}\n\nUser question:\n{prompt}\n\nPlease output according to the above Output Format, ensuring to include the Experimental Conclusion, Key Parameters/Path, and Engineer Insight sections. Your answer must be based strictly on the provided historical data, and you must not fabricate any DOE numbers or experimental data."
        
        data = {
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
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

def is_general_chat(query):
    """判断是否为普通聊天对话"""
    # 问候语
    greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
    for greeting in greetings:
        if greeting in query.lower():
            return True
    
    # 闲聊话题
    chat_topics = ['how are you', 'how are you doing', 'what are you doing', 'nice to meet you', 'hows it going']
    for topic in chat_topics:
        if topic in query.lower():
            return True
    
    # 非技术问题
    non_technical = ['thanks', 'thank you', 'bye', 'goodbye', 'see you', 'see you later']
    for phrase in non_technical:
        if phrase in query.lower():
            return True
    
    return False

def get_general_response(query, language='zh'):
    """获取普通聊天响应"""
    if language == 'zh':
        responses = [
            '你好！我是你的半导体封装专家助手。我可以帮助你解决封装相关的技术问题，包括封装类型、材料、失效模式和DOE实验设计等。请问有什么可以帮到你的？',
            '你好！我是半导体封装领域的AI助手，专注于解决封装工艺优化、材料选择和可靠性问题。有什么我可以协助你的吗？',
            '嗨！我是你的半导体封装技术顾问。我可以提供关于先进封装技术、工艺参数优化和失效分析的专业建议。请问你有什么问题需要解答？'
        ]
    else:
        responses = [
            'Hello! I am your semiconductor packaging expert assistant. I can help you with packaging-related technical issues, including packaging types, materials, failure modes, and DOE experimental design. How can I assist you today?',
            'Hello! I am an AI assistant in the field of semiconductor packaging, focused on solving packaging process optimization, material selection, and reliability issues. Is there anything I can help you with?',
            'Hi! I am your semiconductor packaging technical advisor. I can provide professional advice on advanced packaging technologies, process parameter optimization, and failure analysis. What questions do you have?'
        ]
    
    import random
    return random.choice(responses)

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
    keywords = ['warpage', 'crack', 'delamination', 'void', 'reliability', 'thermal', 'bonding', 'flow', 'desmear', 'blister', 'plasma']
    for keyword in keywords:
        if keyword in query.lower():
            analysis['keywords'].append(keyword)
    
    # 提取参数
    temp_pattern = r'(\d+)\s*C'
    temp_matches = re.findall(temp_pattern, query)
    if temp_matches:
        analysis['parameters']['temperature'] = temp_matches
    
    return analysis

def get_all_activities_for_query():
    """从数据库获取所有活动数据用于AI查询"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有主要活动及其子活动
        cursor.execute("""
            SELECT 
                m.id as main_id,
                m.name as main_name,
                m.background as main_background,
                m.summary as main_summary,
                s.id as sub_id,
                s.order_num,
                s.doe_number,
                s.background as sub_background,
                s.activity_name,
                s.result
            FROM main_activities m
            LEFT JOIN sub_activities s ON m.id = s.main_activity_id
            ORDER BY m.id, s.order_num
        """)
        
        rows = cursor.fetchall()
        
        activities_dict = {}
        for row in rows:
            main_id = row[0]  # 索引0: main_id
            if main_id not in activities_dict:
                activities_dict[main_id] = {
                    'id': main_id,
                    'name': row[1],  # 索引1: main_name
                    'background': row[2],  # 索引2: main_background
                    'summary': row[3],  # 索引3: main_summary
                    'sub_activities': []
                }
            
            if row[4]:  # 索引4: sub_id
                activities_dict[main_id]['sub_activities'].append({
                    'id': row[4],  # 索引4: sub_id
                    'order_num': row[5],  # 索引5: order_num
                    'doe_number': row[6],  # 索引6: doe_number
                    'background': row[7],  # 索引7: sub_background
                    'activity_name': row[8],  # 索引8: activity_name
                    'result': row[9]  # 索引9: result
                })
        
        cursor.close()
        conn.close()
        
        return list(activities_dict.values())
    except Exception as e:
        print(f"获取活动数据出错: {str(e)}")
        return []

def find_similar_cases(analysis):
    """从Activity List查找相似案例"""
    activities = get_all_activities_for_query()
    similar_cases = []
    
    for activity in activities:
        score = 0
        matched_sub = None
        
        # 在主要活动名称和背景中搜索
        activity_text = f"{activity['name']} {activity['background']} {activity['summary']}".lower()
        
        # 在子活动中搜索
        for sub in activity['sub_activities']:
            sub_text = f"{sub['activity_name']} {sub['background']} {sub['result']}".lower()
            
            # 关键词匹配
            for keyword in analysis['keywords']:
                if keyword in activity_text or keyword in sub_text:
                    score += 2
                    if not matched_sub or score > matched_sub['score']:
                        matched_sub = {'score': score, 'activity': activity, 'sub_activity': sub}
            
            # 技术匹配
            if analysis['technology']:
                if analysis['technology'].lower() in sub_text:
                    score += 3
                    if not matched_sub or score > matched_sub['score']:
                        matched_sub = {'score': score, 'activity': activity, 'sub_activity': sub}
        
        # 在主要活动名称中搜索
        if analysis['package_type']:
            if analysis['package_type'].lower() in activity['name'].lower():
                score += 3
                if not matched_sub or score > matched_sub['score']:
                    matched_sub = {'score': score, 'activity': activity, 'sub_activity': None}
        
        if score >= 2:
            similar_cases.append({
                'score': score,
                'activity': activity,
                'sub_activity': matched_sub['sub_activity'] if matched_sub else None
            })
    
    # 按分数排序
    similar_cases.sort(key=lambda x: x['score'], reverse=True)
    return similar_cases[:3]  # 只返回前3个最相似的案例

def generate_ai_response(analysis, similar_cases, language='zh'):
    """生成AI响应"""
    response = {
        'similar_cases': [],
        'recommended_params': [],
        'engineer_insights': [],
        'risk_alert': [],
        'theoretical_suggestions': []
    }
    
    # 处理相似案例
    for case in similar_cases:
        activity = case['activity']
        sub = case['sub_activity']
        
        # 相似案例
        if sub:
            response['similar_cases'].append({
                'project_name': activity['name'],
                'package_type': 'Panel-level packaging',
                'doe_number': sub['doe_number'],
                'activity_name': sub['activity_name'],
                'result': sub['result']
            })
        else:
            response['similar_cases'].append({
                'project_name': activity['name'],
                'package_type': 'Panel-level packaging',
                'doe_number': None,
                'activity_name': activity['name'],
                'result': activity['summary']
            })
        
        # 推荐参数
        if sub and 'CF4' in sub['activity_name']:
            if language == 'zh':
                response['recommended_params'].append({
                    'project': activity['name'],
                    'params': f"DOE {sub['doe_number']}: {sub['activity_name']}"
                })
            else:
                response['recommended_params'].append({
                    'project': activity['name'],
                    'params': f"DOE {sub['doe_number']}: {sub['activity_name']}"
                })
        
        # 工程师洞见
        if sub and sub['result']:
            response['engineer_insights'].append({
                'activity': activity['name'],
                'sub_activity': sub['activity_name'],
                'insight': sub['result']
            })
        
        # 潜在风险
        if sub and sub['result']:
            if language == 'zh':
                if 'blister' in sub['result'].lower():
                    response['risk_alert'].append({
                        'type': 'Blister',
                        'description': '气泡可能影响封装可靠性'
                    })
                if 'crack' in sub['result'].lower():
                    response['risk_alert'].append({
                        'type': 'Crack',
                        'description': '开裂可能导致器件失效'
                    })
                if 'delamination' in sub['result'].lower():
                    response['risk_alert'].append({
                        'type': 'Delamination',
                        'description': '分层可能影响热性能'
                    })
            else:
                if 'blister' in sub['result'].lower():
                    response['risk_alert'].append({
                        'type': 'Blister',
                        'description': 'Blister may affect package reliability'
                    })
                if 'crack' in sub['result'].lower():
                    response['risk_alert'].append({
                        'type': 'Crack',
                        'description': 'Cracking may lead to device failure'
                    })
                if 'delamination' in sub['result'].lower():
                    response['risk_alert'].append({
                        'type': 'Delamination',
                        'description': 'Delamination may affect thermal performance'
                    })
    
    # 理论建议（当无相似案例时）
    if not similar_cases:
        if language == 'zh':
            response['theoretical_suggestions'].append({
                'note': '[本建议基于活动数据中的知识进行推断]',
                'suggestions': [
                    '请参考Activity List中的相关活动',
                    '查看类似DOE实验的结果',
                    '咨询相关领域的专家'
                ]
            })
        else:
            response['theoretical_suggestions'].append({
                'note': '[This suggestion is based on knowledge from Activity List]',
                'suggestions': [
                    'Please refer to relevant activities in Activity List',
                    'Check results from similar DOE experiments',
                    'Consult with domain experts'
                ]
            })
    
    return response

def extract_referenced_activities(llm_analysis):
    """从LLM分析结果中提取本次回答采纳的Main Activity"""
    referenced_activities = []
    if llm_analysis:
        # 匹配中文格式（支持不同换行符格式和空格）
        import re
        zhMatch = re.search(r'##\s*\[本次回答采纳的Main Activity\]\s*[\r\n]+\s*-\s*(.+?)(?=\s*[\r\n]+##|$)', llm_analysis, re.DOTALL)
        if zhMatch:
            referenced_activities = zhMatch.group(1).strip().split(re.compile(r'\s*[\r\n]+\s*-\s*'))
            referenced_activities = [item for item in referenced_activities if item]
        # 匹配英文格式（支持不同换行符格式和空格）
        enMatch = re.search(r'##\s*\[Main Activity References\]\s*[\r\n]+\s*-\s*(.+?)(?=\s*[\r\n]+##|$)', llm_analysis, re.DOTALL)
        if enMatch:
            referenced_activities = enMatch.group(1).strip().split(re.compile(r'\s*[\r\n]+\s*-\s*'))
            referenced_activities = [item for item in referenced_activities if item]
        # 如果没有匹配到，尝试直接从文本中提取活动名称
        if not referenced_activities:
            activityRegex = re.compile(r'-\s*(Post ELP Blister Activity|Dry Desmear Outsourcing|Dry \+ Wet Desmear pathfinding)')
            matches = activityRegex.findall(llm_analysis)
            referenced_activities = matches
    return referenced_activities

@api.route('/ai/query', methods=['POST'])
def ai_query():
    """AI助手查询接口"""
    data = request.json
    query = data.get('query', '')
    language = data.get('language', 'zh')
    
    # 获取所有活动作为相似案例
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM main_activities ORDER BY id")
    activities = cursor.fetchall()
    cursor.close()
    conn.close()
    
    similar_cases = []
    for activity in activities:
        similar_cases.append({
            'project_name': activity[1],
            'package_type': 'Panel-level packaging'
        })
    
    # 准备LLM上下文 - 包含所有activity flow表格的内容
    context = "所有Activity Flow表格数据：\n\n"
    all_activities = get_all_activities_for_query()
    for activity in all_activities:
        context += f"=== 主要活动: {activity['name']} ===\n"
        context += f"背景: {activity['background']}\n"
        context += f"总结: {activity['summary']}\n"
        
        if activity['sub_activities']:
            context += "\n子活动:\n"
            for sub in activity['sub_activities']:
                context += f"- 序号: {sub['order_num']}, DOE #: {sub['doe_number']}\n"
                context += f"  背景: {sub['background']}\n"
                context += f"  活动名称: {sub['activity_name']}\n"
                context += f"  结果: {sub['result']}\n"
        context += "\n"
    
    # 调用LLM进行深度分析
    llm_response = call_llm(query, context, language)
    
    # 提取本次回答采纳的Main Activity
    referenced_activities = extract_referenced_activities(llm_response)
    
    # 构建响应
    response = {
        'rule_based': {
            'similar_cases': similar_cases,
            'recommended_params': [],
            'engineer_insights': [],
            'risk_alert': [],
            'theoretical_suggestions': []
        },
        'llm_analysis': llm_response,
        'similar_cases': [],
        'referenced_activities': referenced_activities
    }
    
    return jsonify(response)

# 活动流相关API

@api.route('/activities', methods=['GET'])
def get_activities():
    """获取所有主要活动"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, background, summary, created_at FROM main_activities ORDER BY id")
        activities = cursor.fetchall()
        
        result = []
        for activity in activities:
            result.append({
                'id': activity[0],  # 索引0: id
                'name': activity[1],  # 索引1: name
                'background': activity[2],  # 索引2: background
                'summary': activity[3],  # 索引3: summary
                'created_at': activity[4]  # 索引4: created_at
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/activities/<int:id>', methods=['GET'])
def get_activity(id):
    """获取单个主要活动及其子活动"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取主要活动
        cursor.execute("SELECT id, name, background, summary, created_at FROM main_activities WHERE id = %s", (id,))
        activity = cursor.fetchone()
        
        if not activity:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Activity not found'}), 404
        
        # 获取子活动
        cursor.execute("SELECT id, order_num, doe_number, background, activity_name, result, created_at FROM sub_activities WHERE main_activity_id = %s ORDER BY order_num", (id,))
        sub_activities = cursor.fetchall()
        
        sub_result = []
        for sub in sub_activities:
            sub_result.append({
                'id': sub[0],  # 索引0: id
                'order_num': sub[1],  # 索引1: order_num
                'doe_number': sub[2],  # 索引2: doe_number
                'background': sub[3],  # 索引3: background
                'activity_name': sub[4],  # 索引4: activity_name
                'result': sub[5],  # 索引5: result
                'created_at': sub[6]  # 索引6: created_at
            })
        
        result = {
            'id': activity[0],  # 索引0: id
            'name': activity[1],  # 索引1: name
            'background': activity[2],  # 索引2: background
            'summary': activity[3],  # 索引3: summary
            'created_at': activity[4],  # 索引4: created_at
            'sub_activities': sub_result
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/activities', methods=['POST'])
def create_activity():
    """创建新的主要活动"""
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO main_activities (name, background, summary) VALUES (%s, %s, %s) RETURNING id""",
            (data.get('name'), data.get('background'), data.get('summary'))
        )
        activity_id = cursor.fetchone()[0]
        conn.commit()
        
        # 获取创建的活动
        cursor.execute("SELECT id, name, background, summary, created_at FROM main_activities WHERE id = %s", (activity_id,))
        activity = cursor.fetchone()
        
        result = {
            'id': activity[0],
            'name': activity[1],
            'background': activity[2],
            'summary': activity[3],
            'created_at': activity[4]
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/activities/<int:activity_id>/subactivities', methods=['POST'])
def create_subactivity(activity_id):
    """为主要活动创建新的子活动"""
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查主要活动是否存在
        cursor.execute("SELECT id FROM main_activities WHERE id = %s", (activity_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Main activity not found'}), 404
        
        cursor.execute(
            """INSERT INTO sub_activities (main_activity_id, order_num, doe_number, background, activity_name, result) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (activity_id, data.get('order_num'), data.get('doe_number'), data.get('background'), data.get('activity_name'), data.get('result'))
        )
        subactivity_id = cursor.fetchone()[0]
        conn.commit()
        
        # 获取创建的子活动
        cursor.execute("SELECT id, main_activity_id, order_num, doe_number, background, activity_name, result, created_at FROM sub_activities WHERE id = %s", (subactivity_id,))
        subactivity = cursor.fetchone()
        
        result = {
            'id': subactivity[0],
            'main_activity_id': subactivity[1],
            'order_num': subactivity[2],
            'doe_number': subactivity[3],
            'background': subactivity[4],
            'activity_name': subactivity[5],
            'result': subactivity[6],
            'created_at': subactivity[7]
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/download/activity/<int:activity_id>', methods=['GET'])
def download_activity_excel(activity_id):
    """下载活动的Excel文件"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取主要活动
        cursor.execute("SELECT id, name, background, summary FROM main_activities WHERE id = %s", (activity_id,))
        activity = cursor.fetchone()
        
        if not activity:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Activity not found'}), 404
        
        cursor.close()
        conn.close()
        
        # 从split_sheets目录中找到对应的Excel文件
        import os
        from flask import send_file
        
        activity_name = activity[1]
        # 构建文件路径
        split_sheets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'split_sheets')
        file_name = f"{activity_name}.xlsx"
        file_path = os.path.join(split_sheets_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': 'Excel file not found in split_sheets directory'}), 404
        
        # 直接发送文件
        return send_file(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/download/all-activities', methods=['GET'])
def download_all_activities_excel():
    """下载所有活动的Excel文件"""
    try:
        import os
        import zipfile
        import io
        from flask import send_file
        
        # 从split_sheets目录中获取所有Excel文件
        split_sheets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'split_sheets')
        
        # 检查split_sheets目录是否存在
        if not os.path.exists(split_sheets_dir):
            return jsonify({'error': 'split_sheets directory not found'}), 404
        
        # 获取目录中的所有Excel文件
        excel_files = [f for f in os.listdir(split_sheets_dir) if f.endswith('.xlsx')]
        
        if not excel_files:
            return jsonify({'error': 'No Excel files found in split_sheets directory'}), 404
        
        # 创建一个zip文件
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as zipf:
            for file_name in excel_files:
                file_path = os.path.join(split_sheets_dir, file_name)
                zipf.write(file_path, file_name)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/zip',
            as_attachment=True,
            download_name="all_activities.zip"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
