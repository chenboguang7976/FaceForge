"""UI strings in English, Simplified Chinese and Vietnamese.

Each key maps to {"en": ..., "zh": ..., "vi": ...}. Placeholders use
``str.format`` syntax and must appear in all three languages.
"""

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ---------------------------------------------------------------- app
    "app.tagline": {
        "en": "Face swap & restoration studio",
        "zh": "AI 换脸与修复工作室",
        "vi": "Studio hoán đổi & phục hồi khuôn mặt",
    },
    "app.about": {"en": "About FaceForge", "zh": "关于 FaceForge", "vi": "Giới thiệu FaceForge"},
    "app.about_text": {
        "en": "FaceForge {edition} {version}\n\nDevice: {device}\n{hardware}\n\n"
              "Models: InsightFace, HyperSwap, GFPGAN, CodeFormer, GPEN, RestoreFormer++, XSeg, BiSeNet "
              "(via FaceFusion assets).\n\nUse responsibly: only process faces of people who have given "
              "their consent, and never use results to deceive, harass or impersonate.",
        "zh": "FaceForge {edition} {version}\n\n设备：{device}\n{hardware}\n\n"
              "模型：InsightFace、HyperSwap、GFPGAN、CodeFormer、GPEN、RestoreFormer++、XSeg、BiSeNet"
              "（来自 FaceFusion 资源）。\n\n请负责任地使用：仅处理已获得本人同意的人脸，"
              "切勿将结果用于欺骗、骚扰或冒充他人。",
        "vi": "FaceForge {edition} {version}\n\nThiết bị: {device}\n{hardware}\n\n"
              "Model: InsightFace, HyperSwap, GFPGAN, CodeFormer, GPEN, RestoreFormer++, XSeg, BiSeNet "
              "(từ kho FaceFusion).\n\nHãy sử dụng có trách nhiệm: chỉ xử lý khuôn mặt của người đã đồng ý, "
              "không dùng kết quả để lừa đảo, quấy rối hay mạo danh.",
    },
    "app.toggle_theme": {"en": "Light / dark theme", "zh": "浅色 / 深色主题", "vi": "Giao diện sáng / tối"},
    "app.quit_title": {"en": "Quit FaceForge?", "zh": "退出 FaceForge？", "vi": "Thoát FaceForge?"},
    "app.quit_busy": {
        "en": "A job is still running. Quit anyway? Video progress is saved and resumes next time.",
        "zh": "任务仍在进行。确定退出吗？视频进度已保存，下次可继续。",
        "vi": "Tác vụ vẫn đang chạy. Vẫn thoát? Tiến độ video đã được lưu và sẽ tiếp tục ở lần sau.",
    },
    "welcome.title": {"en": "Welcome to FaceForge", "zh": "欢迎使用 FaceForge", "vi": "Chào mừng đến với FaceForge"},
    "welcome.text": {
        "en": "Your computer: {hardware}\n\nFaceForge picked the \"{preset}\" preset for it. You can change "
              "it at any time in the panel on the right.\n\nThe AI models (0.1–2 GB) are downloaded "
              "automatically the first time they are needed.\n\nPlease use FaceForge responsibly and only "
              "with the consent of the people shown.",
        "zh": "您的电脑：{hardware}\n\nFaceForge 已为其选择“{preset}”预设，可随时在右侧面板中更改。"
              "\n\nAI 模型（0.1–2 GB）会在首次需要时自动下载。\n\n请负责任地使用 FaceForge，"
              "并且仅在获得相关人员同意的情况下使用。",
        "vi": "Máy của bạn: {hardware}\n\nFaceForge đã chọn preset \"{preset}\" phù hợp. Bạn có thể đổi "
              "bất cứ lúc nào ở bảng bên phải.\n\nCác model AI (0,1–2 GB) sẽ được tải tự động khi cần "
              "lần đầu.\n\nHãy sử dụng FaceForge có trách nhiệm và chỉ khi được người trong ảnh đồng ý.",
    },
    "welcome.pro_warning": {
        "en": "Note: FaceForge Pro is built for strong hardware (NVIDIA RTX with 8 GB+ VRAM or Apple "
              "Silicon, 16 GB+ RAM). This computer is below that, so processing will be slow. "
              "FaceForge Lite is recommended for it.",
        "zh": "注意：FaceForge Pro 面向高性能硬件（8 GB 以上显存的 NVIDIA RTX 或 Apple Silicon，"
              "16 GB 以上内存）。此电脑低于该配置，处理速度会较慢，建议使用 FaceForge Lite。",
        "vi": "Lưu ý: FaceForge Pro dành cho máy mạnh (NVIDIA RTX từ 8 GB VRAM hoặc Apple Silicon, "
              "RAM từ 16 GB). Máy này thấp hơn mức đó nên xử lý sẽ chậm. Nên dùng FaceForge Lite.",
    },
    # ------------------------------------------------------------- common
    "common.browse": {"en": "Browse…", "zh": "浏览…", "vi": "Chọn…"},
    "common.cancel": {"en": "Cancel", "zh": "取消", "vi": "Hủy"},
    "common.close": {"en": "Close", "zh": "关闭", "vi": "Đóng"},
    "common.remove": {"en": "Remove", "zh": "移除", "vi": "Gỡ bỏ"},
    "filter.images": {"en": "Images", "zh": "图片", "vi": "Ảnh"},
    "filter.videos": {"en": "Videos", "zh": "视频", "vi": "Video"},
    "filter.media": {"en": "Images and videos", "zh": "图片和视频", "vi": "Ảnh và video"},
    # ------------------------------------------------------------- inputs
    "input.source": {"en": "Source face", "zh": "源人脸", "vi": "Khuôn mặt nguồn"},
    "input.source.drop": {"en": "Add photos of the face", "zh": "添加人脸照片", "vi": "Thêm ảnh khuôn mặt"},
    "input.source.drop_hint": {
        "en": "Drop or click · several photos = better likeness",
        "zh": "拖放或点击 · 多张照片效果更像",
        "vi": "Kéo thả hoặc bấm · nhiều ảnh = giống hơn",
    },
    "input.source.empty": {
        "en": "No source yet. Clear, front-facing photos work best.",
        "zh": "尚未添加源人脸。清晰的正脸照片效果最佳。",
        "vi": "Chưa có ảnh nguồn. Ảnh rõ nét, nhìn thẳng cho kết quả tốt nhất.",
    },
    "input.source.ready": {
        "en": "Identity ready from {count} photo(s).",
        "zh": "已从 {count} 张照片提取身份特征。",
        "vi": "Đã lấy đặc trưng khuôn mặt từ {count} ảnh.",
    },
    "input.source.no_face": {
        "en": "No face found in the source photos.",
        "zh": "源照片中未检测到人脸。",
        "vi": "Không tìm thấy khuôn mặt trong ảnh nguồn.",
    },
    "input.target": {"en": "Target", "zh": "目标", "vi": "Đích"},
    "input.target.drop": {"en": "Open image or video", "zh": "打开图片或视频", "vi": "Mở ảnh hoặc video"},
    "input.target.drop_hint": {
        "en": "Drop or click · select several images for a batch",
        "zh": "拖放或点击 · 多选图片可批量处理",
        "vi": "Kéo thả hoặc bấm · chọn nhiều ảnh để xử lý hàng loạt",
    },
    "input.target.image_meta": {"en": "Image · {w}×{h}", "zh": "图片 · {w}×{h}", "vi": "Ảnh · {w}×{h}"},
    "input.target.video_meta": {
        "en": "Video · {w}×{h} · {fps} fps · {duration}",
        "zh": "视频 · {w}×{h} · {fps} fps · {duration}",
        "vi": "Video · {w}×{h} · {fps} fps · {duration}",
    },
    "input.target.batch_name": {"en": "{count} images", "zh": "{count} 张图片", "vi": "{count} ảnh"},
    "input.target.batch_meta": {
        "en": "Batch · preview shows the first image",
        "zh": "批量 · 预览显示第一张",
        "vi": "Hàng loạt · xem trước ảnh đầu tiên",
    },
    "input.faces": {"en": "Faces in target", "zh": "目标中的人脸", "vi": "Khuôn mặt trong ảnh đích"},
    "input.faces.all": {"en": "Replace all", "zh": "全部替换", "vi": "Thay tất cả"},
    "input.faces.empty": {
        "en": "Open a target to see its faces.",
        "zh": "打开目标后将显示其中的人脸。",
        "vi": "Mở ảnh/video đích để xem các khuôn mặt.",
    },
    "input.faces.none_found": {
        "en": "No faces detected in this frame.",
        "zh": "此帧未检测到人脸。",
        "vi": "Không phát hiện khuôn mặt nào trong khung hình này.",
    },
    "input.faces.hint": {
        "en": "{count} face(s). Click one to replace only that person.",
        "zh": "{count} 张人脸。点击某张即可只替换此人。",
        "vi": "{count} khuôn mặt. Bấm vào một mặt để chỉ thay người đó.",
    },
    # --------------------------------------------------------------- view
    "view.original": {"en": "Original", "zh": "原图", "vi": "Gốc"},
    "view.split": {"en": "Compare", "zh": "对比", "vi": "So sánh"},
    "view.result": {"en": "Result", "zh": "结果", "vi": "Kết quả"},
    "view.fit": {"en": "Fit to window (double-click)", "zh": "适应窗口（双击）", "vi": "Vừa khung (nhấp đúp)"},
    "view.refresh": {"en": "Refresh preview", "zh": "刷新预览", "vi": "Làm mới xem trước"},
    "view.empty_title": {
        "en": "Drop an image or video here",
        "zh": "将图片或视频拖放到这里",
        "vi": "Kéo thả ảnh hoặc video vào đây",
    },
    "view.empty_hint": {
        "en": "Then add a source face on the left. The preview updates live as you change settings.",
        "zh": "然后在左侧添加源人脸。修改设置时预览会实时更新。",
        "vi": "Sau đó thêm khuôn mặt nguồn ở bên trái. Xem trước sẽ cập nhật ngay khi bạn đổi cài đặt.",
    },
    "view.rendering": {"en": "Rendering preview…", "zh": "正在生成预览…", "vi": "Đang tạo xem trước…"},
    "view.preview_time": {"en": "Preview · {ms} ms", "zh": "预览 · {ms} 毫秒", "vi": "Xem trước · {ms} ms"},
    "view.need_source": {
        "en": "Add a source face to see the result",
        "zh": "添加源人脸以查看结果",
        "vi": "Thêm khuôn mặt nguồn để xem kết quả",
    },
    # ------------------------------------------------------------ actions
    "action.start": {"en": "Start", "zh": "开始", "vi": "Bắt đầu"},
    "action.processing": {"en": "Processing…", "zh": "处理中…", "vi": "Đang xử lý…"},
    "action.pause": {"en": "Pause", "zh": "暂停", "vi": "Tạm dừng"},
    "action.resume": {"en": "Resume", "zh": "继续", "vi": "Tiếp tục"},
    "action.stop": {"en": "Stop", "zh": "停止", "vi": "Dừng"},
    "action.open_output": {"en": "Open result", "zh": "打开结果", "vi": "Mở kết quả"},
    "action.ready_hint": {
        "en": "Ready. Ctrl+Enter to start, Ctrl+O to open a target.",
        "zh": "就绪。Ctrl+Enter 开始，Ctrl+O 打开目标。",
        "vi": "Sẵn sàng. Ctrl+Enter để bắt đầu, Ctrl+O để mở file đích.",
    },
    "progress.text": {
        "en": "{done} / {total} · {fps} fps · {eta} left",
        "zh": "{done} / {total} · {fps} fps · 剩余 {eta}",
        "vi": "{done} / {total} · {fps} fps · còn {eta}",
    },
    "progress.warmup": {
        "en": "{done} / {total} · estimating speed…",
        "zh": "{done} / {total} · 正在估算速度…",
        "vi": "{done} / {total} · đang ước tính tốc độ…",
    },
    "progress.done": {"en": "Saved: {path}", "zh": "已保存：{path}", "vi": "Đã lưu: {path}"},
    "progress.done_toast": {"en": "Done!", "zh": "完成！", "vi": "Hoàn tất!"},
    "progress.failed": {"en": "Processing failed", "zh": "处理失败", "vi": "Xử lý thất bại"},
    "progress.cancelled": {
        "en": "Stopped. Start again to resume the video where it left off.",
        "zh": "已停止。再次开始即可从中断处继续处理视频。",
        "vi": "Đã dừng. Bấm Bắt đầu lần nữa để làm tiếp video từ chỗ dừng.",
    },
    "progress.resumed": {
        "en": "Resumed from frame {frame}.",
        "zh": "已从第 {frame} 帧继续。",
        "vi": "Đã tiếp tục từ khung hình {frame}.",
    },
    # ------------------------------------------------------------- errors
    "error.no_target": {"en": "Open an image or video first.", "zh": "请先打开图片或视频。",
                        "vi": "Hãy mở ảnh hoặc video trước."},
    "error.no_source": {"en": "Add a source face photo first.", "zh": "请先添加源人脸照片。",
                        "vi": "Hãy thêm ảnh khuôn mặt nguồn trước."},
    "error.no_reference": {
        "en": "Pick the face to replace in the \"Faces in target\" list.",
        "zh": "请在“目标中的人脸”列表中选择要替换的人脸。",
        "vi": "Hãy chọn khuôn mặt cần thay trong danh sách \"Khuôn mặt trong ảnh đích\".",
    },
    "error.nothing_to_do": {
        "en": "Face swap and enhancement are both off.",
        "zh": "换脸和增强均已关闭。",
        "vi": "Hoán đổi và làm nét đều đang tắt.",
    },
    "error.busy": {"en": "Wait for the current job to finish.", "zh": "请等待当前任务完成。",
                   "vi": "Hãy đợi tác vụ hiện tại hoàn tất."},
    "error.read_video": {"en": "This video can't be read.", "zh": "无法读取此视频。",
                         "vi": "Không đọc được video này."},
    "error.read_frame": {"en": "Couldn't read this file.", "zh": "无法读取此文件。",
                         "vi": "Không đọc được file này."},
    "error.unsupported": {"en": "Unsupported file type.", "zh": "不支持的文件类型。",
                          "vi": "Định dạng file không được hỗ trợ."},
    # ------------------------------------------------------------ presets
    "preset.title": {"en": "Quality preset", "zh": "质量预设", "vi": "Mức chất lượng"},
    "preset.custom": {"en": "Custom", "zh": "自定义", "vi": "Tùy chỉnh"},
    "preset.performance": {"en": "Fast", "zh": "快速", "vi": "Nhanh"},
    "preset.balanced": {"en": "Balanced", "zh": "均衡", "vi": "Cân bằng"},
    "preset.quality": {"en": "Quality", "zh": "高质量", "vi": "Chất lượng"},
    "preset.maximum": {"en": "Maximum", "zh": "极致", "vi": "Tối đa"},
    "preset.performance.hint": {
        "en": "InSwapper 128, fast detector, no restoration. For weak PCs and long videos.",
        "zh": "InSwapper 128、快速检测、不修复。适合低配电脑和长视频。",
        "vi": "InSwapper 128, phát hiện nhanh, không làm nét. Cho máy yếu và video dài.",
    },
    "preset.balanced.hint": {
        "en": "InSwapper with 2× pixel boost plus light GPEN restoration. Good for 4 GB GPUs.",
        "zh": "InSwapper 2 倍像素增强 + 轻量 GPEN 修复。适合 4 GB 显卡。",
        "vi": "InSwapper pixel boost 2× + làm nét GPEN nhẹ. Hợp với GPU 4 GB.",
    },
    "preset.quality.hint": {
        "en": "HyperSwap 256, occlusion mask and GFPGAN restoration.",
        "zh": "HyperSwap 256、遮挡蒙版和 GFPGAN 修复。",
        "vi": "HyperSwap 256, mask che khuất và làm nét GFPGAN.",
    },
    "preset.maximum.hint": {
        "en": "HyperSwap at 512 px (4 passes), occlusion + face-parsing masks, strongest restoration. "
              "Needs a high-end GPU.",
        "zh": "HyperSwap 512 像素（4 次推理）、遮挡 + 人脸解析蒙版、最强修复。需要高端显卡。",
        "vi": "HyperSwap 512 px (4 lượt), mask che khuất + phân vùng mặt, làm nét mạnh nhất. Cần GPU cao cấp.",
    },
    "profile.low": {"en": "Low-end hardware mode", "zh": "低配模式", "vi": "Chế độ máy yếu"},
    "profile.medium": {"en": "Mid-range hardware", "zh": "中端硬件", "vi": "Phần cứng tầm trung"},
    "profile.high": {"en": "High-end hardware", "zh": "高端硬件", "vi": "Phần cứng mạnh"},
    # --------------------------------------------------------------- swap
    "swap.title": {"en": "Face swap", "zh": "换脸", "vi": "Hoán đổi khuôn mặt"},
    "swap.enabled": {"en": "Swap faces", "zh": "启用换脸", "vi": "Bật hoán đổi"},
    "swap.enabled.hint": {
        "en": "Turn off to only restore/enhance faces.",
        "zh": "关闭后仅修复 / 增强人脸。",
        "vi": "Tắt để chỉ làm nét/phục hồi khuôn mặt.",
    },
    "swap.model": {"en": "Model", "zh": "模型", "vi": "Model"},
    "swap.model.hint": {
        "en": "HyperSwap: newest, most natural (256 px). InSwapper: fastest (128 px). "
              "FP16 is only faster on RTX/GTX 16-series and newer.",
        "zh": "HyperSwap：最新、最自然（256 像素）。InSwapper：最快（128 像素）。"
              "FP16 仅在 RTX / GTX 16 系列及更新显卡上更快。",
        "vi": "HyperSwap: mới nhất, tự nhiên nhất (256 px). InSwapper: nhanh nhất (128 px). "
              "FP16 chỉ nhanh hơn trên RTX/GTX 16 trở lên.",
    },
    "swap.boost": {"en": "Pixel boost", "zh": "像素增强", "vi": "Pixel boost"},
    "swap.boost.hint": {
        "en": "Renders the face at a higher resolution in several passes. Sharper, but each step "
              "multiplies the work.",
        "zh": "分多次以更高分辨率渲染人脸。更清晰，但计算量成倍增加。",
        "vi": "Dựng khuôn mặt ở độ phân giải cao hơn qua nhiều lượt. Nét hơn nhưng mỗi mức tăng "
              "khối lượng xử lý lên nhiều lần.",
    },
    "swap.color_match": {"en": "Match skin tone", "zh": "匹配肤色", "vi": "Khớp màu da"},
    "swap.color_match.hint": {
        "en": "Adjusts the swapped face's colours to the lighting of the target.",
        "zh": "根据目标的光照调整换脸后的颜色。",
        "vi": "Chỉnh màu khuôn mặt sau khi thay cho khớp ánh sáng của ảnh đích.",
    },
    # ------------------------------------------------------------ enhance
    "enhance.title": {"en": "Face restoration", "zh": "人脸修复", "vi": "Làm nét khuôn mặt"},
    "enhance.enabled": {"en": "Restore faces", "zh": "启用修复", "vi": "Bật làm nét"},
    "enhance.enabled.hint": {
        "en": "Adds detail and sharpness to faces (recommended for high-resolution output).",
        "zh": "为人脸增加细节和清晰度（高分辨率输出时推荐）。",
        "vi": "Tăng chi tiết và độ nét cho khuôn mặt (nên bật khi xuất độ phân giải cao).",
    },
    "enhance.model": {"en": "Model", "zh": "模型", "vi": "Model"},
    "enhance.blend": {"en": "Strength", "zh": "强度", "vi": "Cường độ"},
    "enhance.blend.hint": {
        "en": "How much of the restored face is mixed over the original.",
        "zh": "修复结果与原图的混合比例。",
        "vi": "Mức pha trộn giữa khuôn mặt đã làm nét và bản gốc.",
    },
    "enhance.fidelity": {"en": "Fidelity", "zh": "保真度", "vi": "Độ trung thực"},
    "enhance.fidelity.hint": {
        "en": "CodeFormer: higher keeps more of the original identity, lower gives stronger restoration.",
        "zh": "CodeFormer：数值越高越保留原貌，越低修复越强。",
        "vi": "CodeFormer: cao giữ nét gốc nhiều hơn, thấp làm nét mạnh hơn.",
    },
    # --------------------------------------------------------------- mask
    "mask.title": {"en": "Blending mask", "zh": "融合蒙版", "vi": "Mask hòa trộn"},
    "mask.blur": {"en": "Edge softness", "zh": "边缘柔和度", "vi": "Độ mềm viền"},
    "mask.blur.hint": {
        "en": "Softer edges hide the seam between the new face and the frame.",
        "zh": "边缘越柔和，新脸与画面的接缝越不明显。",
        "vi": "Viền càng mềm càng che đường nối giữa mặt mới và khung hình.",
    },
    "mask.occlusion": {"en": "Keep objects in front of the face", "zh": "保留脸前遮挡物",
                       "vi": "Giữ vật che trước mặt"},
    "mask.occlusion.hint": {
        "en": "XSeg model: hands, hair, glasses and microphones stay on top of the swapped face.",
        "zh": "XSeg 模型：手、头发、眼镜、麦克风等会保留在换脸结果之上。",
        "vi": "Model XSeg: tay, tóc, kính, micro… vẫn nằm trên khuôn mặt đã thay.",
    },
    "mask.region": {"en": "Face parsing", "zh": "人脸解析", "vi": "Phân vùng khuôn mặt"},
    "mask.region.hint": {
        "en": "BiSeNet model: only skin, brows, eyes, nose and lips are replaced.",
        "zh": "BiSeNet 模型：仅替换皮肤、眉毛、眼睛、鼻子和嘴唇。",
        "vi": "Model BiSeNet: chỉ thay da, lông mày, mắt, mũi và môi.",
    },
    "mask.padding": {"en": "Padding", "zh": "内边距", "vi": "Thu viền"},
    "mask.padding.hint": {
        "en": "Shrink the mask from each side, e.g. to keep the original chin or forehead.",
        "zh": "从各边收缩蒙版，例如保留原始下巴或额头。",
        "vi": "Thu nhỏ mask từ mỗi cạnh, ví dụ để giữ cằm hoặc trán gốc.",
    },
    "mask.pad_top": {"en": "Top", "zh": "上", "vi": "Trên"},
    "mask.pad_right": {"en": "Right", "zh": "右", "vi": "Phải"},
    "mask.pad_bottom": {"en": "Bottom", "zh": "下", "vi": "Dưới"},
    "mask.pad_left": {"en": "Left", "zh": "左", "vi": "Trái"},
    # ----------------------------------------------------------- selector
    "select.title": {"en": "Which faces", "zh": "替换哪些人脸", "vi": "Thay khuôn mặt nào"},
    "select.mode": {"en": "Mode", "zh": "模式", "vi": "Chế độ"},
    "select.mode.hint": {
        "en": "All faces, only the largest face, or only the person you picked.",
        "zh": "全部人脸、仅最大人脸，或仅您选择的人。",
        "vi": "Tất cả, chỉ mặt lớn nhất, hoặc chỉ người bạn đã chọn.",
    },
    "select.all": {"en": "All", "zh": "全部", "vi": "Tất cả"},
    "select.largest": {"en": "Largest", "zh": "最大", "vi": "Lớn nhất"},
    "select.reference": {"en": "Picked", "zh": "指定", "vi": "Đã chọn"},
    "select.distance": {"en": "Match tolerance", "zh": "匹配容差", "vi": "Độ dung sai"},
    "select.distance.hint": {
        "en": "Higher also matches the picked person from harder angles, but may catch look-alikes.",
        "zh": "数值越高越能匹配不同角度的同一人，但可能误匹配相似的人。",
        "vi": "Cao hơn sẽ nhận người đã chọn ở góc khó hơn, nhưng có thể nhầm người giống.",
    },
    # ----------------------------------------------------------- detector
    "detect.title": {"en": "Face detection", "zh": "人脸检测", "vi": "Phát hiện khuôn mặt"},
    "detect.model": {"en": "Detector", "zh": "检测器", "vi": "Bộ phát hiện"},
    "detect.size": {"en": "Detection size", "zh": "检测尺寸", "vi": "Kích thước dò"},
    "detect.size.hint": {
        "en": "Larger finds small faces in big frames; smaller is faster.",
        "zh": "尺寸越大越能发现大画面中的小脸；越小越快。",
        "vi": "Lớn hơn tìm được mặt nhỏ trong khung lớn; nhỏ hơn thì nhanh hơn.",
    },
    "detect.score": {"en": "Confidence", "zh": "置信度", "vi": "Độ tin cậy"},
    "detect.score.hint": {
        "en": "Raise if non-faces are detected, lower if faces are missed.",
        "zh": "误检时调高，漏检时调低。",
        "vi": "Tăng nếu nhận nhầm, giảm nếu bỏ sót khuôn mặt.",
    },
    # ------------------------------------------------------------- output
    "output.title": {"en": "Output", "zh": "输出", "vi": "Xuất file"},
    "output.folder": {"en": "Output folder", "zh": "输出文件夹", "vi": "Thư mục lưu"},
    "output.image_format": {"en": "Image format", "zh": "图片格式", "vi": "Định dạng ảnh"},
    "output.image_quality": {"en": "Image quality", "zh": "图片质量", "vi": "Chất lượng ảnh"},
    "output.video_quality": {"en": "Video quality", "zh": "视频质量", "vi": "Chất lượng video"},
    "output.video_quality.hint": {
        "en": "Higher keeps more detail and makes larger files.",
        "zh": "数值越高细节越多，文件越大。",
        "vi": "Càng cao càng giữ nhiều chi tiết, file càng lớn.",
    },
    "output.encoder": {"en": "Video encoder", "zh": "视频编码器", "vi": "Bộ mã hóa video"},
    "output.encoder.auto": {"en": "Automatic (GPU if available)", "zh": "自动（优先 GPU）",
                            "vi": "Tự động (ưu tiên GPU)"},
    "output.encoder.hint": {
        "en": "Hardware encoders (NVENC, Quick Sync, AMF, VideoToolbox) leave the CPU free for AI.",
        "zh": "硬件编码器（NVENC、Quick Sync、AMF、VideoToolbox）可让 CPU 专注于 AI 计算。",
        "vi": "Mã hóa bằng phần cứng (NVENC, Quick Sync, AMF, VideoToolbox) để CPU rảnh cho AI.",
    },
    "output.keep_audio": {"en": "Keep original audio", "zh": "保留原始音频", "vi": "Giữ âm thanh gốc"},
    # ------------------------------------------------------------- system
    "system.title": {"en": "Performance", "zh": "性能", "vi": "Hiệu năng"},
    "system.device": {"en": "Processing device", "zh": "运算设备", "vi": "Thiết bị xử lý"},
    "system.device.auto": {"en": "Automatic", "zh": "自动", "vi": "Tự động"},
    "system.device.hint": {
        "en": "CUDA is fastest on NVIDIA. DirectML works on any Windows GPU without extra installs.",
        "zh": "NVIDIA 显卡上 CUDA 最快。DirectML 适用于任何 Windows 显卡，无需额外安装。",
        "vi": "CUDA nhanh nhất trên NVIDIA. DirectML chạy trên mọi GPU Windows, không cần cài thêm.",
    },
    "system.active": {"en": "In use: {device}", "zh": "当前使用：{device}", "vi": "Đang dùng: {device}"},
    "system.detected": {"en": "Detected: {hardware}", "zh": "检测到：{hardware}", "vi": "Phát hiện: {hardware}"},
    "system.gpu": {"en": "Graphics card", "zh": "显卡", "vi": "Card đồ họa"},
    "system.gpu.auto": {"en": "Automatic (fastest)", "zh": "自动（最快）", "vi": "Tự động (nhanh nhất)"},
    "system.gpu.hint": {
        "en": "On laptops with two GPUs, Automatic picks the dedicated card (e.g. NVIDIA) instead of the "
              "integrated one.",
        "zh": "在双显卡笔记本上，“自动”会选择独立显卡（如 NVIDIA）而不是集成显卡。",
        "vi": "Trên laptop có 2 GPU, chế độ Tự động sẽ chọn card rời (ví dụ NVIDIA) thay vì card tích hợp.",
    },
    "system.workers": {"en": "Parallel frames", "zh": "并行帧数", "vi": "Số khung xử lý song song"},
    "system.workers.hint": {
        "en": "More keeps a strong GPU busy; too many slows down weak machines.",
        "zh": "数值越大越能让高端显卡满载；过多会拖慢低配电脑。",
        "vi": "Nhiều hơn giúp GPU mạnh chạy hết công suất; quá nhiều làm máy yếu chậm đi.",
    },
    "system.max_models": {"en": "Models kept in memory", "zh": "常驻内存的模型数", "vi": "Số model giữ trong bộ nhớ"},
    "system.max_models.hint": {
        "en": "Fewer saves RAM/VRAM; more avoids reloading when switching options.",
        "zh": "越少越省内存 / 显存；越多切换选项时越少重新加载。",
        "vi": "Ít hơn tiết kiệm RAM/VRAM; nhiều hơn đỡ phải nạp lại khi đổi tùy chọn.",
    },
    "system.recommended": {"en": "Recommended", "zh": "推荐设置", "vi": "Đề xuất"},
    # ------------------------------------------------------------- models
    "models.title": {"en": "AI models", "zh": "AI 模型", "vi": "Model AI"},
    "models.manage": {"en": "Models…", "zh": "模型…", "vi": "Model…"},
    "models.headline": {
        "en": "Models are downloaded once and stored on this computer.",
        "zh": "模型只需下载一次，保存在本机。",
        "vi": "Model chỉ cần tải một lần và được lưu trên máy này.",
    },
    "models.required_headline": {
        "en": "{count} model(s) need to be downloaded first ({size} MB).",
        "zh": "需要先下载 {count} 个模型（{size} MB）。",
        "vi": "Cần tải {count} model trước ({size} MB).",
    },
    "models.location": {"en": "Folder: {path}", "zh": "文件夹：{path}", "vi": "Thư mục: {path}"},
    "models.col.name": {"en": "Model", "zh": "模型", "vi": "Model"},
    "models.col.type": {"en": "Type", "zh": "类型", "vi": "Loại"},
    "models.col.size": {"en": "Size", "zh": "大小", "vi": "Dung lượng"},
    "models.col.status": {"en": "Status", "zh": "状态", "vi": "Trạng thái"},
    "models.cat.detector": {"en": "Detection", "zh": "检测", "vi": "Phát hiện"},
    "models.cat.recognizer": {"en": "Recognition", "zh": "识别", "vi": "Nhận dạng"},
    "models.cat.swapper": {"en": "Face swap", "zh": "换脸", "vi": "Hoán đổi"},
    "models.cat.enhancer": {"en": "Restoration", "zh": "修复", "vi": "Làm nét"},
    "models.cat.mask": {"en": "Mask", "zh": "蒙版", "vi": "Mask"},
    "models.installed": {"en": "Installed", "zh": "已安装", "vi": "Đã có"},
    "models.missing": {"en": "Not downloaded", "zh": "未下载", "vi": "Chưa tải"},
    "models.open_folder": {"en": "Open folder", "zh": "打开文件夹", "vi": "Mở thư mục"},
    "models.download_selected": {"en": "Download selected", "zh": "下载所选", "vi": "Tải mục đã chọn"},
    "models.download_missing": {"en": "Download all missing", "zh": "下载全部缺失模型", "vi": "Tải tất cả còn thiếu"},
    "models.download_required": {"en": "Download now", "zh": "立即下载", "vi": "Tải ngay"},
    "models.downloading": {
        "en": "Downloading {name}: {done} / {total} MB",
        "zh": "正在下载 {name}：{done} / {total} MB",
        "vi": "Đang tải {name}: {done} / {total} MB",
    },
    "models.download_done": {"en": "Download complete.", "zh": "下载完成。", "vi": "Đã tải xong."},
    "models.download_failed": {
        "en": "Download failed: {error}. Run it again to continue where it stopped.",
        "zh": "下载失败：{error}。再次下载会从中断处继续。",
        "vi": "Tải thất bại: {error}. Tải lại sẽ tiếp tục từ chỗ bị dừng.",
    },
    "models.download_cancelled": {"en": "Download cancelled.", "zh": "下载已取消。", "vi": "Đã hủy tải."},
    "models.nothing_to_download": {"en": "Everything is already installed.", "zh": "所有模型均已安装。",
                                   "vi": "Tất cả đã được cài đặt."},
    # ------------------------------------------------------------- status
    "status.loading_model": {"en": "Loading {name}…", "zh": "正在加载 {name}…", "vi": "Đang nạp {name}…"},
    "status.ram": {"en": "RAM {used}/{total} GB (app {app})", "zh": "内存 {used}/{total} GB（本程序 {app}）",
                   "vi": "RAM {used}/{total} GB (app {app})"},
    "status.vram": {"en": "VRAM {used}/{total} GB", "zh": "显存 {used}/{total} GB", "vi": "VRAM {used}/{total} GB"},
}
