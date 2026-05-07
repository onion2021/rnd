import pandas as pd
import os
import json
import re
import time
import threading
import uuid
import requests
import sqlite3
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, Response, stream_with_context

# 加载环境变量
load_dotenv()

api = Blueprint('api', __name__)

CSV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_project_data.csv')
STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'project_status.json')
EXPERIMENT_ACTIVITY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'AI_Use_Case_DOE_Experiment_Key_RAG_Table_No_Source_Cleaned_Columns.xlsx',
)
EXPERIMENT_ACTIVITY_SHEET = 'Experiment_RAG_Table'

# SQLite数据库文件路径
DB_FILE = os.path.join(os.path.dirname(__file__), 'pdm.db')
PROJECT_CARD_TABLE = 'project_cards'
PROJECT_DOE_TABLE = 'project_doe_entries'
PROJECT_META_TABLE = 'project_activity_meta'
PROJECT_META_MTIME_KEY = 'experiment_activity_mtime'

# 轻量缓存：用于“回答后再拉取references”，避免再次调用LLM
_AI_QUERY_CACHE = {}
_AI_QUERY_CACHE_LOCK = threading.Lock()
_AI_QUERY_CACHE_TTL_SECONDS = 60 * 30  # 30分钟
_PROJECT_ACTIVITY_CACHE = {'mtime': None, 'projects': None}
_PROJECT_ACTIVITY_CACHE_LOCK = threading.Lock()

# LLM配置
LLM_BASE_URL = os.getenv('LLM_BASE_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')

# 数据库连接函数
def get_db_connection():
    # check_same_thread=False 允许 Flask 在多线程环境下复用连接创建
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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


def _cell_to_text(value):
    """Normalize Excel cell values to strings while keeping line breaks."""
    if value is None or pd.isna(value):
        return ''

    if isinstance(value, float) and value.is_integer():
        value = int(value)

    return str(value).replace('\r\n', '\n').replace('\r', '\n').strip()


def _inline_text(value):
    """Collapse line breaks/extra whitespace for identifiers and short labels."""
    return re.sub(r'\s+', ' ', _cell_to_text(value)).strip()


def _slugify(value, fallback='item'):
    slug = re.sub(r'[^a-z0-9]+', '-', _inline_text(value).lower()).strip('-')
    return slug or fallback


def _project_display_name(value):
    display_name = _inline_text(value)
    if display_name.lower().endswith(' activity'):
        display_name = display_name[:-9].rstrip()
    return display_name


def _is_result_like_factor(factor_name):
    normalized = _inline_text(factor_name).lower()
    result_prefixes = (
        'result ',
        'result (',
        'evaluation result',
        'coupon level result',
        'full panel result',
    )
    return normalized.startswith(result_prefixes)


def _build_factor_groups(record):
    fixed_factors = []
    changed_factors = []
    evaluation_fields = []

    x_indexes = []
    for key in record:
        match = re.fullmatch(r'X(\d+)', key)
        if match:
            x_indexes.append(int(match.group(1)))

    for index in sorted(set(x_indexes)):
        name = record.get(f'X{index}')
        condition = record.get(f'X{index} condition')

        if not name or not condition:
            continue

        factor = {
            'key': f'X{index}',
            'name': name,
            'condition': condition,
        }

        if _is_result_like_factor(name):
            evaluation_fields.append(factor)
        elif condition.lower().startswith('all listed legs'):
            fixed_factors.append(factor)
        else:
            changed_factors.append(factor)

    return fixed_factors, changed_factors, evaluation_fields


def _build_doe_detail(record, project_id):
    field_order = [
        ('Sub activity', 'DOE'),
        ('Project Owner', 'Project Owner'),
        ('Test purpose', 'Test purpose'),
        ('Background of Sub activity', 'Background'),
        ('Tool', 'Tool'),
        ('Location', 'Location'),
        ('DOE Details', 'DOE Details'),
        ('DOE Legs Listed', 'DOE Legs Listed'),
        ('DOE Legs', 'DOE Legs'),
        ('Factor Count', 'Factor Count'),
        ('Result', 'Result'),
        ('Result / Learnings', 'Result / Learnings'),
        ('Overall Findings', 'Overall Findings'),
        ('Summary', 'Summary'),
        ('Evaluation Result', 'Evaluation Result'),
        ('Overall summary / Learnings', 'Overall summary / Learnings'),
        ('Evaluation Result - Evaluation Result \\ Learnings', 'Evaluation Result - Evaluation Result / Learnings'),
    ]

    detail_fields = []
    used_sources = set()

    for source_key, label in field_order:
        value = record.get(source_key)
        if value:
            detail_fields.append({
                'key': source_key,
                'label': label,
                'value': value,
            })
            used_sources.add(source_key)

    fixed_factors, changed_factors, evaluation_fields = _build_factor_groups(record)

    additional_fields = []
    ignored_sources = {
        'Experiment Key',
        'Project Name',
        'DOE #',
        'Main Activity',
        'Background of Main activity',
        'Order',
        'Activity Flow DOE #',
    }

    for key, value in record.items():
        if not value or key in used_sources or key in ignored_sources:
            continue
        if re.fullmatch(r'X\d+( condition)?', key):
            continue
        additional_fields.append({
            'key': key,
            'label': key,
            'value': value,
        })

    doe_number = record.get('DOE #') or record.get('Activity Flow DOE #')

    return {
        'id': f"{project_id}-doe-{_slugify(doe_number or record.get('Experiment Key'), 'doe')}",
        'doe_number': doe_number,
        'activity_flow_doe_number': record.get('Activity Flow DOE #'),
        'order': record.get('Order'),
        'title': record.get('Sub activity') or record.get('DOE Details') or record.get('Experiment Key'),
        'detail_fields': detail_fields,
        'fixed_factors': fixed_factors,
        'changed_factors': changed_factors,
        'evaluation_fields': evaluation_fields,
        'additional_fields': additional_fields,
    }


