from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from typing import Optional
import pymysql
from uuid import uuid4
from routers.common import *

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

class LoginForm(BaseModel):
    id: str = None
    password: str = None

class RegisterField(BaseModel):
    id: str = None
    name: str = None
    std_no: str = None
    password: str = None
    email: str = None
    country: str = None
    college: str = None
    major: str = None

class RandomUserInfoFilter(BaseModel):
    blacklist: Optional[list] = None


if True: # 로그인
    # 로그인
    @router.post("/login")
    def login(item: LoginForm, response: Response, session_id: Optional[str] = Cookie(None)):
        if (is_session_valid(session_id)):
            return {"result" : "fail", "detail": "already_logged_in"}

        if not (item.id and item.password):
            return {"result" : "fail", "detail": "invalid"}
        
        conn, cur = connect_db()

        query = 'SELECT count(*) FROM user WHERE id=%s and password=%s'
        cur.execute(query, (item.id, item.password))
        row = cur.fetchone()

        if row[0] == 1:
            query = 'SELECT std_no FROM user WHERE id=%s'
            cur.execute(query, (item.id))
            row = cur.fetchone()

            sess = gen_sess()
            sessData[sess] = {"id":item.id, "std_no":row[0]}
            cookie = f"session_id={sess}; Path=/; SameSite=None;Secure; HttpOnly"
            print(sess)

            response.headers["Set-Cookie"]= cookie

            conn.close()
            return {"result" : "success"}
        elif row[0] < 1:
            conn.close()
            return {"result" : "fail", "detail": "not_found"}
        else:
            conn.close()
            return {"result" : "fail", "detail": "unknown"}

    # 로그아웃
    @router.get("/logout")
    @router.post("/logout")
    def logout(response: Response, session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}
        cookie = "session_id=deleted; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly"
        response.headers["Set-Cookie"]= cookie
        return {"result" : "success"}

    # 회원가입
    @router.post("/register")
    def register(registerField: RegisterField):
        if not (registerField.id and registerField.name and registerField.std_no \
                and registerField.password and registerField.email and registerField.country \
                and registerField.college and registerField.major):
            return {"result" : "fail", "detail": "invalid"}

        conn, cur = connect_db()

        query = 'SELECT count(*) FROM user WHERE id=%s or std_no=%s'
        cur.execute(query, (registerField.id, registerField.std_no))
        row = cur.fetchone()
        
        if row[0] == 0:

            #INSERT INTO user VALUES("donghwi04", "Leedonghwi", "2023019516", "dlehdgnl04*", "donghwi04@naver.com")
            query = 'INSERT INTO user VALUES(%s, %s, %s, %s, %s)'
            cur.execute(query, (registerField.id, registerField.name, registerField.std_no, \
                                registerField.password, registerField.email))
            
            #INSERT INTO profile VALUES("2023019516", "KR", "IT", "CSE", "{Introduction}", "{img_src}", 1);
            query = 'INSERT INTO profile VALUES(%s, %s, %s, %s, %s, %s, %s)'
            cur.execute(query, (registerField.std_no, registerField.country, \
                        registerField.college, registerField.major, "", "", 1))
            conn.commit()

            conn.close()
            return {"result" : "success"}
        else:
            conn.close()
            return {"result" : "fail", "detail": "exist_account"}

if True: # 조회
    # 자기 유저 정보 조회 (학번 포함됨)
    @router.get("/userInfo")
    def userInfo(session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}
        
        conn, cur = connect_db()

        query = 'SELECT a.id, a.name, a.std_no, b.college, b.major, b.country, b.introduction, b.img, b.visible FROM user a INNER JOIN profile b ON a.std_no=b.std_no WHERE a.std_no=%s'
        cur.execute(query, (sessData[session_id]["std_no"]))
        row = cur.fetchone()
        
        conn.close()

        if not row:
            return {"result" : "not_found"}
        
        return {"result" : "success", \
                "info" : {
                    "id": row[0],
                    "name": row[1],
                    "std_no": row[2],
                    "college": row[3],
                    "major": row[4],
                    "country": row[5],
                    "introduction": row[6],
                    "img": row[7] if row[7] else DEFAULT_IMG_URL,
                    "visible": True if row[8] else False
                }}

    # 타 유저 정보 조회 (학번 제외, id 기반 검색)
    @router.get("/userInfo/{target_id:str}")
    def userInfo(target_id, session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}

        conn, cur = connect_db()

        query = 'SELECT a.id, a.name, b.college, b.major, b.country, b.introduction, b.img FROM user a INNER JOIN profile b ON a.std_no=b.std_no WHERE a.id=%s and b.visible=1'
        cur.execute(query, (target_id))
        row = cur.fetchone()
        
        conn.close()

        if not row:
            return {"result" : "fail", "detail" : "not_found"}
        
        return {"result" : "success",
                "info" : {
                    "id": row[0],
                    "name": row[1],
                    "college": row[2],
                    "major": row[3],
                    "country": row[4],
                    "introduction": row[5],
                    "img": row[6] if row[6] else DEFAULT_IMG_URL
                }}

    # 랜덤 유저 정보 (all, college, major, country)
    @router.get("/userInfo/randomSuggestion/{search_type:str}")
    @router.post("/userInfo/randomSuggestion/{search_type:str}")
    def userInfo(search_type, userFilter: RandomUserInfoFilter | None = None, session_id: Optional[str] = Cookie(None)):    
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}

        conn, cur = connect_db()

        # Get User Data For Search
        query = 'SELECT college, major, country FROM profile WHERE std_no=%s'
        cur.execute(query, (sessData[session_id]["std_no"]))
        college, major, country = cur.fetchone()
        baseFilter = {"college" : college, "major" : major, "country" : country}

        query = 'SELECT a.id, a.name, b.college, b.major, b.country, b.introduction, b.img \
                FROM user a INNER JOIN profile b ON a.std_no=b.std_no \
                WHERE b.visible=1 and a.std_no!=%s '
        searchFilter = tuple([sessData[session_id]["std_no"]])

        if userFilter and len(userFilter.blacklist) > 0:
            query += ' and a.id NOT IN (' + ('%s ' * len(userFilter.blacklist)).replace(" ", ",")[:-1] +')'
            searchFilter += tuple(userFilter.blacklist)

        if search_type in ["college", "major", "country"]:
            query += ' and b.' + search_type + '=%s'
            searchFilter += tuple([baseFilter[search_type]])
        elif search_type != "all":
            return {"result" : "fail", "detail": "invalid"}
        
        query += " ORDER BY RAND() LIMIT 10"

        print(query%searchFilter)
        cur.execute(query, searchFilter)

        rows = cur.fetchall()    
        conn.close()
        
        recved_info_list = []
        for row in rows:
            recved_info_list.append({
                    "id": row[0],
                    "name": row[1],
                    "college": row[2],
                    "major": row[3],
                    "country": row[4],
                    "introduction": row[5],
                    "img": row[6] if row[6] else DEFAULT_IMG_URL
                })

        return {"result" : "success",
                "count" : len(rows),
                "info" : recved_info_list}