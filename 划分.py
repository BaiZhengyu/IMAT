import os
import random
import shutil

# ================= 1. 配置参数 =================
# 【新增配置】：你之前生成的扁平化源数据图像和标签文件夹路径
src_images_dir = r"D:\Users\18703\Desktop\xout\out\yolo_dataset\images"
src_labels_dir = r"D:\Users\18703\Desktop\xout\out\yolo_dataset\labels"

# 【新增配置】：你要最终自动生成的 YOLO11 项目内部标准数据集根目录
output_base = r"D:\Users\18703\Desktop\xout\out"

# 划分比例 (8:2)
train_ratio = 0.8

# 支持的图片格式
valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


# ================= 2. 核心处理逻辑 =================
def create_yolo11_dataset():
    # 1. 自动在目标路径建立标准的 YOLO 训练和验证集子文件夹
    splits = ["train", "val"]
    for split in splits:
        os.makedirs(os.path.join(output_base, "images", split), exist_ok=True)
        os.makedirs(os.path.join(output_base, "labels", split), exist_ok=True)

    print(f"🚀 开始从扁平化目录读取数据，准备按照 8:2 划分并同步导出至 YOLO11 项目...")

    # 2. 检查源目录是否存在
    if not os.path.exists(src_images_dir) or not os.path.exists(src_labels_dir):
        print(f"❌ 错误：找不到源图像或标签文件夹，请检查路径：\n- {src_images_dir}\n- {src_labels_dir}")
        return

    # 3. 扫描源文件夹中所有的图片文件
    all_files = os.listdir(src_images_dir)
    images = [f for f in all_files if os.path.splitext(f)[1].lower() in valid_extensions]

    if not images:
        print(f"⚠️ 警告：在源图片目录中未发现有效的图片文件：{src_images_dir}")
        return

    print(f"📊 扫描完成：共检测到 {len(images)} 张图片，正在随机打乱样本顺序以防过拟合...")

    # 4. 随机打乱序列，确保 train 和 val 集中同时混有 ng 和 ok 的图
    random.shuffle(images)

    # 计算 80% 的切分边界点
    train_bound = int(len(images) * train_ratio)

    # 自动切分为训练集与验证集字典
    subsets = {
        "train": images[:train_bound],
        "val": images[train_bound:]
    }

    # 5. 开始批量迁移图片与对应的 yolo .txt 标签
    for subset_name, subset_images in subsets.items():
        # 定位到最终的导出子文件夹路径
        img_target_dir = os.path.join(output_base, "images", subset_name)
        lbl_target_dir = os.path.join(output_base, "labels", subset_name)

        moved_count = 0
        missing_lbl_count = 0

        for img_name in subset_images:
            base_name = os.path.splitext(img_name)[0]
            txt_name = f"{base_name}.txt"

            # 源路径与目标目标路径构建
            src_img_path = os.path.join(src_images_dir, img_name)
            dst_img_path = os.path.join(img_target_dir, img_name)

            src_txt_path = os.path.join(src_labels_dir, txt_name)
            dst_txt_path = os.path.join(lbl_target_dir, txt_name)

            # 只有当对应的标签 txt 存在时才执行迁移，防止漏标引发 YOLO 训练报错
            if os.path.exists(src_txt_path):
                # 迁移图片
                shutil.copy2(src_img_path, dst_img_path)
                # 迁移标签文件
                shutil.copy2(src_txt_path, dst_txt_path)
                moved_count += 1
            else:
                missing_lbl_count += 1

        print(f" ╰─> 成功同步到 [{subset_name}] 集合: {moved_count} 组图片与标签")
        if missing_lbl_count > 0:
            print(f"     ⚠️ 注意：有 {missing_lbl_count} 张图片因缺失标签文件被安全忽略。")

    # ================= 3. 在目标目录自动生成独家适配的 data.yaml =================
    yaml_path = os.path.join(output_base, "data.yaml")

    # 将 Windows 路径的斜杠替换为正斜杠，防止 YOLO 解析 yaml 时发生转义错误
    clean_output_base = output_base.replace('\\', '/')

    yaml_content = f"""# 自动生成的晶圆/芯片缺陷检测 YOLO11 训练配置文件
path: {clean_output_base}  # 数据集根目录绝对路径
train: images/train  # 训练集图像路径
val: images/val      # 验证集图像路径

# 类别定义 (0: ng 不良品, 1: ok 合格品)
names:
  0: ng
  1: ok
"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"\n🎉 完美收工！标准的 YOLO11 数据集已全部规范化生成在:")
    print(f"📁 目标根目录: {output_base}")
    print(f"📄 训练配置文件直达: {yaml_path}")


if __name__ == "__main__":
    create_yolo11_dataset()