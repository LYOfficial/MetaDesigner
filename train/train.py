import gradio as gr
import os
import json
import hashlib
import shutil
from typing import List, Optional

# 确保cache目录存在
cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
os.makedirs(cache_dir, exist_ok=True)

# designer.json文件路径
designer_json_path = os.path.join(cache_dir, "designer.json")

def load_designers():
    """加载已有的设计师数据"""
    if os.path.exists(designer_json_path):
        try:
            with open(designer_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_designers(designers_data):
    """保存设计师数据"""
    with open(designer_json_path, 'w', encoding='utf-8') as f:
        json.dump(designers_data, f, ensure_ascii=False, indent=2)

def generate_hash(designer_name: str) -> str:
    """根据设计师名字和当前时间生成唯一哈希值"""
    import time
    unique_string = f"{designer_name}_{int(time.time() * 1000000)}"
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()[:16]

def upload_images(designer_name: str, images: List) -> tuple:
    """处理图片上传"""
    if not designer_name or not designer_name.strip():
        return "请输入设计师名字！", None, None, gr.update(), gr.update()
    
    if not images or len(images) == 0:
        return "请上传至少一张图片！", None, None, gr.update(), gr.update()
    
    if len(images) > 30:
        return "最多只能上传30张图片！", None, None, gr.update(), gr.update()
    
    designer_name = designer_name.strip()
    
    # 加载现有设计师数据
    designers_data = load_designers()
    
    # 检查设计师名字是否已存在
    for existing_hash, existing_name in designers_data.items():
        if existing_name == designer_name:
            return f"设计师名字 '{designer_name}' 已存在！请使用不同的名字。", None, None, gr.update(), gr.update()
    
    # 生成唯一哈希值
    designer_hash = generate_hash(designer_name)
    
    # 确保哈希值唯一
    while designer_hash in designers_data:
        designer_hash = generate_hash(designer_name)
    
    # 创建设计师文件夹
    designer_folder = os.path.join(cache_dir, designer_hash)
    os.makedirs(designer_folder, exist_ok=True)
    
    try:
        # 复制图片到设计师文件夹
        for i, image in enumerate(images):
            if image is not None:
                # 获取图片文件扩展名
                file_extension = os.path.splitext(image.name)[-1] if hasattr(image, 'name') and image.name else '.jpg'
                # 目标文件名
                target_filename = f"image_{i+1:03d}{file_extension}"
                target_path = os.path.join(designer_folder, target_filename)
                
                # 复制文件
                if hasattr(image, 'name'):
                    # 如果是文件对象
                    shutil.copy2(image.name, target_path)
                else:
                    # 如果是其他格式
                    shutil.copy2(image, target_path)
        
        # 更新设计师数据
        designers_data[designer_hash] = designer_name
        save_designers(designers_data)
        
        success_message = f"上传完毕！\n设计师: {designer_name}\n哈希值: {designer_hash}\n共上传 {len(images)} 张图片"
        
        # 返回成功消息和锁定的控件
        return success_message, gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=True), gr.update(visible=True)
        
    except Exception as e:
        # 如果出错，清理创建的文件夹
        if os.path.exists(designer_folder):
            shutil.rmtree(designer_folder)
        return f"上传失败：{str(e)}", None, None, gr.update(), gr.update()

def train_model():
    """训练模型（待实现）"""
    return "训练功能待实现..."

def reset_interface():
    """重置界面"""
    return "", None, "请输入设计师名字并上传图片", gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=False), gr.update(visible=False)

# 创建Gradio界面
with gr.Blocks(title="Meta Designer", theme=gr.themes.Soft()) as app:
    # 置顶大标题
    gr.HTML("""
        <div style="text-align: center; margin: 20px 0;">
            <h1 style="font-size: 3em; color: #2E86AB; margin: 0;">Meta Designer</h1>
            <p style="font-size: 1.2em; color: #666; margin: 10px 0;">AI设计师训练平台</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column():
            # 设计师名字输入框
            designer_name_input = gr.Textbox(
                label="设计师名字",
                placeholder="请输入设计师的名字...",
                interactive=True
            )
            
            # 图片上传框
            image_upload = gr.File(
                label="上传设计作品",
                file_count="multiple",
                file_types=["image"],
                interactive=True
            )
            
            # 图片预览
            with gr.Row():
                image_gallery = gr.Gallery(
                    label="预览上传的图片",
                    show_label=True,
                    elem_id="gallery",
                    columns=3,
                    rows=3,
                    height="auto"
                )
    
    # 状态显示
    status_output = gr.Textbox(
        label="状态",
        value="请输入设计师名字并上传图片",
        interactive=False,
        lines=3
    )
    
    # 按钮区域
    with gr.Row():
        upload_btn = gr.Button("上传", variant="primary", size="lg")
        train_btn = gr.Button("训练", variant="secondary", size="lg", interactive=False)
        reset_btn = gr.Button("重置", variant="stop", size="lg", visible=False)
    
    # 图片上传时自动预览
    def update_gallery(files):
        if files:
            # 限制显示最多30张图片
            display_files = files[:30] if len(files) > 30 else files
            return display_files
        return None
    
    image_upload.change(
        fn=update_gallery,
        inputs=[image_upload],
        outputs=[image_gallery]
    )
    
    # 上传按钮点击事件
    upload_btn.click(
        fn=upload_images,
        inputs=[designer_name_input, image_upload],
        outputs=[status_output, designer_name_input, image_upload, train_btn, reset_btn]
    )
    
    # 训练按钮点击事件
    train_btn.click(
        fn=train_model,
        inputs=[],
        outputs=[status_output]
    )
    
    # 重置按钮点击事件
    reset_btn.click(
        fn=reset_interface,
        inputs=[],
        outputs=[designer_name_input, image_upload, status_output, designer_name_input, image_upload, train_btn, reset_btn]
    )

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=12002,
        share=False,
        show_error=True
    )
