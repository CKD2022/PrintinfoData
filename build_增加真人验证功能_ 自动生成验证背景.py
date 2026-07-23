import os
import re
import json
import datetime
from jinja2 import Template

POSTS_DIR = 'posts'
OUTPUT_DIR = 'docs'
SUMMARIES_FILE = os.path.join(POSTS_DIR, 'summaries.json')
ORDER_FILE = os.path.join(POSTS_DIR, 'order.json')

# 验证组件模板（使用 Canvas 生成背景）
CAPTCHA_TEMPLATE = '''
<div class="captcha-overlay" id="captchaOverlay">
    <div class="captcha-wrapper" id="captchaWrapper">
        <div class="captcha-header">🔐 安全验证</div>
        <button class="refresh-btn" onclick="initCaptcha()" title="刷新验证">↻</button>

        <div class="puzzle-area" id="puzzleArea">
            <canvas id="bgCanvas" width="300" height="180"></canvas>
            <div class="puzzle-hole" id="puzzleHole"></div>
            <div class="puzzle-piece" id="puzzlePiece"></div>
        </div>

        <div class="slider-container" id="sliderContainer">
            <div class="slider-text" id="sliderText">向右滑动填充拼图</div>
            <div class="slider-btn" id="sliderBtn"></div>
        </div>

        <div class="status-msg" id="statusMsg"></div>
    </div>
</div>

<style>
    /* === 验证组件样式 === */
    .captcha-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.55);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        transition: opacity 0.5s ease, visibility 0.5s ease;
    }
    .captcha-overlay.hidden {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
    }
    .captcha-wrapper {
        background: #ffffff;
        padding: 24px 20px 20px;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        width: 340px;
        position: relative;
        transition: transform 0.3s ease;
    }
    .captcha-wrapper .captcha-header {
        text-align: center;
        margin-bottom: 12px;
        color: #1e293b;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .captcha-wrapper .refresh-btn {
        position: absolute;
        top: 12px;
        right: 14px;
        background: none;
        border: none;
        cursor: pointer;
        font-size: 20px;
        color: #94a3b8;
        transition: transform 0.3s, color 0.3s;
        padding: 4px 8px;
        border-radius: 6px;
    }
    .captcha-wrapper .refresh-btn:hover {
        color: #2563eb;
        transform: rotate(60deg);
    }
    .captcha-wrapper .puzzle-area {
        position: relative;
        width: 300px;
        height: 180px;
        margin: 0 auto 16px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
        background: #e2e8f0;
    }
    .captcha-wrapper .puzzle-area canvas {
        display: block;
        width: 100%;
        height: 100%;
        border-radius: 10px;
    }
    .captcha-wrapper .puzzle-hole {
        position: absolute;
        width: 50px;
        height: 50px;
        background-color: rgba(0, 0, 0, 0.5);
        border: 2px dashed rgba(255,255,255,0.8);
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
        z-index: 1;
        border-radius: 4px;
        pointer-events: none;
    }
    .captcha-wrapper .puzzle-piece {
        position: absolute;
        width: 50px;
        height: 50px;
        border: 2px solid rgba(255,255,255,0.9);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        cursor: grab;
        z-index: 2;
        top: 0;
        left: 0;
        border-radius: 4px;
        transition: left 0.08s linear;
        will-change: left;
        pointer-events: auto;
    }
    .captcha-wrapper .puzzle-piece:active {
        cursor: grabbing;
    }
    .captcha-wrapper .slider-container {
        position: relative;
        width: 300px;
        height: 44px;
        background: #f1f5f9;
        border-radius: 22px;
        margin: 0 auto;
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
    }
    .captcha-wrapper .slider-text {
        position: absolute;
        width: 100%;
        height: 100%;
        line-height: 44px;
        text-align: center;
        font-size: 14px;
        color: #94a3b8;
        user-select: none;
        pointer-events: none;
        font-weight: 500;
        letter-spacing: 0.5px;
        transition: opacity 0.25s ease;
    }
    .captcha-wrapper .slider-btn {
        position: absolute;
        left: 0;
        top: -1px;
        width: 44px;
        height: 44px;
        background: #ffffff;
        border-radius: 50%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: grab;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: background 0.25s ease, box-shadow 0.25s ease;
        z-index: 3;
        border: 1px solid #e2e8f0;
        pointer-events: auto;
    }
    .captcha-wrapper .slider-btn::after {
        content: "→";
        color: #2563eb;
        font-weight: bold;
        font-size: 20px;
        transition: color 0.25s ease;
    }
    .captcha-wrapper .slider-btn.active {
        background: #2563eb;
        border-color: #2563eb;
        box-shadow: 0 4px 16px rgba(37,99,235,0.3);
        cursor: grabbing;
    }
    .captcha-wrapper .slider-btn.active::after {
        color: #ffffff;
    }
    .captcha-wrapper .slider-btn.error {
        background: #ef4444;
        border-color: #ef4444;
        animation: shake 0.4s ease;
    }
    .captcha-wrapper .slider-btn.error::after {
        content: "✕";
        color: #ffffff;
        font-size: 18px;
    }
    .captcha-wrapper .slider-btn.success {
        background: #22c55e;
        border-color: #22c55e;
        animation: pop 0.35s ease;
    }
    .captcha-wrapper .slider-btn.success::after {
        content: "✓";
        color: #ffffff;
        font-size: 20px;
    }
    .captcha-wrapper .status-msg {
        text-align: center;
        margin-top: 12px;
        font-size: 14px;
        height: 22px;
        color: #94a3b8;
        font-weight: 500;
        transition: color 0.3s ease;
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        20% { transform: translateX(-8px); }
        40% { transform: translateX(8px); }
        60% { transform: translateX(-6px); }
        80% { transform: translateX(6px); }
    }
    @keyframes pop {
        0% { transform: scale(1); }
        50% { transform: scale(1.15); }
        100% { transform: scale(1); }
    }

    @media (max-width: 480px) {
        .captcha-wrapper {
            width: 94%;
            padding: 18px 14px 16px;
        }
        .captcha-wrapper .puzzle-area {
            width: 100%;
            height: 0;
            padding-bottom: 60%;
        }
        .captcha-wrapper .puzzle-area canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        .captcha-wrapper .puzzle-area .puzzle-hole,
        .captcha-wrapper .puzzle-area .puzzle-piece {
            width: 16%;
            height: 0;
            padding-bottom: 16%;
        }
        .captcha-wrapper .slider-container {
            width: 100%;
        }
        .captcha-wrapper .slider-btn {
            width: 44px;
            height: 44px;
            top: -1px;
        }
    }
</style>

<script>
    (function() {
        // ----- 验证逻辑 -----
        const CONFIG = {
            tolerance: 5,
            pieceSize: 50,
            canvasWidth: 300,
            canvasHeight: 180
        };

        let isDragging = false;
        let startX = 0;
        let currentX = 0;
        let holeX = 0;
        let holeY = 0;
        let maxSlideWidth = 0;
        let isVerified = false;
        let currentBgDataURL = '';

        const overlay = document.getElementById('captchaOverlay');
        const puzzleArea = document.getElementById('puzzleArea');
        const puzzleHole = document.getElementById('puzzleHole');
        const puzzlePiece = document.getElementById('puzzlePiece');
        const sliderContainer = document.getElementById('sliderContainer');
        const sliderBtn = document.getElementById('sliderBtn');
        const sliderText = document.getElementById('sliderText');
        const statusMsg = document.getElementById('statusMsg');
        const bgCanvas = document.getElementById('bgCanvas');

        // ----- 生成随机几何背景 (使用 Canvas) -----
        function generateBackground(canvas) {
            const ctx = canvas.getContext('2d');
            const w = CONFIG.canvasWidth;
            const h = CONFIG.canvasHeight;

            // 清空
            ctx.clearRect(0, 0, w, h);

            // 随机选择配色方案
            const schemes = [
                // [背景色, 图形色1, 图形色2, 图形色3]
                { bg: '#f8fafc', colors: ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd'] },
                { bg: '#fef3c7', colors: ['#d97706', '#f59e0b', '#fbbf24', '#fcd34d'] },
                { bg: '#ecfdf5', colors: ['#059669', '#10b981', '#34d399', '#6ee7b7'] },
                { bg: '#fef2f2', colors: ['#dc2626', '#ef4444', '#f87171', '#fca5a5'] },
                { bg: '#f5f3ff', colors: ['#7c3aed', '#8b5cf6', '#a78bfa', '#c4b5fd'] },
                { bg: '#fce7f3', colors: ['#db2777', '#ec4899', '#f472b6', '#f9a8d4'] },
                { bg: '#e0f2fe', colors: ['#0284c7', '#0ea5e9', '#38bdf8', '#7dd3fc'] },
                { bg: '#f1f5f9', colors: ['#475569', '#64748b', '#94a3b8', '#cbd5e1'] },
            ];

            const scheme = schemes[Math.floor(Math.random() * schemes.length)];

            // 填充背景
            ctx.fillStyle = scheme.bg;
            ctx.fillRect(0, 0, w, h);

            // 随机绘制几何图形
            const shapes = ['rect', 'circle', 'triangle', 'diamond', 'hexagon'];
            const numShapes = 20 + Math.floor(Math.random() * 15);

            for (let i = 0; i < numShapes; i++) {
                const color = scheme.colors[Math.floor(Math.random() * scheme.colors.length)];
                const shape = shapes[Math.floor(Math.random() * shapes.length)];
                const x = Math.random() * w;
                const y = Math.random() * h;
                const size = 10 + Math.random() * 35;
                const alpha = 0.15 + Math.random() * 0.4;

                ctx.globalAlpha = alpha;
                ctx.fillStyle = color;
                ctx.strokeStyle = color;
                ctx.lineWidth = 1 + Math.random() * 2;

                switch (shape) {
                    case 'rect':
                        ctx.fillRect(x - size/2, y - size/2, size, size * (0.6 + Math.random() * 0.8));
                        break;
                    case 'circle':
                        ctx.beginPath();
                        ctx.arc(x, y, size/2, 0, Math.PI * 2);
                        ctx.fill();
                        break;
                    case 'triangle':
                        ctx.beginPath();
                        ctx.moveTo(x, y - size/2);
                        ctx.lineTo(x - size/2, y + size/2);
                        ctx.lineTo(x + size/2, y + size/2);
                        ctx.closePath();
                        ctx.fill();
                        break;
                    case 'diamond':
                        ctx.beginPath();
                        ctx.moveTo(x, y - size/2);
                        ctx.lineTo(x + size/2, y);
                        ctx.lineTo(x, y + size/2);
                        ctx.lineTo(x - size/2, y);
                        ctx.closePath();
                        ctx.fill();
                        break;
                    case 'hexagon':
                        ctx.beginPath();
                        for (let j = 0; j < 6; j++) {
                            const angle = (Math.PI / 3) * j - Math.PI / 6;
                            const px = x + (size/2) * Math.cos(angle);
                            const py = y + (size/2) * Math.sin(angle);
                            j === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
                        }
                        ctx.closePath();
                        ctx.fill();
                        break;
                }
            }

            // 绘制一些细线作为装饰
            ctx.globalAlpha = 0.08;
            for (let i = 0; i < 12; i++) {
                ctx.strokeStyle = scheme.colors[Math.floor(Math.random() * scheme.colors.length)];
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(Math.random() * w, Math.random() * h);
                ctx.lineTo(Math.random() * w, Math.random() * h);
                ctx.stroke();
            }

            ctx.globalAlpha = 1.0;

            // 返回 dataURL 用于拼图块
            return canvas.toDataURL('image/png');
        }

        // ----- 更新拼图块背景 -----
        function updatePieceBackground(dataURL) {
            puzzlePiece.style.backgroundImage = 'url(' + dataURL + ')';
            puzzlePiece.style.backgroundSize = CONFIG.canvasWidth + 'px ' + CONFIG.canvasHeight + 'px';
        }

        function initCaptcha() {
            if (isVerified) return;

            isDragging = false;
            sliderBtn.style.left = '0px';
            puzzlePiece.style.left = '0px';
            sliderBtn.className = 'slider-btn';
            sliderText.style.opacity = '1';
            statusMsg.textContent = '';
            statusMsg.style.color = '#94a3b8';
            currentX = 0;

            // 生成背景
            currentBgDataURL = generateBackground(bgCanvas);

            // 更新拼图块背景
            updatePieceBackground(currentBgDataURL);

            // 随机生成缺口位置
            const areaWidth = CONFIG.canvasWidth;
            const areaHeight = CONFIG.canvasHeight;

            holeX = Math.floor(Math.random() * (areaWidth - CONFIG.pieceSize - 40)) + 20;
            holeY = Math.floor(Math.random() * (areaHeight - CONFIG.pieceSize - 40)) + 20;

            puzzleHole.style.left = holeX + 'px';
            puzzleHole.style.top = holeY + 'px';

            puzzlePiece.style.top = holeY + 'px';
            puzzlePiece.style.left = '0px';

            maxSlideWidth = sliderContainer.offsetWidth - sliderBtn.offsetWidth;

            // 设置拼图块背景偏移
            puzzlePiece.style.backgroundPosition = '-' + holeX + 'px -' + holeY + 'px';

            // 确保拼图块可见
            puzzlePiece.style.display = 'block';
        }

        function startDrag(e) {
            if (isVerified) return;
            isDragging = true;
            const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
            startX = clientX;
            sliderBtn.classList.add('active');
            sliderText.style.opacity = '0';
        }

        function onDrag(e) {
            if (!isDragging || isVerified) return;
            e.preventDefault();

            const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
            let moveX = clientX - startX;

            if (moveX < 0) moveX = 0;
            if (moveX > maxSlideWidth) moveX = maxSlideWidth;

            currentX = moveX;
            sliderBtn.style.left = moveX + 'px';
            puzzlePiece.style.left = moveX + 'px';
        }

        function endDrag() {
            if (!isDragging || isVerified) return;
            isDragging = false;
            sliderBtn.classList.remove('active');

            const diff = Math.abs(currentX - holeX);

            if (diff <= CONFIG.tolerance) {
                // 验证成功
                isVerified = true;
                sliderBtn.classList.add('success');
                statusMsg.textContent = '✅ 验证通过';
                statusMsg.style.color = '#22c55e';

                sliderBtn.onmousedown = null;
                sliderBtn.ontouchstart = null;

                setTimeout(function() {
                    overlay.classList.add('hidden');
                    document.body.style.overflow = 'auto';
                    sessionStorage.setItem('captchaVerified', 'true');
                }, 600);
            } else {
                // 验证失败
                sliderBtn.classList.add('error');
                statusMsg.textContent = '❌ 验证失败，请重试';
                statusMsg.style.color = '#ef4444';

                setTimeout(function() {
                    sliderBtn.classList.remove('error');
                    sliderBtn.style.left = '0px';
                    puzzlePiece.style.left = '0px';
                    sliderText.style.opacity = '1';
                    statusMsg.textContent = '';
                    statusMsg.style.color = '#94a3b8';
                    currentX = 0;
                }, 900);
            }
        }

        // 绑定事件
        sliderBtn.addEventListener('mousedown', startDrag);
        sliderBtn.addEventListener('touchstart', startDrag, { passive: false });

        document.addEventListener('mousemove', onDrag);
        document.addEventListener('touchmove', onDrag, { passive: false });

        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);

        // 暴露 init 给全局
        window.initCaptcha = initCaptcha;

        // 检查是否已经验证过
        if (sessionStorage.getItem('captchaVerified') === 'true') {
            overlay.classList.add('hidden');
            document.body.style.overflow = 'auto';
        } else {
            // 页面加载时初始化
            if (document.readyState === 'complete') {
                initCaptcha();
            } else {
                window.addEventListener('load', initCaptcha);
            }
        }
    })();
</script>
'''

