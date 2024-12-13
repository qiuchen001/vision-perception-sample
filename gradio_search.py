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
    <div style="height: 100%; padding: 20px; background: #f5f5f5; border-radius: 8px;">
        <h3 style="margin-top: 0; margin-bottom: 15px;">{title}</h3>
        <div style="position: relative; width: 100%; padding-top: 56.25%;">
            <video style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 4px;" controls>
                <source src="{video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
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
                    return [], None, "请输入搜索文本"
                results = search_service.search_by_text(
                    text_query,
                    page=page,
                    page_size=page_size,
                    search_mode=search_mode
                )
            else:  # 图片搜索
                if image_file is None and not image_url.strip():
                    return [], None, "请上传图片或输入图片URL"
                
                try:
                    if image_url.strip():
                        # 使用图片URL进行搜索
                        print(f"Using image URL: {image_url}")  # 调试日志
                        results = search_service.search_by_image(
                            image_file=None,
                            image_url=image_url,
                            page=page,
                            page_size=page_size
                        )
                    elif isinstance(image_file, Image.Image):
                        # 使用上传的图片进行搜索
                        print("Using PIL Image directly")  # 调试日志
                        results = search_service.search_by_image(
                            image_file=image_file,
                            image_url=None,
                            page=page,
                            page_size=page_size
                        )
                    else:
                        print(f"Unexpected image type: {type(image_file)}")  # 调试日志
                        return [], None, f"不支持的图片格式: {type(image_file)}"
                except Exception as e:
                    print(f"Error processing image: {str(e)}")  # 调试日志
                    return [], None, f"图片处理失败: {str(e)}"

            # 格式化输出结果
            if not results:
                return [], None, "未找到匹配的视频"

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
        print(f"Search error: {str(e)}")  # 调试日志
        return [], None, f"搜索失败: {str(e)}"


def on_select(evt: gr.SelectData):
    """处理视选择事件"""
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
            gr.update(visible=True),   # 文本输入
            gr.update(visible=True),   # 搜索模式
            gr.update(visible=False),  # 图片上传
            gr.update(visible=False)   # 图片URL
        )
    else:  # 图片搜索
        return (
            gr.update(visible=False),  # 文本输入
            gr.update(visible=False),  # 搜索模式
            gr.update(visible=True),   # 图片上传
            gr.update(visible=True)    # 图片URL
        )


# 创建Gradio界面
def create_interface():
    css = """
    #container {
        min-height: calc(100vh - 100px);
        padding: 1rem;
    }
    .search-controls {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    .results-container {
        display: flex;
        gap: 2rem;
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .gallery-area {
        flex: 1;
        min-width: 0;
    }
    .video-area {
        flex: 1;
        min-width: 300px;
        position: sticky;
        top: 1rem;
        max-height: calc(100vh - 120px);
        overflow-y: auto;
    }
    .status-box {
        margin-top: 1rem;
        padding: 0.75rem;
        border-radius: 6px;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    .search-button {
        background: #007bff;
        color: white;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        transition: background 0.3s;
    }
    .search-button:hover {
        background: #0056b3;
    }
    """

    with gr.Blocks(title="视频搜索系统", css=css) as iface:
        with gr.Column(elem_id="container"):
            # 搜索控制区域
            with gr.Column(elem_classes="search-controls"):
                gr.Markdown("## 搜索条件")
                with gr.Row():
                    search_type = gr.Radio(
                        choices=["文本搜索", "图片搜索"],
                        label="搜索类型",
                        value="文本搜索",
                        container=False
                    )

                with gr.Row():
                    # 文本搜索相关组件
                    text_query = gr.Textbox(
                        label="搜索文本",
                        placeholder="请输入搜索关键词",
                        lines=2,
                        visible=True,
                        container=True
                    )
                    search_mode = gr.Radio(
                        choices=["frame", "summary"],
                        label="搜索模式",
                        value="frame",
                        visible=True,
                        info="frame: 搜索视频帧 | summary: 搜索视频摘要",
                        container=True
                    )

                # 图片搜索相关组件
                with gr.Row() as image_search_row:
                    image_file = gr.Image(
                        label="上传图片",
                        type="pil",
                        container=True,
                        visible=False
                    )
                    image_url = gr.Textbox(
                        label="图片URL",
                        placeholder="请输入图片URL",
                        container=True,
                        visible=False
                    )

                with gr.Row():
                    with gr.Column(scale=1):
                        page = gr.Number(
                            label="页码",
                            value=1,
                            minimum=1,
                            step=1
                        )
                    with gr.Column(scale=1):
                        page_size = gr.Number(
                            label="每页数量",
                            value=6,
                            minimum=1,
                            maximum=20,
                            step=1
                        )

                with gr.Row():
                    search_button = gr.Button("搜索", elem_classes="search-button")

            # 搜索结果和视频播放区域
            with gr.Row(elem_classes="results-container"):
                # 左侧搜索结果
                with gr.Column(elem_classes="gallery-area"):
                    gr.Markdown("## 搜索结果")
                    gallery = gr.Gallery(
                        label="",
                        show_label=False,
                        elem_id="gallery",
                        columns=[2],
                        rows=[3],
                        height="auto",
                        allow_preview=False,
                        object_fit="cover"
                    )

                    status = gr.Textbox(
                        label="状态",
                        interactive=False,
                        elem_classes="status-box"
                    )

                # 右侧视频播放区域
                with gr.Column(elem_classes="video-area"):
                    gr.Markdown("## 视频播放")
                    video_area = gr.HTML(
                        value="""
                        <div style="height: 100%; display: flex; align-items: center; justify-content: center; 
                             background: white; border-radius: 10px; padding: 2rem; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                            <div style="text-align: center;">
                                <svg style="width:64px;height:64px;margin-bottom:1.5rem;color:#6c757d" viewBox="0 0 24 24">
                                    <path fill="currentColor" d="M17,10.5V7A1,1 0 0,0 16,6H4A1,1 0 0,0 3,7V17A1,1 0 0,0 4,18H16A1,1 0 0,0 17,17V13.5L21,17.5V6.5L17,10.5Z" />
                                </svg>
                                <div style="color:#6c757d;font-size:1.1rem;">请选择要播放的视频</div>
                            </div>
                        </div>
                        """
                    )

        # 添加图片输入组件的互斥处理
        def clear_other_input(value, is_url):
            """当一个输入有值时，清除另一个输入"""
            if is_url and value:  # URL输入有值时
                return gr.update(value=None), gr.update()
            elif not is_url and value is not None:  # 图片上传有值时
                return gr.update(), gr.update(value="")
            return gr.update(), gr.update()

        # 绑定事件
        search_type.change(
            fn=update_input_visibility,
            inputs=[search_type],
            outputs=[text_query, search_mode, image_file, image_url]
        )

        # 添加图片输入互斥处理
        image_file.change(
            fn=lambda x: clear_other_input(x, False),
            inputs=[image_file],
            outputs=[image_file, image_url]
        )

        image_url.change(
            fn=lambda x: clear_other_input(x, True),
            inputs=[image_url],
            outputs=[image_file, image_url]
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