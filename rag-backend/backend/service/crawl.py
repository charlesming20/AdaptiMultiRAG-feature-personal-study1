import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, DefaultMarkdownGenerator, BrowserConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
from crawl4ai.content_filter_strategy import LLMContentFilter, PruningContentFilter, RelevantContentFilter
from backend.param.crawl import CrawlRequest
from backend.rag.storage.milvus_storage import MilvusStorage
from backend.rag.storage.lightrag_storage import LightRAGStorage
from backend.config.embedding import get_embedding_model
from backend.rag.chunks.chunks import ChunkResult, TextChunker
from backend.rag.chunks.models import ChunkConfig, ChunkStrategy, DocumentContent
from backend.config.log import get_logger
from backend.config.redis import get_redis_client
import asyncio
import subprocess


# 获取logger实例
logger = get_logger("crawl_service")

# 定义爬虫状态常量
CRAWL_STATUS_PROCESSING = "processing"
CRAWL_STATUS_COMPLETED = "completed"
CRAWL_STATUS_ERROR = "error"

async def initialize_collection_and_store(request: CrawlRequest):
    milvus_storage = MilvusStorage(
        embedding_function=get_embedding_model(),
        collection_name=request.collection_id,
    )

    lightrag_storage = LightRAGStorage(workspace=request.collection_id)
    
    
    # 初始化爬虫状态
    await init_crawl_status(request.collection_id)
    
    # 为对应的知识库添加文档记录
    from backend.service.knowledge_library import add_document
    from backend.param.knowledge_library import AddDocumentRequest
    from backend.config.database import DatabaseFactory
    from backend.model.knowledge_library import KnowledgeLibrary, KnowledgeDocument
    
    try:
        # 根据collection_id查找知识库
        db = DatabaseFactory.create_session()
        library = db.query(KnowledgeLibrary).filter(
            KnowledgeLibrary.collection_id == request.collection_id,
            KnowledgeLibrary.is_active == True
        ).first()
        
        if library:
            existing_doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.library_id == library.id,
                KnowledgeDocument.url == request.url
            ).first()

            if existing_doc:
                logger.info(f"文档记录已存在，跳过重复添加: {existing_doc.name}")
            else:
                # 创建文档记录
                doc_request = AddDocumentRequest(
                    library_id=library.id,
                    name=request.title or "爬虫文档",
                    type="link",  # 爬虫类型为链接
                    url=request.url
                )
                
                # 添加文档到知识库
                await add_document(doc_request, library.user_id)
                logger.info(f"成功为知识库 {library.title} 添加文档记录: {request.title or '爬虫文档'}")
        else:
            logger.warning(f"未找到collection_id为 {request.collection_id} 的知识库")
            
    except Exception as e:
        logger.error(f"添加文档记录失败: {str(e)}")
    finally:
        if db:
            db.close()
    
    try:
        processed_count = await crawl_doc(request.url, request.prefix, request.if_llm, request.model_id, request.provider, request.base_url, request.api_key, milvus_storage, lightrag_storage, request.collection_id)
        # await test_crawl_doc(request.url, request.prefix, request.if_llm, request.model_id, request.provider, request.base_url, request.api_key)
        # 爬虫完成，且至少成功处理一个页面时才标记为已完成
        if processed_count > 0:
            await update_crawl_status(request.collection_id, CRAWL_STATUS_COMPLETED)
        else:
            await update_crawl_status(request.collection_id, CRAWL_STATUS_ERROR, "未成功处理任何页面")
    except Exception as e:
        # 爬虫异常，更新状态为错误
        await update_crawl_status(request.collection_id, CRAWL_STATUS_ERROR, str(e))
        raise


async def init_crawl_status(collection_id: str):
    """初始化爬虫状态"""
    redis_client = await get_redis_client()
    status_data = {
        "status": CRAWL_STATUS_PROCESSING,
        "count": 0,
        "message": "爬虫任务开始",
        "start_time": datetime.now().isoformat(),
        "last_update": datetime.now().isoformat()
    }
    await redis_client.set(f"crawl_status:{collection_id}", json.dumps(status_data))
    logger.info(f"初始化爬虫状态: {collection_id}")


