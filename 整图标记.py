import os
import shutil

# ================= 1. 路径与配置参数 =================
# 你原始的图片文件夹路径
dir_ng = r"D:\Users\18703\Desktop\xout\out\zon\ng"
dir_ok = r"D:\Users\18703\Desktop\xout\out\zon\ok"

# 【扁平化结构】：最终导出的扁平 YOLO 数据集位置
export_base = r"D:\Users\18703\Desktop\xout\out\yolo_dataset"

# 映射 YOLO 目标分类索引 (Index)
# 0: NG, 1: OK
CLASS_MAP = {
    'ng': 0,
    'ok': 1
}


# ================= 2. 核心批处理与重定位逻辑 =================

def process_dataset(source_dir, class_name):
    """
    将不同渠道的图片统一聚合到 images，标签聚合到 labels
    """
    if not os.path.exists(source_dir):
        print(f"⚠️ 找不到指定的源图片路径，已跳过: {source_dir}")
        return

    # 直接建立两个大总管文件夹：images 和 labels
    target_img_dir = os.path.join(export_base, "images")
    target_lbl_dir = os.path.join(export_base, "labels")

    os.makedirs(target_img_dir, exist_ok=True)
    os.makedirs(target_lbl_dir, exist_ok=True)

    class_id = CLASS_MAP[class_name]
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    count = 0

    print(f"\n⏳ 正在聚合 [{class_name}] 队列到扁平化 YOLO 目录...")

    # 开始高速拷贝与标签映射
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(valid_extensions):
            base_name = os.path.splitext(filename)[0]

            src_img_path = os.path.join(source_dir, filename)
            dst_img_path = os.path.join(target_img_dir, filename)
            dst_txt_path = os.path.join(target_lbl_dir, f"{base_name}.txt")

            try:
                # 复制图片到统一的 images
                shutil.copy2(src_img_path, dst_img_path)

                # 构建整图标注 YOLO 字符串
                yolo_line = f"{class_id} 0.5 0.5 1.0 1.0\n"

                # 写到统一的 labels
                with open(dst_txt_path, 'w', encoding='utf-8') as f:
                    f.write(yolo_line)

                count += 1
            except Exception as e:
                print(f"❌ 文件 {filename} 扁平化迁移失败: {e}")

    print(f"🎉 处理完成！[{class_name}] 队列成功处理了 {count} 组数据。")


def main():
    # 执行 ng 组迁移与标注 (分类为 0)
    process_dataset(dir_ng, 'ng')

    # 执行 ok 组迁移与标注 (分类为 1)
    process_dataset(dir_ok, 'ok')

    # 在根目录下自动生成配置文件
    yaml_path = os.path.join(export_base, "dataset.yaml")
    yaml_content = f"""# 精简版数据集 YOLO 训练配置文件
path: {export_base} # 数据集根目录
train: images/ # 训练集子路径
val: images/   # 验证集子路径

# 类别定义
nc: 2
names:
  0: NG
  1: OK
"""
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        print(f"\n📁 dataset.yaml 配置文件已生成在: {yaml_path}")
    except:
        pass


if __name__ == "__main__":
    main()