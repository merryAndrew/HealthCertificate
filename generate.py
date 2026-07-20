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

# 只获取未关闭的 Issue（open）
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
    title = issue['title']
    body = issue['body'] or ''
    comments_url = issue['comments_url']
    comments = requests.get(comments_url, headers=headers).json()
    all_text = body
    for comment in comments:
        all_text += ' ' + comment.get('body', '')

    name = title

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

    middle_text_match = re.search(r'中间文字[：:]\s*(.+)', all_text)
    middle_text = middle_text_match.group(1).strip() if middle_text_match else '广东省食品从业人员'

    img_url = extract_first_image(all_text)
    if not img_url:
        img_url = 'https://via.placeholder.com/70x90?text=No+Photo'
    print(f"📸 标题 '{title}' 的图片链接: {img_url}")

    encoded_title = urllib.parse.quote(title)
    page_url = f'https://{USER}.github.io/{REPO_NAME}/index.html?id={encoded_title}'
    qr = qrcode.make(page_url)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    if style == 'A':
        return f'''
        <div class="cert-wrapper" data-title="{title}" data-issue-number="{issue['number']}">
            <div class="cert-module top-card">
                <div class="top-title">广东省食品从业人员健康证明</div>
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
                            <span>广州东仁医院</span>
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
                <div class="middle-line">{middle_text}</div>
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
                    <div class="notice-content">目前实体证明申请的入口已经关闭，全面推广电子证，请广大从业人员和用人单位积极使用。如对查询信息存疑，请与体检机构联系。</div>
                </div>
            </div>
        </div>
        '''
    else:
        return f'''
        <div class="cert-wrapper" data-title="{title}" data-issue-number="{issue['number']}" style="position: relative; padding-bottom: 60px;">
            <div class="cert-module top-card">
                <div class="top-title" id="title_{issue['number']}">广东省食品从业人员健康证明</div>
                <div class="top-content">
                    <div class="text-container">
                        <div class="info-line">
                            <span class="label">姓 名</span>
                            <span class="colon">∶</span>
                            <span class="content" id="name_{issue['number']}">{name}</span>
                        </div>
                        <div class="info-line">
                            <span class="label">性 别</span>
                            <span class="colon">∶</span>
                            <span class="content" id="gender_{issue['number']}">{gender}</span>
                        </div>
                        <div class="id-group">
                            <div class="info-line">
                                <span class="label">身份证号码</span>
                                <span class="colon">∶</span>
                                <span class="content" id="id_{issue['number']}">{id_num}</span>
                            </div>
                            <div class="info-line">(或其它有效证明)</div>
                        </div>
                        <div class="info-line">
                            <span class="label">体检单位</span>
                            <span class="colon">∶</span>
                            <span class="content">广州东仁医院</span>
                        </div>
                        <div class="info-line last-line">
                            <span class="label">体检日期</span>
                            <span class="colon">∶</span>
                            <span class="content" id="date_{issue['number']}">{date_display}</span>
                        </div>
                    </div>
                    <div class="photo">
                        <img src="{img_url}" alt="持证人照片">
                    </div>
                </div>
            </div>
            <div class="cert-module middle-card">
                <div class="middle-line" id="middleText_{issue['number']}">{middle_text}</div>
                <div class="middle-line">健康证明</div>
            </div>
            <div class="bottom-card">
                <div class="qrcode-area">
                    <div class="qrcode-img">
                        <img src="data:image/png;base64,{qr_base64}" alt="防伪二维码">
                    </div>
                    <div class="qrcode-title">此健康信息已上报平台</div>
                </div>
            </div>
        </div>
        '''