# 基础模板（不含验证层，用于文章页）
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
<body class="{{ body_class }}" id="mainBody">
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

# 首页专用模板（含验证层）
INDEX_TEMPLATE = '''<!DOCTYPE html>
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
            overflow: hidden;
        }
        body.verified { overflow: auto; }

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

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 24px;
        }

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

        @media (max-width: 768px) {
            .container { padding: 24px 16px; }
            .post-card { padding: 16px 18px; }
        }
    </style>
    {{ head_extra }}
</head>
<body class="{{ body_class }}" id="mainBody">
    {{ captcha_html }}

    <nav class="nav">
        <a href="index.html" class="brand">
            <span class="main-title">📊 印务中心生产数据</span>
        </a>
        <div style="display: flex; gap: 24px; align-items: center;">
            <a href="index.html" class="nav-link">首页</a>
        </div>
    </nav>

    {{ content }}

    <footer class="footer">
        <p>© {{ year }} 印务中心生产数据 · Powered by Python</p>
    </footer>

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

            // 监听验证完成，给 body 添加 verified 类以启用滚动
            const overlay = document.getElementById('captchaOverlay');
            if (overlay) {
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                            if (overlay.classList.contains('hidden')) {
                                document.getElementById('mainBody').classList.add('verified');
                            }
                        }
                    });
                });
                observer.observe(overlay, { attributes: true });
            }
        })();
    </script>
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

    # 使用不同的模板
    article_template = Template(BASE_TEMPLATE)
    index_template = Template(INDEX_TEMPLATE)
    current_year = datetime.datetime.now().year

    # --- 生成首页（带验证） ---
    cards_html = ''
    for post in posts:
        cards_html += f'''
        <a href="{post['link']}" class="post-card">
            <h2>{post['title']}</h2>
            <div class="meta">📅 {post['date']}</div>
            <div class="summary">{post['summary'] or '暂无摘要'}</div>
        </a>'''

    index_html = index_template.render(
        title='印务中心 · 数据大屏',
        content=f'''
        <div class="container">
            <div style="margin-bottom: 8px;">
                <h1 style="font-size:1.6rem; font-weight:700; margin:0;">印务中心 · 数据大屏</h1>
                <p style="color:var(--muted); margin-top:8px;">共 {len(posts)} 篇报告</p>
            </div>
            <div style="display: flex; justify-content: flex-end; margin-bottom: 24px;">
                <button class="sort-btn" id="sortByDate">
                    按时间排序 <span class="sort-icon">▼</span>
                </button>
            </div>
            <div class="post-list">
                {cards_html if cards_html else '<p style="color:var(--muted);">暂无报告。</p>'}
            </div>
        </div>''',
        head_extra='',
        year=current_year,
        body_class='',
        captcha_html=CAPTCHA_TEMPLATE
    )
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print('生成: index.html (带真人验证，使用 Canvas 生成背景)')

    # --- 生成文章页（不带验证） ---
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
        full_html = article_template.render(
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
        print(f'生成: {post["link"]} (无验证)')

    print(f'\n✅ 完成！文件在 {OUTPUT_DIR}/')
    print('   - index.html: 带真人验证 (Canvas 生成背景，无需网络请求)')
    print('   - 文章页: 无验证，可直接访问')


if __name__ == '__main__':
    build()