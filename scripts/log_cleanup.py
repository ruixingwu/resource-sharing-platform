#!/usr/bin/env python3
"""
日志清理脚本
清理超过90天的日志文件和数据库记录
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 添加到Python路径
sys.path.append('/app')

from app import create_app, db
from app.models import AccessLog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def cleanup_old_logs():
    """清理旧日志"""
    app = create_app()
    
    with app.app_context():
        try:
            # 计算90天前的日期
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            # 清理数据库中的访问日志
            old_logs = AccessLog.query.filter(
                AccessLog.created_at < cutoff_date
            ).all()
            
            old_log_count = len(old_logs)
            for log in old_logs:
                db.session.delete(log)
            
            db.session.commit()
            logging.info(f"已删除 {old_log_count} 条访问日志记录")
            
            # 清理文件系统日志文件
            log_dirs = [
                '/app/logs',
                '/var/log/nginx'
            ]
            
            for log_dir in log_dirs:
                if not os.path.exists(log_dir):
                    continue
                
                log_path = Path(log_dir)
                
                # 清理日志文件
                for log_file in log_path.glob('*.log*'):
                    try:
                        file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if file_date < cutoff_date:
                            log_file.unlink()
                            logging.info(f"已删除旧日志文件: {log_file}")
                    except Exception as e:
                        logging.error(f"删除日志文件失败 {log_file}: {e}")
                
                # 清理归档日志
                for log_archive in log_path.glob('*.log.*[0-9]'.format()):
                    try:
                        file_date = datetime.fromtimestamp(log_archive.stat().st_mtime)
                        if file_date < cutoff_date:
                            log_archive.unlink()
                            logging.info(f"已删除旧日志归档: {log_archive}")
                    except Exception as e:
                        logging.error(f"删除日志归档失败 {log_archive}: {e}")
                        
            # 清理大型日志文件（大于100MB）
            max_log_size = 100 * 1024 * 1024  # 100MB
            for log_dir in log_dirs:
                if not os.path.exists(log_dir):
                    continue
                
                log_path = Path(log_dir)
                for log_file in log_path.glob('*.log'):
                    try:
                        if log_file.stat().st_size > max_log_size:
                            # 截断日志文件
                            with open(log_file, 'r+') as f:
                                lines = f.readlines()
                                f.seek(0)
                                f.truncate()
                                # 保留最后1000行
                                f.writelines(lines[-1000:])
                            logging.info(f"已截断大日志文件: {log_file}")
                    except Exception as e:
                        logging.error(f"处理大日志文件失败 {log_file}: {e}")
                        
            logging.info("日志清理任务完成")
            
        except Exception as e:
            logging.error(f"日志清理任务失败: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    cleanup_old_logs()