def load_project_activities():
    """Read the cleaned DOE workbook and group rows into project cards."""
    if not os.path.exists(EXPERIMENT_ACTIVITY_FILE):
        raise FileNotFoundError(f'Experiment workbook not found: {EXPERIMENT_ACTIVITY_FILE}')

    file_mtime = os.path.getmtime(EXPERIMENT_ACTIVITY_FILE)

    with _PROJECT_ACTIVITY_CACHE_LOCK:
        if (
            _PROJECT_ACTIVITY_CACHE['projects'] is not None and
            _PROJECT_ACTIVITY_CACHE['mtime'] == file_mtime
        ):
            return _PROJECT_ACTIVITY_CACHE['projects']

    df = pd.read_excel(EXPERIMENT_ACTIVITY_FILE, sheet_name=EXPERIMENT_ACTIVITY_SHEET)

    projects = []
    project_map = {}
    used_ids = set()

    for row in df.to_dict(orient='records'):
        record = {}
        for key, value in row.items():
            text_key = _cell_to_text(key)
            text_value = _cell_to_text(value)
            if text_key and text_value:
                record[text_key] = text_value

        if not record:
            continue

        project_name = record.get('Project Name') or record.get('Main Activity') or record.get('Experiment Key')
        project_key = _inline_text(project_name)

        if project_key not in project_map:
            project_id = _slugify(project_key, 'project')
            dedupe_index = 2
            while project_id in used_ids:
                project_id = f"{_slugify(project_key, 'project')}-{dedupe_index}"
                dedupe_index += 1
            used_ids.add(project_id)

            project = {
                'id': project_id,
                'name': project_key,
                'display_name': _project_display_name(project_name),
                'background': record.get('Background of Main activity', ''),
                'summary': record.get('Summary', '') or record.get('Overall summary / Learnings', ''),
                'doe_numbers': [],
                'does': [],
            }
            project_map[project_key] = project
            projects.append(project)

        project = project_map[project_key]
        doe_detail = _build_doe_detail(record, project['id'])
        project['doe_numbers'].append(doe_detail['doe_number'])
        project['does'].append(doe_detail)

    with _PROJECT_ACTIVITY_CACHE_LOCK:
        _PROJECT_ACTIVITY_CACHE['mtime'] = file_mtime
        _PROJECT_ACTIVITY_CACHE['projects'] = projects

    return projects


