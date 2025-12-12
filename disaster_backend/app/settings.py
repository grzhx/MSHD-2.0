# app/settings.py
"""
系统配置 / 常量配置
在这里配置数据库地址、生命周期策略等参数，
方便后面统一修改。
"""

from datetime import timedelta

# 实验环境使用 SQLite 数据库：
# 文件名为 disaster.db，会出现在项目根目录（D:\disaster_backend\disaster.db）
DATABASE_URL = "sqlite:///./disaster.db"

# 生命周期管理策略：
# 如果某条记录在 RETENTION_INACTIVE_DAYS 天内没有被访问（last_accessed_at），
# 则 run_retention 接口会将其标记为 is_archived = True
RETENTION_INACTIVE_DAYS = 365 * 3  # 示例：3 年未访问则建议归档

# 最大保留时间（目前代码中没强制使用，可以在后续扩展自动清理逻辑）
RETENTION_MAX_AGE = timedelta(days=365 * 10)  # 示例：10 年
