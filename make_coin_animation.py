import bpy
import math
from pathlib import Path

# 1. Очистка сцены
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Путь к карте высот и результирующему видео
work_dir = Path(__file__).resolve().parent
depth_map_path = str(work_dir / "coin_depth.png")
output_video_path = str(work_dir / "dragon_coin.mp4")

# 2. Создание основания монеты
bpy.ops.mesh.primitive_cylinder_add(
    radius=2.0,
    depth=0.2,
    vertices=128,
    location=(0, 0, 0)
)
coin = bpy.context.active_object
coin.name = "DragonCoin"

# Сглаживание нормалей
bpy.ops.object.shade_smooth()

# Подразделение сетки для плотного рельефа
subsurf = coin.modifiers.new(name="Subdivision", type='SUBSURF')
subsurf.subdivision_type = 'SIMPLE'
subsurf.levels = 3
subsurf.render_levels = 4

# 3. Настройка модификатора Displace
if Path(depth_map_path).exists():
    tex = bpy.data.textures.new("CoinDepthTex", type='IMAGE')
    tex.image = bpy.data.images.load(depth_map_path)

    displace = coin.modifiers.new(name="DisplaceRelief", type='DISPLACE')
    displace.texture = tex
    displace.texture_coords = 'LOCAL'
    displace.direction = 'Z'       # Выдавливание перпендикулярно плоскостям монеты
    displace.mid_level = 0.05
    displace.strength = 0.15

# 4. Базовый материал темного металла
mat = bpy.data.materials.new(name="DragonMetal")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    # Металлический серебристый оттенок
    bsdf.inputs["Base Color"].default_value = (0.75, 0.77, 0.82, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.95
    bsdf.inputs["Roughness"].default_value = 0.28
coin.data.materials.append(mat)

# 5. Анимация вращения вокруг вертикальной оси Z (360 градусов)
total_frames = 90  # 3 секунды при 30 fps
scene.frame_start = 1
scene.frame_end = total_frames

coin.rotation_euler = (0, 0, 0)
coin.keyframe_insert(data_path="rotation_euler", frame=1)

# Вращение на 360 градусов
coin.rotation_euler = (0, 0, math.radians(360))
coin.keyframe_insert(data_path="rotation_euler", frame=total_frames + 1)

# Линейная интерполяция вращения (без ускорений и замедлений)
if coin.animation_data and coin.animation_data.action:
    for fc in coin.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# 6. Камера (смотрит точно на фронтальную часть монеты)
# Приподнимаем и слегка наклоняем камеру для красивой перспективы
bpy.ops.object.camera_add(location=(0, -5.5, 0.4), rotation=(math.radians(86), 0, 0))
cam = bpy.context.active_object
scene.camera = cam

# 7. Драматичное неоновое освещение
# Контурный синий свет сзади (Rim light)
bpy.ops.object.light_add(type='SPOT', location=(0, 3.0, 2.0))
rim = bpy.context.active_object.data
rim.energy = 800
rim.color = (0.05, 0.4, 1.0)
rim.spot_size = math.radians(75)

# Фронтальный холодный свет
bpy.ops.object.light_add(type='POINT', location=(-3.0, -4.0, 2.5))
key = bpy.context.active_object.data
key.energy = 400
key.color = (0.85, 0.9, 1.0)

# 8. Настройки вывода сразу в MP4 видео
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderEngine.bl_rna.properties['engine'].enum_items else 'BLENDER_EEVEE'
scene.render.fps = 30
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.render.filepath = output_video_path

# Настройки кодека H.264
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'