import pygame
import sys
import os
import math
from datetime import datetime

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (255, 255, 255)
DEFAULT_COLOR = (0, 0, 0)
DEFAULT_THICKNESS = 2
SELECTION_COLOR = (0, 120, 255)  # Синий цвет для выделения
SELECTION_THICKNESS = 2
MULTI_SELECTION_COLOR = (255, 165, 0)  # Оранжевый для мультивыделения

COLORS = {
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'PURPLE': (128, 0, 128),
    'ORANGE': (255, 165, 0)
}

class DrawingApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("трофим (в8) - мультивыделение")

        self.shapes = []
        self.selected_shape_indices = set()  # Множество индексов выбранных фигур
        self.current_tool = 'rectangle'
        self.current_color = COLORS['BLACK']
        self.thickness = DEFAULT_THICKNESS
        self.drawing = False
        self.start_pos = None
        self.last_pos = None
        self.preview_surface = None
        self.dragging_selected = False  # Флаг перетаскивания выбранных фигур
        self.drag_offsets = {}  # Словарь смещений для каждой фигуры
        self.selection_rect = None  # Прямоугольник выделения
        self.selecting = False  # Режим выделения прямоугольником
        self.ctrl_pressed = False  # Флаг нажатия Ctrl

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        self.preview_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        self.ui_elements = self.create_ui()

    def create_ui(self):
        """создание элементов"""
        ui = {
            'tools': [],
            'colors': [],
            'thickness_slider': None
        }

        tool_y = 10

        ui['tools'].append({
            'rect': pygame.Rect(0, tool_y, 70, 30),
            'type': 'rectangle',
            'text': 'прям',
            'active': True
        })

        ui['tools'].append({
            'rect': pygame.Rect(70, tool_y, 70, 30),
            'type': 'triangle',
            'text': 'треу',
            'active': False
        })

        color_x = 180
        for i, (color_name, color_value) in enumerate(COLORS.items()):
            ui['colors'].append({
                'rect': pygame.Rect(color_x + i * 40, tool_y, 30, 30),
                'color': color_value,
                'name': color_name,
                'active': color_value == self.current_color
            })

        ui['thickness_slider'] = {
            'rect': pygame.Rect(480, tool_y + 10, 100, 6),
            'handle_rect': pygame.Rect(
                480 + int((self.thickness - 1) / (10 - 1) * (100 - 8)),
                tool_y + 8,
                8, 14
            ),
            'min': 1,
            'max': 10,
            'value': self.thickness
        }

        ui['save_button'] = {
            'rect': pygame.Rect(SCREEN_WIDTH - 120, tool_y, 60, 30),
            'text': 'сейв'
        }

        ui['clear_button'] = {
            'rect': pygame.Rect(SCREEN_WIDTH - 60, tool_y, 60, 30),
            'text': 'клир'
        }

        ui['deselect_button'] = {
            'rect': pygame.Rect(SCREEN_WIDTH - 180, tool_y, 60, 30),
            'text': 'снять'
        }

        ui['select_all_button'] = {
            'rect': pygame.Rect(SCREEN_WIDTH - 240, tool_y, 60, 30),
            'text': 'все'
        }

        return ui

    def update_ui_active_states(self):
        """активные состояния"""
        for tool in self.ui_elements['tools']:
            tool['active'] = (tool['type'] == self.current_tool)

        for color_btn in self.ui_elements['colors']:
            color_btn['active'] = (color_btn['color'] == self.current_color)

        slider = self.ui_elements['thickness_slider']
        slider['value'] = self.thickness
        slider['handle_rect'].x = slider['rect'].x + (self.thickness - slider['min']) * 10

    def draw_ui(self):
        """отрисовка интерфейса для юзера"""
        pygame.draw.rect(self.screen, (240, 240, 240), (0, 0, SCREEN_WIDTH, 50))
        pygame.draw.line(self.screen, (200, 200, 200), (0, 50), (SCREEN_WIDTH, 50), 2)

        for tool in self.ui_elements['tools']:
            color = (200, 230, 200) if tool['active'] else (220, 220, 220)
            pygame.draw.rect(self.screen, color, tool['rect'])
            pygame.draw.rect(self.screen, (100, 100, 100), tool['rect'], 1)

            text = self.font.render(tool['text'], True, (0, 0, 0))
            text_rect = text.get_rect(center=tool['rect'].center)
            self.screen.blit(text, text_rect)

        for color_btn in self.ui_elements['colors']:
            pygame.draw.rect(self.screen, color_btn['color'], color_btn['rect'])
            if color_btn['active']:
                pygame.draw.rect(self.screen, (255, 255, 255), color_btn['rect'], 3)
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), color_btn['rect'], 1)

        slider = self.ui_elements['thickness_slider']
        pygame.draw.rect(self.screen, (200, 200, 200), slider['rect'])
        pygame.draw.rect(self.screen, (100, 100, 100), slider['rect'], 1)
        pygame.draw.rect(self.screen, (100, 100, 200), slider['handle_rect'])

        thickness_text = self.small_font.render(f"толщина: {self.thickness}", True, (0, 0, 0))
        self.screen.blit(thickness_text, (slider['rect'].x, slider['rect'].y - 15))

        save_btn = self.ui_elements['save_button']
        pygame.draw.rect(self.screen, (200, 230, 200), save_btn['rect'])
        pygame.draw.rect(self.screen, (100, 100, 100), save_btn['rect'], 1)
        save_text = self.font.render(save_btn['text'], True, (0, 0, 0))
        save_text_rect = save_text.get_rect(center=save_btn['rect'].center)
        self.screen.blit(save_text, save_text_rect)

        clear_btn = self.ui_elements['clear_button']
        pygame.draw.rect(self.screen, (255, 200, 200), clear_btn['rect'])
        pygame.draw.rect(self.screen, (100, 100, 100), clear_btn['rect'], 1)
        clear_text = self.font.render(clear_btn['text'], True, (0, 0, 0))
        clear_text_rect = clear_text.get_rect(center=clear_btn['rect'].center)
        self.screen.blit(clear_text, clear_text_rect)

        deselect_btn = self.ui_elements['deselect_button']
        btn_color = (200, 200, 255) if self.selected_shape_indices else (220, 220, 220)
        pygame.draw.rect(self.screen, btn_color, deselect_btn['rect'])
        pygame.draw.rect(self.screen, (100, 100, 100), deselect_btn['rect'], 1)
        deselect_text = self.font.render(deselect_btn['text'], True, (0, 0, 0))
        deselect_text_rect = deselect_text.get_rect(center=deselect_btn['rect'].center)
        self.screen.blit(deselect_text, deselect_text_rect)

        select_all_btn = self.ui_elements['select_all_button']
        pygame.draw.rect(self.screen, (200, 255, 200), select_all_btn['rect'])
        pygame.draw.rect(self.screen, (100, 100, 100), select_all_btn['rect'], 1)
        select_all_text = self.font.render(select_all_btn['text'], True, (0, 0, 0))
        select_all_text_rect = select_all_text.get_rect(center=select_all_btn['rect'].center)
        self.screen.blit(select_all_text, select_all_text_rect)

        help_text = self.small_font.render(
            "r - прямоугольник | t - треугольник | c - очистить | s - сохранить | "
            "del - удалить выбранные | ctrl+клик - добавить | a - все",
            True, (80, 80, 80))
        self.screen.blit(help_text, (10, SCREEN_HEIGHT - 25))

        """отображаем инфу о выбранных фигурах"""
        if self.selected_shape_indices:
            count = len(self.selected_shape_indices)
            selected_info = self.small_font.render(
                f"Выбрано фигур: {count}", True, SELECTION_COLOR)
            self.screen.blit(selected_info, (10, SCREEN_HEIGHT - 45))

    def point_in_rect(self, point, rect_start, rect_end):
        """проверка, находится ли точка внутри прямоугольника"""
        x, y = point
        x1, y1 = rect_start
        x2, y2 = rect_end
        
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        
        """небольшой допуск для удобства выделения"""
        tolerance = 5
        return (min_x - tolerance <= x <= max_x + tolerance and 
                min_y - tolerance <= y <= max_y + tolerance)

    def point_in_triangle(self, point, p1, p2, p3):
        """проверка, находится ли точка внутри треугольника"""
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        
        d1 = sign(point, p1, p2)
        d2 = sign(point, p2, p3)
        d3 = sign(point, p3, p1)
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)

    def get_triangle_points(self, start, end):
        """получение точек треугольника"""
        x1, y1 = start
        x2, y2 = end
        
        base_y = max(y1, y2)
        top_y = min(y1, y2)
        mid_x = (x1 + x2) // 2
        
        return [(x1, base_y), (x2, base_y), (mid_x, top_y)]

    def get_shape_bounds(self, shape):
        """получение границ фигуры для прямоугольника выделения"""
        if shape['type'] == 'rectangle':
            x1, y1 = shape['start']
            x2, y2 = shape['end']
            return (min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
        elif shape['type'] == 'triangle':
            points = self.get_triangle_points(shape['start'], shape['end'])
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        return (0, 0, 0, 0)

    def rect_collides_with_shape(self, rect, shape):
        """проверка пересечения прямоугольника выделения с фигурой"""
        shape_bounds = self.get_shape_bounds(shape)
        shape_rect = pygame.Rect(shape_bounds)
        return rect.colliderect(shape_rect)

    def find_shapes_in_rect(self, rect):
        """поиск всех фигур внутри прямоугольника выделения"""
        found_indices = []
        selection_rect = pygame.Rect(rect)
        
        for i, shape in enumerate(self.shapes):
            if self.rect_collides_with_shape(selection_rect, shape):
                found_indices.append(i)
        
        return found_indices

    def find_shape_at_point(self, point):
        """поиск фигуры по координатам точки"""
        for i in range(len(self.shapes) - 1, -1, -1):  # Ищем с конца (сверху)
            shape = self.shapes[i]
            
            if shape['type'] == 'rectangle':
                if self.point_in_rect(point, shape['start'], shape['end']):
                    return i
            elif shape['type'] == 'triangle':
                points = self.get_triangle_points(shape['start'], shape['end'])
                if self.point_in_triangle(point, points[0], points[1], points[2]):
                    return i
        
        return -1

    def draw_selection_highlight(self, shape, is_multi=False):
        """отрисовка выделения вокруг фигуры"""
        color = MULTI_SELECTION_COLOR if is_multi and len(self.selected_shape_indices) > 1 else SELECTION_COLOR
        
        if shape['type'] == 'rectangle':
            x1, y1 = shape['start']
            x2, y2 = shape['end']
            
            rect = pygame.Rect(min(x1, x2), min(y1, y2),
                               abs(x1 - x2), abs(y1 - y2))
            pygame.draw.rect(self.screen, color, rect, SELECTION_THICKNESS)
            
            # Рисуем маркеры по углам
            for x, y in [(rect.left, rect.top), (rect.right, rect.top),
                         (rect.left, rect.bottom), (rect.right, rect.bottom)]:
                pygame.draw.circle(self.screen, color, (x, y), 4)
                
        elif shape['type'] == 'triangle':
            points = self.get_triangle_points(shape['start'], shape['end'])
            pygame.draw.polygon(self.screen, color, points, SELECTION_THICKNESS)
            
            """рисуем маркеры в вершинах"""
            for point in points:
                pygame.draw.circle(self.screen, color, point, 4)

    def handle_events(self):
        """обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.current_tool = 'rectangle'
                    self.update_ui_active_states()
                elif event.key == pygame.K_t:
                    self.current_tool = 'triangle'
                    self.update_ui_active_states()
                elif event.key == pygame.K_c:
                    self.shapes.clear()
                    self.selected_shape_indices.clear()
                elif event.key == pygame.K_s:
                    self.save_image()
                elif event.key == pygame.K_ESCAPE:
                    self.drawing = False
                    self.start_pos = None
                    self.dragging_selected = False
                    self.selecting = False
                    self.selection_rect = None
                elif event.key == pygame.K_DELETE:
                    if self.selected_shape_indices:
                        # Удаляем выбранные фигуры (с конца, чтобы индексы не съезжали)
                        indices_to_delete = sorted(self.selected_shape_indices, reverse=True)
                        for idx in indices_to_delete:
                            if idx < len(self.shapes):
                                del self.shapes[idx]
                        self.selected_shape_indices.clear()
                elif event.key == pygame.K_a:
                    # Выделить все
                    self.selected_shape_indices = set(range(len(self.shapes)))
                elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.ctrl_pressed = True

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.ctrl_pressed = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # левая кнопка мыши
                    if not self.handle_ui_click(event.pos):
                        if event.pos[1] > 50:
                            # Проверяем, кликнули ли на фигуру
                            clicked_shape_index = self.find_shape_at_point(event.pos)
                            
                            if clicked_shape_index != -1:
                                # Кликнули на фигуру
                                if self.ctrl_pressed:
                                    # Ctrl + клик: добавляем/убираем из выделения
                                    if clicked_shape_index in self.selected_shape_indices:
                                        self.selected_shape_indices.remove(clicked_shape_index)
                                    else:
                                        self.selected_shape_indices.add(clicked_shape_index)
                                else:
                                    # Обычный клик: проверяем, кликнули ли на уже выделенную фигуру
                                    if clicked_shape_index in self.selected_shape_indices:
                                        # Начинаем перетаскивание всех выбранных фигур
                                        self.dragging_selected = True
                                        self.drag_offsets.clear()
                                        for idx in self.selected_shape_indices:
                                            shape = self.shapes[idx]
                                            self.drag_offsets[idx] = (
                                                shape['start'][0] - event.pos[0],
                                                shape['start'][1] - event.pos[1]
                                            )
                                    else:
                                        # Кликнули на другую фигуру - выделяем только её
                                        self.selected_shape_indices = {clicked_shape_index}
                                        self.dragging_selected = False
                            else:
                                # Кликнули в пустое место
                                if not self.ctrl_pressed:
                                    # Если не зажат Ctrl - снимаем выделение
                                    self.selected_shape_indices.clear()
                                
                                # Начинаем рисование или выделение прямоугольником
                                self.start_pos = event.pos
                                if self.ctrl_pressed:
                                    # Режим выделения прямоугольником
                                    self.selecting = True
                                else:
                                    # Режим рисования
                                    self.drawing = True
                                
                                self.last_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.selecting and self.start_pos and self.start_pos != event.pos:
                        # Завершаем выделение прямоугольником
                        rect = (min(self.start_pos[0], event.pos[0]),
                               min(self.start_pos[1], event.pos[1]),
                               abs(self.start_pos[0] - event.pos[0]),
                               abs(self.start_pos[1] - event.pos[1]))
                        
                        found_indices = self.find_shapes_in_rect(rect)
                        if self.ctrl_pressed:
                            # Добавляем найденные фигуры к выделению
                            self.selected_shape_indices.update(found_indices)
                        else:
                            # Заменяем выделение найденными фигурами
                            self.selected_shape_indices = set(found_indices)
                    
                    elif self.drawing and self.start_pos and self.start_pos != event.pos:
                        end_pos = event.pos
                        if end_pos[1] > 50:
                            self.add_shape(self.start_pos, end_pos)
                    
                    self.drawing = False
                    self.selecting = False
                    self.dragging_selected = False
                    self.start_pos = None
                    self.selection_rect = None
                    self.drag_offsets.clear()
                    self.preview_surface.fill((0, 0, 0, 0))

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_selected and self.selected_shape_indices:
                    # Перетаскивание всех выбранных фигур
                    for idx in self.selected_shape_indices:
                        if idx in self.drag_offsets and idx < len(self.shapes):
                            shape = self.shapes[idx]
                            dx = event.pos[0] + self.drag_offsets[idx][0] - shape['start'][0]
                            dy = event.pos[1] + self.drag_offsets[idx][1] - shape['start'][1]
                            
                            shape['start'] = (shape['start'][0] + dx, shape['start'][1] + dy)
                            shape['end'] = (shape['end'][0] + dx, shape['end'][1] + dy)
                            
                            # Обновляем смещение
                            self.drag_offsets[idx] = (
                                shape['start'][0] - event.pos[0],
                                shape['start'][1] - event.pos[1]
                            )
                elif self.drawing or self.selecting:
                    self.last_pos = event.pos
                    if self.drawing:
                        self.update_preview()
                    elif self.selecting:
                        # Обновляем прямоугольник выделения
                        self.selection_rect = (
                            min(self.start_pos[0], self.last_pos[0]),
                            min(self.start_pos[1], self.last_pos[1]),
                            abs(self.start_pos[0] - self.last_pos[0]),
                            abs(self.start_pos[1] - self.last_pos[1])
                        )

            elif event.type == pygame.MOUSEWHEEL:
                self.thickness += event.y
                self.thickness = max(1, min(10, self.thickness))
                self.update_ui_active_states()

        return True

    def handle_ui_click(self, pos):
        """клики по интерфейсу"""
        for tool in self.ui_elements['tools']:
            if tool['rect'].collidepoint(pos):
                self.current_tool = tool['type']
                self.update_ui_active_states()
                return True

        for color_btn in self.ui_elements['colors']:
            if color_btn['rect'].collidepoint(pos):
                self.current_color = color_btn['color']
                self.update_ui_active_states()
                return True

        slider = self.ui_elements['thickness_slider']
        if slider['rect'].collidepoint(pos):
            relative_x = pos[0] - slider['rect'].x
            relative_x = max(0, min(slider['rect'].width - slider['handle_rect'].width,
                                    relative_x - slider['handle_rect'].width / 2))
            thickness_value = round(relative_x / (slider['rect'].width - slider['handle_rect'].width) *
                                    (slider['max'] - slider['min']) + slider['min'])
            self.thickness = thickness_value
            self.update_ui_active_states()
            return True

        if self.ui_elements['save_button']['rect'].collidepoint(pos):
            self.save_image()
            return True

        if self.ui_elements['clear_button']['rect'].collidepoint(pos):
            self.shapes.clear()
            self.selected_shape_indices.clear()
            return True

        if self.ui_elements['deselect_button']['rect'].collidepoint(pos):
            self.selected_shape_indices.clear()
            return True

        if self.ui_elements['select_all_button']['rect'].collidepoint(pos):
            self.selected_shape_indices = set(range(len(self.shapes)))
            return True

        return False

    def add_shape(self, start_pos, end_pos):
        """добавление новой фигуры"""
        start_pos = (max(0, min(SCREEN_WIDTH, start_pos[0])),
                     max(50, min(SCREEN_HEIGHT, start_pos[1])))
        end_pos = (max(0, min(SCREEN_WIDTH, end_pos[0])),
                   max(50, min(SCREEN_HEIGHT, end_pos[1])))

        shape = {
            'type': self.current_tool,
            'start': start_pos,
            'end': end_pos,
            'color': self.current_color,
            'thickness': self.thickness
        }
        self.shapes.append(shape)
        
        if not self.ctrl_pressed:
            # Если не зажат Ctrl, выделяем только новую фигуру
            self.selected_shape_indices = {len(self.shapes) - 1}
        else:
            # Если зажат Ctrl, добавляем новую фигуру к выделению
            self.selected_shape_indices.add(len(self.shapes) - 1)

    def update_preview(self):
        """предпросмотр фигуры"""
        self.preview_surface.fill((0, 0, 0, 0))
        if self.start_pos and self.last_pos and self.drawing:
            if self.last_pos[1] > 50:
                self.draw_shape(self.preview_surface,
                                self.current_tool,
                                self.start_pos,
                                self.last_pos,
                                self.current_color,
                                self.thickness,
                                preview=True)

    def draw_shape(self, surface, shape_type, start, end, color, thickness, preview=False):
        """отрисовка одной фигуры"""
        x1, y1 = start
        x2, y2 = end

        if shape_type == 'rectangle':
            rect = pygame.Rect(min(x1, x2), min(y1, y2),
                               abs(x1 - x2), abs(y1 - y2))
            pygame.draw.rect(surface, color, rect, thickness)

        elif shape_type == 'triangle':
            base_y = max(y1, y2)
            top_y = min(y1, y2)
            mid_x = (x1 + x2) // 2

            points = [(x1, base_y), (x2, base_y), (mid_x, top_y)]
            pygame.draw.polygon(surface, color, points, thickness)

        if preview:
            preview_surface = surface.copy()
            preview_surface.set_alpha(128)
            surface.blit(preview_surface, (0, 0))

    def draw_shapes(self):
        """отрисовка всех фигур"""
        for i, shape in enumerate(self.shapes):
            self.draw_shape(self.screen,
                            shape['type'],
                            shape['start'],
                            shape['end'],
                            shape['color'],
                            shape['thickness'])
            
            # Рисуем обводку выделения для выбранных фигур
            if i in self.selected_shape_indices:
                is_multi = len(self.selected_shape_indices) > 1
                self.draw_selection_highlight(shape, is_multi)

        # Рисуем прямоугольник выделения
        if self.selecting and self.selection_rect:
            rect_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            rect_surface.fill((0, 0, 0, 0))
            pygame.draw.rect(rect_surface, (*SELECTION_COLOR, 64), 
                           self.selection_rect, 2)
            pygame.draw.rect(rect_surface, (*SELECTION_COLOR, 32), 
                           self.selection_rect, 0)
            self.screen.blit(rect_surface, (0, 0))

    def save_image(self):
        """сохранение изображения"""
        program_dir = os.path.dirname(os.path.abspath(__file__))
        saves_dir = os.path.join(program_dir, 'saves')

        if not os.path.exists(saves_dir):
            os.makedirs(saves_dir)
            print(f"создана папка: {saves_dir}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(saves_dir, f"drawing_{timestamp}.png")

        try:
            drawing_surface = self.screen.subsurface(
                (0, 50, SCREEN_WIDTH, SCREEN_HEIGHT - 50 - 30)
            )
            pygame.image.save(drawing_surface, filename)
            print(f"изображение сохранено: {filename}")
        
            notification_text = self.font.render("сохранено!", True, (0, 128, 0))
            notification_rect = notification_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(notification_text, notification_rect)
            pygame.display.flip()
            pygame.time.wait(500)
        except Exception as e:
            print(f"ошибка при сохранении: {e}")

    def run(self):
        """здесь запуск"""
        clock = pygame.time.Clock()
        running = True

        while running:
            running = self.handle_events()

            self.screen.fill(BACKGROUND_COLOR)

            self.draw_shapes()

            if self.drawing and self.start_pos and self.last_pos:
                self.screen.blit(self.preview_surface, (0, 0))

            self.draw_ui()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

def main():
    app = DrawingApp()
    app.run()

if __name__ == "__main__":
    main()