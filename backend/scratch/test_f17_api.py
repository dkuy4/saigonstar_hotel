import httpx
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(timeout=10.0)

def print_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    if not passed:
        sys.exit(1)

def run_tests():
    print("=== BAT DAU KIEM THU F17: QUAN LY TAI KHOAN NHAN VIEN ===")

    # 1. Dang nhap cac tai khoan mau
    res_mgr = client.post(f"{BASE_URL}/auth/login", json={"username": "quanly", "password": "QuanLy123#"})
    assert res_mgr.status_code == 200, f"Manager login failed: {res_mgr.text}"
    mgr_token = res_mgr.json()["token"]
    mgr_id = res_mgr.json()["user"]["id"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    res_letan = client.post(f"{BASE_URL}/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res_letan.status_code == 200, f"Receptionist login failed: {res_letan.text}"
    letan_token = res_letan.json()["token"]
    letan_headers = {"Authorization": f"Bearer {letan_token}"}

    print_test("Dang nhap tai khoan quan ly va le tan", True)

    # 2. Phan quyen: Khong co token -> 401
    res = client.get(f"{BASE_URL}/users")
    print_test("Khong token truy cap /users tra ve 401", res.status_code == 401, f"Status: {res.status_code}")

    # 3. Phan quyen: Token le tan -> 403 FORBIDDEN
    res = client.get(f"{BASE_URL}/users", headers=letan_headers)
    print_test("Le tan truy cap /users tra ve 403", res.status_code == 403, f"Status: {res.status_code}")

    # 4. Quan ly lay danh sach nguoi dung -> 200
    res = client.get(f"{BASE_URL}/users", headers=mgr_headers)
    print_test("Quan ly truy cap /users tra ve 200", res.status_code == 200 and res.json().get("success"), f"Total: {res.json().get('total')}")
    users_list = res.json()["data"]
    assert any(u["tenDangNhap"] == "quanly" for u in users_list)

    # 5. Rule 3: Kiem tra validation dau vao
    # Username sai quy cach (chu hoa hoac ky tu dac biet)
    res = client.post(f"{BASE_URL}/users", headers=mgr_headers, json={
        "tenDangNhap": "Invalid Name!",
        "hoTen": "Nhan Vien Test",
        "vaiTro": "LE_TAN"
    })
    print_test("Tao user voi tenDangNhap sai dinh dang tra ve 422", res.status_code == 422)

    # Vai tro khong hop le
    res = client.post(f"{BASE_URL}/users", headers=mgr_headers, json={
        "tenDangNhap": "user_role_invalid",
        "hoTen": "Nhan Vien Test",
        "vaiTro": "GIAM_DOC"
    })
    print_test("Tao user voi vaiTro khong hop le tra ve 422", res.status_code == 422)

    # 6. Tao tai khoan moi voi mat khau sinh ngau nhien
    test_username = "test_staff_f17"
    # Don dep truoc neu da ton tai
    existing_user = next((u for u in users_list if u["tenDangNhap"] == test_username), None)
    if existing_user:
        test_user_id = existing_user["id"]
    else:
        res = client.post(f"{BASE_URL}/users", headers=mgr_headers, json={
            "tenDangNhap": test_username,
            "hoTen": "Nguyen Van Test F17",
            "vaiTro": "LE_TAN"
        })
        print_test("Quan ly tao tai khoan le tan moi thanh cong (200)", res.status_code == 200, res.text)
        created_data = res.json()
        assert created_data["success"] is True
        temp_pwd = created_data["matKhauTam"]
        assert len(temp_pwd) >= 12, f"Mat khau tam phai >= 12 ky tu: {temp_pwd}"
        assert created_data["user"]["phaiDoiMatKhau"] is True
        test_user_id = created_data["user"]["id"]
        print_test("Mat khau tam du manh va co phaiDoiMatKhau=True", True, f"MatKhauTam: {temp_pwd}")

        # Rule 3: Tranh trung ten dang nhap -> 409 USERNAME_EXISTS
        res_dup = client.post(f"{BASE_URL}/users", headers=mgr_headers, json={
            "tenDangNhap": test_username,
            "hoTen": "Nguyen Van Test Trung",
            "vaiTro": "BUONG_PHONG"
        })
        print_test("Tao trung tenDangNhap tra ve 409 USERNAME_EXISTS", res_dup.status_code == 409 and res_dup.json().get("code") == "USERNAME_EXISTS")

    # 7. Dat lai mat khau cho test user de co mat khau tam moi xac dinh
    res_reset = client.post(f"{BASE_URL}/users/{test_user_id}/reset-password", headers=mgr_headers)
    print_test("Dat lai mat khau cho nhan vien tra ve 200", res_reset.status_code == 200)
    temp_pwd = res_reset.json()["matKhauTam"]

    # 8. Rule 5: Dang nhap voi mat khau tam -> phaiDoiMatKhau=True
    res_login_temp = client.post(f"{BASE_URL}/auth/login", json={"username": test_username, "password": temp_pwd})
    print_test("Dang nhap bang mat khau tam thanh cong", res_login_temp.status_code == 200)
    assert res_login_temp.json()["user"]["phaiDoiMatKhau"] is True
    temp_staff_token = res_login_temp.json()["token"]
    temp_staff_headers = {"Authorization": f"Bearer {temp_staff_token}"}

    # Rule 5: Goi cac API nghiep vu khac bi chan 403 PASSWORD_CHANGE_REQUIRED
    res_blocked = client.get(f"{BASE_URL}/rooms/board", headers=temp_staff_headers)
    print_test("User chua doi mat khau goi API bi chan 403 PASSWORD_CHANGE_REQUIRED", 
               res_blocked.status_code == 403 and res_blocked.json().get("code") == "PASSWORD_CHANGE_REQUIRED",
               f"Code: {res_blocked.json().get('code')}")

    # API /auth/me duoc phep
    res_me = client.get(f"{BASE_URL}/auth/me", headers=temp_staff_headers)
    print_test("User chua doi mat khau goi /auth/me duoc phep", res_me.status_code == 200 and res_me.json()["user"]["phaiDoiMatKhau"] is True)

    # Doi mat khau thanh cong qua /auth/change-password
    new_staff_pwd = "NewStaffPassword123#"
    res_change = client.post(
        f"{BASE_URL}/auth/change-password",
        headers=temp_staff_headers,
        json={"current_password": temp_pwd, "new_password": new_staff_pwd}
    )
    print_test("Doi mat khau moi thanh cong", res_change.status_code == 200)

    # Sau khi doi mat khau, goi lai API nghiep vu -> Thanh cong!
    res_unblocked = client.get(f"{BASE_URL}/rooms/board", headers=temp_staff_headers)
    print_test("Sau khi doi mat khau, goi API nghiep vu thanh cong (200)", res_unblocked.status_code == 200)

    # 9. Rule 1: Khong duoc tu khoa chinh minh
    res_self_lock = client.post(f"{BASE_URL}/users/{mgr_id}/lock", headers=mgr_headers, json={"khoa": True})
    print_test("Tu khoa chinh minh tra ve 409 SELF_LOCK_NOT_ALLOWED", 
               res_self_lock.status_code == 409 and res_self_lock.json().get("code") == "SELF_LOCK_NOT_ALLOWED")

    # Rule 1: Khong duoc tu doi vai tro cua chinh minh
    res_self_role = client.put(f"{BASE_URL}/users/{mgr_id}", headers=mgr_headers, json={
        "hoTen": "Quan Ly SaigonStar",
        "vaiTro": "LE_TAN"
    })
    print_test("Tu doi vai tro chinh minh tra ve 409 SELF_ROLE_CHANGE_NOT_ALLOWED",
               res_self_role.status_code == 409 and res_self_role.json().get("code") == "SELF_ROLE_CHANGE_NOT_ALLOWED")

    # 10. Rule 2: Khong duoc khoa hoac ha vai tro quan ly cuoi cung
    res_all_users = client.get(f"{BASE_URL}/users", headers=mgr_headers).json()["data"]
    active_mgrs = [u for u in res_all_users if u["vaiTro"] == "QUAN_LY" and u["trangThai"] == "HOAT_DONG"]
    if len(active_mgrs) == 1:
        # Quan ly cuoi cung
        target_mgr = active_mgrs[0]
        # Thu tao 1 quan ly thu 2 de test
        res_m2 = client.post(f"{BASE_URL}/users", headers=mgr_headers, json={
            "tenDangNhap": "test_mgr_2",
            "hoTen": "Quan Ly Phu",
            "vaiTro": "QUAN_LY"
        })
        m2_id = res_m2.json()["user"]["id"]
        # Gio co 2 quan ly. Khoa m2 -> thanh cong
        res_lock_m2 = client.post(f"{BASE_URL}/users/{m2_id}/lock", headers=mgr_headers, json={"khoa": True})
        print_test("Khoa quan ly thu hai khi con quan ly khac hoat dong -> Thanh cong", res_lock_m2.status_code == 200)

        # Gio chi con 1 quan ly hoat dong (mgr_id). Neu thu ha vai tro cua quan ly duy nhat con lai:
        # Mo khoa m2, roi ha vai tro m2 ve LE_TAN -> thanh cong
        client.post(f"{BASE_URL}/users/{m2_id}/lock", headers=mgr_headers, json={"khoa": False})
        res_demote_m2 = client.put(f"{BASE_URL}/users/{m2_id}", headers=mgr_headers, json={
            "hoTen": "Quan Ly Phu",
            "vaiTro": "LE_TAN"
        })
        print_test("Ha vai tro quan ly thu hai ve LE_TAN -> Thanh cong", res_demote_m2.status_code == 200)

    # 11. Rule 4: Khoa tai khoan co hieu luc ngay lap tuc
    # Khoa tai khoan test_staff_f17
    res_lock = client.post(f"{BASE_URL}/users/{test_user_id}/lock", headers=mgr_headers, json={"khoa": True})
    print_test("Khoa tai khoan test_staff_f17 thanh cong", res_lock.status_code == 200 and res_lock.json()["user"]["trangThai"] == "KHOA")

    # Dung token dang co cua test_staff goi ngay mot API -> Tra ve 403 AUTH_ACCOUNT_LOCKED
    res_locked_token = client.get(f"{BASE_URL}/rooms/board", headers=temp_staff_headers)
    print_test("Tai khoan vua bi khoa dung token cu goi API bi tu choi ngay lap tuc 403",
               res_locked_token.status_code == 403 and res_locked_token.json().get("code") == "AUTH_ACCOUNT_LOCKED",
               f"Code: {res_locked_token.json().get('code')}")

    # Mo khoa tai khoan test_staff_f17
    res_unlock = client.post(f"{BASE_URL}/users/{test_user_id}/lock", headers=mgr_headers, json={"khoa": False})
    print_test("Mo khoa tai khoan test_staff_f17 thanh cong", res_unlock.status_code == 200 and res_unlock.json()["user"]["trangThai"] == "HOAT_DONG")

    # Sau khi mo khoa, token hop le tro lai
    res_reunlocked = client.get(f"{BASE_URL}/rooms/board", headers=temp_staff_headers)
    print_test("Sau khi mo khoa, goi API binh thuong tro lai (200)", res_reunlocked.status_code == 200)

    # 12. Cap nhat thong tin tai khoan (hoTen, vaiTro)
    res_update = client.put(f"{BASE_URL}/users/{test_user_id}", headers=mgr_headers, json={
        "hoTen": "Nguyen Van Test F17 Cap Nhat",
        "vaiTro": "BUONG_PHONG"
    })
    print_test("Cap nhat ho ten va vai tro thanh cong", 
               res_update.status_code == 200 
               and res_update.json()["user"]["hoTen"] == "Nguyen Van Test F17 Cap Nhat"
               and res_update.json()["user"]["vaiTro"] == "BUONG_PHONG")

    print("\n=== TAT CA CAC TEST CHO F17 DA HOAN TAT XUAT SAC ===")

if __name__ == "__main__":
    run_tests()
