-- 修复数据库注释乱码 (使用 UTF8MB4 字符集)
SET NAMES utf8mb4;
USE work_journal_db;

ALTER TABLE `users` MODIFY COLUMN `theme` VARCHAR(30) DEFAULT 'indigo' COMMENT '用户界面主题偏好';

ALTER TABLE `summary_histories` 
MODIFY COLUMN `user_id` INT NOT NULL COMMENT '执行人ID',
MODIFY COLUMN `summary_type` VARCHAR(20) NOT NULL COMMENT '总结类型: monthly, quarterly, annual',
MODIFY COLUMN `summary_id` INT NOT NULL COMMENT '关联总结表的ID',
MODIFY COLUMN `year` SMALLINT NOT NULL COMMENT '年份',
MODIFY COLUMN `month` SMALLINT DEFAULT NULL COMMENT '月份(仅限月度总结)',
MODIFY COLUMN `quarter` SMALLINT DEFAULT NULL COMMENT '季度(仅限季度总结)',
MODIFY COLUMN `content` TEXT COMMENT '版本内容文本',
MODIFY COLUMN `version_note` VARCHAR(100) DEFAULT NULL COMMENT '版本自定义注释',
MODIFY COLUMN `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '存档时间';

ALTER TABLE `summary_histories` COMMENT '总结版本历史存档表';
