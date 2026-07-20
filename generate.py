import os
import requests
import re
import qrcode
from io import BytesIO
import base64
import shutil
import urllib.parse

REPO = os.getenv('GITHUB_REPOSITORY')
TOKEN = os.getenv('GITHUB_TOKEN')
USER = REPO.split('/')[0] if REPO else 'merryAndrew'
REPO_NAME = REPO.split('/')[1] if REPO and '/' in REPO else 'HealthCertificate'

# 只获取未关闭的 Issue
url = f'https://api.github.com/repos/{REPO}/issues?state=open&per_page=100'
headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
issues = requests.get(url, headers=headers).json()

print(f"📡 获取到 {len(issues)} 个 Issue")

def extract_first_image(text):
    match = re.search(r'!\[.*?\]\((https?://[^\s]+)\)', text)
    if match:
        return match.group(1)
    match = re.search(r'<img[^>]+src="(https?://[^\s"]+)"', text)
    if match:
        return match.group(1)
    match = re.search(r'(https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp|svg))', text)
    if match:
        return match.group(1)
    match = re.search(r'头像图片[：:]\s*(https?://[^\s]+)', text)
    if match:
        return match.group(1)
    return None

def format_date(raw_date):
    if not raw_date:
        return '未选择日期 (有效期一年)'
    raw_date = raw_date.strip()
    match = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', raw_date)
    if match:
        year, month, day = match.groups()
        return f'{year}年{int(month)}月{int(day)}日 (有效期一年)'
    return raw_date

