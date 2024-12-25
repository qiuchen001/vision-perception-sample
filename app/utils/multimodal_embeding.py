import os
import base64
from PIL import Image
import io
import dashscope
from http import HTTPStatus
from app.utils.logger import logger


class MultiModalEmbedding:
    """通义千问多模态embedding实现"""

    def __init__(self):
        """初始化DashScope配置"""
        dashscope.api_key = os.getenv("API_KEY")

    def _image_to_base64(self, image: Image.Image) -> str:
        """将PIL Image转换为base64编码"""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def embedding_image(self, image: Image.Image):
        """生成图片的embedding向量"""
        try:
            # 将图片转换为base64
            image_b64 = self._image_to_base64(image)
            image_data = f"data:image/png;base64,{image_b64}"

            # 调用DashScope API
            resp = dashscope.MultiModalEmbedding.call(
                model="multimodal-embedding-v1",
                input=[{'image': image_data}]
            )

            if resp.status_code == HTTPStatus.OK:
                embedding = resp.output['embeddings'][0]['embedding']
                logger.info(f"成功生成图片embedding,维度:{len(embedding)}")
                return embedding
            else:
                raise Exception(f"API调用失败: {resp.code}, {resp.message}")

        except Exception as e:
            logger.error(f"生成图片embedding失败:{str(e)}")
            raise e

    def embedding_text(self, text: str):
        """生成文本的embedding向量"""
        try:
            # 调用DashScope API
            resp = dashscope.MultiModalEmbedding.call(
                model="multimodal-embedding-v1",
                input=[{'text': text}]
            )

            if resp.status_code == HTTPStatus.OK:
                embedding = resp.output['embeddings'][0]['embedding']
                logger.info(f"成功生成文本embedding,维度:{len(embedding)}")
                return embedding
            else:
                raise Exception(f"API调用失败: {resp.code}, {resp.message}")

        except Exception as e:
            logger.error(f"生成文本embedding失败:{str(e)}")
            raise e

    def embedding(self, image: Image.Image, text: str):
        """生成图文联合embedding向量"""
        image_embedding = self.embedding_image(image)
        text_embedding = self.embedding_text(text)
        return image_embedding, text_embedding


# 创建全局实例
multimodal_embedding = MultiModalEmbedding()

if __name__ == "__main__":
    # 测试代码
    image_path = "test.png"
    pil_image = Image.open(image_path)

    # 测试图片embedding
    image_embeddings = multimodal_embedding.embedding_image(pil_image)
    print(f"图片embedding维度:{len(image_embeddings)}")

    # 测试文本embedding
    text_embeddings = multimodal_embedding.embedding_text("这是一张测试图片")
    print(f"文本embedding维度:{len(text_embeddings)}")

    # 测试图文联合embedding
    img_emb, txt_emb = multimodal_embedding.embedding(pil_image, "这是一张测试图片")
    print(f"图文embedding维度:{len(img_emb)}, {len(txt_emb)}")
