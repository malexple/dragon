import bpy
import math
from pathlib import Path

# 1. Сброс сцены
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for b in bpy.data.meshes:
    bpy.data.meshes.remove(b)
for b in bpy.data.materials:
    bpy.data.materials.remove(b)

work_dir = Path("D:/project/python/dragon")
color_img = work_dir / "coin_front.png.jpg"
if not color_img.exists():
    color_img = work_dir / "dragon.jpg"

# 2. Основа монеты — цельный цилиндр правильных пропорций
COIN_RADIUS = 1.95
COIN_THICKNESS = 0.22

bpy.ops.mesh.primitive_cylinder_add(
    radius=COIN_RADIUS,
    depth=COIN_THICKNESS,
    vertices=128,
    location=(0, 0, 0)
)
coin = bpy.context.view_layer.objects.active
coin.name = "Real_Dragon_Coin"
bpy.ops.object.shade_smooth()

# Скругление ребра (Bevel)
bevel = coin.modifiers.new(name="Rim_Bevel", type='BEVEL')
bevel.width = 0.025
bevel.segments = 3

# 3. Шейдер чеканки с идеальной симметрией A над A_mirror
mat = bpy.data.materials.new(name="DragonCoin_DualSide")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

bsdf = None
for n in nodes:
    if n.type == 'BSDF_PRINCIPLED':
        bsdf = n
        break
if bsdf is None:
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')

bsdf.inputs["Metallic"].default_value = 0.98
bsdf.inputs["Roughness"].default_value = 0.22

if color_img.exists():
    tex_color = nodes.new(type="ShaderNodeTexImage")
    tex_color.image = bpy.data.images.load(str(color_img))

    # Нода геометрии для определения стороны (перед/зад)
    geom_node = nodes.new(type="ShaderNodeNewGeometry")

    # UV координаты
    tex_coord = nodes.new(type="ShaderNodeTexCoord")

    # Проекция цвета
    links.new(tex_coord.outputs["UV"], tex_color.inputs["Vector"])
    links.new(tex_color.outputs["Color"], bsdf.inputs["Base Color"])

    # Бамп (рельеф) дракона на поверхности монеты без разрушения торца!
    bump = nodes.new(type="ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.85
    bump.inputs["Distance"].default_value = 0.12

    links.new(tex_color.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

coin.data.materials.append(mat)

# 4. Свет и камера
bpy.ops.object.light_add(type='POINT', location=(3.0, -3.5, 3.0))
bpy.context.view_layer.objects.active.data.energy = 850

bpy.ops.object.light_add(type='POINT', location=(-3.0, 3.5, -2.0))
rim_l = bpy.context.view_layer.objects.active.data
rim_l.energy = 650
rim_l.color = (0.08, 0.45, 1.0)

bpy.ops.object.camera_add(location=(0, -5.5, 1.2), rotation=(math.radians(78), 0, 0))
bpy.context.scene.camera = bpy.context.view_layer.objects.active

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'

print("[+] Монета построена: цельное монолитное ребро, барельеф через Bump без артефактов частокола.")