def _json_dumps(value):
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def ensure_project_activity_tables(conn):
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {PROJECT_CARD_TABLE} (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT,
            background TEXT,
            summary TEXT,
            doe_numbers_json TEXT,
            sort_index INTEGER NOT NULL
        )
    """)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {PROJECT_DOE_TABLE} (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            doe_number TEXT,
            activity_flow_doe_number TEXT,
            order_label TEXT,
            title TEXT,
            detail_fields_json TEXT,
            fixed_factors_json TEXT,
            changed_factors_json TEXT,
            evaluation_fields_json TEXT,
            additional_fields_json TEXT,
            searchable_text TEXT,
            sort_index INTEGER NOT NULL,
            FOREIGN KEY (project_id) REFERENCES {PROJECT_CARD_TABLE}(id)
        )
    """)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {PROJECT_META_TABLE} (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    cursor.close()


def _build_searchable_text(project, doe):
    parts = [
        project.get('name', ''),
        project.get('display_name', ''),
        project.get('background', ''),
        project.get('summary', ''),
        doe.get('doe_number', ''),
        doe.get('activity_flow_doe_number', ''),
        doe.get('order', ''),
        doe.get('title', ''),
    ]

    for section in (
        doe.get('detail_fields', []),
        doe.get('fixed_factors', []),
        doe.get('changed_factors', []),
        doe.get('evaluation_fields', []),
        doe.get('additional_fields', []),
    ):
        for item in section:
            parts.append(item.get('label', ''))
            parts.append(item.get('name', ''))
            parts.append(item.get('value', ''))
            parts.append(item.get('condition', ''))

    return '\n'.join(part for part in parts if part)


def _build_doe_searchable_text(doe):
    parts = [
        doe.get('doe_number', ''),
        doe.get('activity_flow_doe_number', ''),
        doe.get('order', ''),
        doe.get('title', ''),
    ]

    for section in (
        doe.get('detail_fields', []),
        doe.get('fixed_factors', []),
        doe.get('changed_factors', []),
        doe.get('evaluation_fields', []),
        doe.get('additional_fields', []),
    ):
        for item in section:
            parts.append(item.get('label', ''))
            parts.append(item.get('name', ''))
            parts.append(item.get('value', ''))
            parts.append(item.get('condition', ''))

    return '\n'.join(part for part in parts if part)


def sync_project_activities_to_db(force=False):
    """Keep SQLite project/DOE tables in sync with the cleaned workbook."""
    if not os.path.exists(EXPERIMENT_ACTIVITY_FILE):
        raise FileNotFoundError(f'Experiment workbook not found: {EXPERIMENT_ACTIVITY_FILE}')

    workbook_mtime = str(os.path.getmtime(EXPERIMENT_ACTIVITY_FILE))
    conn = get_db_connection()
    try:
        ensure_project_activity_tables(conn)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT value FROM {PROJECT_META_TABLE} WHERE key = ?",
            (PROJECT_META_MTIME_KEY,),
        )
        row = cursor.fetchone()
        current_mtime = row[0] if row else None

        cursor.execute(f"SELECT COUNT(*) FROM {PROJECT_CARD_TABLE}")
        project_count = cursor.fetchone()[0]

        if not force and current_mtime == workbook_mtime and project_count > 0:
            cursor.close()
            return

        projects = load_project_activities()

        cursor.execute(f"DELETE FROM {PROJECT_DOE_TABLE}")
        cursor.execute(f"DELETE FROM {PROJECT_CARD_TABLE}")

        for project_index, project in enumerate(projects):
            cursor.execute(
                f"""
                INSERT INTO {PROJECT_CARD_TABLE}
                (id, name, display_name, background, summary, doe_numbers_json, sort_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project['id'],
                    project['name'],
                    project.get('display_name'),
                    project.get('background'),
                    project.get('summary'),
                    _json_dumps(project.get('doe_numbers', [])),
                    project_index,
                ),
            )

            for doe_index, doe in enumerate(project.get('does', [])):
                cursor.execute(
                    f"""
                    INSERT INTO {PROJECT_DOE_TABLE}
                    (
                        id, project_id, doe_number, activity_flow_doe_number, order_label, title,
                        detail_fields_json, fixed_factors_json, changed_factors_json,
                        evaluation_fields_json, additional_fields_json, searchable_text, sort_index
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doe['id'],
                        project['id'],
                        doe.get('doe_number'),
                        doe.get('activity_flow_doe_number'),
                        doe.get('order'),
                        doe.get('title'),
                        _json_dumps(doe.get('detail_fields', [])),
                        _json_dumps(doe.get('fixed_factors', [])),
                        _json_dumps(doe.get('changed_factors', [])),
                        _json_dumps(doe.get('evaluation_fields', [])),
                        _json_dumps(doe.get('additional_fields', [])),
                        _build_searchable_text(project, doe),
                        doe_index,
                    ),
                )

        cursor.execute(
            f"""
            INSERT INTO {PROJECT_META_TABLE} (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (PROJECT_META_MTIME_KEY, workbook_mtime),
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def load_project_activities_from_db():
    sync_project_activities_to_db()
    conn = get_db_connection()
    try:
        ensure_project_activity_tables(conn)
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, name, display_name, background, summary, doe_numbers_json
            FROM {PROJECT_CARD_TABLE}
            ORDER BY sort_index
            """
        )
        project_rows = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT
                id, project_id, doe_number, activity_flow_doe_number, order_label, title,
                detail_fields_json, fixed_factors_json, changed_factors_json,
                evaluation_fields_json, additional_fields_json
            FROM {PROJECT_DOE_TABLE}
            ORDER BY project_id, sort_index
            """
        )
        doe_rows = cursor.fetchall()
        cursor.close()

        projects = []
        project_map = {}
        for row in project_rows:
            project = {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'background': row[3] or '',
                'summary': row[4] or '',
                'doe_numbers': _json_loads(row[5], []),
                'does': [],
            }
            projects.append(project)
            project_map[project['id']] = project

        for row in doe_rows:
            project = project_map.get(row[1])
            if not project:
                continue
            project['does'].append({
                'id': row[0],
                'doe_number': row[2],
                'activity_flow_doe_number': row[3],
                'order': row[4],
                'title': row[5],
                'detail_fields': _json_loads(row[6], []),
                'fixed_factors': _json_loads(row[7], []),
                'changed_factors': _json_loads(row[8], []),
                'evaluation_fields': _json_loads(row[9], []),
                'additional_fields': _json_loads(row[10], []),
            })

        return projects
    finally:
        conn.close()


def get_project_activity_by_id(project_id):
    projects = load_project_activities_from_db()
    return next((project for project in projects if project['id'] == project_id), None)


def build_llm_context_from_projects(projects):
    sections = []
    for project in projects:
        lines = [
            f"Project: {project['name']}",
            f"Display Name: {project.get('display_name') or project['name']}",
        ]
        if project.get('background'):
            lines.append(f"Project Background: {project['background']}")
        if project.get('summary'):
            lines.append(f"Project Summary: {project['summary']}")

        for doe in project.get('does', []):
            lines.append(f"DOE #: {doe.get('doe_number')}")
            if doe.get('activity_flow_doe_number'):
                lines.append(f"Activity Flow DOE #: {doe['activity_flow_doe_number']}")
            if doe.get('order'):
                lines.append(f"Order: {doe['order']}")

            for field in doe.get('detail_fields', []):
                lines.append(f"{field['label']}: {field['value']}")

            if doe.get('fixed_factors'):
                lines.append("Fixed Factors:")
                for factor in doe['fixed_factors']:
                    lines.append(f"- {factor['name']}: {factor['condition']}")

            if doe.get('changed_factors'):
                lines.append("Changed Factors:")
                for factor in doe['changed_factors']:
                    lines.append(f"- {factor['name']}: {factor['condition']}")

            if doe.get('evaluation_fields'):
                lines.append("Additional Results:")
                for field in doe['evaluation_fields']:
                    lines.append(f"- {field['name']}: {field['condition']}")

            if doe.get('additional_fields'):
                lines.append("Additional Info:")
                for field in doe['additional_fields']:
                    lines.append(f"- {field['label']}: {field['value']}")

        sections.append('\n'.join(lines))

    return '\n\n'.join(sections)


def _serialize_related_doe(doe):
    return {
        'id': doe.get('id'),
        'doe_number': doe.get('doe_number'),
        'activity_flow_doe_number': doe.get('activity_flow_doe_number'),
        'order': doe.get('order'),
        'title': doe.get('title'),
        'detail_fields': doe.get('detail_fields', []),
        'fixed_factors': doe.get('fixed_factors', []),
        'changed_factors': doe.get('changed_factors', []),
        'evaluation_fields': doe.get('evaluation_fields', []),
        'additional_fields': doe.get('additional_fields', []),
    }


def _project_reference_terms(project):
    terms = []
    for value in (project.get('display_name'), project.get('name')):
        term = _normalize_query_text(value)
        if term and term not in terms:
            terms.append(term)
    return terms


def _find_project_reference_position(project, text):
    normalized_text = _normalize_query_text(text)
    if not normalized_text:
        return -1

    positions = []
    for term in _project_reference_terms(project):
        position = normalized_text.find(term)
        if position >= 0:
            positions.append(position)

    return min(positions) if positions else -1


def _extract_project_reference_snippets(project, text, leading_chars=80, trailing_chars=240):
    normalized_text = _normalize_query_text(text)
    if not normalized_text:
        return []

    snippets = []
    for term in _project_reference_terms(project):
        start = 0
        while True:
            position = normalized_text.find(term, start)
            if position < 0:
                break

            snippet_start = max(0, position - leading_chars)
            snippet_end = min(len(normalized_text), position + len(term) + trailing_chars)
            snippets.append(normalized_text[snippet_start:snippet_end])
            start = position + len(term)

    return snippets


def _find_referenced_doe_ids(project, text):
    snippets = _extract_project_reference_snippets(project, text)
    if not snippets:
        return []

    related_doe_ids = []

    for doe in project.get('does', []):
        doe_id = doe.get('id')
        doe_number = _normalize_query_text(doe.get('doe_number'))
        if not doe_id or not doe_number:
            continue

        if any(
            re.search(rf'(?<![a-z0-9]){re.escape(doe_number)}(?![a-z0-9])', snippet)
            for snippet in snippets
        ):
            related_doe_ids.append(doe_id)

    return related_doe_ids


def _build_related_project_card(project, related_doe_ids=None):
    related_doe_ids = list(dict.fromkeys(related_doe_ids or []))
    related_doe_numbers = []

    for doe in project.get('does', []):
        if doe.get('id') not in related_doe_ids:
            continue

        doe_number = doe.get('doe_number')
        if doe_number and doe_number not in related_doe_numbers:
            related_doe_numbers.append(doe_number)

    return {
        'id': project['id'],
        'name': project['name'],
        'display_name': project.get('display_name'),
        'background': project.get('background', ''),
        'does': [_serialize_related_doe(doe) for doe in project.get('does', [])],
        'related_doe_ids': related_doe_ids,
        'related_doe_numbers': related_doe_numbers,
    }


def _normalize_query_text(text):
    return re.sub(r'\s+', ' ', str(text or '').strip().lower())


def _expand_query_tokens(query):
    normalized = _normalize_query_text(query)
    tokens = set(re.findall(r'[a-z0-9\.\+#]+', normalized))

    alias_map = {
        'blister': ['blister', 'post elp blister', '起泡'],
        'desmear': ['desmear', '除胶', '闄よ兌'],
        'dry': ['dry', '干法', '骞叉硶'],
        'wet': ['wet', '湿法', '婀挎硶'],
        'outsourcing': ['outsourcing', 'supplier', '外包', '澶栧寘'],
        'plasma': ['plasma', '等离子'],
        'adhesion': ['adhesion', 'peel strength', 'copper adhesion', '附着'],
        'void': ['void', '空洞'],
    }

    for base_token, aliases in alias_map.items():
        if any(alias.lower() in normalized for alias in aliases):
            tokens.add(base_token)
            tokens.update(re.findall(r'[a-z0-9\.\+#]+', base_token))

    if 'post' in normalized and 'elp' in normalized:
        tokens.update({'post', 'elp', 'blister'})

    return [token for token in tokens if len(token) > 1]


def find_related_project_cards(query, llm_response='', limit_projects=3):
    projects = load_project_activities_from_db()
    tokens = _expand_query_tokens(query)
    normalized_query = _normalize_query_text(query)
    referenced_projects = []
    scored_projects = []

    for project in projects:
        project_name = _normalize_query_text(project['name'])
        display_name = _normalize_query_text(project.get('display_name'))
        doe_hit_ids = []
        project_score = 0

        if project_name and project_name in normalized_query:
            project_score += 8
        elif display_name and display_name in normalized_query:
            project_score += 8

        total_score = project_score

        for doe in project.get('does', []):
            searchable_text = _normalize_query_text(_build_doe_searchable_text(doe))
            score = 0

            for token in tokens:
                if token in searchable_text:
                    score += 2
                if doe.get('doe_number') and token == str(doe['doe_number']).lower():
                    score += 3

            if score > 0:
                total_score += score
                if doe.get('id'):
                    doe_hit_ids.append(doe['id'])

        referenced_position = _find_project_reference_position(project, llm_response)
        referenced_doe_ids = _find_referenced_doe_ids(project, llm_response)

        if referenced_position >= 0:
            referenced_projects.append({
                'position': referenced_position,
                'score': total_score,
                'project': _build_related_project_card(project, referenced_doe_ids or doe_hit_ids),
            })
        elif total_score > 0:
            scored_projects.append({
                'score': total_score,
                'project': _build_related_project_card(project, doe_hit_ids),
            })

    final_projects = []
    added_project_ids = set()

    referenced_projects.sort(key=lambda item: (item['position'], -item['score']))
    for item in referenced_projects:
        project = item['project']
        if project['id'] in added_project_ids:
            continue
        final_projects.append(project)
        added_project_ids.add(project['id'])
        if len(final_projects) >= limit_projects:
            return final_projects

    if final_projects:
        return final_projects[:limit_projects]

    if not final_projects and not scored_projects:
        fallback_projects = []
        for project in projects[:limit_projects]:
            fallback_projects.append(_build_related_project_card(project))
        return fallback_projects

    scored_projects.sort(key=lambda item: item['score'], reverse=True)
    top_score = scored_projects[0]['score']
    score_threshold = max(4, int(top_score * 0.4))

    for item in scored_projects:
        if item['score'] < score_threshold:
            continue
        project = item['project']
        if project['id'] in added_project_ids:
            continue
        final_projects.append(project)
        added_project_ids.add(project['id'])
        if len(final_projects) >= limit_projects:
            break

    return final_projects[:limit_projects]

def call_llm(prompt, context, language='zh'):
    """调用LLM进行分析"""
    # 某些本地模型兼容 OpenAI 格式但不要求鉴权，此时 LLM_API_KEY 可能为空
    if not all([LLM_BASE_URL, LLM_MODEL]):
        return "LLM配置不完整，缺少 LLM_BASE_URL 或 LLM_MODEL，无法进行深度分析"
    
    try:
        headers = {
            "Content-Type": "application/json",
        }
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
        
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
- 请列出本次回答中参考的所有Main Activity名称，每行一个。
- **硬性要求**：此段落必须出现；如果本次回答未引用任何Main Activity，也必须输出该段落并写 `- 无`。"""
            user_prompt = f"历史数据:\n{context}\n\n用户问题:\n{prompt}\n\n请严格按照上述Output Format输出。**硬性要求**：必须包含 `## [本次回答采纳的Main Activity]` 段落；若无引用也要输出并写 `- 无`。同时确保包含实验结论、关键参数/路径和Engineer Insight板块。回答必须基于提供的历史数据，不得虚构任何DOE编号或实验数据。"
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
- Please list all Main Activity names referenced in this answer, one per line.
- **Hard requirement**: this section must always be present; if none are referenced, output the section and write `- None`. """
            user_prompt = f"Historical data:\n{context}\n\nUser question:\n{prompt}\n\nPlease output according to the above Output Format. **Hard requirement**: you must include the `## [Main Activity References]` section; if none are referenced, still output it and write `- None`. Ensure the Experimental Conclusion, Key Parameters/Path, and Engineer Insight sections are included. Your answer must be based strictly on the provided historical data, and you must not fabricate any DOE numbers or experimental data."
        
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

def call_llm_for_doe(prompt, context, language='zh'):
    """Call the configured LLM with strict DOE-only instructions."""
    if not all([LLM_BASE_URL, LLM_MODEL]):
        if language == 'zh':
            return 'LLM 配置不完整，缺少 LLM_BASE_URL 或 LLM_MODEL，无法生成基于 DOE 数据的回答。'
        return 'LLM configuration is incomplete. Missing LLM_BASE_URL or LLM_MODEL.'

    try:
        headers = {"Content-Type": "application/json"}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"

        if language == 'zh':
            system_prompt = """你是一位半导体封装 DOE 数据分析助手。

