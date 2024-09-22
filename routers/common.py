from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from typing import Optional
import pymysql
from uuid import uuid4

DEFAULT_IMG_URL = "https://cdn-icons-png.flaticon.com/512/1144/1144760.png"

sessData = {
    "4fb19538-dee8-430b-9a7f-638d98f975b7" : {"std_no":"2023019516", "id":"donghwi04"},
    "__TEST_TOKEN_GUEST__" : {"std_no":"2023011001", "id":"guest"},
    "__TEST_TOKEN_DONGHWI04__" : {"std_no":"2023019516", "id":"donghwi04"},
}

id_func = id

def connect_db():
    conn = pymysql.connect(host="127.0.0.1", user="ummai",
                password="-dnakdl2024-", db="ft_db", charset="utf8")
    cur = conn.cursor()
    return conn, cur

def gen_sess():
    return str(uuid4())

def is_session_valid(session_id): 
    if session_id and session_id in sessData.keys():
        return True
    return False