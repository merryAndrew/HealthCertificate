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

url = f'https://api.github.com/repos/{REPO}/issues?state=all&per_page=100'
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

    # 检测卡片是否被标记为删除
    deleted_match = re.search(r'删除卡片[：:]\s*(.+)', all_text)
    is_deleted = deleted_match.group(1).strip() if deleted_match else '否'

    # 如果卡片被标记删除，返回空字符串（不显示）
    if is_deleted == '是':
        return ''

    if style == 'A':
        return f'''
        <div class="cert-wrapper" data-title="{title}">
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
                <div class="middle-line">广东省食品从业人员</div>
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
        <div class="cert-wrapper" data-title="{title}" data-body="{body}" data-issue-number="{issue['number']}" style="position: relative;">
            <!-- 编辑按钮（默认隐藏） -->
            <button id="editBtn_{issue['number']}" class="edit-btn" style="display: none; position: absolute; bottom: 12px; right: 12px; background: #2b6ef0; color: #fff; border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; z-index: 20;">编辑</button>
            <button id="saveBtn_{issue['number']}" class="save-btn" style="display: none; position: absolute; bottom: 12px; right: 100px; background: #2f9e44; color: #fff; border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; z-index: 20;">保存</button>
            <button id="deleteBtn_{issue['number']}" class="delete-btn" style="display: none; position: absolute; bottom: 12px; right: 180px; background: #e53e3e; color: #fff; border: none; border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; z-index: 20;">删除卡片</button>
            <div id="editStatus_{issue['number']}" style="display: none; position: absolute; bottom: 52px; right: 12px; font-size: 12px; color: #2b6ef0; z-index: 20;"></div>
            
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
                <div class="middle-line">广东省食品从业人员</div>
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
    card_A = build_card(issue, 'A')
    card_B = build_card(issue, 'B')
    if card_A:
        cards_A.append(card_A)
    if card_B:
        cards_B.append(card_B)

cards_A.reverse()
cards_B.reverse()

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
        .cert-wrapper {{ max-width: 450px; margin: 0 auto 20px auto; position: relative; }}
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
    </style>
</head>
<body>
    {''.join(cards_B)}
    
    <script>
        (function() {{
            const params = new URLSearchParams(window.location.search);
            const editParam = params.get('edit');
            const isEditor = (editParam === '123456');
            
            if (!isEditor) return;
            
            document.querySelectorAll('.edit-btn').forEach(btn => {{
                btn.style.display = 'inline-block';
            }});
            document.querySelectorAll('.delete-btn').forEach(btn => {{
                btn.style.display = 'inline-block';
            }});
            
            // 编辑功能
            document.querySelectorAll('.edit-btn').forEach(btn => {{
                const wrapper = btn.closest('.cert-wrapper');
                const issueNumber = wrapper.dataset.issueNumber;
                const titleEl = document.getElementById('title_' + issueNumber);
                const nameEl = document.getElementById('name_' + issueNumber);
                const genderEl = document.getElementById('gender_' + issueNumber);
                const idEl = document.getElementById('id_' + issueNumber);
                const dateEl = document.getElementById('date_' + issueNumber);
                const saveBtn = document.getElementById('saveBtn_' + issueNumber);
                const deleteBtn = document.getElementById('deleteBtn_' + issueNumber);
                const editStatus = document.getElementById('editStatus_' + issueNumber);
                
                btn.addEventListener('click', function() {{
                    [titleEl, nameEl, genderEl, idEl, dateEl].forEach(el => {{
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
                    
                    saveBtn.style.display = 'inline-block';
                    deleteBtn.style.display = 'none';
                    btn.style.display = 'none';
                    editStatus.textContent = '点击保存修改';
                    editStatus.style.display = 'block';
                }});
                
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
                    
                    const body = `姓名：${{newName}}\\n性别：${{newGender}}\\n身份证：${{newId}}\\n体检日期：${{newDate}}`;
                    
                    let token = localStorage.getItem('github_token');
                    if (!token) {{
                        token = prompt('请输入您的 GitHub Token（编辑需要）:');
                        if (token) localStorage.setItem('github_token', token);
                    }}
                    if (!token) {{
                        editStatus.textContent = '❌ 需要 Token 才能保存';
                        editStatus.style.color = '#e53e3e';
                        return;
                    }}
                    
                    const repo = 'merryAndrew/HealthCertificate';
                    const url = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                    
                    editStatus.textContent = '⏳ 保存中...';
                    editStatus.style.color = '#2b6ef0';
                    
                    fetch(url, {{
                        method: 'PATCH',
                        headers: {{
                            'Authorization': `Bearer ${{token}}`,
                            'Accept': 'application/vnd.github.v3+json',
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            body: body
                        }})
                    }})
                    .then(res => {{
                        if (!res.ok) throw new Error('保存失败: ' + res.status);
                        return res.json();
                    }})
                    .then(data => {{
                        editStatus.textContent = '✅ 保存成功！正在重新生成...';
                        editStatus.style.color = '#2f9e44';
                        [titleEl, nameEl, idEl, dateEl].forEach(el => {{
                            if (el) {{
                                el.contentEditable = false;
                                el.classList.remove('editable-field');
                            }}
                        }});
                        if (genderSelect) {{
                            const genderVal = genderSelect.value;
                            genderEl.innerHTML = genderVal;
                        }}
                        saveBtn.style.display = 'none';
                        deleteBtn.style.display = 'inline-block';
                        btn.style.display = 'inline-block';
                        editStatus.textContent = '⏳ 等待 Actions 重新生成（约1-2分钟）...';
                        editStatus.style.color = '#b36b1e';
                        setTimeout(() => {{
                            editStatus.textContent = '🔄 刷新页面查看更新';
                            editStatus.style.color = '#2b6ef0';
                        }}, 3000);
                    }})
                    .catch(err => {{
                        editStatus.textContent = '❌ ' + err.message;
                        editStatus.style.color = '#e53e3e';
                    }});
                }});
            }});
            
            // 删除卡片功能
            document.querySelectorAll('.delete-btn').forEach(btn => {{
                const wrapper = btn.closest('.cert-wrapper');
                const issueNumber = wrapper.dataset.issueNumber;
                const editStatus = document.getElementById('editStatus_' + issueNumber);
                
                btn.addEventListener('click', function() {{
                    if (!confirm('确定要删除这张卡片吗？删除后不可恢复。')) return;
                    
                    let token = localStorage.getItem('github_token');
                    if (!token) {{
                        token = prompt('请输入您的 GitHub Token（删除需要）:');
                        if (token) localStorage.setItem('github_token', token);
                    }}
                    if (!token) {{
                        editStatus.textContent = '❌ 需要 Token 才能删除';
                        editStatus.style.color = '#e53e3e';
                        return;
                    }}
                    
                    const body = `删除卡片：是`;
                    const repo = 'merryAndrew/HealthCertificate';
                    const url = `https://api.github.com/repos/${{repo}}/issues/${{issueNumber}}`;
                    
                    editStatus.textContent = '⏳ 删除中...';
                    editStatus.style.color = '#e53e3e';
                    
                    fetch(url, {{
                        method: 'PATCH',
                        headers: {{
                            'Authorization': `Bearer ${{token}}`,
                            'Accept': 'application/vnd.github.v3+json',
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            body: body
                        }})
                    }})
                    .then(res => {{
                        if (!res.ok) throw new Error('删除失败: ' + res.status);
                        return res.json();
                    }})
                    .then(data => {{
                        editStatus.textContent = '✅ 删除成功！正在重新生成...';
                        editStatus.style.color = '#2f9e44';
                        // 直接隐藏卡片
                        wrapper.style.display = 'none';
                        setTimeout(() => {{
                            location.reload();
                        }}, 2000);
                    }})
                    .catch(err => {{
                        editStatus.textContent = '❌ ' + err.message;
                        editStatus.style.color = '#e53e3e';
                    }});
                }});
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
        .qr-area-hidden {{ display: none; }}
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