async def update_crawl_status(collection_id: str, status: str, message: str = None, count: int = None):
    """更新爬虫状态"""
    redis_client = await get_redis_client()
    
    # 获取当前状态
    current_status = await redis_client.get(f"crawl_status:{collection_id}")
    if current_status:
        status_data = json.loads(current_status)
    else:
        status_data = {
            "status": status,
            "count": 0,
            "message": message or "",
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    
    # 更新状态数据
    status_data["status"] = status
    status_data["last_update"] = datetime.now().isoformat()
    
    if message:
        status_data["message"] = message
    
    if count is not None:
        status_data["count"] = count
    
    await redis_client.set(f"crawl_status:{collection_id}", json.dumps(status_data))
    logger.info(f"更新爬虫状态: {collection_id} - {status}")


async def increment_crawl_count(collection_id: str):
    """增加爬虫计数"""
    redis_client = await get_redis_client()
    
    current_status = await redis_client.get(f"crawl_status:{collection_id}")
    if current_status:
        status_data = json.loads(current_status)
        status_data["count"] = status_data.get("count", 0) + 1
        status_data["last_update"] = datetime.now().isoformat()
        await redis_client.set(f"crawl_status:{collection_id}", json.dumps(status_data))


async def get_crawl_status(collection_id: str) -> dict:
    """
    获取爬虫状态
    
    Args:
        collection_id: 集合ID
        
    Returns:
        dict: 爬虫状态信息，包含status, count, message, start_time, last_update字段
              如果不存在该集合的状态，返回空字典
    """
    redis_client = await get_redis_client()
    
    status_data = await redis_client.get(f"crawl_status:{collection_id}")
    if status_data:
        return json.loads(status_data)
    else:
        return {}


async def get_all_crawl_status() -> dict:
    """
    获取所有爬虫状态
    
    Returns:
        dict: 所有爬虫状态，key为集合ID，value为状态信息
    """
    redis_client = await get_redis_client()
    
    # 获取所有以crawl_status:开头的key
    keys = await redis_client.keys("crawl_status:*")
    
    status_dict = {}
    for key in keys:
        # 提取集合ID
        collection_id = key.replace("crawl_status:", "")
        status_data = await redis_client.get(key)
        if status_data:
            status_dict[collection_id] = json.loads(status_data)
    
    return status_dict

async def test_crawl_doc(site: str, prefix: str, if_llm: bool, model_id: str, provider: str, base_url: str, api_token: str):
    content_filter: RelevantContentFilter
    if if_llm:
        content_filter = LLMContentFilter(
                llm_config = LLMConfig(provider=f"{provider}/{model_id}",api_token=api_token,base_url=base_url), #or use environment variable
                instruction="""
                Focus on extracting the core educational content.
                Include:
                - Key concepts and explanations
                - Important code examples
                - Essential technical details
                Exclude:
                - Navigation elements
                - Sidebars
                - Footer content
                Format the output as clean markdown with proper code blocks and headers.
                """,
                chunk_token_threshold=4096,  # Adjust based on your needs
                verbose=True # 生产时关掉
        )
    else:
        content_filter = PruningContentFilter(
                    threshold=0.4,
                    threshold_type="fixed"
                )
    md_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={"ignore_links": True,"ignore_images": True}
    )

    browser_conf = BrowserConfig(
        browser_type="chromium",
        headless=True,
        text_mode=True
    )

    prefix_filter = URLPatternFilter(
    patterns=[f"{prefix}*"]
    )
    filter_chain = FilterChain([prefix_filter])

    # Basic configuration
    bfsstrategy = BFSDeepCrawlStrategy(
        max_depth=4,               # Crawl initial page + 2 levels deep
        include_external=False,    # Stay within the same domain
        max_pages=200,              # Maximum number of pages to crawl (optional)
        # filter_chain=filter_chain
    )

        # Basic configuration
    dfsstrategy = DFSDeepCrawlStrategy(
        max_depth=8,               # Crawl initial page + 2 levels deep
        include_external=False,    # Stay within the same domain
        max_pages=200,              # Maximum number of pages to crawl (optional)
        #score_threshold=0.5,       # Minimum score for URLs to be crawled (optional)
    )

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=bfsstrategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True, #上线时关闭
        stream=True,
        markdown_generator=md_generator,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
            async for result in await crawler.arun(site, config=config):
                print(f"URL: {result.url}")
                # print(result.markdown.fit_markdown) 
                # handle_md(result.markdown.fit_markdown, type="print", path=f"{result}.md")
    print("测试完成")


