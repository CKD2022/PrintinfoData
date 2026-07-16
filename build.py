import os
import re
import json
import datetime
from jinja2 import Template

POSTS_DIR = 'posts'
OUTPUT_DIR = 'docs'
SUMMARIES_FILE = os.path.join(POSTS_DIR, 'summaries.json')
ORDER_FILE = os.path.join(POSTS_DIR, 'order.json')

BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - 印务中心生产数据</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600&display=swap');
        :root {
            --bg: #f8fafc;
            --text: #0f172a;
            --muted: #64748b;
            --accent: #2563eb;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --nav-bg: rgba(255,255,255,0.75);
            --content-max-width: 100%;
            --footer-border: #e2e8f0;
        }
        body.dark { --bg: #1e293b; --text: #f1f5f9; --muted: #94a3b8; --card-bg: #334155; --border: #475569; --nav-bg: rgba(30,41,59,0.8); --footer-border: #475569; }
        body.light-gray { --bg: #f1f5f9; --text: #1e293b; --muted: #64748b; --card-bg: #ffffff; --border: #cbd5e1; --nav-bg: rgba(241,245,249,0.8); }
        body.warm { --bg: #fef7ed; --text: #431407; --muted: #9a3412; --card-bg: #fff7ed; --border: #fdba74; --nav-bg: rgba(254,247,237,0.8); }
        body.dark-black { --bg: #0f172a; --text: #e2e8f0; --muted: #94a3b8; --card-bg: #1e293b; --border: #334155; --nav-bg: rgba(15,23,42,0.9); --footer-border: #334155; }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
            transition: background 0.3s, color 0.3s;
        }

        .nav {
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            background: var(--nav-bg);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
            transition: background 0.3s;
        }
        .nav .brand {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            text-decoration: none;
            color: var(--text);
            font-weight: 600;
            font-size: 16px;
            line-height: 1.4;
        }
        .nav .brand .main-title { font-weight: 600; }
        .nav .brand .article-title { font-weight: 500; opacity: 0.9; }
        .nav .brand .article-date { font-size: 0.85em; opacity: 0.7; margin-left: 4px; }
        .nav .nav-link {
            text-decoration: none;
            color: var(--text);
            font-weight: 500;
            font-size: 15px;
            cursor: pointer;
            background: none;
            border: none;
        }
        .nav .nav-link:hover { color: var(--accent); }

        .article-wrapper {
            width: 100%;
            display: flex;
            justify-content: center;
            padding: 40px 24px;
        }
        .article {
            width: 100%;
            max-width: var(--content-max-width);
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 40px 48px;
            transition: max-width 0.3s, background 0.3s, border-color 0.3s;
        }
        .article .body img { max-width: 100%; height: auto; border-radius: 8px; }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 24px;
        }

        /* 排序按钮 */
        .sort-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            white-space: nowrap;
        }
        .sort-btn:hover {
            color: var(--accent);
            background: rgba(37,99,235,0.05);
        }
        .sort-btn .sort-icon {
            font-size: 12px;
            transition: transform 0.3s;
        }
        .sort-btn.asc .sort-icon {
            transform: rotate(180deg);
        }

        .post-list { display: flex; flex-direction: column; gap: 24px; }
        .post-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px 28px;
            text-decoration: none;
            color: var(--text);
            transition: all 0.2s;
            display: block;
        }
        .post-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-color: #cbd5e1; }
        .post-card h2 { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
        .post-card .meta { font-size: 13px; color: var(--muted); margin-bottom: 10px; }
        .post-card .summary { font-size: 15px; color: #334155; line-height: 1.6; }

        .footer {
            text-align: center;
            padding: 32px 24px;
            color: var(--muted);
            font-size: 13px;
            border-top: 1px solid var(--footer-border);
            transition: border-color 0.3s;
        }

        .settings-panel {
            position: fixed;
            top: 64px;
            right: 32px;
            width: 300px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            z-index: 99;
            display: none;
            transition: all 0.2s;
        }
        .settings-panel.show { display: block; }
        .settings-panel h3 { font-size: 16px; margin-bottom: 16px; font-weight: 600; }
        .settings-panel label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            font-size: 14px;
        }
        .settings-panel input[type="range"] {
            width: 140px;
            accent-color: var(--accent);
        }
        .color-schemes { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
        .color-schemes button {
            flex: 1 0 calc(50% - 8px);
            padding: 8px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--card-bg);
            color: var(--text);
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }
        .color-schemes button.active { border-color: var(--accent); background: rgba(37,99,235,0.1); font-weight: 500; }

        @media (max-width: 768px) {
            .article { padding: 24px; }
            .settings-panel { width: calc(100vw - 48px); right: 24px; }
        }
    </style>
    {{ head_extra }}
</head>
<body class="{{ body_class }}">
    <nav class="nav">
        <a href="index.html" class="brand">
            <span class="main-title">📊 印务中心生产数据</span>
            {% if is_article %}
            <span class="article-title">– {{ article_title }}</span>
            <span class="article-date">📅 {{ article_date }}</span>
            {% endif %}
        </a>
        <div style="display: flex; gap: 24px; align-items: center;">
            <a href="index.html" class="nav-link">首页</a>
            {% if is_article %}
            <a href="javascript:void(0)" class="nav-link" id="settingsToggle">设置</a>
            {% endif %}
        </div>
    </nav>

    {{ content }}

    <footer class="footer">
        <p>© {{ year }} 印务中心生产数据 · Powered by Python</p>
    </footer>

    {% if is_article %}
    <div class="settings-panel" id="settingsPanel">
        <h3>🔧 显示设置</h3>
        <label>📐 内容宽度 <span id="widthValue">100%</span></label>
        <input type="range" id="widthSlider" min="600" max="1400" value="1400" step="50">
        <div style="margin-top: 16px;">
            <span style="font-size:14px; font-weight:500;">🎨 配色方案</span>
            <div class="color-schemes">
                <button data-scheme="default">默认</button>
                <button data-scheme="light-gray">浅灰</button>
                <button data-scheme="warm">护眼米色</button>
                <button data-scheme="dark">深色</button>
                <button data-scheme="dark-black">纯黑</button>
            </div>
        </div>
        <button id="resetSettings" style="margin-top:12px; width:100%; padding:8px; border:1px solid var(--border); border-radius:8px; background:transparent; color:var(--text); cursor:pointer;">恢复默认</button>
    </div>

    <script>
        (function() {
            const root = document.documentElement;
            const body = document.body;
            const toggleBtn = document.getElementById('settingsToggle');
            const panel = document.getElementById('settingsPanel');

            toggleBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                panel.classList.toggle('show');
            });
            document.addEventListener('click', function(e) {
                if (!panel.contains(e.target) && e.target !== toggleBtn) {
                    panel.classList.remove('show');
                }
            });

            const widthSlider = document.getElementById('widthSlider');
            const widthValue = document.getElementById('widthValue');
            function setWidth(val) {
                let maxWidth = val >= 1400 ? '100%' : val + 'px';
                root.style.setProperty('--content-max-width', maxWidth);
                widthValue.textContent = maxWidth;
                localStorage.setItem('reportWidth', val);
            }
            const savedWidth = localStorage.getItem('reportWidth') || 1400;
            widthSlider.value = savedWidth;
            setWidth(savedWidth);
            widthSlider.addEventListener('input', function(e) { setWidth(e.target.value); });

            const schemeButtons = document.querySelectorAll('.color-schemes button');
            function applyScheme(scheme) {
                body.className = '';
                if (scheme && scheme !== 'default') body.classList.add(scheme);
                localStorage.setItem('colorScheme', scheme);
                schemeButtons.forEach(function(btn) {
                    btn.classList.remove('active');
                    if (btn.dataset.scheme === scheme) btn.classList.add('active');
                });
            }
            applyScheme(localStorage.getItem('colorScheme') || 'default');
            schemeButtons.forEach(function(btn) {
                btn.addEventListener('click', function() {
                    applyScheme(btn.dataset.scheme);
                });
            });
            document.getElementById('resetSettings').addEventListener('click', function() {
                widthSlider.value = 1400;
                setWidth(1400);
                applyScheme('default');
            });
        })();
    </script>
    {% endif %}

    {% if not is_article %}
    <script>
        (function() {
            const postList = document.querySelector('.post-list');
            const sortBtn = document.getElementById('sortByDate');
            let sortAsc = false;

            function getCards() {
                return Array.from(postList.querySelectorAll('.post-card'));
            }

            function parseDate(card) {
                const metaEl = card.querySelector('.meta');
                if (!metaEl) return '';
                const text = metaEl.textContent.trim();
                const match = text.match(/(\d{4}-\d{2}-\d{2})/);
                return match ? match[1] : text.replace('📅 ', '');
            }

            function sortCards() {
                const cards = getCards();
                cards.sort(function(a, b) {
                    const dateA = parseDate(a);
                    const dateB = parseDate(b);
                    if (sortAsc) {
                        return dateA.localeCompare(dateB);
                    } else {
                        return dateB.localeCompare(dateA);
                    }
                });
                cards.forEach(function(card) {
                    postList.appendChild(card);
                });
            }

            function updateButtonState() {
                if (sortAsc) {
                    sortBtn.classList.add('asc');
                    sortBtn.innerHTML = '按时间排序 <span class="sort-icon">▼</span>';
                } else {
                    sortBtn.classList.remove('asc');
                    sortBtn.innerHTML = '按时间排序 <span class="sort-icon">▼</span>';
                }
            }

            sortBtn.addEventListener('click', function() {
                sortAsc = !sortAsc;
                sortCards();
                updateButtonState();
                localStorage.setItem('sortAsc', sortAsc);
            });

            const savedSort = localStorage.getItem('sortAsc');
            if (savedSort === 'true') {
                sortAsc = true;
                sortCards();
            }
            updateButtonState();
        })();
    </script>
    {% endif %}
