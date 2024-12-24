# GouCloud
Advanced and aesthetically pleasing cloud storage.
## 数据库配置-MySQL V8.0.4
```c++
CREATE DATABASE cloud_disk;

USE cloud_disk;

CREATE TABLE cloud_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cloud_file (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_uuid VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES cloud_user(id) ON DELETE CASCADE
);

CREATE TABLE file_shares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_uuid VARCHAR(36) NOT NULL,
    share_code VARCHAR(6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_file_uuid (file_uuid)
);
```
## Python库安装
```bash
pip install Flask mysql-connector-python Werkzeug
```
