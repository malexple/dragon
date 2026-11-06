import bpy
import math
import mathutils
from pathlib import Path

# ==========================================
# 1. Сброс и очистка сцены
# ==========================================
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

BASE_DIR = Path("D:/project/python/dragon")
OBJ_PATH = BASE_DIR / "dragon3d.obj"
OUT_VIDEO = str(BASE_DIR / "dragon_coin_silver_spin.mov")

# ==========================================
# 2. Импорт OBJ модели
# ==========================================
print(f"[*] Загрузка модели: {OBJ_PATH}")
# Поддержка современного и классического операторов импорта OBJ в Blender
try:
    bpy.ops.wm.obj_import(filepath=str(OBJ_PATH))
except AttributeError:
    bpy.ops.import_scene.obj(filepath=str(OBJ_PATH))

# Получаем импортированную монету
coin = bpy.context.selected_objects[0]
coin.name = "DragonCoin"

# Центрирование pivot-точки точно в геометрический центр монеты
bpy.context.view_layer.objects.active = coin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
coin.location = (0, 0, 0)

# Масштабируем до удобного размера (диаметр около 2 единиц)
dim = max(coin.dimensions.x, coin.dimensions.y, coin.dimensions.z)
if dim > 0:
    scale_factor = 2.0 / dim
    coin.scale = (scale_factor, scale_factor, scale_factor)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Сглаживание нормалей
bpy.ops.object.shade_smooth()

# ==========================================
# 3. Материал благородного серебра
# ==========================================
mat_silver = bpy.data.materials.new(name="Ancient_Silver")
mat_silver.use_nodes = True
nodes = mat_silver.node_tree.nodes
links = mat_silver.node_tree.links
nodes.clear()

node_out = nodes.new('ShaderNodeOutputMaterial')
node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')

# Настройки физического серебра
node_bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.97, 1.0) # Серебристо-белый тон
node_bsdf.inputs['Metallic'].default_value = 1.0                     # 100% металл
node_bsdf.inputs['Roughness'].default_value = 0.22                    # Мягкий блеск полировки

# Добавляем микротекстуру шума для реализма старинной чеканки
node_noise = nodes.new('ShaderNodeTexNoise')
node_noise.inputs['Scale'].default_value = 85.0
node_noise.inputs['Detail'].default_value = 8.0

node_bump = nodes.new('ShaderNodeBump')
node_bump.inputs['Strength'].default_value = 0.04
node_bump.inputs['Distance'].default_value = 0.05

links.new(node_noise.outputs['Fac'], node_bump.inputs['Height'])
links.new(node_bump.outputs['Normal'], node_bsdf.inputs['Normal'])
links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

coin.data.materials.clear()
coin.data.materials.append(mat_silver)

# ==========================================
# 4. Синее пламя в глазах дракона
# ==========================================
bbox = [coin.matrix_world @ mathutils.Vector(corner) for corner in coin.bound_box] if 'mathutils' in globals() else None
# Находим координаты головы дракона (верхняя четверть монеты)
max_z = max(v.co.z for v in coin.data.vertices)
min_y = min(v.co.y for v in coin.data.vertices)
max_y = max(v.co.y for v in coin.data.vertices)

# Создаем сияющие огоньки для обеих сторон монеты
eye_lights = []
for side, y_offset in [("Front", min_y * 0.95), ("Back", max_y * 0.95)]:
    light_data = bpy.data.lights.new(name=f"DragonEyeLight_{side}", type='POINT')
    light_data.energy = 85.0
    light_data.color = (0.0, 0.55, 1.0) # Глубокий синий неоновый огонь
    light_data.shadow_soft_size = 0.05

    light_obj = bpy.data.objects.new(name=f"DragonEye_{side}", object_data=light_data)
    # Позиционирование в область глаз дракона
    light_obj.location = (-0.55, y_offset, max_z * 0.45)
    bpy.context.collection.objects.link(light_obj)

    # Привязываем свет к монете, чтобы огонь вращался вместе с головой
    light_obj.parent = coin
    eye_lights.append(light_obj)

# ==========================================
# 5. Анимация: 2 секунды, 360° по диагональной оси (XZ)
# ==========================================
scene = bpy.context.scene
FPS = 30
TOTAL_FRAMES = 60  # 2 секунды * 30 FPS

scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

# Наклон оси вращения монеты на 15 градусов для красивой демонстрации ребер
coin.rotation_mode = 'XYZ'
coin.rotation_euler = (math.radians(15), 0, 0)
coin.keyframe_insert(data_path="rotation_euler", frame=1)

# Вращение против часовой стрелки (360 градусов)
coin.rotation_euler = (math.radians(15), 0, math.radians(-360))
coin.keyframe_insert(data_path="rotation_euler", frame=TOTAL_FRAMES + 1)

# Делаем вращение строго линейным (без ускорения на старте и торможения в конце)
if coin.animation_data and coin.animation_data.action:
    for fcurve in coin.animation_data.action.fcurves:
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'LINEAR'

# Пульсация синего пламени в глазах (эффект мерцающего огня)
for light_obj in eye_lights:
    for f in range(1, TOTAL_FRAMES + 1, 5):
        # Мерцание энергии света от 60 до 120 Вт
        pulse = 90.0 + 30.0 * math.sin(f * 0.7)
        light_obj.data.energy = pulse
        light_obj.data.keyframe_insert(data_path="energy", frame=f)

# ==========================================
# 6. Камера и студийный свет
# ==========================================
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = (0, -3.8, 0)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

# Контурный и заполняющий свет для металлического объема
def add_studio_light(name, pos, energy, color):
    ld = bpy.data.lights.new(name, type='POINT')
    ld.energy = energy
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = pos
    bpy.context.collection.objects.link(lo)

add_studio_light("KeyLight", (2.5, -2.5, 2.0), 350, (1.0, 0.98, 0.95))
add_studio_light("FillLight", (-2.5, -2.5, -1.5), 180, (0.8, 0.9, 1.0))
add_studio_light("BackRim", (0.0, 3.0, 1.5), 400, (0.1, 0.6, 1.0)) # Синий контровой свет

# ==========================================
# 7. Настройки рендера (Быстрый EEVEE, MP4 H.264 ~1-2 МБ)
# ==========================================
scene.render.engine = 'BLENDER_EEVEE'

# Ускорение рендера для мгновенного превью
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 720
scene.render.resolution_y = 720

# Глубокий темный фон (напрямую без пустых нод)
scene.render.film_transparent = False
if not scene.world:
    scene.world = bpy.data.worlds.new("World")
scene.world.color = (0.02, 0.02, 0.03)

# Сохранение в легкий стандартный MP4 (H.264)
OUT_MP4 = str(BASE_DIR / "dragon_coin_preview.mp4")
scene.render.filepath = OUT_MP4
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.ffmpeg.ffmpeg_preset = 'REALTIME'
scene.render.image_settings.color_mode = 'RGB'

print("[*] Старт быстрого рендера MP4...")
bpy.ops.render.render(animation=True)
print(f"[+] Готово! Видео сохранено: {OUT_MP4}")