import gradio as gr
from app.services.video.search import SearchVideoService
from app import create_app
from PIL import Image
import json

# 创建Flask应用实例
config_name = "config.Config"
app = create_app(config_name)


def format_video_info(video):
    """格式化视频信息为HTML"""
    video_url = video.get('path', '')
    title = video.get('title', '未知')

    info = f"""
    <div style='margin-bottom: 10px;'>
    <strong>标题:</strong> {title}<br>
    """
    if 'timestamp' in video:
        info += f"<strong>时间戳:</strong> {video['timestamp']}秒<br>"
    if 'tags' in video and video['tags']:
        info += f"<strong>标签:</strong> {', '.join(video['tags'])}<br>"
    if 'summary_txt' in video and video['summary_txt']:
        info += f"<strong>摘要:</strong> {video['summary_txt']}<br>"
    info += "</div>"
    return info, video_url, title


def create_video_player_html(video_url, title):
    """创建视频播放器HTML"""
    return f"""
    <div style="width:100%; max-width:800px; margin:auto;">
        <h3>{title}</h3>
        <video width="100%" controls>
            <source src="{video_url}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    """


def search_videos(
        search_type,
        text_query="",
        image_file=None,
        image_url="",
        search_mode="frame",
        page=1,
        page_size=6
):
    """处理视频搜索请求"""
    try:
        with app.app_context():
            search_service = SearchVideoService()

            # 根据搜索类型调用不同的搜索方法
            if search_type == "文本搜索":
                if not text_query.strip():
                    return None, None, "请输入搜索文本"
                results = search_service.search_by_text(
                    text_query,
                    page=page,
                    page_size=page_size,
                    search_mode=search_mode
                )
            else:  # 图片搜索
                if image_file is None and not image_url.strip():
                    return None, None, "请上传图片或输入图片URL"
                results = search_service.search_by_image(
                    image_file=image_file,
                    image_url=image_url if not image_file else None,
                    page=page,
                    page_size=page_size
                )

            # 格式化输出结果
            if not results:
                return None, None, "未找到匹配的视频"

            # 准备Gallery数据
            gallery_data = []
            video_data = {}  # 存储视频信息

            for idx, video in enumerate(results):
                # 获取视频封面URL
                thumbnail_url = video.get('thumbnail_path', '')
                if not thumbnail_url:
                    # 如果没有封面，可以使用一个默认图片
                    thumbnail_url = "path/to/default/thumbnail.jpg"

                # 准备视频信息
                video_info, video_url, title = format_video_info(video)
                video_data[str(idx)] = {
                    'url': video_url,
                    'title': title,
                    'info': video_info
                }

                # 添加到Gallery数据
                gallery_data.append((
                    thumbnail_url,  # 图片URL
                    f"{title}"  # 显示标题
                ))

            # 将video_data存储为全局变量
            global _video_data
            _video_data = video_data

            return gallery_data, gr.HTML(value=""), "搜索完成"

    except Exception as e:
        return None, None, f"搜索失败: {str(e)}"


def on_select(evt: gr.SelectData):
    """处理视频选择事件"""
    try:
        global _video_data
        if hasattr(evt, 'index'):
            video_info = _video_data.get(str(evt.index))
            if video_info:
                html_content = create_video_player_html(
                    video_info['url'],
                    video_info['title']
                )
                return gr.HTML(value=html_content)

        return gr.HTML(value="<p>无法播放视频</p>")
    except Exception as e:
        print(f"Error in on_select: {e}")
        return gr.HTML(value=f"<p>播放错误: {str(e)}</p>")


def update_input_visibility(search_type):
    """更新输入组件的可见性"""
    if search_type == "文本搜索":
        return (
            gr.update(visible=True),  # 文本输入
            gr.update(visible=True),  # 搜索模式
            gr.update(visible=False),  # 图片上传
            gr.update(visible=False)   # 图片URL
        )
    else:
        return (
            gr.update(visible=False),  # 文本输入
            gr.update(visible=False),  # 搜索模式
            gr.update(visible=True),   # 图片上传
            gr.update(visible=True)    # 图片URL
        )


# 创建Gradio界面
def create_interface():
    with gr.Blocks(title="视频搜索系统") as iface:
        gr.Markdown("# 视频搜索系统")

        with gr.Row():
            search_type = gr.Radio(
                choices=["文本搜索", "图片搜索"],
                label="搜索类型",
                value="文本搜索"
            )

        with gr.Row():
            # 文本搜索相关组件
            text_query = gr.Textbox(
                label="搜索文本",
                placeholder="请输入搜索关键词",
                lines=2,
                visible=True
            )
            search_mode = gr.Radio(
                choices=["frame", "summary"],
                label="搜索模式",
                value="frame",
                visible=True,
                info="frame: 搜索视频帧 | summary: 搜索视频摘要"
            )

            # 图片搜索相关组件
            image_file = gr.Image(
                label="上传图片",
                type="pil",
                visible=False
            )
            image_url = gr.Textbox(
                label="图片URL",
                placeholder="请输入图片URL",
                visible=False
            )

        with gr.Row():
            page = gr.Number(
                label="页码",
                value=1,
                minimum=1,
                step=1
            )
            page_size = gr.Number(
                label="每页数量",
                value=6,
                minimum=1,
                maximum=20,
                step=1
            )

        with gr.Row():
            search_button = gr.Button("搜索")

        # 搜索结果展示
        with gr.Row():
            gallery = gr.Gallery(
                label="搜索结果",
                show_label=True,
                elem_id="gallery",
                columns=[2],
                rows=[3],
                height="auto",
                allow_preview=False
            )

        # 状态信息
        status = gr.Textbox(label="状态", interactive=False)

        # 视频播放区域
        video_area = gr.HTML(label="视频播放")

        # 绑定事件
        search_type.change(
            fn=update_input_visibility,
            inputs=[search_type],
            outputs=[text_query, search_mode, image_file, image_url]
        )

        search_button.click(
            fn=search_videos,
            inputs=[
                search_type,
                text_query,
                image_file,
                image_url,
                search_mode,
                page,
                page_size
            ],
            outputs=[gallery, video_area, status]
        )

        # 绑定Gallery点击事件
        gallery.select(
            fn=on_select,
            outputs=video_area
        )

    return iface


# 初始化全局变量
_video_data = {}

# 启动服务
if __name__ == "__main__":
    iface = create_interface()
    iface.launch(server_name="0.0.0.0", server_port=7862)  # 使用7862端口