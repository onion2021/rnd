import sqlite3
import os

# SQLite数据库文件路径
DB_FILE = os.path.join(os.path.dirname(__file__), 'pdm.db')

def init_database():
    """初始化SQLite数据库"""
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 创建main_activities表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS main_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                background TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建sub_activities表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sub_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                main_activity_id INTEGER,
                order_num INTEGER,
                doe_number TEXT,
                background TEXT,
                activity_name TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (main_activity_id) REFERENCES main_activities (id)
            )
        """)
        
        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM main_activities")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # 插入主要活动数据
            main_activities = [
                {
                    'name': 'Post ELP Blister Activity',
                    'background': 'During the loading of the actual glass panels it was observed that there are blisters on the panels surface after post ELP',
                    'summary': 'The problem is with the treatment uniformity of the Nordson March tool\n\nCan have a good result but with higher cost, since need to load at complete the slot loading\n\nSlot 13 - Dummy\nSlot 7 - Dummy\nSlot 4 - Dummy\nSlot 1 - Actual Panel\n\nLoading Condition:\nO2 + N2 + CF4\n(2x CF4 Duration)\n(2x CF4 Flow rate)\n\n*Best since it has flow rate is only 2x, more cost effective'
                },
                {
                    'name': 'Dry Desmear Outsourcing',
                    'background': 'Due to the previous result of the post ELP blister activity that the CHQ2 tool has limitations, it was discussed to search for different plasma (dry desmear) suppliers to try to process some samples\n\nTarget is to replace wet desmear\'s\nSurface and 10um Via Cleaning',
                    'summary': 'CHQ2 tool is still favorable to use compared to supplier tools'
                },
                {
                    'name': 'Dry + Wet Desmear pathfinding',
                    'background': 'Due to the previous result of low Copper adhesion and Dry desmear showed the capability to clean the Via bottom it was discussed to combine both the Dry + Wet desmear to get clean Via bottom result and get good copper adhesion',
                    'summary': ''
                }
            ]
            
            for activity in main_activities:
                cursor.execute(
                    """INSERT INTO main_activities (name, background, summary) VALUES (?, ?, ?)""",
                    (activity['name'], activity['background'], activity['summary'])
                )
                main_activity_id = cursor.lastrowid
                
                # 插入子活动数据
                if activity['name'] == 'Post ELP Blister Activity':
                    sub_activities = [
                        {
                            'order_num': 1,
                            'doe_number': '#1',
                            'background': 'During the abnormality discussion, one of the hypothesis is possibly due to the Non-POR process of Dry Desmear as replacement to Wet Desmear',
                            'activity_name': 'Plasma treatment chemistry and condition search to determine different HVM POR Plasma conditions effect as Dry Desmear',
                            'result': 'Best Condition found based on QC items is O2 + N2 + CF4'
                        },
                        {
                            'order_num': 2,
                            'doe_number': '#2.1',
                            'background': 'Best condition (O2 + N2 + CF4) still has blisters, and was tackled during a discussion 3 possible hypothesis due to the location of the blisters',
                            'activity_name': 'Hypothesis # 1\nTo Determine if the ABF Thickness and CCL status (With or Without pattern) has effect on the Plasma (Dry Desmear) post ELP blister result',
                            'result': 'ABF thickness and CCL Status (with and without pattern) does not affect the occurrence of blister'
                        },
                        {
                            'order_num': 2,
                            'doe_number': '#2.2',
                            'background': 'Best condition (O2 + N2 + CF4) still has blisters, and was tackled during a discussion 3 possible hypothesis due to the location of the blisters',
                            'activity_name': 'Hypothesis # 2\nTo determine if there is a correlation between the ABF Curing temperature and post ELP blister\n\n1. Possible Low BF Cure temperature\n2. Solvent is trapped by the PET film in the panel\'s edge\n(Remark: remove one side PET during plasma)',
                            'result': 'The best result was found using POR+ BF Curing temperature through occurrence of less blisters\n\nWith PET or without PET film does not affect occurrence of Blister\n\nAll panels encountered blisters'
                        },
                        {
                            'order_num': 2,
                            'doe_number': '#2.3',
                            'background': 'Best condition (O2 + N2 + CF4) still has blisters, and was tackled during a discussion 3 possible hypothesis due to the location of the blisters',
                            'activity_name': 'Hypothesis # 3\nTo Determine if the Post ELP blister is correlated with ABF type ',
                            'result': 'Different ABF material still encountered Blister.'
                        },
                        {
                            'order_num': 3,
                            'doe_number': '#3',
                            'background': 'Due to the Root cause was still not found after the initial evaluations, it was triggered in a discussion to contact ABF Supplier (Ajinomoto) to discuss the Blister and Dry desmear',
                            'activity_name': 'Discussed with Ajinomoto and comment\n1. ATS Plasma condition is weak\n2. Batch Type Plasma treatment is not that good',
                            'result': 'Slot # 4 for 2x CF4 flow rate did not encounter blister\n\nSlot # 7 for 3x CF4 flow rate encountered few blisters but it was noticed during unloading that the panel was slanted (Possible cause of blister)\n\nDuring this time, we were sentitive to specific slot loading.'
                        },
                        {
                            'order_num': 4,
                            'doe_number': '#4',
                            'background': 'Due to the panels used at DOE # 3 were reworked panels, it is needed to validated to fresh dummy CCL',
                            'activity_name': 'Validation of result from DOE # 3 using Actual dummy panels using EFB setting and process flow',
                            'result': '2x CF4 flow rate and 3x CF4 flow rate did not encounter blister at Slot # 1'
                        }
                    ]
                elif activity['name'] == 'Dry Desmear Outsourcing':
                    sub_activities = [
                        {
                            'order_num': 5,
                            'doe_number': '#1',
                            'background': 'Local supplier found (Boffoto)',
                            'activity_name': 'Trying different supplier tool to check if can perform AT&S requirement of replacement of CHQ2 plasma (Dry Desmear) tool',
                            'result': 'Found leg # 2 and Leg # 3 to have no blisters but has low copper adhesion, other legs were not proceeded due to presence of unremoved fillers at the surface'
                        },
                        {
                            'order_num': 6,
                            'doe_number': '#2',
                            'background': '2nd supplier found (AMAT)',
                            'activity_name': 'Trying different supplier tool to check if can perform AT&S requirement of replacement of CHQ2 plasma (Dry Desmear) tool',
                            'result': 'Found that plasma condition of AMAT is not compatible with AT&S plating, resulted in abnormal electroless plating (Unplated)'
                        }
                    ]
                else:  # Dry + Wet Desmear pathfinding
                    sub_activities = [
                        {
                            'order_num': 7,
                            'doe_number': '#1',
                            'background': 'Using AT&S CHQinternal tools, CHQ2 plasma and CHQ1 ELP',
                            'activity_name': 'Finding a combination of processes that will result in the required result',
                            'result': 'Combination of Dry and Wet Desmear is feasbile for surface and via cleaning, but need optimization of conditions to achieve higher Copper Adhesion but some of key targets are achieved, No blister, clean via bottom, via sidewall and Via specs'
                        }
                    ]
                
                for sub_activity in sub_activities:
                    cursor.execute(
                        """INSERT INTO sub_activities (main_activity_id, order_num, doe_number, background, activity_name, result) VALUES (?, ?, ?, ?, ?, ?)""",
                        (main_activity_id, sub_activity['order_num'], sub_activity['doe_number'], sub_activity['background'], sub_activity['activity_name'], sub_activity['result'])
                    )
            
            conn.commit()
            print("活动数据插入成功")
        else:
            print("数据库已有数据，跳过插入")
        
        cursor.close()
        conn.close()
        print("SQLite数据库初始化完成")
        
    except Exception as e:
        print(f"初始化SQLite数据库时出错: {str(e)}")

def test_connection():
    """测试数据库连接"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute("SELECT COUNT(*) FROM main_activities")
        count = cursor.fetchone()[0]
        print(f"数据库中有 {count} 个主要活动")
        
        cursor.execute("SELECT COUNT(*) FROM sub_activities")
        count = cursor.fetchone()[0]
        print(f"数据库中有 {count} 个子活动")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"测试数据库连接时出错: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()
    test_connection()
