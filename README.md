# 合唱/发声训练应用 (Choir Training App)

[English](#english-readme) | [中文说明](#中文说明)

---

<a name="中文说明"></a>
## 📖 中文说明

这是一个基于 Django 开发的合唱与发声训练应用。它包含学员每日打卡、录音作业提交以及老师点评（支持语音和文字）等功能。

### ✨ 功能特性

- **学员端**:
  - 📝 每日打卡系统。
  - 🎧 收听示范音频并上传练习录音。
  - 💬 查看老师反馈（文字 & 语音）。
  - 📅 追踪练习历史记录。
- **老师端**:
  - 📊 仪表盘查看学员进度。
  - ✍️ 批改作业，支持录制语音点评。
  - 👍 对每日打卡进行点赞和互动。

### 🛠️ 环境要求

- Python 3.8+
- pip
- virtualenv (推荐)

### 🚀 安装步骤

1.  **克隆项目** (如果是从 Git 获取) 或进入项目根目录。

2.  **创建并激活虚拟环境**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows 用户请使用: venv\Scripts\activate
    ```

3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置环境**:
    - 将 `.env.example` 复制为 `.env`:
      ```bash
      cp .env.example .env
      ```
    - 编辑 `.env` 文件，设置您的 `SECRET_KEY` 和其他配置。

5.  **初始化数据库**:
    ```bash
    python manage.py migrate
    ```

6.  **创建管理员账号** (用于访问老师后台):
    ```bash
    python manage.py createsuperuser
    ```
    按照提示输入用户名和密码。

### ▶️ 运行服务

```bash
python manage.py runserver
```

打开浏览器访问 `http://127.0.0.1:8000`。

### 📌 使用指南

- **登录**: `/login` (默认跳转)
- **学员主页**: `/dashboard`
- **老师后台**: `/teacher/dashboard` (需要管理员权限)

### 🔒 安全提示

在生产环境中，请务必在 `.env` 文件中将 `DEBUG` 设置为 `False`，并设置一个强密码作为 `SECRET_KEY`。

---

<a name="english-readme"></a>
## 📖 English Readme

A Django-based application for choir and voice training, featuring student daily check-ins, audio recording submissions, and teacher reviews.

### ✨ Features

- **Students**:
  - 📝 Daily check-in system.
  - 🎧 Listen to demo audio and upload practice recordings.
  - 💬 View teacher feedback (text & audio).
  - 📅 Track practice history.
- **Teachers**:
  - 📊 Dashboard to view student progress.
  - ✍️ Review submitted recordings with text and audio feedback.
  - 👍 "Like" and comment on daily check-ins.

### 🛠️ Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### 🚀 Installation

1.  **Clone the repository** (if applicable) or navigate to the project root.

2.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**:
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edit `.env` and set your `SECRET_KEY` and other settings.

5.  **Initialize the database**:
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser** (for the teacher dashboard):
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to set a username and password.

### ▶️ Running the Server

```bash
python manage.py runserver
```

Access the application at `http://127.0.0.1:8000`.

### 📌 Usage

- **Login**: `/login` (default redirect)
- **Student Dashboard**: `/dashboard`
- **Teacher Dashboard**: `/teacher/dashboard` (requires staff account)

### 🔒 Security Note

Ensure `DEBUG=False` in production and a strong `SECRET_KEY` is set in your `.env` file.
