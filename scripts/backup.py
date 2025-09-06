#!/usr/bin/env python3
"""
自动备份脚本
支持数据库备份和文件备份
"""

import os
import shutil
import subprocess
from datetime import datetime, timedelta
import gzip
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/backup.log'),
        logging.StreamHandler()
    ]
)

class BackupManager:
    def __init__(self):
        self.backup_dir = os.getenv('BACKUP_DIR', '/backups')
        self.db_name = os.getenv('MYSQL_DATABASE', 'resource_sharing')
        self.db_user = os.getenv('MYSQL_USER', 'root')
        self.db_host = os.getenv('MYSQL_HOST', 'localhost')
        self.db_port = os.getenv('MYSQL_PORT', '3306')
        self.db_pass = os.getenv('MYSQL_PASSWORD', 'root123')
        self.upload_dir = os.getenv('UPLOAD_FOLDER', '/app/uploads')
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """确保备份目录存在"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        Path(f"{self.backup_dir}/db").mkdir(parents=True, exist_ok=True)
        Path(f"{self.backup_dir}/files").mkdir(parents=True, exist_ok=True)
    
    def backup_database(self):
        """备份数据库"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.db_name}_{timestamp}.sql"
            filepath = f"{self.backup_dir}/db/{filename}"
            
            # 使用mysqldump备份
            cmd = [
                'mysqldump',
                f'--host={self.db_host}',
                f'--port={self.db_port}',
                f'--user={self.db_user}',
                f'--password={self.db_pass}',
                self.db_name,
                '--result-file', filepath,
                '--single-transaction',
                '--routines',
                '--triggers'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 压缩备份文件
                with open(filepath, 'rb') as f_in:
                    with gzip.open(f"{filepath}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                os.remove(filepath)
                logging.info(f"数据库备份成功: {filepath}.gz")
                return True
            else:
                logging.error(f"数据库备份失败: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"备份数据库时出错: {str(e)}")
            return False
    
    def backup_files(self):
        """备份上传的文件"""
        try:
            if not os.path.exists(self.upload_dir):
                logging.warning("上传目录不存在，跳过文件备份")
                return True
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dirname = f"files_{timestamp}"
            backup_path = f"{self.backup_dir}/files/{dirname}"
            
            # 使用tar打包压缩
            tar_path = f"{backup_path}.tar.gz"
            
            cmd = [
                'tar',
                '-czf',
                tar_path,
                '-C',
                os.path.dirname(self.upload_dir),
                os.path.basename(self.upload_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"文件备份成功: {tar_path}")
                return True
            else:
                logging.error(f"文件备份失败: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"备份文件时出错: {str(e)}")
            return False
    
    def cleanup_old_backups(self):
        """清理过期的备份文件"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        try:
            # 清理数据库备份
            db_backup_path = Path(f"{self.backup_dir}/db")
            for file in db_backup_path.glob("*.sql.gz"):
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                if file_date < cutoff_date:
                    file.unlink()
                    logging.info(f"删除过期数据库备份: {file}")
            
            # 清理文件备份
            files_backup_path = Path(f"{self.backup_dir}/files")
            for file in files_backup_path.glob("files_*.tar.gz"):
                file_date = datetime.fromtimestamp(file.stat().st_mtime)
                if file_date < cutoff_date:
                    file.unlink()
                    logging.info(f"删除过期文件备份: {file}")
            
            return True
            
        except Exception as e:
            logging.error(f"清理过期备份时出错: {str(e)}")
            return False
    
    def send_notification(self, success, message):
        """发送备份通知邮件 - 配置可选"""
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        recipient = os.getenv('BACKUP_EMAIL')
        
        if not all([smtp_server, smtp_port, smtp_user, smtp_pass, recipient]):
            return  # 未配置邮件通知
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient
            msg['Subject'] = f'资源平台备份通知 - {"成功" if success else "失败"}'
            
            body = f"""
            尊敬的系统管理员：
            
            资源共享平台自动备份任务{ "已完成" if success else "失败" }。
            
            备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            状态: {"成功" if success else "失败"}
            消息: {message}
            
            本邮件由系统自动发送，请勿回复。
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient, msg.as_string())
            server.quit()
            
            logging.info("备份通知邮件发送成功")
            
        except Exception as e:
            logging.error(f"发送备份通知邮件时出错: {str(e)}")
    
    def run_backup(self):
        """执行完整备份流程"""
        try:
            logging.info("开始执行备份任务...")
            
            backup_success = True
            messages = []
            
            # 备份数据库
            if self.backup_database():
                messages.append("数据库备份成功")
            else:
                backup_success = False
                messages.append("数据库备份失败")
            
            # 备份文件
            if self.backup_files():
                messages.append("文件备份成功")
            else:
                backup_success = False
                messages.append("文件备份失败")
            
            # 清理过期备份
            self.cleanup_old_backups()
            
            message = "; ".join(messages)
            logging.info(f"备份任务完成: {message}")
            
            # 发送通知（如配置）
            self.send_notification(backup_success, message)
            
        except Exception as e:
            logging.error(f"备份任务执行失败: {str(e)}")
            self.send_notification(False, str(e))

if __name__ == "__main__":
    backup = BackupManager()
    backup.run_backup()