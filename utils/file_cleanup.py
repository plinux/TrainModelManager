"""
文件清理工具（P2-2）

删除模型时清理其关联的文件（物理文件 + DB 记录）和功能键，防止孤儿数据。
"""
import os
import logging
from utils.file_sync import get_absolute_file_path
from models import db, ModelFile, FunctionKey

logger = logging.getLogger(__name__)


def delete_model_files(model_type, model_id):
  """删除指定模型的全部文件（物理 + DB 记录）和功能键。

  在删除模型主记录前调用；本函数不 commit，由调用方统一提交。
  物理文件删除失败不阻断流程（DB 记录已删，残留由文件同步清理）。

  Args:
    model_type: 模型类型（locomotive/carriage/trainset/locomotive_head）
    model_id: 模型 ID
  """
  files = ModelFile.query.filter_by(model_type=model_type, model_id=model_id).all()
  for f in files:
    try:
      os.remove(get_absolute_file_path(f.file_path))
    except (FileNotFoundError, ValueError):
      pass
    except OSError as e:
      logger.warning(f"删除文件失败 {f.file_path}: {e}")
    db.session.delete(f)

  # 功能键（仅 locomotive/trainset 有；其他类型无记录，delete 无副作用）
  FunctionKey.query.filter_by(model_type=model_type, model_id=model_id).delete()

  if files:
    logger.info(f"已清理 {model_type}:{model_id} 的 {len(files)} 个文件")
