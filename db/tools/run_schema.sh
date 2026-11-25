#!/bin/bash
cd /tmp/db
sqlplus -s hotel_owner/HotelOwner123#@FREEPDB1 << 'EOF'
SET DEFINE OFF
SET SERVEROUTPUT ON SIZE UNLIMITED
@01_schema.sql
@02_seed.sql
@03_packages.sql
@04_triggers.sql
@05_trigger_nhat_ky.sql
@08_pkg_nghiep_vu.sql
@11_f02_tim_hang_con_phong.sql
-- Check invalid objects
SELECT object_name, object_type, status FROM user_objects WHERE status <> 'VALID';
SELECT name, type, line, text FROM user_errors ORDER BY name, sequence;
EXIT;
EOF
