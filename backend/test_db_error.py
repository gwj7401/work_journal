# -*- coding: utf-8 -*-
import sys
sys.path.append('f:\\work-journal\\backend')

from database import SessionLocal
from models.user import User
from auth import get_password_hash
import traceback

def main():
    db = SessionLocal()
    try:
        user = User(
            username="test_user_for_debug",
            password_hash=get_password_hash("123"),
            display_name="Debug User",
            email="test@test.com",
            dept="质检部"
        )
        db.add(user)
        db.commit()
        print("Success: Inserted test user.")
    except Exception as e:
        print("Error encountered:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
