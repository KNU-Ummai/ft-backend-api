from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from typing import Optional
import pymysql
from uuid import uuid4
from routers.common import *

router = APIRouter(
    prefix="/board",
    tags=["users"]
)

class writeArticleField(BaseModel):
    title: str
    content: str
    files: Optional[list] = None

if True: # 게시물 작성/조회
    # 게시물 리스트 조회
    @router.get("/article")
    def get_article_list(q:Optional[str] = None,
                            p:int = 1, session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}

        article_list = []
        rows = []

        conn, cur = connect_db()
        query_params = tuple()

        if not (p > 0):
            p = 1
        offset = (p-1) * 20
        query_params += tuple([offset])

        conditions = ""
        if q and len(q) > 0:
            search_term = q.strip()
            conditions = " WHERE author LIKE %s or title LIKE %s or content LIKE %s"
            query_params = tuple(["%"+search_term+"%" for x in range(3)]) + query_params

        query = 'SELECT article_id, title, content FROM tip_board ' \
                    + conditions + 'ORDER BY article_id DESC LIMIT 20 OFFSET %s'
        
        print(query% query_params)
        cur.execute(query, query_params)
        rows = cur.fetchall()
        conn.close()

        article_list = []
        for row in rows:
            article_list.append({
                "article_id": row[0],
                "title": row[1],
                "content": row[2] if len(row[2]) < 20 else row[2][:20] + "..."
            })
        
        return {
            "result":"success",
            "count":len(rows),
            "articles":article_list
        }
    
    # 게시물 내용 조회
    @router.get("/article/{article_id:int}")
    def get_article_list(article_id:int, q:Optional[str] = None,
                            p:int = 1, session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}

        conn, cur = connect_db()

        query = 'SELECT article_id, title, content, \
                    author, files, scrap_count FROM tip_board WHERE article_id=%s'
        cur.execute(query, article_id)
        row = cur.fetchone()
        conn.close()

        if not row:
            return {"result": "fail", "detail": "not_found"}
        
        return {
            "result":"success",
            "info":{
                "article_id": row[0],
                "title": row[1],
                "content": row[2],
                "author": row[3],
                "files": eval(row[4]),
                "scrap_count": row[5]
            }
        }
    
    # 게시물 작성
    @router.post("/article")
    def get_article_list(article_param:writeArticleField,
                            session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}
        
        conn, cur = connect_db()
        query_params = tuple()


        # 기본 값들 Setup
        std_no = sessData[session_id]["std_no"]
        id = sessData[session_id]["id"]

        files = article_param.files if article_param.files else []

        query_params += (
            None, article_param.title,
            article_param.content, std_no, id, str(files), 0
        )
        
        # article_id, title, content, std_no, file, scrap_count
        query = 'INSERT INTO tip_board \
                    VALUES(%s, %s, %s, %s, %s, %s, %s)'
        cur.execute(query, query_params)
        conn.commit()
        
        cur.execute('SELECT article_id FROM tip_board WHERE std_no=%s ORDER BY article_id DESC', sessData[session_id]["std_no"])
        article_id = cur.fetchone()[0]
        conn.close()

        return {
            "result":"success",
            "article_id":article_id
        }
        
    # 게시물 삭제
    @router.delete("/article/{article_id:int}")
    def get_article_list(article_id,
                            session_id: Optional[str] = Cookie(None)):
        if not is_session_valid(session_id):
            return {"result" : "fail", "detail": "no_sessions"}
        
        conn, cur = connect_db()
        query_params = tuple()


        # 삭제 대상 조회
        cur.execute('SELECT std_no FROM tip_board WHERE article_id=%s LIMIT 1', article_id)
        row = cur.fetchone()
        if not row:
            return {"result": "fail", "detail": "not_found"}
        
        if row[0] != sessData[session_id]["std_no"]:
            return {"result": "fail", "detail": "unauthorized"}
               
        query = 'DELETE FROM tip_board WHERE article_id=%s'
        cur.execute(query, article_id)
        query = 'DELETE FROM tip_reply WHERE article_id=%s'
        cur.execute(query, article_id)
        conn.commit()

        conn.close()

        return {"result":"success"}