cards_A = []
cards_B = []
for issue in issues:
    if 'pull_request' in issue:
        continue
    cards_A.append(build_card(issue, 'A'))
    cards_B.append(build_card(issue, 'B'))

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
        .cert-wrapper {{ max-width: 450px; margin: 0 auto 20px auto; position: relative; padding-bottom: 60px; }}
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
        .photo {{ width: 70px; height: 90px; border: 1px solid #ddd; margin-left: 10px; }}
        .photo img {{ width: 100%; height: 100%; object-fit: cover; }}
        .middle-card {{ display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 18px; color: #333; text-align: center; width: 100%; height: 180px; font-weight: bold; }}
        .middle-line {{ margin: 5px 0; }}
        .bottom-card {{ border-radius: 12px; padding: 20px; margin-bottom: 15px; font-size: 11px; text-align: center; background: #f8f8f8; box-shadow: 0 8px 16px rgba(0,0,0,0.35); }}
        .qrcode-area {{ text-align: center; margin-bottom: 15px; display: flex; flex-direction: column; align-items: center; }}
        .qrcode-img {{ width: 120px; height: 120px; margin: 0 auto 10px; }}
        .qrcode-img img {{ width: 100%; height: 100%; object-fit: contain; }}
        .qrcode-title {{ color: #333; margin-bottom: 0; font-size: 13px; font-weight: bold; }}
        
        .editable-field {{
            border: 1px dashed #2b6ef0;
            border-radius: 4px;
            padding: 2px 6px;
            background: #fff;
            min-width: 40px;
            display: inline-block;
        }}
        .editable-field:focus {{
            outline: none;
            border-color: #2f9e44;
            box-shadow: 0 0 0 2px rgba(47, 158, 68, 0.2);
        }}
        .not-found {{
            text-align: center;
            padding: 40px 20px;
            font-size: 18px;
            color: #666;
            background: #f8f8f8;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .admin-bar {{
            background: #fff;
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
        }}
        .admin-bar input {{
            flex: 1;
            min-width: 150px;
            padding: 8px 12px;
            border: 1px solid #dce0e6;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
        }}
        .admin-bar input:focus {{
            border-color: #2b6ef0;
        }}
        .admin-bar .btn-danger {{
            background: #e53e3e;
            color: #fff;
            border: none;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 13px;
            cursor: pointer;
        }}
        .admin-bar .btn-danger:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .admin-bar .btn-primary {{
            background: #2b6ef0;
            color: #fff;
            border: none;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 13px;
            cursor: pointer;
        }}
        .admin-bar .btn-success {{
            background: #2f9e44;
            color: #fff;
            border: none;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 13px;
            cursor: pointer;
        }}
        .checkbox-container {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #333;
        }}
        .checkbox-container input[type="checkbox"] {{
            width: 16px;
            height: 16px;
            cursor: pointer;
        }}
        .card-checkbox {{
            position: absolute;
            top: 12px;
            left: 12px;
            z-index: 25;
        }}
        .card-checkbox input[type="checkbox"] {{
            width: 18px;
            height: 18px;
            cursor: pointer;
        }}
        .edit-btn, .save-btn, .delete-btn, .cancel-btn {{
            border: none;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 13px;
            cursor: pointer;
        }}
        .edit-btn {{ background: #2b6ef0; color: #fff; }}
        .save-btn {{ background: #2f9e44; color: #fff; }}
        .delete-btn {{ background: #e53e3e; color: #fff; }}
        .cancel-btn {{ background: #6c757d; color: #fff; }}
        .button-group {{
            position: absolute;
            bottom: 10px;
            left: 12px;
            right: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 30;
        }}
        .button-group.hidden {{ display: none; }}
        .edit-status {{
            position: absolute;
            bottom: 50px;
            right: 12px;
            font-size: 12px;
            color: #2b6ef0;
            z-index: 20;
            display: none;
        }}
        .edit-status.error {{ color: #e53e3e; }}
        .edit-status.success {{ color: #2f9e44; }}
    </style>
</head>
<body>
    <div id="app">
        <!-- 管理员栏（超级管理员） -->
        <div id="adminBar" style="display: none;" class="admin-bar">
            <input type="text" id="searchInput" placeholder="🔍 搜索姓名..." />
            <div class="checkbox-container">
                <input type="checkbox" id="selectAll" />
                <label for="selectAll">全选</label>
            </div>
            <button class="btn-danger" id="batchDeleteBtn">删除选中</button>
            <span id="batchStatus" style="font-size: 12px; color: #666;"></span>
        </div>
        
        <!-- 卡片列表 -->
        <div id="cardsContainer">
            {''.join(cards_B)}
        </div>
        
        <!-- 未找到提示 -->
        <div id="notFoundMessage" class="not-found" style="display: none;">未找到该健康证</div>
    </div>
    
    <script>
        (function() {{
            const params = new URLSearchParams(window.location.search);
            const idParam = params.get('id');
            const editParam = params.get('edit');
            const adminParam = params.get('admin');
            
            const wrappers = document.querySelectorAll('.cert-wrapper');
            const notFound = document.getElementById('notFoundMessage');
            const adminBar = document.getElementById('adminBar');
            const searchInput = document.getElementById('searchInput');
            const selectAll = document.getElementById('selectAll');
            const batchDeleteBtn = document.getElementById('batchDeleteBtn');
            const batchStatus = document.getElementById('batchStatus');
            
            // ===== 判断角色 =====
            const isSuperAdmin = (adminParam === '888888');
            const isNormalAdmin = (editParam === '123456');
            const hasAdmin = isSuperAdmin || isNormalAdmin;
            
            // ===== 超级管理员：显示所有卡片，显示管理栏 =====
            if (isSuperAdmin) {{
                adminBar.style.display = 'flex';
                wrappers.forEach(w => {{
                    w.style.display = 'block';
                    // 添加复选框
                    const cb = document.createElement('div');
                    cb.className = 'card-checkbox';
                    cb.innerHTML = `<input type="checkbox" class="card-select" data-issue="$${{w.dataset.issueNumber}}" data-title="$${{w.dataset.title}}" />`;
                    w.prepend(cb);
                    // 在超级管理员模式下，显示编辑按钮
                    const editBtn = w.querySelector('.edit-btn');
                    if (editBtn) editBtn.style.display = 'block';
                }});
                notFound.style.display = 'none';
            }}
            
            // ===== 普通管理员：只显示匹配的卡片 =====
            if (isNormalAdmin && idParam) {{
                let decodedId = '';
                try {{ decodedId = decodeURIComponent(idParam); }} catch(e) {{ decodedId = idParam; }}
                let found = false;
                wrappers.forEach(w => {{
                    const title = w.dataset.title;
                    if (title === decodedId) {{
                        w.style.display = 'block';
                        found = true;
                        // 显示编辑按钮
                        const editBtn = w.querySelector('.edit-btn');
                        if (editBtn) editBtn.style.display = 'block';
                    }} else {{
                        w.style.display = 'none';
                    }}
                }});
                if (!found) {{
                    wrappers.forEach(w => w.style.display = 'none');
                    notFound.style.display = 'block';
                }}
            }}
            
            // ===== 没有管理员：只按 id 过滤（普通用户） =====
            if (!hasAdmin && idParam) {{
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
            }}
            
            // ===== 如果没有任何管理员且没有 id，显示所有卡片 =====
            if (!hasAdmin && !idParam) {{
                wrappers.forEach(w => w.style.display = 'block');
            }}
            
            // ===== 如果只有普通管理员但没有 id，显示所有卡片（但无编辑权限） =====
            if (isNormalAdmin && !idParam) {{
                wrappers.forEach(w => w.style.display = 'block');
            }}
            
            // ===== 只有管理员才能看到编辑功能 =====
            if (!hasAdmin) return;
            
            // ===== 超级管理员搜索 =====
            if (isSuperAdmin && searchInput) {{
                searchInput.addEventListener('input', function() {{
                    const keyword = this.value.trim().toLowerCase();
                    wrappers.forEach(w => {{
                        const title = w.dataset.title.toLowerCase();
                        w.style.display = title.includes(keyword) ? 'block' : 'none';
                    }});
                }});
            }}
            
            // ===== 全选/取消全选 =====
            if (isSuperAdmin && selectAll) {{
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
                batchStatus.textContent = `已选 ${{checked.length}} 张`;
            }}
            
            // ===== 批量删除 =====
            if (isSuperAdmin && batchDeleteBtn) {{
                batchDeleteBtn.addEventListener('click', function() {{
                    const checked = document.querySelectorAll('.card-select:checked');
                    if (checked.length === 0) {{
                        alert('请至少选择一张卡片');
                        return;
                    }}
                    if (!confirm(`确定要删除选中的 ${{checked.length}} 张卡片吗？此操作不可恢复！`)) return;
                    
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
                    const total = checked.length;
                    
                    checked.forEach(cb => {{
                        const issueNumber = cb.dataset.issue;
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
                                batchStatus.textContent = `✅ 已删除 ${{completed}} 张，失败 ${{failed}} 张，正在刷新...`;
                                batchStatus.style.color = '#2f9e44';
                                batchDeleteBtn.disabled = false;
                                setTimeout(() => location.reload(), 2000);
                            }}
                        }});
                    }});
                }});
            }}
            
            // ===== 单张卡片编辑功能 =====
            document.querySelectorAll('.edit-btn').forEach(btn => {{
                const wrapper = btn.closest('.cert-wrapper');
                const issueNumber = wrapper.dataset.issueNumber;
                const titleEl = document.getElementById('title_' + issueNumber);
                const nameEl = document.getElementById('name_' + issueNumber);
                const genderEl = document.getElementById('gender_' + issueNumber);
                const idEl = document.getElementById('id_' + issueNumber);
                const dateEl = document.getElementById('date_' + issueNumber);
                const middleTextEl = document.getElementById('middleText_' + issueNumber);
                const group = document.getElementById('buttonGroup_' + issueNumber);
                const saveBtn = document.getElementById('saveBtn_' + issueNumber);
                const deleteBtn = document.getElementById('deleteBtn_' + issueNumber);
                const cancelBtn = document.getElementById('cancelBtn_' + issueNumber);
                const editStatus = document.getElementById('editStatus_' + issueNumber);
                
                if (!group) return;
                
                btn.addEventListener('click', function() {{
                    btn.style.display = 'none';
                    group.classList.remove('hidden');
                    [titleEl, nameEl, genderEl, idEl, dateEl, middleTextEl].forEach(el => {{
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
                    editStatus.style.display = 'block';
                }});
                
                if (cancelBtn) {{
                    cancelBtn.addEventListener('click', function() {{
                        location.reload();
                    }});
                }}
                
                if (saveBtn) {{
                    saveBtn.addEventListener('click', function() {{
                        const newTitle = titleEl ? titleEl.textContent.trim() : '广东省食品从业人员健康证明';
                        const newName = nameEl ? nameEl.textContent.trim() : '';
                        let newGender = '';
                        const genderSelect = genderEl ? genderEl.querySelector('.gender-select') : null;
                        if (genderSelect) {{
                            newGender = genderSelect.value;
                        }} else {{
                            newGender = genderEl ? genderEl.textContent.trim() : '男';
                        }}
                        const newId = idEl ? idEl.textContent.trim() : '';
                        const newDate = dateEl ? dateEl.textContent.trim() : '';
                        const newMiddle = middleTextEl ? middleTextEl.textContent.trim() : '广东省食品从业人员';
                        
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
                        const body = `姓名：${{newName}}\\n性别：${{newGender}}\\n身份证：${{newId}}\\n体检日期：${{newDate}}\\n中间文字：${{newMiddle}}`;
                        
                        editStatus.textContent = '⏳ 保存中...';
                        editStatus.className = 'edit-status';
                        
                        fetch(url, {{
                            method: 'PATCH',
                            headers: {{
                                'Authorization': `Bearer ${{token}}`,
                                'Accept': 'application/vnd.github.v3+json',
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ title: newTitle, body: body }})
                        }})
                        .then(res => {{
                            if (!res.ok) throw new Error('保存失败: ' + res.status);
                            return res.json();
                        }})
                        .then(() => {{
                            editStatus.textContent = '✅ 保存成功！正在重新生成...';
                            editStatus.className = 'edit-status success';
                            [titleEl, nameEl, idEl, dateEl, middleTextEl].forEach(el => {{
                                if (el) {{
                                    el.contentEditable = false;
                                    el.classList.remove('editable-field');
                                }}
                            }});
                            if (genderSelect) {{
                                genderEl.innerHTML = genderSelect.value;
                            }}
                            group.classList.add('hidden');
                            btn.style.display = 'block';
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
                
                if (deleteBtn) {{
                    deleteBtn.addEventListener('click', function() {{
                        if (!confirm('确定删除此卡片？不可恢复。')) return;
                        let token = localStorage.getItem('github_token');
                        if (!token) {{
                            token = prompt('请输入您的 GitHub Token（删除需要）:');
                            if (token) localStorage.setItem('github_token', token);
                        }}
                        if (!token) {{
                            editStatus.textContent = '❌ 需要 Token';
                            editStatus.className = 'edit-status error';
                            return;
                        }}
                        const repo = 'merryAndrew/HealthCertificate';
                        const url = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                        editStatus.textContent = '⏳ 删除中...';
                        editStatus.className = 'edit-status';
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
                            if (!res.ok) throw new Error('删除失败');
                            return res.json();
                        }})
                        .then(() => {{
                            editStatus.textContent = '✅ 已删除，正在刷新...';
                            editStatus.className = 'edit-status success';
                            setTimeout(() => location.reload(), 1500);
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
        {''.join(cards_A)}
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