def build_card(issue, style='A'):
    # Issue 标题 = 姓名
    name = issue['title']
    body = issue['body'] or ''
    comments_url = issue['comments_url']
    comments = requests.get(comments_url, headers=headers).json()
    all_text = body
    for comment in comments:
        all_text += ' ' + comment.get('body', '')

    # 提取所有字段
    gender_match = re.search(r'性别[：:]\s*(.+)', all_text)
    gender = gender_match.group(1).strip() if gender_match else '男'

    id_match = re.search(r'身份证[：:]\s*(.+)', all_text)
    id_num = id_match.group(1).strip() if id_match else '无'

    date_match = re.search(r'体检日期[：:]\s*(.+)', all_text)
    if date_match:
        raw_date = date_match.group(1).strip()
        date_display = format_date(raw_date)
    else:
        date_display = '未选择日期 (有效期一年)'

    hospital_match = re.search(r'体检单位[：:]\s*(.+)', all_text)
    hospital = hospital_match.group(1).strip() if hospital_match else '广州东仁医院'

    # 卡片1标题（独立于 Issue 标题）
    card1_title_match = re.search(r'卡片1标题[：:]\s*(.+)', all_text)
    card1_title = card1_title_match.group(1).strip() if card1_title_match else '广东省食品从业人员健康证明'

    # 卡片2中间文字（独立编辑）
    card2_text_match = re.search(r'卡片2文字[：:]\s*(.+)', all_text)
    card2_text = card2_text_match.group(1).strip() if card2_text_match else '广东省食品从业人员'

    # 卡片3底部文字
    card3_text_match = re.search(r'卡片3文字[：:]\s*(.+)', all_text)
    card3_text = card3_text_match.group(1).strip() if card3_text_match else '此健康信息已上报平台'

    # 隐藏卡片列表
    hidden_match = re.search(r'隐藏卡片[：:]\s*(.+)', all_text)
    hidden_list = hidden_match.group(1).strip() if hidden_match else ''
    hidden_cards = [h.strip() for h in hidden_list.split('|') if h.strip()]

    img_url = extract_first_image(all_text)
    if not img_url:
        img_url = 'https://via.placeholder.com/70x90?text=No+Photo'
    print(f"📸 姓名 '{name}' 的图片链接: {img_url}")

    encoded_name = urllib.parse.quote(name)
    page_url = f'https://{USER}.github.io/{REPO_NAME}/index.html?id={encoded_name}'
    qr = qrcode.make(page_url)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    # 判断卡片是否隐藏
    is_hidden = style in hidden_cards

    if style == 'A':
        if is_hidden:
            return ''  # A版隐藏则返回空
        return f'''
        <div class="cert-wrapper" data-title="{name}" data-issue-number="{issue['number']}" data-card-type="A">
            <div class="cert-module top-card">
                <div class="top-title">{card1_title}</div>
                <div class="top-content">
                    <div class="text-container">
                        <div class="info-line">
                            <span style="font-weight: bold;">姓 名</span>
                            <span>∶</span>
                            <span>{name}</span>
                            <span class="gender-separator" style="font-weight: bold;">性 别</span>
                            <span>∶</span>
                            <span>{gender}</span>
                        </div>
                        <div class="id-group">
                            <div class="info-line">
                                <span style="font-weight: bold;">身份证号码</span>
                                <span>∶</span>
                                <span>{id_num}</span>
                            </div>
                            <div class="info-line">(或其它有效证明)</div>
                        </div>
                        <div class="info-line">
                            <span style="font-weight: bold;">体检单位</span>
                            <span>∶</span>
                            <span>{hospital}</span>
                        </div>
                        <div class="info-line last-line">
                            <span style="font-weight: bold;">体检日期</span>
                            <span>∶</span>
                            <span>{date_display}</span>
                        </div>
                    </div>
                    <div class="photo">
                        <div class="seal-container">
                            <img class="seal-img" src="https://cdn.jsdelivr.net/gh/merryAndrew/imge@main/than.png" alt="印章图片">
                        </div>
                        <img src="{img_url}" alt="持证人照片">
                    </div>
                </div>
            </div>
            <div class="cert-module middle-card">
                <div class="middle-line">{card2_text}</div>
                <div class="middle-line">健康证明</div>
            </div>
            <div class="bottom-card">
                <div class="qrcode-area">
                    <div class="qrcode-title">防伪标识二维码</div>
                    <div class="qrcode-img">
                        <img src="data:image/png;base64,{qr_base64}" alt="防伪二维码">
                    </div>
                </div>
                <div class="notice">
                    <div class="notice-title">
                        <i class="fas fa-exclamation-circle exclamation-icon"></i>
                        关于申请实体证明通知：
                    </div>
                    <div class="notice-content">{card3_text}</div>
                </div>
            </div>
        </div>
        '''
    elif style == 'B':
        if is_hidden:
            return ''
        return f'''
        <div class="cert-wrapper" data-title="{name}" data-issue-number="{issue['number']}" data-card-type="B">
            <div class="cert-module top-card">
                <div class="top-title">{card1_title}</div>
                <div class="top-content">
                    <div class="text-container">
                        <div class="info-line">
                            <span class="label">姓 名</span>
                            <span class="colon">∶</span>
                            <span class="content">{name}</span>
                            <span class="gender-separator"></span>
                            <span class="label">性 别</span>
                            <span class="colon">∶</span>
                            <span class="content">{gender}</span>
                        </div>
                        <div class="id-group">
                            <div class="info-line">
                                <span class="label">身份证号码</span>
                                <span class="colon">∶</span>
                                <span class="content">{id_num}</span>
                            </div>
                            <div class="info-line">(或其它有效证明)</div>
                        </div>
                        <div class="info-line">
                            <span class="label">体检单位</span>
                            <span class="colon">∶</span>
                            <span class="content">{hospital}</span>
                        </div>
                        <div class="info-line last-line">
                            <span class="label">体检日期</span>
                            <span class="colon">∶</span>
                            <span class="content">{date_display}</span>
                        </div>
                    </div>
                    <div class="photo">
                        <img src="{img_url}" alt="持证人照片">
                    </div>
                </div>
            </div>
            <div class="cert-module middle-card">
                <div class="middle-line">{card2_text}</div>
                <div class="middle-line">健康证明</div>
            </div>
            <div class="bottom-card">
                <div class="qrcode-area">
                    <div class="qrcode-img">
                        <img src="data:image/png;base64,{qr_base64}" alt="防伪二维码">
                    </div>
                    <div class="qrcode-title">{card3_text}</div>
                </div>
            </div>
        </div>
        '''
    else:  # C版
        if is_hidden:
            return ''
        return f'''
        <div class="cert-wrapper" data-title="{name}" data-issue-number="{issue['number']}" data-card-type="C">
            <div class="cert-module top-card">
                <div class="top-title">{card1_title}</div>
                <div class="top-content">
                    <div class="text-container">
                        <div class="info-line">
                            <span style="font-weight: bold;">姓 名</span>
                            <span>∶</span>
                            <span>{name}</span>
                            <span class="gender-separator" style="font-weight: bold;">性 别</span>
                            <span>∶</span>
                            <span>{gender}</span>
                        </div>
                        <div class="id-group">
                            <div class="info-line">
                                <span style="font-weight: bold;">身份证号码</span>
                                <span>∶</span>
                                <span>{id_num}</span>
                            </div>
                            <div class="info-line">(或其它有效证明)</div>
                        </div>
                        <div class="info-line">
                            <span style="font-weight: bold;">体检单位</span>
                            <span>∶</span>
                            <span>{hospital}</span>
                        </div>
                        <div class="info-line last-line">
                            <span style="font-weight: bold;">体检日期</span>
                            <span>∶</span>
                            <span>{date_display}</span>
                        </div>
                    </div>
                    <div class="photo">
                        <img src="{img_url}" alt="持证人照片">
                    </div>
                </div>
            </div>
            <div class="cert-module middle-card">
                <div class="middle-line">{card2_text}</div>
                <div class="middle-line">健康证明</div>
            </div>
            <div class="bottom-card">
                <div class="qrcode-area">
                    <div class="qrcode-img">
                        <img src="data:image/png;base64,{qr_base64}" alt="防伪二维码">
                    </div>
                    <div class="qrcode-title">{card3_text}</div>
                </div>
            </div>
        </div>
        '''

