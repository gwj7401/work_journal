-- 数据库升级脚本: 增加主题字段与总结版本历史表

-- 1. 为用户表增加主题偏好字段
ALTER TABLE `users` ADD COLUMN `theme` VARCHAR(30) DEFAULT 'indigo' COMMENT '用户界面主题偏好';

-- 2. 创建总结版本历史表
CREATE TABLE IF NOT EXISTS `summary_histories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL COMMENT '执行人ID',
    `summary_type` VARCHAR(20) NOT NULL COMMENT '总结类型: monthly, quarterly, annual',
    `summary_id` INT NOT NULL COMMENT '关联总结表的ID',
    `year` SMALLINT NOT NULL COMMENT '年份',
    `month` SMALLINT DEFAULT NULL COMMENT '月份(仅限月度总结)',
    `quarter` SMALLINT DEFAULT NULL COMMENT '季度(仅限季度总结)',
    `content` TEXT COMMENT '版本内容文本',
    `version_note` VARCHAR(100) DEFAULT NULL COMMENT '版本自定义注释',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '存档时间',
    INDEX `idx_user_summary` (`user_id`, `summary_type`, `summary_id`),
    INDEX `idx_time_lookup` (`year`, `month`, `quarter`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='总结版本历史存档表';