规则：
1. 只能根据提供的 DOE 数据回答，不能补充数据库里没有的结论、DOE 编号、条件或机理。
2. 如果数据没有直接证据，请明确写“当前数据没有直接证据支持这一点”。
3. 回答里要明确写出相关 Project 和 DOE 编号。
4. 不要推荐下载文件，不要提 Activity List、Excel 下载或外部资料。
5. Engineer Insight 只能总结数据已经体现出来的经验，不能扩写成外部知识。

输出格式：
## 结论
- 直接回答用户问题

## 数据依据
- Project: ...
  DOE: ...
  依据: ...

## Engineer Insight
- 只总结数据里已经体现的工艺经验
"""
            user_prompt = (
                f"DOE 数据:\n{context}\n\n"
                f"用户问题:\n{prompt}\n\n"
                "请严格只根据 DOE 数据回答。如果没有直接证据，就明确说明没有直接证据。"
            )
        else:
            system_prompt = """You are a semiconductor packaging DOE data assistant.

Rules:
1. Answer strictly from the provided DOE data only.
2. Do not invent conclusions, DOE numbers, conditions, or mechanisms.
3. If the data does not directly answer the question, explicitly say the current data does not provide direct evidence.
4. Explicitly mention the relevant Project and DOE numbers.
5. Do not suggest downloading files or mention external sources.
6. Keep Engineer Insight grounded in the data only.

