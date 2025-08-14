# 图片展示网站（Image Showcase Website）

> 本项目由 GitHub Copilot AI 辅助开发，适用于毕业设计或课程项目，尤其适合需要快速搭建图片展示平台的学习/水课场景。

---

## 项目简介

本项目是一个基于 HTML、JavaScript、CSS 和 Python 的图片展示网站，用户可以上传、浏览和管理图片。项目结构简洁，功能实用，易于扩展和二次开发。适合高校课程作业、毕业设计及个人学习参考。部分代码由 Copilot AI 辅助生成，仅供参考。

---

## 功能特性

- **图片上传与管理**：支持本地图片上传，展示已上传图片列表。
- **图片分类与标签**：可对图片进行分类、添加标签，便于管理与检索。
- **多格式支持**：支持 JPG、PNG、GIF 等常见图片格式。
- **响应式设计**：采用 CSS，兼容 PC 与移动端，适合多设备访问。
- **图片预览与放大**：点击图片可弹窗预览或放大查看细节。
- **后端 API（Python Flask）**：为图片上传、分类等功能提供简单 API 支持。
- **易于定制**：代码结构清晰，前后端可根据需求扩展新功能。
- **Live2D 看板娘**：集成 Live2D 看板娘插件，为网站增添二次元互动元素，提高趣味性和用户体验。

---

## 简单代码示例(与源码略有差异) 详情参照源码

### HTML 片段（主页面结构）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>图片展示网站</title>
  <link rel="stylesheet" href="static/style.css">
</head>
<body>
  <h1>图片展示</h1>
  <form id="upload-form" enctype="multipart/form-data">
    <input type="file" name="image" multiple accept="image/*">
    <button type="submit">上传图片</button>
  </form>
  <div id="gallery"></div>
  <!-- Live2D 模型容器 -->
  <div id="live2d-widget"></div>
  <script src="static/main.js"></script>
  <!-- Live2D 看板娘脚本示例 -->
  <script src="https://cdn.jsdelivr.net/npm/live2d-widget@3.1.4/lib/L2Dwidget.min.js"></script>
  <script>
    L2Dwidget.init();
  </script>
</body>
</html>
```

### JavaScript 片段（上传与展示）

```javascript
// static/main.js
document.getElementById('upload-form').onsubmit = async function(e) {
  e.preventDefault();
  const files = e.target.image.files;
  for (let file of files) {
    // 简单本地预览（如需后端存储可改为 fetch 上传）
    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    img.className = 'preview-img';
    document.getElementById('gallery').appendChild(img);
  }
}
```

### Python 后端（Flask API 示例）

```python
# app.py
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    img = request.files['image']
    img.save(os.path.join('static/uploads', img.filename))
    return jsonify({'status': 'success', 'filename': img.filename})

if __name__ == '__main__':
    app.run(debug=True)
```

---

## 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/ChenLX233/ImageShowcaseWebsite-SuitableForGraduationProjects.git
   ```

2. **安装依赖（如有 Python 后端）**
   ```bash
   pip install flask
   ```

3. **启动服务**
   - 前端：直接在浏览器打开 `index.html`
   - 后端（如有）：运行 Python 服务
     ```bash
     python app.py
     ```

---

## 适用场景

- 课程作业、毕业设计
- Copilot AI 辅助开发学习
- 个人/团队快速搭建图片管理平台
- 图片展示类 Demo，便于二次开发

---

## 许可证

本项目采用 [CC BY-NC 4.0（署名-非商业性）](https://creativecommons.org/licenses/by-nc/4.0/) 协议，禁止商用，欢迎学习与交流。

---

## 联系方式

如有疑问或建议，请通过 GitHub Issues 联系，或在项目主页留言。

---

> *本项目是学习与交流用途，部分代码由 Copilot AI 辅助生成，集成了 Live2D 看板娘插件。欢迎大家使用并反馈改进建议！*
