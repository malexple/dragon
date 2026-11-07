import numpy as np
import matplotlib.pyplot as plt

def draw_snowflake_branch(ax, length, thickness, angle, ox=0, oy=0):
    """Рекурсивная функция для отрисовки одного луча и его фрактальных веточек"""
    if length < 0.1:
        return

    # Вычисляем конечную точку текущего сегмента
    rad = np.radians(angle)
    nx = ox + length * np.cos(rad)
    ny = oy + length * np.sin(rad)

    # Рисуем линию (основную кость луча) со свечением
    # Рисуем несколько линий друг на друге: толстая полупрозрачная для свечения + тонкая яркая в центре
    ax.plot([ox, nx], [oy, ny], color='#00d9ff', alpha=0.15, linewidth=thickness*4, solid_capstyle='round')
    ax.plot([ox, nx], [oy, ny], color='#00a2ff', alpha=0.4, linewidth=thickness*2, solid_capstyle='round')
    ax.plot([ox, nx], [oy, ny], color='#ffffff', alpha=0.9, linewidth=thickness*0.7, solid_capstyle='round')

    # Если сегмент достаточно длинный, пускаем от него симметричные боковые веточки
    if length > 0.3:
        # Ответвления на 2/3 длины ствола
        bx1 = ox + (length * 0.5) * np.cos(rad)
        by1 = oy + (length * 0.5) * np.sin(rad)
        draw_snowflake_branch(ax, length * 0.4, thickness * 0.7, angle + 60, bx1, by1)
        draw_snowflake_branch(ax, length * 0.4, thickness * 0.7, angle - 60, bx1, by1)

        # Второе ответвление ближе к концу
        bx2 = ox + (length * 0.75) * np.cos(rad)
        by2 = oy + (length * 0.75) * np.sin(rad)
        draw_snowflake_branch(ax, length * 0.3, thickness * 0.6, angle + 60, bx2, by2)
        draw_snowflake_branch(ax, length * 0.3, thickness * 0.6, angle - 60, bx2, by2)

def generate_snowflake_image(output_filename="snowflake_procedural.png"):
    # Создаем холст в темных тонах (космический/зимний фон)
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='#060a17')
    ax.set_facecolor('#060a17')

    # Настраиваем оси (скрываем их)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')

    # Генерируем 6 главных лучей (шаг 60 градусов) для идеальной гексагональной симметрии
    for i in range(6):
        main_angle = i * 60
        draw_snowflake_branch(ax, length=1.0, thickness=5.0, angle=main_angle)

    # Добавляем центральное декоративное ядро (кристалл в центре)
    ax.scatter([0], [0], color='#ffffff', s=250, alpha=0.9, zorder=5)
    ax.scatter([0], [0], color='#00d9ff', s=700, alpha=0.3, zorder=4)

    # Сохраняем результат в высоком качестве
    plt.savefig(output_filename, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f"[+] Изображение снежинки успешно сгенерировано и сохранено как: {output_filename}")

if __name__ == "__main__":
    generate_snowflake_image()