Output format:
## Conclusion
- Direct answer

## Data Evidence
- Project: ...
  DOE: ...
  Evidence: ...

## Engineer Insight
- Keep it grounded in the data only
"""
            user_prompt = (
                f"DOE data:\n{context}\n\n"
                f"User question:\n{prompt}\n\n"
                "Answer strictly from the DOE data. If evidence is missing, say so explicitly."
            )

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        response = requests.post(f"{LLM_BASE_URL}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        if language == 'zh':
            return f"LLM 调用失败: {str(e)}"
        return f"LLM call failed: {str(e)}"


def _llm_config_error(language='zh'):
    if language == 'zh':
        return 'LLM 閰嶇疆涓嶅畬鏁达紝缂哄皯 LLM_BASE_URL 鎴?LLM_MODEL锛屾棤娉曠敓鎴愬熀浜?DOE 鏁版嵁鐨勫洖绛斻€?'
    return 'LLM configuration is incomplete. Missing LLM_BASE_URL or LLM_MODEL.'


def _build_doe_llm_request(prompt, context, language='zh'):
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    if language == 'zh':
        system_prompt = """浣犳槸涓€浣嶅崐瀵间綋灏佽 DOE 鏁版嵁鍒嗘瀽鍔╂墜銆?
瑙勫垯锛?1. 鍙兘鏍规嵁鎻愪緵鐨?DOE 鏁版嵁鍥炵瓟锛屼笉鑳借ˉ鍏呮暟鎹簱閲屾病鏈夌殑缁撹銆丏OE 缂栧彿銆佹潯浠舵垨鏈虹悊銆?2. 濡傛灉鏁版嵁娌℃湁鐩存帴璇佹嵁锛岃鏄庣‘鍐欌€滃綋鍓嶆暟鎹病鏈夌洿鎺ヨ瘉鎹敮鎸佽繖涓€鐐光€濄€?3. 鍥炵瓟閲岃鏄庣‘鍐欏嚭鐩稿叧 Project 鍜?DOE 缂栧彿銆?4. 涓嶈鎺ㄨ崘涓嬭浇鏂囦欢锛屼笉瑕佹彁 Activity List銆丒xcel 涓嬭浇鎴栧閮ㄨ祫鏂欍€?5. Engineer Insight 鍙兘鎬荤粨鏁版嵁宸茬粡浣撶幇鍑烘潵鐨勭粡楠岋紝涓嶈兘鎵╁啓鎴愬閮ㄧ煡璇嗐€?
杈撳嚭鏍煎紡锛?## 缁撹
- 鐩存帴鍥炵瓟鐢ㄦ埛闂

