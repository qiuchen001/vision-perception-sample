import gradio as gr
from app.services.video.search import SearchVideoService
from app import create_app
import json
import urllib.parse
from pathlib import Path

# 创建Flask应用实例
config_name = "config.Config"
app = create_app(config_name)

# 配置项
HOST = "http://localhost:7862"  # 替换为实际的域名
THUMBNAIL_DIR = "static/thumbnails"  # 缩略图目录

def search_videos(query, page=1, page_size=12):
    """搜索视频"""
    try:
        with app.app_context():
            search_service = SearchVideoService()
            results = search_service.search_by_text(query, page, page_size)
            return results, None
    except Exception as e:
        return None, str(e)

def format_video_info(video):
    """格式化视频信息"""
    try:
        info = f"""
        # {video['title']}
        
        **时长:** {video['duration']}秒
        **时间戳:** {video.get('timestamp', 0)}秒
        
        ### 描述
        {video.get('summary', '暂无描述')}
        
        ### 标签
        {', '.join(json.loads(video['tags']))}
        """
        return info
    except Exception as e:
        return f"Error: {str(e)}"

def get_thumbnail_url(thumbnail_path):
    """获取缩略图URL"""
    if thumbnail_path.startswith(('http://', 'https://')):
        return thumbnail_path
    
    # 确保缩略图路径存在
    thumb_path = Path(THUMBNAIL_DIR) / Path(thumbnail_path).name
    if not thumb_path.exists():
        return "static/default_thumb.jpg"
    
    return str(thumb_path)

def create_interface():
    """创建Gradio界面"""
    with gr.Blocks(css="""
        #video-container { 
            min-height: 400px;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            background: #f8f9fa;
        }
        #video-info {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            background: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    """) as interface:
        error_box = gr.Textbox(visible=False)
        
        with gr.Row():
            with gr.Column(scale=4):
                search_input = gr.Textbox(
                    label="搜索视频",
                    placeholder="输入关键词搜索视频...",
                    show_label=False
                )
            with gr.Column(scale=1):
                search_btn = gr.Button("搜索", variant="primary")
                
        with gr.Row():
            with gr.Column(scale=2):
                gallery = gr.Gallery(
                    label="搜索结果",
                    show_label=False,
                    columns=[2, 3, 4],  # 响应式列数
                    height=600,
                    object_fit="cover",
                    preview=False
                )
                video_list = gr.State([])
                current_page = gr.State(1)
                
                with gr.Row():
                    prev_btn = gr.Button("上一页", visible=False)
                    next_btn = gr.Button("下一页", visible=False)
                    page_info = gr.Markdown("", visible=False)
            
            with gr.Column(scale=3):
                video_player = gr.Video(
                    label="视频播放",
                    height=400,
                    show_label=False,
                    elem_id="video-container"
                )
                video_info = gr.Markdown(
                    value="点击左侧缩略图播放视频",
                    elem_id="video-info"
                )
                with gr.Row(visible=False) as loading_indicator:
                    gr.Markdown("加载中...")

        def on_search(query, page):
            results, error = search_videos(query, page)
            if error:
                return {
                    error_box: gr.update(visible=True, value=f"搜索出错: {error}"),
                    gallery: None,
                    video_list: None
                }
                
            if not results:
                return {
                    error_box: gr.update(visible=True, value="未找到相关视频"),
                    gallery: None,
                    video_list: None
                }
                
            # 处理缩略图和视频列表
            thumbnails = [get_thumbnail_url(v['thumbnail_path']) for v in results]
            
            # 更新分页控件
            has_prev = page > 1
            has_next = len(results) >= 12  # 假设每页12个
            
            return {
                error_box: gr.update(visible=False),
                gallery: thumbnails,
                video_list: results,
                prev_btn: gr.update(visible=has_prev),
                next_btn: gr.update(visible=has_next),
                page_info: gr.update(visible=True, value=f"第 {page} 页")
            }

        def update_video(evt: gr.SelectData, gallery, video_list):
            try:
                selected_video = video_list[evt.index]
                video_url = selected_video['url']
                
                # 构建代理URL
                proxy_url = f"{HOST}/video_proxy?url={urllib.parse.quote(video_url)}"
                
                # 格式化视频信息
                video_info = format_video_info(selected_video)
                
                return {
                    video_player: proxy_url,
                    video_info: video_info,
                    error_box: gr.update(visible=False)
                }
            except Exception as e:
                return {
                    error_box: gr.update(visible=True, value=f"播放出错: {str(e)}"),
                    video_player: None,
                    video_info: "视频加载失败"
                }

        # 绑定事件处理
        search_btn.click(
            fn=on_search,
            inputs=[search_input, current_page],
            outputs=[error_box, gallery, video_list, prev_btn, next_btn, page_info]
        )
        
        gallery.select(
            fn=update_video,
            inputs=[gallery, video_list],
            outputs=[video_player, video_info, error_box]
        )
        
        # 分页处理
        def update_page(page, delta):
            return page + delta
            
        prev_btn.click(
            fn=update_page,
            inputs=[current_page, gr.State(-1)],
            outputs=current_page
        ).then(
            fn=on_search,
            inputs=[search_input, current_page],
            outputs=[error_box, gallery, video_list, prev_btn, next_btn, page_info]
        )
        
        next_btn.click(
            fn=update_page,
            inputs=[current_page, gr.State(1)],
            outputs=current_page
        ).then(
            fn=on_search,
            inputs=[search_input, current_page],
            outputs=[error_box, gallery, video_list, prev_btn, next_btn, page_info]
        )
        
        # 回车搜索
        search_input.submit(
            fn=on_search,
            inputs=[search_input, current_page],
            outputs=[error_box, gallery, video_list, prev_btn, next_btn, page_info]
        )
        
    return interface

if __name__ == "__main__":
    iface = create_interface()
    iface.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        debug=True
    )