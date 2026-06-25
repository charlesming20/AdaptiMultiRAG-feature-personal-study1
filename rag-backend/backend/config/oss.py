import os
from datetime import timedelta
import alibabacloud_oss_v2  as oss
from threading import Lock
from dotenv import load_dotenv



class OssClientFactory:
    _instance = None
    _lock = Lock()

    @classmethod # 类方法，第一个参数是类本身 (cls)，可以访问类变量和调用其他类方法，常用于工厂方法或替代构造函数。
    def get_client(cls):
        """
        获取 OSS Client 的单例实例
        """
        if cls._instance is None:
            with cls._lock:  # 线程安全
                if cls._instance is None:  # Double check
                    # 加载凭证
                    credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()

                    # 默认配置
                    cfg = oss.config.load_default()
                    cfg.credentials_provider = credentials_provider

                    # 从环境变量里获取 region / endpoint
                    cfg.region = os.getenv('OSS_REGION', 'oss-cn-shanghai')
                    endpoint = os.getenv('OSS_ENDPOINT')
                    if endpoint:
                        cfg.endpoint = endpoint

                    cls._instance = oss.Client(cfg)

        return cls._instance



# 只管用这里的两个方法就行了，第一个是获取上传文件到指定桶的url，key是文件名，第二个就是获取一个对应的下载url，这个url就是提供给mineru那边下载的
# bucket目前有两个，一个是ragagent-file，一个是ragagent-image，你给mineru的先放到第一个就行，第二个是本来我打算放用户聊天图片的
# 因为你后端需要直接上传文件，所以在demo包里提供了一个使用request库直接使用预签名上传url和本地filepath上传的示例，不一定对，可以参考

def get_presigned_url_for_upload(bucket: str, key: str, expire_seconds: int = 3600):
    """
    通过工厂函数获取 client，并生成预签名 URL
    """
    # 这里自动加载 .env 文件
    load_dotenv()

    client = OssClientFactory.get_client()
    pre_result = client.presign( # 调用 OSS 客户端的 presign 方法生成预签名 URL。
        oss.PutObjectRequest(bucket=bucket, key=key), # 指定要上传的对象信息，包括存储桶和对象键。
        expires=timedelta(seconds=expire_seconds) # 设置预签名 URL 的过期时间。
    )

    return {
        "method": pre_result.method,
        "expiration": pre_result.expiration.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "url": pre_result.url,
        "signed_headers": dict(pre_result.signed_headers)
    }

def get_presigned_url_for_download(bucket: str, key: str, expire_seconds: int = 3600):
    """
    通过工厂函数获取 client，并生成预签名 URL
    """
    # 这里自动加载 .env 文件
    load_dotenv()
    client = OssClientFactory.get_client()
    pre_result = client.presign(
        oss.GetObjectRequest(bucket=bucket, key=key),
        expires=timedelta(seconds=expire_seconds)
    )

    # 打印预签名请求的方法、过期时间和URL
    return {
        'method': pre_result.method,
        'expiration': pre_result.expiration.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        'url': pre_result.url
    }


if __name__ == "__main__":
    # 使用示例
    result = get_presigned_url_for_upload(bucket="ragagent-file", key="test.md")
    print(result)