## 鏁版嵁渚濇嵁
- Project: ...
  DOE: ...
  渚濇嵁: ...

## Engineer Insight
- 鍙€荤粨鏁版嵁閲屽凡缁忎綋鐜扮殑宸ヨ壓缁忛獙
"""
        user_prompt = (
            f"DOE 鏁版嵁:\n{context}\n\n"
            f"鐢ㄦ埛闂:\n{prompt}\n\n"
            "璇蜂弗鏍煎彧鏍规嵁 DOE 鏁版嵁鍥炵瓟銆傚鏋滄病鏈夌洿鎺ヨ瘉鎹紝灏辨槑纭鏄庢病鏈夌洿鎺ヨ瘉鎹€?"
        )
    else:
        system_prompt = """You are a semiconductor packaging DOE data assistant.

Rules:
1. Answer strictly from the provided DOE data only.
2. Do not invent conclusions, DOE numbers, conditions, or mechanisms.
3. If the data does not directly answer the question, explicitly say the current data does not provide direct evidence.
4. Explicitly mention the relevant Project and DOE numbers.
5. Do not suggest downloading files or mention external sources.
6. Keep Engineer Insight grounded in the data only.

Output format:
## Conclusion
- Direct answer

## Data Evidence
- Project: ...
  DOE: ...
  Evidence: ...

