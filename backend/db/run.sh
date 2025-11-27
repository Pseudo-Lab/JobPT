#!/bin/bash
docker run --name jobpt-mysql -e LC_ALL=C.UTF-8 -e MYSQL_ROOT_PASSWORD=root -d -p 3306:3306 mysql:latest --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci