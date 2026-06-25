#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库服务层
提供知识库相关的业务逻辑处理
"""
import uuid
import time
import re
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from backend.model.knowledge_library import KnowledgeLibrary, KnowledgeDocument
from backend.param.knowledge_library import (
    CreateLibraryRequest, UpdateLibraryRequest, AddDocumentRequest, UpdateDocumentRequest
)
from backend.param.common import Response
from backend.config.log import get_logger
from backend.config.database import DatabaseFactory
from backend.config.embedding import get_embedding_model
from backend.rag.chunks.chunks import TextChunker
from backend.rag.chunks.document_extraction import DocumentExtractor
from backend.rag.chunks.models import ChunkConfig, ChunkStrategy, DocumentContent
from backend.rag.storage.milvus_storage import MilvusStorage
from backend.rag.storage.lightrag_storage import LightRAGStorage

logger = get_logger(__name__)


def _safe_filename(filename: str) -> str:
    name = Path(filename or "uploaded_document").name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


async def get_user_libraries(user_id: str) -> Response:
    """获取用户的知识库列表"""
    db = None
    try:
        logger.info(f"开始获取用户 {user_id} 的知识库列表")
        db = DatabaseFactory.create_session()
        
        libraries = db.query(KnowledgeLibrary).filter(
            KnowledgeLibrary.user_id == user_id,
            KnowledgeLibrary.is_active == True
        ).order_by(KnowledgeLibrary.updated_at.desc()).all()
        
        result = []
        for library in libraries:
            library_dict = library.to_dict()
            # 添加文档数量统计
            library_dict['document_count'] = len(library.documents) if library.documents else 0
            result.append(library_dict)
        
        logger.info(f"成功获取用户 {user_id} 的知识库列表，共 {len(result)} 个")
        return Response.success(result)
        
    except Exception as e:
        logger.error(f"获取用户知识库列表失败: {str(e)}")
        return Response.error(f"获取知识库列表失败: {str(e)}")
    finally:
        if db:
            db.close()


async def get_library_detail(library_id: int, user_id: str) -> Response:
    """获取知识库详情"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            library = session.query(KnowledgeLibrary).filter(
                KnowledgeLibrary.id == library_id,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if not library:
                return Response.error("知识库不存在或无权限访问")
            
            logger.info(f"成功获取知识库详情: {library.title}")
            return Response.success(library.to_dict())
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取知识库详情失败: {str(e)}")
        return Response.error(f"获取知识库详情失败: {str(e)}")


async def create_library(request: CreateLibraryRequest, user_id: str) -> Response:
    """创建知识库"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            # 检查同名知识库
            existing = session.query(KnowledgeLibrary).filter(
                KnowledgeLibrary.title == request.title,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if existing:
                return Response.error("已存在同名知识库")
            
            # 创建新知识库
            library = KnowledgeLibrary(
                title=request.title,
                description=request.description,
                user_id=user_id
            )
            
            session.add(library)
            session.commit()
            session.refresh(library)
            
            # 生成collection_id: kb + 知识库ID + 下划线 + 时间戳
            timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
            collection_id = f"kb{library.id}_{timestamp}"
            
            # 更新collection_id
            library.collection_id = collection_id
            session.commit()
            session.refresh(library)
            
            logger.info(f"成功创建知识库: {library.title}")
            return Response.success(library.to_dict())
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"创建知识库失败: {str(e)}")
        return Response.error(f"创建知识库失败: {str(e)}")


async def update_library(library_id: int, request: UpdateLibraryRequest, user_id: str) -> Response:
    """更新知识库"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            library = session.query(KnowledgeLibrary).filter(
                KnowledgeLibrary.id == library_id,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if not library:
                return Response.error("知识库不存在或无权限访问")
            
            # 更新字段
            if request.title is not None:
                # 检查同名知识库（排除当前库）
                existing = session.query(KnowledgeLibrary).filter(
                    KnowledgeLibrary.title == request.title,
                    KnowledgeLibrary.user_id == user_id,
                    KnowledgeLibrary.id != library_id,
                    KnowledgeLibrary.is_active == True
                ).first()
                
                if existing:
                    return Response.error("已存在同名知识库")
                
                library.title = request.title
            
            if request.description is not None:
                library.description = request.description
            
            session.commit()
            session.refresh(library)
            
            logger.info(f"成功更新知识库: {library.title}")
            return Response.success(library.to_dict())
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"更新知识库失败: {str(e)}")
        return Response.error(f"更新知识库失败: {str(e)}")


async def delete_library(library_id: int, user_id: str) -> Response:
    """删除知识库"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            library = session.query(KnowledgeLibrary).filter(
                KnowledgeLibrary.id == library_id,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if not library:
                return Response.error("知识库不存在或无权限访问")
            
            # 软删除
            library.is_active = False
            session.commit()
            
            logger.info(f"成功删除知识库: {library.title}")
            return Response.success({"message": "知识库删除成功"})
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"删除知识库失败: {str(e)}")
        return Response.error(f"删除知识库失败: {str(e)}")


async def add_document(request: AddDocumentRequest, user_id: str) -> Response:
    """添加文档到知识库"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            # 验证知识库权限
            library = session.query(KnowledgeLibrary).filter(
                KnowledgeLibrary.id == request.library_id,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if not library:
                return Response.error("知识库不存在或无权限访问")
            
            # 创建文档
            document = KnowledgeDocument(
                library_id=request.library_id,
                name=request.name,
                type=request.type,
                url=request.url,
                file_path=request.file_path,
                file_size=request.file_size
            )
            
            session.add(document)
            session.commit()
            session.refresh(document)
            
            logger.info(f"成功添加文档到知识库 {library.title}: {document.name}")
            return Response.success(document.to_dict())
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"添加文档失败: {str(e)}")
        return Response.error(f"添加文档失败: {str(e)}")