async def crawl_doc(site: str, prefix: str, if_llm: bool, model_id: str, provider: str, base_url: str, api_token: str, milvus_storage: MilvusStorage, lightrag_storage: LightRAGStorage, collection_id: str):
    content_filter: RelevantContentFilter
    if if_llm:
        content_filter = LLMContentFilter(
                llm_config = LLMConfig(provider=f"{provider}/{model_id}",api_token=api_token,base_url=base_url), #or use environment variable
                instruction="""
                Focus on extracting the core educational content.
                Include:
                - Key concepts and explanations
                - Important code examples
                - Essential technical details
                Exclude:
                - Navigation elements
                - Sidebars
                - Footer content
                Format the output as clean markdown with proper code blocks and headers.
                """,
                chunk_token_threshold=4096,  # Adjust based on your needs
                verbose=True # 生产时关掉
        )
    else:
        content_filter = PruningContentFilter(
                    threshold=0.4,
                    threshold_type="fixed"
                )
    md_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={"ignore_links": True,"ignore_images": True}
    )

    browser_conf = BrowserConfig(
        browser_type="chromium",
        headless=True,
        text_mode=True
    )

    prefix_filter = URLPatternFilter(
        patterns=[f"{prefix}*"]
    )
    filter_chain = FilterChain([prefix_filter])

    # Basic configuration
    bfsstrategy = BFSDeepCrawlStrategy(
        max_depth=4,               # Crawl initial page + 2 levels deep
        include_external=False,    # Stay within the same domain
        max_pages=200,              # Maximum number of pages to crawl (optional)
        filter_chain=filter_chain
    )

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=bfsstrategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True, #上线时关闭
        stream=True,
        markdown_generator=md_generator,
    )

    processed_count = 0
    async with AsyncWebCrawler(config=browser_conf) as crawler:
            try:
                async for result in await crawler.arun(site, config=config):
                    try:
                        logger.info(f"URL: {result.url}")
                        
                        # 检查result.markdown是否存在且不为None
                        if result.markdown is None:
                            logger.warning(f"URL {result.url} 的markdown内容为空，跳过处理")
                            continue
                            
                        # 检查fit_markdown是否存在且不为空
                        if not hasattr(result.markdown, 'fit_markdown') or result.markdown.fit_markdown is None:
                            logger.warning(f"URL {result.url} 的fit_markdown内容为空，跳过处理")
                            continue
                            
                        # 检查内容是否为空字符串
                        if not result.markdown.fit_markdown.strip():
                            logger.warning(f"URL {result.url} 的内容为空，跳过处理")
                            continue
                            
                        stored = await handle_md(md_content=result.markdown.fit_markdown, type="light_and_milvus", param=[milvus_storage, lightrag_storage], collection_id=collection_id)
                        # await handle_md(md_content=result.markdown.fit_markdown, type="milvus", param=[milvus_storage], collection_id=collection_id)
                        if stored:
                            processed_count += 1
                            logger.info(f"成功处理: {result.url}")
                        else:
                            logger.warning(f"未成功存储: {result.url}")
                        
                    except Exception as e:
                        error_msg = f"处理URL {result.url} 时发生错误: {str(e)}"
                        logger.error(error_msg)
                        logger.info("跳过此URL，继续处理下一个...")
                        # 更新状态为错误
                        await update_crawl_status(collection_id, CRAWL_STATUS_ERROR, error_msg)
                        continue
                        
            except Exception as e:
                error_msg = f"爬虫运行时发生错误: {str(e)}"
                logger.error(error_msg)
                logger.info("爬虫任务中断，但程序继续运行...")
                # 更新状态为错误
                await update_crawl_status(collection_id, CRAWL_STATUS_ERROR, error_msg)
            logger.info("爬虫运行完成")
    return processed_count


async def handle_md(md_content, type="print", param=None, collection_id: str = None):
    try:
        if type == "print":
            logger.info(md_content)
            return True
        elif type == "stdio":
            with open(param, 'w') as f:
                f.write(md_content)
            return True
        elif type == "milvus":
            if param is None:
                logger.error("Milvus存储参数为空")
                return False
                
            chunker = TextChunker()
            md_config = ChunkConfig(
                strategy=ChunkStrategy.MARKDOWN_HEADER
            )
            document = DocumentContent(content=md_content, document_name="crawled_document")
            md_result = chunker.chunk_document(document, md_config)
            
            # 检查分块结果
            if md_result is None or not md_result.chunks:
                logger.warning("文档分块结果为空，跳过存储")
                return False
                
            param[0].store_chunks_batch([md_result])
            logger.info(f"成功存储文档分块，共 {len(md_result.chunks)} 个分块")
            
            # 更新爬虫计数
            if collection_id:
                await increment_crawl_count(collection_id)
            return True
                
        elif type == "light_and_milvus":
            if param is None:
                logger.error("Milvus存储参数为空")
                return False
                
            chunker = TextChunker()
            md_config = ChunkConfig(
                strategy=ChunkStrategy.MARKDOWN_HEADER
            )
            document = DocumentContent(content=md_content, document_name="crawled_document")
            md_result = chunker.chunk_document(document, md_config)
            
            # 检查分块结果
            if md_result is None or not md_result.chunks:
                logger.warning("文档分块结果为空，跳过存储")
                return False
            
            param[0].store_chunks_batch([md_result])
            logger.info(f"成功存储文档分块到Milvus，共 {len(md_result.chunks)} 个分块")
            # 将Document对象转换为字符串列表
            text_chunks = [chunk.page_content for chunk in md_result.chunks]
            await param[1].insert_texts(text_chunks)
            logger.info("成功存储文档到LightRAG")
            
            # 更新爬虫计数
            if collection_id:
                await increment_crawl_count(collection_id)
            return True
        
            
    except Exception as e:
        error_msg = f"处理markdown内容时发生错误: {str(e)}"
        logger.error(error_msg)
        logger.info("跳过此内容的处理...")
        # 更新状态为错误
        if collection_id:
            await update_crawl_status(collection_id, CRAWL_STATUS_ERROR, error_msg)
        return False