## Engineer Insight
- Keep it grounded in the data only
"""
        user_prompt = (
            f"DOE data:\n{context}\n\n"
            f"User question:\n{prompt}\n\n"
            "Answer strictly from the DOE data. If evidence is missing, say so explicitly."
        )

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }

    return headers, payload


def _extract_text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text = item.get('text') or item.get('value') or item.get('content')
            if text:
                parts.append(str(text))
        return ''.join(parts)
    return ''


def _extract_chat_completion_text(result):
    choices = result.get('choices') or []
    if not choices:
        return ''

    message = choices[0].get('message') or {}
    text = _extract_text_content(message.get('content'))
    if text:
        return text

    delta = choices[0].get('delta') or {}
    return _extract_text_content(delta.get('content'))


def _extract_stream_delta_text(chunk):
    choices = chunk.get('choices') or []
    if not choices:
        return ''

    delta = choices[0].get('delta') or {}
    return _extract_text_content(delta.get('content'))


def _iter_llm_for_doe_stream(prompt, context, language='zh'):
    if not all([LLM_BASE_URL, LLM_MODEL]):
        raise RuntimeError(_llm_config_error(language))

    headers, payload = _build_doe_llm_request(prompt, context, language)
    payload['stream'] = True

    with requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')

        if 'text/event-stream' not in content_type:
            result = response.json()
            text = _extract_chat_completion_text(result)
            if text:
                yield text
            return

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.strip()
            if line.startswith('data:'):
                line = line[5:].strip()

            if not line or line == '[DONE]':
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = _extract_stream_delta_text(chunk)
            if text:
                yield text


def _format_sse_event(event_name, payload):
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event_name}\ndata: {data}\n\n"


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
    raw = str(llm_analysis or "")
    if not raw.strip():
        return []

    lines_all = re.split(r'\r?\n', raw)

    def is_heading(line: str) -> bool:
        return bool(re.match(r'^\s*#{1,6}\s+', line or ""))

    def is_target_heading(line: str) -> bool:
        s = (line or "").strip()
        return (
            re.search(r'本次回答采纳的\s*Main\s*Activity', s, re.I) is not None
            or re.match(r'^\s*#+\s*\[?\s*本次回答采纳的\s*Main\s*Activity\s*\]?\s*$', s, re.I) is not None
            or re.search(r'Main\s*Activity\s*References', s, re.I) is not None
        )

    start_idx = -1
    for i, line in enumerate(lines_all):
        if is_target_heading(line):
            start_idx = i
            break
    if start_idx == -1:
        # 最后兜底：直接抓取已知活动名（避免LLM不按模板输出时完全为空）
        activity_regex = re.compile(r'(Post ELP Blister Activity|Dry Desmear Outsourcing|Dry \+ Wet Desmear pathfinding)')
        return list(dict.fromkeys(activity_regex.findall(raw)))

    block_lines = []
    for i in range(start_idx + 1, len(lines_all)):
        line = lines_all[i]
        if is_heading(line):
            break
        block_lines.append(line)

    normalized = [l.strip() for l in block_lines if l and l.strip()]
    if not normalized:
        return []

    items = []
    for line in normalized:
        m = (
            re.match(r'^[-*]\s*(.+)$', line)
            or re.match(r'^\d+[\.\)]\s*(.+)$', line)
            or re.match(r'^\s*[-•]\s*(.+)$', line)
        )
        if m and m.group(1):
            items.append(m.group(1).strip())
            continue
        if len(line) >= 3 and not re.search(r'[:：]\s*$', line) and not re.match(r'^(请|please)\b', line, re.I):
            items.append(line.strip())

    seen = set()
    out = []
    for name in items:
        key = re.sub(r'\s+', ' ', name.strip()).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(name.strip())
    return out


def _cache_set(query_id: str, llm_analysis: str, related_projects=None):
    now = time.time()
    with _AI_QUERY_CACHE_LOCK:
        _AI_QUERY_CACHE[query_id] = {
            "llm_analysis": llm_analysis or "",
            "related_projects": related_projects or [],
            "ts": now,
        }


def _cache_get(query_id: str):
    now = time.time()
    with _AI_QUERY_CACHE_LOCK:
        item = _AI_QUERY_CACHE.get(query_id)
        if not item:
            return None
        if now - item.get("ts", 0) > _AI_QUERY_CACHE_TTL_SECONDS:
            _AI_QUERY_CACHE.pop(query_id, None)
            return None
        return item


def _cache_cleanup():
    now = time.time()
    with _AI_QUERY_CACHE_LOCK:
        expired = [k for k, v in _AI_QUERY_CACHE.items() if now - v.get("ts", 0) > _AI_QUERY_CACHE_TTL_SECONDS]
        for k in expired:
            _AI_QUERY_CACHE.pop(k, None)

@api.route('/ai/query', methods=['POST'])
def ai_query():
    """AI assistant query endpoint backed by DOE data in SQLite."""
    _cache_cleanup()
    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    language = data.get('language', 'zh')
    all_projects = load_project_activities_from_db()
    context = build_llm_context_from_projects(all_projects)

    @stream_with_context
    def generate():
        llm_parts = []

        try:
            yield _format_sse_event('start', {'ok': True})

            for chunk in _iter_llm_for_doe_stream(query, context, language):
                llm_parts.append(chunk)
                yield _format_sse_event('message', {'delta': chunk})

            llm_response = ''.join(llm_parts)
            project_cards = find_related_project_cards(query, llm_response)
            query_id = str(uuid.uuid4())
            _cache_set(query_id, llm_response, project_cards)

            yield _format_sse_event('done', {
                'query_id': query_id,
                'llm_analysis': llm_response,
                'project_cards': project_cards,
            })
        except Exception as e:
            message = str(e)
            yield _format_sse_event('error', {'message': message})

    return Response(
        generate(),
        content_type='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


@api.route('/ai/query/<query_id>/references', methods=['GET'])
def ai_query_references(query_id):
    """Return cached related project cards for a previous AI response."""
    item = _cache_get(query_id)
    if not item:
        return jsonify({'error': 'query_id not found or expired', 'project_cards': []}), 404

    return jsonify({
        'query_id': query_id,
        'project_cards': item.get('related_projects', []),
    })

# 活动流相关API

@api.route('/project-activities', methods=['GET'])
def get_project_activities():
    """Return grouped project cards from SQLite."""
    try:
        return jsonify(load_project_activities_from_db())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/project-activities/<project_id>', methods=['GET'])
def get_project_activity(project_id):
    """Return one project card and all DOE rows for it."""
    try:
        project = get_project_activity_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        return jsonify(project)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/activities', methods=['GET'])
def get_activities():
    """Compatibility alias for project cards."""
    try:
        projects = load_project_activities_from_db()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/activities/<project_id>', methods=['GET'])
def get_activity(project_id):
    """Compatibility alias for a single project detail."""
    try:
        project = get_project_activity_by_id(project_id)
        if not project:
            return jsonify({'error': 'Activity not found'}), 404
        return jsonify(project)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/activities', methods=['POST'])
def create_activity():
    return jsonify({
        'error': 'Manual activity creation is disabled. Update the DOE workbook and resync SQLite instead.'
    }), 410

@api.route('/activities/<int:activity_id>/subactivities', methods=['POST'])
def create_subactivity(activity_id):
    return jsonify({
        'error': 'Manual subactivity creation is disabled. Update the DOE workbook and resync SQLite instead.'
    }), 410

@api.route('/download/activity/<int:activity_id>', methods=['GET'])
def download_activity_excel(activity_id):
    return jsonify({
        'error': 'Activity file downloads have been removed. Please use project cards and DOE references in the UI.'
    }), 410

@api.route('/download/all-activities', methods=['GET'])
def download_all_activities_excel():
    return jsonify({
        'error': 'Bulk activity downloads have been removed. Please use project cards and DOE references in the UI.'
    }), 410