</body>
</html>'''


def load_summaries():
    if os.path.exists(SUMMARIES_FILE):
        with open(SUMMARIES_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️  summaries.json 格式错误，已忽略。")
                return {}
    return {}


def load_order():
    if os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    print("⚠️  order.json 格式应为数组，已忽略。")
            except json.JSONDecodeError:
                print("⚠️  order.json 格式错误，已忽略。")
    return None


def get_post_info(filepath, summaries):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_html = f.read()

    title_match = re.search(r'<title>(.*?)</title>', raw_html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(filepath))[0]

    filename = os.path.basename(filepath)
    summary = summaries.get(filename, '')
    if not summary:
        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', raw_html, re.IGNORECASE)
        summary = desc_match.group(1).strip() if desc_match else ''

    mtime = os.path.getmtime(filepath)
    date = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

    body_match = re.search(r'<body[^>]*>(.*?)</body>', raw_html, re.IGNORECASE | re.DOTALL)
    body_html = body_match.group(1).strip() if body_match else raw_html.strip()

    head_match = re.search(r'<head[^>]*>(.*?)</head>', raw_html, re.IGNORECASE | re.DOTALL)
    head_content = head_match.group(1).strip() if head_match else ''
    head_content = re.sub(r'<title>.*?</title>', '', head_content, flags=re.IGNORECASE | re.DOTALL)
    head_content = re.sub(r'<meta\s+name=["\']description["\']\s+content=.*?>', '', head_content, flags=re.IGNORECASE)

    return {
        'title': title,
        'summary': summary,
        'date': date,
        'body': body_html,
        'head_extra': head_content.strip(),
        'link': filename
    }


def sort_posts(posts, order_list):
    if not order_list:
        return posts
    post_dict = {p['link']: p for p in posts}
    sorted_posts = []
    for name in order_list:
        if name in post_dict:
            sorted_posts.append(post_dict[name])
            del post_dict[name]
    sorted_posts.extend(post_dict.values())
    return sorted_posts


def build():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    summaries = load_summaries()
    order = load_order()

    raw_posts = []
    for fname in sorted(os.listdir(POSTS_DIR)):
        if fname.endswith('.html'):
            info = get_post_info(os.path.join(POSTS_DIR, fname), summaries)
            raw_posts.append(info)

    posts = sort_posts(raw_posts, order)

    template = Template(BASE_TEMPLATE)
    current_year = datetime.datetime.now().year

    cards_html = ''
    for post in posts:
        cards_html += f'''
        <a href="{post['link']}" class="post-card">
            <h2>{post['title']}</h2>
            <div class="meta">📅 {post['date']}</div>
            <div class="summary">{post['summary'] or '暂无摘要'}</div>
        </a>'''

    index_html = template.render(
        title='印务中心 · 数据大屏',
        content=f'''
        <div class="container">
            <div style="margin-bottom: 8px;">
                <h1 style="font-size:1.6rem; font-weight:700; margin:0;">印务中心 · 数据大屏</h1>
                <p style="color:var(--muted); margin-top:8px;">共 {len(posts)} 篇报告</p>
            </div>
            <div style="display: flex; justify-content: flex-end; margin-bottom: 24px;">
                <button class="sort-btn" id="sortByDate">
                    按时间排序 <span class="sort-icon"></span>
                </button>
            </div>
            <div class="post-list">
                {cards_html if cards_html else '<p style="color:var(--muted);">暂无报告。</p>'}
            </div>
        </div>''',
        head_extra='',
        year=current_year,
        is_article=False,
        article_title='',
        article_date='',
        body_class=''
    )
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print('生成: index.html')

    for post in posts:
        article_html = f'''
        <div class="article-wrapper">
            <article class="article">
                <div class="body">
                    {post['body']}
                </div>
            </article>
        </div>
        '''
        full_html = template.render(
            title=post['title'],
            content=article_html,
            head_extra=post['head_extra'],
            year=current_year,
            is_article=True,
            article_title=post['title'],
            article_date=post['date'],
            body_class=''
        )
        out_path = os.path.join(OUTPUT_DIR, post['link'])
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f'生成: {post["link"]}')

    print(f'\n✅ 完成！文件在 {OUTPUT_DIR}/')


if __name__ == '__main__':
    build()