cards_A = []
cards_B = []
cards_C = []
for issue in issues:
    if 'pull_request' in issue:
        continue
    card_a = build_card(issue, 'A')
    card_b = build_card(issue, 'B')
    card_c = build_card(issue, 'C')
    if card_a:
        cards_A.append(card_a)
    if card_b:
        cards_B.append(card_b)
    if card_c:
        cards_C.append(card_c)

# 合并三套卡片，按顺序排列
all_cards = []
for i in range(max(len(cards_A), len(cards_B), len(cards_C))):
    if i < len(cards_A):
        all_cards.append(cards_A[i])
    if i < len(cards_B):
        all_cards.append(cards_B[i])
    if i < len(cards_C):
        all_cards.append(cards_C[i])

html_B = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>健康证查询</title>
    <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft Yahei", sans-serif; background-color: #e9e9e9; padding: 10px; }}
        .cert-wrapper {{ max-width: 450px; margin: 0 auto 20px auto; position: relative; padding-bottom: 50px; }}
        .cert-module {{ background: #f8f8f8; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.35); width: 100%; height: 180px; }}
        .top-card {{ font-size: 11px; display: flex; flex-direction: column; height: 100%; margin-top: 5px; }}
        .top-title {{ text-align: center; font-size: 16px; color: #333; margin-top: 5px; margin-bottom: 10px; font-weight: bold; }}
        .top-content {{ display: flex; justify-content: space-between; align-items: flex-start; flex: 1; }}
        .text-container {{ width: 65%; display: flex; flex-direction: column; height: 100%; }}
        .info-line {{ margin-bottom: 6px; white-space: nowrap; display: flex; align-items: center; gap: 1px; }}
        .label {{}} .colon {{}} .content {{ font-weight: bold; }}
        .gender-separator {{ margin-left: 10px; }}
        .id-group {{ margin-bottom: 6px; }}
        .id-group .info-line {{ margin-bottom: 0; line-height: 1.2; }}
        .last-line {{ margin-top: auto; margin-bottom: 6px; }}
        .photo {{ width: 70px; height: 90px; border: 1px solid #ddd; margin-left: 10px; position: relative; overflow: visible; }}
        .photo img {{ width: 100%; height: 100%; object-fit: cover; }}
        .photo .seal-container {{ position: absolute; top: 44px; left: -47px; z-index: 999; }}
        .photo .seal-img {{ width: 63px; height: 63px; object-fit: contain; opacity: 1; display: block; }}
        .middle-card {{ display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 18px; color: #333; text-align: center; width: 100%; height: 180px; font-weight: bold; }}
        .middle-line {{ margin: 5px 0; }}
        .bottom-card {{ border-radius: 12px; padding: 20px; margin-bottom: 15px; font-size: 11px; text-align: center; background: #f8f8f8; box-shadow: 0 8px 16px rgba(0,0,0,0.35); }}
        .qrcode-area {{ text-align: center; margin-bottom: 15px; display: flex; flex-direction: column; align-items: center; }}
        .qrcode-img {{ width: 120px; height: 120px; margin: 0 auto 10px; }}
        .qrcode-img img {{ width: 100%; height: 100%; object-fit: contain; }}
        .qrcode-title {{ color: #333; margin-bottom: 0; font-size: 13px; font-weight: bold; }}
        
        .editable-field {{ border: 1px dashed #2b6ef0; border-radius: 4px; padding: 2px 6px; background: #fff; min-width: 40px; display: inline-block; }}
        .editable-field:focus {{ outline: none; border-color: #2f9e44; box-shadow: 0 0 0 2px rgba(47, 158, 68, 0.2); }}
        .not-found {{ text-align: center; padding: 40px 20px; font-size: 18px; color: #666; background: #f8f8f8; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .admin-bar {{ background: #fff; padding: 12px 16px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }}
        .admin-bar input[type="text"] {{ flex: 1; min-width: 120px; padding: 8px 12px; border: 1px solid #dce0e6; border-radius: 8px; font-size: 14px; outline: none; }}
        .admin-bar input:focus {{ border-color: #2b6ef0; }}
        .admin-bar .btn-danger {{ background: #e53e3e; color: #fff; border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; }}
        .admin-bar .btn-danger:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .admin-bar .btn-success {{ background: #2f9e44; color: #fff; border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; }}
        .admin-bar .checkbox-container {{ display: flex; align-items: center; gap: 6px; font-size: 13px; }}
        .admin-bar .checkbox-container input[type="checkbox"] {{ width: 16px; height: 16px; cursor: pointer; }}
        .admin-bar .badge {{ font-size: 12px; color: #666; }}
        .card-checkbox {{ position: absolute; top: 12px; left: 12px; z-index: 25; }}
        .card-checkbox input[type="checkbox"] {{ width: 18px; height: 18px; cursor: pointer; }}
        .button-group {{ position: absolute; bottom: 10px; right: 12px; display: flex; gap: 8px; z-index: 30; }}
        .button-group button {{ border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; }}
        .edit-status {{ position: absolute; bottom: 45px; right: 12px; font-size: 12px; z-index: 20; display: none; }}
        .edit-status.error {{ color: #e53e3e; }}
        .edit-status.success {{ color: #2f9e44; }}
        .hide-btn {{ position: absolute; top: 12px; right: 12px; z-index: 15; background: #e53e3e; color: #fff; border: none; border-radius: 50%; width: 24px; height: 24px; font-size: 14px; cursor: pointer; display: none; align-items: center; justify-content: center; line-height: 1; }}
        .hide-btn:hover {{ background: #c0392b; }}
        .admin-bar .btn-orange {{ background: #f39c12; color: #fff; border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; }}
    </style>
</head>
<body>
    <div id="app">
        <div id="adminBar" style="display: none;" class="admin-bar">
            <input type="text" id="searchInput" placeholder="🔍 搜索姓名..." />
            <div class="checkbox-container">
                <input type="checkbox" id="selectAll" />
                <label for="selectAll">全选</label>
            </div>
            <button class="btn-danger" id="batchDeleteBtn">删除数据</button>
            <button class="btn-orange" id="showAllBtn">显示全部</button>
            <span class="badge" id="batchStatus"></span>
        </div>
        
        <div id="cardsContainer">
            {''.join(all_cards)}
        </div>
        
        <div id="notFoundMessage" class="not-found" style="display: none;">未找到该健康证</div>
    </div>
    
    <script>
        (function() {{
            const params = new URLSearchParams(window.location.search);
            const idParam = params.get('id');
            const editParam = params.get('edit');
            
            const isAdmin = (editParam === '123456');
            const wrappers = document.querySelectorAll('.cert-wrapper');
            const notFound = document.getElementById('notFoundMessage');
            const adminBar = document.getElementById('adminBar');
            const searchInput = document.getElementById('searchInput');
            const selectAll = document.getElementById('selectAll');
            const batchDeleteBtn = document.getElementById('batchDeleteBtn');
            const showAllBtn = document.getElementById('showAllBtn');
            const batchStatus = document.getElementById('batchStatus');
            
            // 收集同一人的所有卡片
            function groupByPerson() {{
                const groups = {{}};
                wrappers.forEach(w => {{
                    const title = w.dataset.title;
                    if (!groups[title]) groups[title] = [];
                    groups[title].push(w);
                }});
                return groups;
            }}
            
            // ===== 管理员模式 =====
            if (isAdmin) {{
                adminBar.style.display = 'flex';
                document.querySelectorAll('.card-checkbox').forEach(cb => cb.style.display = 'block');
                document.querySelectorAll('.hide-btn').forEach(btn => btn.style.display = 'flex');
                
                if (idParam) {{
                    let decodedId = '';
                    try {{ decodedId = decodeURIComponent(idParam); }} catch(e) {{ decodedId = idParam; }}
                    let found = false;
                    wrappers.forEach(w => {{
                        const title = w.dataset.title;
                        if (title === decodedId) {{
                            w.style.display = 'block';
                            found = true;
                        }} else {{
                            w.style.display = 'none';
                        }}
                    }});
                    if (!found) {{
                        wrappers.forEach(w => w.style.display = 'none');
                        notFound.style.display = 'block';
                    }}
                }} else {{
                    wrappers.forEach(w => w.style.display = 'block');
                    notFound.style.display = 'none';
                }}
            }} else {{
                if (idParam) {{
                    let decodedId = '';
                    try {{ decodedId = decodeURIComponent(idParam); }} catch(e) {{ decodedId = idParam; }}
                    let found = false;
                    wrappers.forEach(w => {{
                        const title = w.dataset.title;
                        if (title === decodedId) {{
                            w.style.display = 'block';
                            found = true;
                        }} else {{
                            w.style.display = 'none';
                        }}
                    }});
                    if (!found) {{
                        wrappers.forEach(w => w.style.display = 'none');
                        notFound.style.display = 'block';
                    }}
                }} else {{
                    wrappers.forEach(w => w.style.display = 'block');
                    notFound.style.display = 'none';
                }}
            }}
            
            if (!isAdmin) return;
            
            // ===== 搜索 =====
            if (searchInput) {{
                searchInput.addEventListener('input', function() {{
                    const keyword = this.value.trim().toLowerCase();
                    wrappers.forEach(w => {{
                        const title = w.dataset.title.toLowerCase();
                        w.style.display = title.includes(keyword) ? 'block' : 'none';
                    }});
                }});
            }}
            
            // ===== 全选 =====
            if (selectAll) {{
                selectAll.addEventListener('change', function() {{
                    const checked = this.checked;
                    document.querySelectorAll('.card-select').forEach(cb => cb.checked = checked);
                    updateBatchStatus();
                }});
                document.addEventListener('change', function(e) {{
                    if (e.target.classList.contains('card-select')) {{
                        updateBatchStatus();
                        const all = document.querySelectorAll('.card-select');
                        const checked = document.querySelectorAll('.card-select:checked');
                        selectAll.checked = (all.length === checked.length && all.length > 0);
                    }}
                }});
            }}
            
            function updateBatchStatus() {{
                const checked = document.querySelectorAll('.card-select:checked');
                const persons = new Set();
                checked.forEach(cb => persons.add(cb.dataset.title));
                batchStatus.textContent = checked.length > 0 ? `已选 ${{checked.length}} 张卡片 (共 ${{persons.size}} 人)` : '';
            }}
            
            // ===== 删除数据 =====
            if (batchDeleteBtn) {{
                batchDeleteBtn.addEventListener('click', function() {{
                    const checked = document.querySelectorAll('.card-select:checked');
                    if (checked.length === 0) {{
                        alert('请至少选择一张卡片');
                        return;
                    }}
                    const persons = new Set();
                    checked.forEach(cb => persons.add(cb.dataset.title));
                    if (!confirm(`确定要删除选中的 ${{persons.size}} 个用户的所有数据吗？此操作不可恢复！`)) return;
                    
                    let token = localStorage.getItem('github_token');
                    if (!token) {{
                        token = prompt('请输入您的 GitHub Token（删除需要）:');
                        if (token) localStorage.setItem('github_token', token);
                    }}
                    if (!token) {{
                        batchStatus.textContent = '❌ 需要 Token';
                        batchStatus.style.color = '#e53e3e';
                        return;
                    }}
                    
                    batchDeleteBtn.disabled = true;
                    batchStatus.textContent = '⏳ 删除中...';
                    batchStatus.style.color = '#2b6ef0';
                    
                    const repo = 'merryAndrew/HealthCertificate';
                    let completed = 0;
                    let failed = 0;
                    const total = persons.size;
                    
                    persons.forEach(name => {{
                        // 找到该人的所有卡片，取第一个的 issue-number
                        const wrapper = document.querySelector(`.cert-wrapper[data-title="${{name}}"]`);
                        if (!wrapper) {{ failed++; return; }}
                        const issueNumber = wrapper.dataset.issueNumber;
                        const url = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                        fetch(url, {{
                            method: 'PATCH',
                            headers: {{
                                'Authorization': `Bearer ${{token}}`,
                                'Accept': 'application/vnd.github.v3+json',
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ state: 'closed' }})
                        }})
                        .then(res => {{
                            if (!res.ok) throw new Error('失败');
                            completed++;
                        }})
                        .catch(() => failed++)
                        .finally(() => {{
                            if (completed + failed === total) {{
                                batchStatus.textContent = `✅ 已删除 ${{completed}} 人，失败 ${{failed}} 人，正在刷新...`;
                                batchStatus.style.color = '#2f9e44';
                                batchDeleteBtn.disabled = false;
                                setTimeout(() => location.reload(), 2000);
                            }}
                        }});
                    }});
                }});
            }}
            
            // ===== 显示全部（取消隐藏） =====
            if (showAllBtn) {{
                showAllBtn.addEventListener('click', function() {{
                    const checked = document.querySelectorAll('.card-select:checked');
                    if (checked.length === 0) {{
                        alert('请至少选择一张卡片');
                        return;
                    }}
                    const persons = new Set();
                    checked.forEach(cb => persons.add(cb.dataset.title));
                    if (!confirm(`确定要恢复选中的 ${{persons.size}} 个用户的所有卡片吗？`)) return;
                    
                    let token = localStorage.getItem('github_token');
                    if (!token) {{
                        token = prompt('请输入您的 GitHub Token（操作需要）:');
                        if (token) localStorage.setItem('github_token', token);
                    }}
                    if (!token) {{
                        batchStatus.textContent = '❌ 需要 Token';
                        batchStatus.style.color = '#e53e3e';
                        return;
                    }}
                    
                    showAllBtn.disabled = true;
                    batchStatus.textContent = '⏳ 操作中...';
                    batchStatus.style.color = '#2b6ef0';
                    
                    const repo = 'merryAndrew/HealthCertificate';
                    let completed = 0;
                    let failed = 0;
                    const total = persons.size;
                    
                    persons.forEach(name => {{
                        const wrapper = document.querySelector(`.cert-wrapper[data-title="${{name}}"]`);
                        if (!wrapper) {{ failed++; return; }}
                        const issueNumber = wrapper.dataset.issueNumber;
                        // 获取当前 Issue 正文
                        const getUrl = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                        fetch(getUrl, {{
                            headers: {{
                                'Authorization': `Bearer ${{token}}`,
                                'Accept': 'application/vnd.github.v3+json',
                            }}
                        }})
                        .then(res => res.json())
                        .then(data => {{
                            let body = data.body || '';
                            // 移除隐藏卡片字段
                            body = body.replace(/\\n?隐藏卡片[：:][^\\n]*/, '');
                            body = body.replace(/隐藏卡片[：:][^\\n]*\\n?/, '');
                            // 更新 Issue
                            return fetch(getUrl, {{
                                method: 'PATCH',
                                headers: {{
                                    'Authorization': `Bearer ${{token}}`,
                                    'Accept': 'application/vnd.github.v3+json',
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify({{ body: body }})
                            }});
                        }})
                        .then(res => {{
                            if (!res.ok) throw new Error('失败');
                            completed++;
                        }})
                        .catch(() => failed++)
                        .finally(() => {{
                            if (completed + failed === total) {{
                                batchStatus.textContent = `✅ 已恢复 ${{completed}} 人，失败 ${{failed}} 人，正在刷新...`;
                                batchStatus.style.color = '#2f9e44';
                                showAllBtn.disabled = false;
                                setTimeout(() => location.reload(), 2000);
                            }}
                        }});
                    }});
                }});
            }}
            
            // ===== 单张卡片编辑 =====
            document.querySelectorAll('.edit-btn').forEach(btn => {{
                const wrapper = btn.closest('.cert-wrapper');
                const issueNumber = wrapper.dataset.issueNumber;
                const titleEl = document.getElementById('title_' + issueNumber);
                const nameEl = document.getElementById('name_' + issueNumber);
                const genderEl = document.getElementById('gender_' + issueNumber);
                const idEl = document.getElementById('id_' + issueNumber);
                const hospitalEl = document.getElementById('hospital_' + issueNumber);
                const dateEl = document.getElementById('date_' + issueNumber);
                const middleTextEl = document.getElementById('middleText_' + issueNumber);
                const bottomTextEl = document.getElementById('bottomText_' + issueNumber);
                const card1TitleEl = document.getElementById('card1Title_' + issueNumber);
                const card2TextEl = document.getElementById('card2Text_' + issueNumber);
                const card3TextEl = document.getElementById('card3Text_' + issueNumber);
                const saveBtn = document.getElementById('saveBtn_' + issueNumber);
                const cancelBtn = document.getElementById('cancelBtn_' + issueNumber);
                const editStatus = document.getElementById('editStatus_' + issueNumber);
                const hideBtn = document.getElementById('hideBtn_' + issueNumber);
                
                // 隐藏按钮
                if (hideBtn) {{
                    hideBtn.addEventListener('click', function() {{
                        const cardType = wrapper.dataset.cardType;
                        if (!confirm(`确定要隐藏这张 ${{cardType}} 版卡片吗？`)) return;
                        let token = localStorage.getItem('github_token');
                        if (!token) {{
                            token = prompt('请输入您的 GitHub Token（操作需要）:');
                            if (token) localStorage.setItem('github_token', token);
                        }}
                        if (!token) {{
                            if (editStatus) {{
                                editStatus.textContent = '❌ 需要 Token';
                                editStatus.className = 'edit-status error';
                                editStatus.style.display = 'block';
                            }}
                            return;
                        }}
                        const repo = 'merryAndrew/HealthCertificate';
                        const getUrl = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                        fetch(getUrl, {{
                            headers: {{
                                'Authorization': `Bearer ${{token}}`,
                                'Accept': 'application/vnd.github.v3+json',
                            }}
                        }})
                        .then(res => res.json())
                        .then(data => {{
                            let body = data.body || '';
                            let hidden = '';
                            const hiddenMatch = body.match(/隐藏卡片[：:]\s*(.+)/);
                            if (hiddenMatch) {{
                                let existing = hiddenMatch[1].trim();
                                if (existing) {{
                                    const parts = existing.split('|').map(s => s.trim());
                                    if (!parts.includes(cardType)) {{
                                        parts.push(cardType);
                                        hidden = parts.join('|');
                                    }} else {{
                                        hidden = existing;
                                    }}
                                }} else {{
                                    hidden = cardType;
                                }}
                                body = body.replace(/隐藏卡片[：:][^\\n]*/, `隐藏卡片：${{hidden}}`);
                            }} else {{
                                body += `\\n隐藏卡片：${{cardType}}`;
                            }}
                            return fetch(getUrl, {{
                                method: 'PATCH',
                                headers: {{
                                    'Authorization': `Bearer ${{token}}`,
                                    'Accept': 'application/vnd.github.v3+json',
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify({{ body: body }})
                            }});
                        }})
                        .then(res => {{
                            if (!res.ok) throw new Error('失败');
                            if (editStatus) {{
                                editStatus.textContent = '✅ 已隐藏，正在刷新...';
                                editStatus.className = 'edit-status success';
                                editStatus.style.display = 'block';
                            }}
                            setTimeout(() => location.reload(), 1500);
                        }})
                        .catch(err => {{
                            if (editStatus) {{
                                editStatus.textContent = '❌ ' + err.message;
                                editStatus.className = 'edit-status error';
                                editStatus.style.display = 'block';
                            }}
                        }});
                    }});
                }}
                
                btn.addEventListener('click', function() {{
                    const isEditing = btn.textContent === '取消编辑';
                    if (isEditing) {{
                        btn.textContent = '编辑';
                        saveBtn.style.display = 'none';
                        cancelBtn.style.display = 'none';
                        [titleEl, nameEl, genderEl, idEl, hospitalEl, dateEl, middleTextEl, bottomTextEl, card1TitleEl, card2TextEl, card3TextEl].forEach(el => {{
                            if (el) {{
                                el.contentEditable = false;
                                el.classList.remove('editable-field');
                            }}
                        }});
                        if (genderEl) {{
                            const select = genderEl.querySelector('.gender-select');
                            if (select) {{
                                genderEl.innerHTML = select.value;
                            }}
                        }}
                        editStatus.style.display = 'none';
                        return;
                    }}
                    
                    btn.textContent = '取消编辑';
                    saveBtn.style.display = 'inline-block';
                    cancelBtn.style.display = 'inline-block';
                    [titleEl, nameEl, genderEl, idEl, hospitalEl, dateEl, middleTextEl, bottomTextEl, card1TitleEl, card2TextEl, card3TextEl].forEach(el => {{
                        if (el) {{
                            el.contentEditable = true;
                            el.classList.add('editable-field');
                        }}
                    }});
                    if (genderEl) {{
                        const currentGender = genderEl.textContent.trim();
                        genderEl.contentEditable = false;
                        genderEl.innerHTML = `<select class="gender-select" style="padding:2px 6px;border-radius:4px;border:1px solid #2b6ef0;font-size:13px;">
                            <option value="男" ${{currentGender === '男' ? 'selected' : ''}}>男</option>
                            <option value="女" ${{currentGender === '女' ? 'selected' : ''}}>女</option>
                        </select>`;
                    }}
                    editStatus.textContent = '编辑中...';
                    editStatus.className = 'edit-status';
                    editStatus.style.display = 'block';
                }});
                
                if (cancelBtn) {{
                    cancelBtn.addEventListener('click', function() {{
                        location.reload();
                    }});
                }}
                
                if (saveBtn) {{
                    saveBtn.addEventListener('click', function() {{
                        const newName = nameEl ? nameEl.textContent.trim() : '';
                        let newGender = '';
                        const genderSelect = genderEl ? genderEl.querySelector('.gender-select') : null;
                        if (genderSelect) {{
                            newGender = genderSelect.value;
                        }} else {{
                            newGender = genderEl ? genderEl.textContent.trim() : '男';
                        }}
                        const newId = idEl ? idEl.textContent.trim() : '';
                        const newHospital = hospitalEl ? hospitalEl.textContent.trim() : '广州东仁医院';
                        const newDate = dateEl ? dateEl.textContent.trim() : '';
                        const newMiddle = middleTextEl ? middleTextEl.textContent.trim() : '广东省食品从业人员';
                        const newBottom = bottomTextEl ? bottomTextEl.textContent.trim() : '此健康信息已上报平台';
                        const newCard1Title = card1TitleEl ? card1TitleEl.textContent.trim() : '广东省食品从业人员健康证明';
                        const newCard2Text = card2TextEl ? card2TextEl.textContent.trim() : '广东省食品从业人员';
                        const newCard3Text = card3TextEl ? card3TextEl.textContent.trim() : '此健康信息已上报平台';
                        
                        const imgUrl = wrapper.querySelector('.photo img')?.src || '';
                        let avatarField = '';
                        if (imgUrl && !imgUrl.includes('placeholder')) {{
                            avatarField = `\\n头像图片：${{imgUrl}}`;
                        }}
                        
                        let token = localStorage.getItem('github_token');
                        if (!token) {{
                            token = prompt('请输入您的 GitHub Token（编辑需要）:');
                            if (token) localStorage.setItem('github_token', token);
                        }}
                        if (!token) {{
                            editStatus.textContent = '❌ 需要 Token';
                            editStatus.className = 'edit-status error';
                            return;
                        }}
                        
                        const repo = 'merryAndrew/HealthCertificate';
                        const url = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                        const body = `姓名：${{newName}}\\n性别：${{newGender}}\\n身份证：${{newId}}\\n体检单位：${{newHospital}}\\n体检日期：${{newDate}}\\n中间文字：${{newMiddle}}\\n底部文字：${{newBottom}}\\n卡片1标题：${{newCard1Title}}\\n卡片2文字：${{newCard2Text}}\\n卡片3文字：${{newCard3Text}}${{avatarField}}`;
                        
                        editStatus.textContent = '⏳ 保存中...';
                        editStatus.className = 'edit-status';
                        
                        fetch(url, {{
                            method: 'PATCH',
                            headers: {{
                                'Authorization': `Bearer ${{token}}`,
                                'Accept': 'application/vnd.github.v3+json',
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ title: newName, body: body }})
                        }})
                        .then(res => {{
                            if (!res.ok) throw new Error('保存失败: ' + res.status);
                            return res.json();
                        }})
                        .then(() => {{
                            editStatus.textContent = '✅ 保存成功！正在重新生成...';
                            editStatus.className = 'edit-status success';
                            [titleEl, nameEl, genderEl, idEl, hospitalEl, dateEl, middleTextEl, bottomTextEl, card1TitleEl, card2TextEl, card3TextEl].forEach(el => {{
                                if (el) {{
                                    el.contentEditable = false;
                                    el.classList.remove('editable-field');
                                }}
                            }});
                            if (genderSelect) {{
                                genderEl.innerHTML = genderSelect.value;
                            }}
                            btn.textContent = '编辑';
                            saveBtn.style.display = 'none';
                            cancelBtn.style.display = 'none';
                            setTimeout(() => {{
                                editStatus.textContent = '🔄 刷新查看更新';
                            }}, 3000);
                        }})
                        .catch(err => {{
                            editStatus.textContent = '❌ ' + err.message;
                            editStatus.className = 'edit-status error';
                        }});
                    }});
                }}
            }});
        }})();
    </script>
</body>
</html>'''

html_A = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>健康证服务-证件查询</title>
    <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft Yahei", sans-serif; background-color: #e0d6c7; padding: 10px; min-height: 100vh; }}
        .app-wrapper {{ max-width: 450px; margin: 0 auto; }}
        .photo .seal-container {{ position: absolute !important; top: 44px !important; left: -47px !important; z-index: 999 !important; }}
        .photo .seal-img {{ width: 63px !important; height: 63px !important; object-fit: contain !important; opacity: 1 !important; display: block !important; }}
        .cert-module {{ background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 100%; height: 180px; }}
        .top-card {{ font-size: 11px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .top-title {{ text-align: center; font-size: 16px; color: #333; font-weight: bold; }}
        .top-content {{ display: flex; justify-content: space-between; align-items: flex-start; }}
        .text-container {{ width: 65%; }}
        .info-line {{ margin-bottom: 8px; white-space: nowrap; display: flex; align-items: center; gap: 1px; }}
        .id-group {{ margin-bottom: 8px; }}
        .id-group .info-line {{ margin-bottom: 0; line-height: 1.2; }}
        .last-line {{ margin-bottom: 0; }}
        .photo {{ width: 70px; height: 90px; border: 1px solid #ddd; margin-left: 10px; position: relative !important; overflow: visible !important; }}
        .photo img[alt="持证人照片"] {{ width: 100%; height: 100%; object-fit: cover; position: relative; z-index: 1; }}
        .middle-card {{ display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 18px; color: #333; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .middle-line {{ margin: 5px 0; }}
        .bottom-card {{ background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); font-size: 11px; }}
        .qrcode-area {{ text-align: center; margin-bottom: 15px; }}
        .qrcode-title {{ color: #333; margin-bottom: 10px; font-size: 13px; }}
        .qrcode-img {{ width: 140px; height: 140px; margin: 0 auto; }}
        .qrcode-img img {{ width: 100%; height: 100%; object-fit: contain; }}
        .notice {{ background-color: #fffbeb; border: 1px solid #ffeeba; border-radius: 8px; padding: 12px; font-size: 10px; }}
        .notice-title {{ color: #856404; font-weight: bold; margin-bottom: 6px; display: flex; align-items: center; }}
        .exclamation-icon {{ margin-right: 5px; font-size: 12px; }}
        .notice-content {{ color: #856404; line-height: 1.4; }}
        .gender-separator {{ margin-left: 15px; }}
        .cert-wrapper {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="app-wrapper">
        {''.join(all_cards)}
    </div>
    <script>
        (function() {{
            const params = new URLSearchParams(window.location.search);
            const id = params.get('id');
            if (id) {{
                const wrappers = document.querySelectorAll('.cert-wrapper');
                let found = false;
                wrappers.forEach(w => {{
                    const title = w.getAttribute('data-title');
                    if (title === id) {{
                        w.style.display = 'block';
                        found = true;
                    }} else {{
                        w.style.display = 'none';
                    }}
                }});
                if (!found) {{
                    wrappers.forEach(w => w.style.display = 'block');
                }}
            }}
        }})();
    </script>
</body>
</html>'''

os.makedirs('dist', exist_ok=True)
with open('dist/index.html', 'w', encoding='utf-8') as f:
    f.write(html_B)
with open('dist/card.html', 'w', encoding='utf-8') as f:
    f.write(html_A)

if os.path.exists('upload.html'):
    shutil.copy('upload.html', 'dist/upload.html')
    print("✅ 已复制 upload.html 到发布目录")
else:
    print("⚠️ 未找到 upload.html，请确保该文件与 generate.py 在同一目录")

print("✅ 生成成功！已生成 index.html (B样式)、card.html (A样式) 和 upload.html（若存在）")