async def upload_document_file(library_id: int, name: Optional[str], file: UploadFile, user_id: str) -> Response:
    """上传文件到知识库，并在后台写入 Milvus 和 LightRAG。"""
    db = None
    saved_path = None
    try:
        db = DatabaseFactory.create_session()
        library = db.query(KnowledgeLibrary).filter(
            KnowledgeLibrary.id == library_id,
            KnowledgeLibrary.user_id == user_id,
            KnowledgeLibrary.is_active == True
        ).first()

        if not library:
            return Response.error("知识库不存在或无权限访问")

        original_filename = _safe_filename(file.filename)
        file_suffix = Path(original_filename).suffix.lower()
        if file_suffix not in [".pdf", ".doc", ".docx", ".md", ".txt"]:
            return Response.error(f"不支持的文件格式: {file_suffix or '未知'}")

        upload_dir = Path("/tmp/rag_uploads") / library.collection_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_path = upload_dir / f"{uuid.uuid4().hex}_{original_filename}"

        file_bytes = await file.read()
        if not file_bytes:
            return Response.error("上传文件为空")

        saved_path.write_bytes(file_bytes)
        logger.info(f"文件已保存: {saved_path}")

        document_name = name or original_filename
        document = KnowledgeDocument(
            library_id=library.id,
            name=document_name,
            type="file",
            url=None,
            file_path=str(saved_path),
            file_size=len(file_bytes),
            is_processed=False
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        document_data = document.to_dict()
        collection_id = library.collection_id

        asyncio.create_task(
            process_uploaded_document_file(
                document_id=document.id,
                collection_id=collection_id,
                document_name=document_name,
                saved_path=str(saved_path)
            )
        )

        logger.info(f"文件上传成功，后台入库任务已启动: library={library.title}, document={document.name}")
        return Response.success_with_msg(document_data, "文件已上传，正在后台解析并生成知识图谱")

    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return Response.error(f"文件上传失败: {str(e)}")
    finally:
        if db:
            db.close()


async def process_uploaded_document_file(
    document_id: int,
    collection_id: str,
    document_name: str,
    saved_path: str
) -> None:
    """后台处理上传文件：解析、分块、写入 Milvus 和 LightRAG。"""
    db = None
    try:
        logger.info(f"后台开始处理上传文件: document_id={document_id}, path={saved_path}")

        extractor = DocumentExtractor()
        doc_content = extractor.read_document(saved_path)
        if not doc_content.content or not doc_content.content.strip():
            logger.error(f"文件解析结果为空，未写入知识库: document_id={document_id}")
            return

        milvus_storage = MilvusStorage(
            embedding_function=get_embedding_model(),
            collection_name=collection_id,
        )
        lightrag_storage = LightRAGStorage(workspace=collection_id)

        chunker = TextChunker()
        chunk_config = ChunkConfig(
            strategy=ChunkStrategy.RECURSIVE,
            chunk_size=800,
            chunk_overlap=100
        )
        chunk_result = chunker.chunk_document(
            DocumentContent(content=doc_content.content, document_name=document_name),
            chunk_config
        )

        if chunk_result is None or not chunk_result.chunks:
            logger.error(f"文件解析成功，但分块结果为空: document_id={document_id}")
            return

        milvus_storage.store_chunks_batch([chunk_result])
        logger.info(f"成功存储文件分块到Milvus，共 {len(chunk_result.chunks)} 个分块")

        text_chunks = [chunk.page_content for chunk in chunk_result.chunks if chunk.page_content.strip()]
        await lightrag_storage.insert_texts(text_chunks)
        logger.info("成功存储文件分块到LightRAG")

        db = DatabaseFactory.create_session()
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not document:
            logger.warning(f"后台处理完成，但文档记录不存在: document_id={document_id}")
            return

        document.is_processed = True
        db.commit()
        logger.info(f"后台文件入库完成: document_id={document_id}, document={document.name}")

    except Exception as e:
        logger.error(f"后台文件入库失败: document_id={document_id}, error={str(e)}")
    finally:
        if db:
            db.close()


async def update_document(document_id: int, request: UpdateDocumentRequest, user_id: str) -> Response:
    """更新文档"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            # 查询文档并验证权限
            document = session.query(KnowledgeDocument).join(KnowledgeLibrary).filter(
                KnowledgeDocument.id == document_id,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if not document:
                return Response.error("文档不存在或无权限访问")
            
            # 更新字段
            if request.name is not None:
                document.name = request.name
            if request.type is not None:
                document.type = request.type
            if request.url is not None:
                document.url = request.url
            if request.file_path is not None:
                document.file_path = request.file_path
            if request.file_size is not None:
                document.file_size = request.file_size
            
            session.commit()
            session.refresh(document)
            
            logger.info(f"成功更新文档: {document.name}")
            return Response.success(document.to_dict())
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"更新文档失败: {str(e)}")
        return Response.error(f"更新文档失败: {str(e)}")


async def delete_document(document_id: int, user_id: str) -> Response:
    """删除文档"""
    try:
        db_factory = DatabaseFactory()
        session = db_factory.create_session()
        
        try:
            # 查询文档并验证权限
            document = session.query(KnowledgeDocument).join(KnowledgeLibrary).filter(
                KnowledgeDocument.id == document_id,
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            ).first()
            
            if not document:
                return Response.error("文档不存在或无权限访问")
            
            # 物理删除文档
            session.delete(document)
            session.commit()
            
            logger.info(f"成功删除文档: {document.name}")
            return Response.success({"message": "文档删除成功"})
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        return Response.error(f"删除文档失败: {str(e)}")
