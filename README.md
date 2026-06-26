# 火车模型管理系统

用于管理火车模型藏品（机车、车厢、动车组、先头车）的录入、统计、文件归档与数据导入导出的 Web 应用，并支持室内灯型号管理与数码功能表（DCC Function Key）AI/OCR 自动解析。

## 功能特性

- **四种模型管理**：机车、车厢、动车组、先头车的增删改查，模态框表单无需跳转
- **文件归档**：模型图片、说明书、数码功能表的上传与预览，按「模型类型/品牌_货号」自动组织
- **统计汇总**：按类型 / 比例 / 品牌 / 商家多维统计，支持表格与饼图切换
- **数据导入导出**：智能 Excel 导入（冲突检测）、自定义导入向导、ZIP 打包导出所有文件
- **数码功能表解析**：上传功能表文件，自动 AI/OCR 提取 DCC 功能键 F0–F31
- **室内灯管理**：室内灯型号维护，按品牌 / 车型 / 比例的适用规则匹配
- **信息维护**：集中管理品牌、商家、系列、车型、芯片等参考数据

> 完整的页面与功能说明见 [用户手册](manual/index.html)。

## 环境要求

- **Python 3.10+**（含 pip）
- 默认使用 SQLite（无需额外安装）；可选 MySQL（见下）
- **可选**（数码功能表本地 OCR 解析需）：系统级 `tesseract`（含中文语言包）与 `poppler`

  ```bash
  brew install tesseract tesseract-lang poppler   # macOS
  ```

## 快速开始

```bash
git clone <repository-url> && cd TrainModelManager

python -m venv myenv
source myenv/bin/activate          # Windows: myenv\Scripts\activate

pip install -r requirements.txt

python init_db.py                  # 初始化数据库并播种预置参考数据

./start.sh                         # 启动（生产模式，端口 8000，后台运行）
```

浏览器打开 **http://127.0.0.1:8000** 即可使用。

- 开发模式（前台运行、代码自动重载）：`./start.sh --debug`
- 指定端口：`./start.sh --port 9000`
- 停止服务：`./stop.sh`

## 数据库配置

**SQLite（默认）**：开箱即用，数据库文件位于 `instance/train_model.db`。

**MySQL（可选）**：通过环境变量切换：

```bash
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=train_model_manager
```

## 用户手册

详细的页面与功能说明见 [用户手册](manual/index.html)（单页 HTML，可离线打开）。

## 许可证

[Apache License 2.0](LICENSE)

## 联系方式

penglixun@gmail.com
