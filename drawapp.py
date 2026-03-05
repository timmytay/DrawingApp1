import pygame
import sys
import os
import math
from datetime import datetime

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (255, 255, 255)
DEFAULT_COLOR = (0, 0, 0)
DEFAULT_THICKNESS = 2
SELECTION_COLOR = (0, 120, 255)
SELECTION_THICKNESS = 2
MULTI_SELECTION_COLOR = (255, 165, 0)
CENTER_COLOR = (255, 0, 0)

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
        pygame.display.set_caption("трофим (в8) - мультивыделение + матричные трансформации")

        self.shapes = []
        self.selected_shape_indices = set()  # множество индексов выбранных фигур
        self.current_tool = 'rectangle'
        self.current_color = COLORS['BLACK']
        self.thickness = DEFAULT_THICKNESS
        self.drawing = False
        self.start_pos = None
        self.last_pos = None
        self.preview_surface = None
        self.dragging_selected = False  # флаг перетаскивания выбранных фигур
        self.drag_offsets = {}  # словарь смещений для каждой фигуры
        self.selection_rect = None  # прямоугольник выделения
        self.selecting = False  # режим выделения прямоугольником
        self.ctrl_pressed = False  # флаг нажатия Ctrl
        self.show_center = True  # флаг отображения центра
        self.last_mouse_pos = None  # для матричных трансформаций
        self.fixed_center = None  # фиксированный центр для текущей трансформации

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        self.preview_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        self.ui_elements = self.create_ui()

    def multiply_matrices(self, A, B):
        """умножение двух матриц 3x3"""
        result = [[0]*3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    result[i][j] += A[i][k] * B[k][j]
        return result

    def multiply_matrix_vector(self, matrix, point):
        """умножение матрицы 3x3 на точку (x, y)"""
        x, y = point
        new_x = matrix[0][0]*x + matrix[0][1]*y + matrix[0][2]
        new_y = matrix[1][0]*x + matrix[1][1]*y + matrix[1][2]
        return (new_x, new_y)

    def apply_matrix_to_shape(self, shape, matrix):
        """применение матрицы трансформации к фигуре"""
        if 'points' in shape:
            # новая структура с points
            shape['points'] = [
                self.multiply_matrix_vector(matrix, p)
                for p in shape['points']
            ]
        else:
            # старая структура с start/end (для обратной совместимости)
            start = shape['start']
            end = shape['end']
            shape['start'] = self.multiply_matrix_vector(matrix, start)
            shape['end'] = self.multiply_matrix_vector(matrix, end)

    def translation_matrix(self, dx, dy):
        """матрица переноса"""
        return [
            [1, 0, dx],
            [0, 1, dy],
            [0, 0, 1]
        ]

    def rotation_matrix(self, angle):
        """матрица поворота (угол в радианах)"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return [
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ]

    def scale_matrix(self, s):
        """матрица масштабирования"""
        return [
            [s, 0, 0],
            [0, s, 0],
            [0, 0, 1]
        ]

    def create_ui(self):
        """создание элементов интерфейса"""
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
        
        ui['center_button'] = {
            'rect': pygame.Rect(SCREEN_WIDTH - 300, tool_y, 60, 30),
            'text': 'центр',
            'active': self.show_center
        }

        return ui

    def update_ui_active_states(self):
        """обновление активных состояний элементов интерфейса"""
        for tool in self.ui_elements['tools']:
            tool['active'] = (tool['type'] == self.current_tool)

        for color_btn in self.ui_elements['colors']:
            color_btn['active'] = (color_btn['color'] == self.current_color)

        slider = self.ui_elements['thickness_slider']
        slider['value'] = self.thickness
        slider['handle_rect'].x = slider['rect'].x + (self.thickness - slider['min']) * 10
        
        self.ui_elements['center_button']['active'] = self.show_center

    def draw_ui(self):
        """отрисовка интерфейса"""
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
        
        center_btn = self.ui_elements['center_button']
        btn_color = (200, 200, 200) if center_btn['active'] else (220, 220, 220)
        pygame.draw.rect(self.screen, btn_color, center_btn['rect'])
        pygame.draw.rect(self.screen, (100, 100, 100), center_btn['rect'], 1)
        center_text = self.font.render(center_btn['text'], True, (0, 0, 0))
        center_text_rect = center_text.get_rect(center=center_btn['rect'].center)
        self.screen.blit(center_text, center_text_rect)

        help_text = self.small_font.render(
            "r - прямоугольник | t - треугольник | c - очистить | s - сохранить | "
            "del - удалить выбранные | ctrl+клик - добавить | a - все | центр - пробел | "
            "колесико: поворот | shift+колесико: масштаб",
            True, (80, 80, 80))
        self.screen.blit(help_text, (10, SCREEN_HEIGHT - 25))

        if self.selected_shape_indices:
            count = len(self.selected_shape_indices)
            selected_info = self.small_font.render(
                f"Выбрано фигур: {count}", True, SELECTION_COLOR)
            self.screen.blit(selected_info, (10, SCREEN_HEIGHT - 45))

    def create_rectangle_points(self, start, end):
        """создание точек прямоугольника"""
        x1, y1 = start
        x2, y2 = end
        return [
            (x1, y1),
            (x2, y1),
            (x2, y2),
            (x1, y2)
        ]

    def create_triangle_points(self, start, end):
        """создание точек треугольника"""
        x1, y1 = start
        x2, y2 = end
        base_y = max(y1, y2)
        top_y = min(y1, y2)
        mid_x = (x1 + x2) // 2
        return [
            (x1, base_y),
            (x2, base_y),
            (mid_x, top_y)
        ]

    def add_shape(self, start_pos, end_pos):
        """добавление новой фигуры"""
        start_pos = (max(0, min(SCREEN_WIDTH, start_pos[0])),
                     max(50, min(SCREEN_HEIGHT, start_pos[1])))
        end_pos = (max(0, min(SCREEN_WIDTH, end_pos[0])),
                   max(50, min(SCREEN_HEIGHT, end_pos[1])))

        if self.current_tool == 'rectangle':
            points = self.create_rectangle_points(start_pos, end_pos)
        else:
            points = self.create_triangle_points(start_pos, end_pos)

        shape = {
            'type': self.current_tool,
            'points': points,  # новая структура с points
            'color': self.current_color,
            'thickness': self.thickness
        }
        self.shapes.append(shape)
        
        if not self.ctrl_pressed:
            # если не зажат Ctrl, выделяем только новую фигуру
            self.selected_shape_indices = {len(self.shapes) - 1}
        else:
            # если зажат Ctrl, добавляем новую фигуру к выделению
            self.selected_shape_indices.add(len(self.shapes) - 1)

    def point_in_rect(self, point, rect_start, rect_end):
        """проверка, находится ли точка внутри прямоугольника"""
        x, y = point
        x1, y1 = rect_start
        x2, y2 = rect_end
        
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        
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

    def point_in_shape(self, point, shape):
        """проверка, находится ли точка внутри фигуры"""
        if shape['type'] == 'rectangle':
            # для прямоугольника используем точки
            xs = [p[0] for p in shape['points']]
            ys = [p[1] for p in shape['points']]
            min_x = min(xs)
            max_x = max(xs)
            min_y = min(ys)
            max_y = max(ys)
            tolerance = 5
            return (min_x - tolerance <= point[0] <= max_x + tolerance and 
                    min_y - tolerance <= point[1] <= max_y + tolerance)
        else:  # triangle
            return self.point_in_triangle(point, shape['points'][0], 
                                        shape['points'][1], shape['points'][2])

    def find_shape_at_point(self, point):
        """поиск фигуры по координатам точки"""
        for i in range(len(self.shapes) - 1, -1, -1):  # ищем с конца (сверху)
            shape = self.shapes[i]
            if self.point_in_shape(point, shape):
                return i
        return -1

    def get_shape_bounds(self, shape):
        """получение границ фигуры для прямоугольника выделения"""
        xs = [p[0] for p in shape['points']]
        ys = [p[1] for p in shape['points']]
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

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
    # выделение
    def draw_selection_highlight(self, shape, is_multi=False):
        """отрисовка выделения вокруг фигуры"""
        color = MULTI_SELECTION_COLOR if is_multi and len(self.selected_shape_indices) > 1 else SELECTION_COLOR
        pygame.draw.polygon(self.screen, color, shape['points'], SELECTION_THICKNESS)
        
        # рисуем маркеры в вершинах
        for point in shape['points']:
            pygame.draw.circle(self.screen, color, (int(point[0]), int(point[1])), 4)

    def calculate_center(self):
        """вычисление центра выделенных фигур"""
        if len(self.selected_shape_indices) == 0:
            return None
        
        total_x = 0
        total_y = 0
        point_count = 0
        
        for idx in self.selected_shape_indices:
            if idx < len(self.shapes):
                shape = self.shapes[idx]
                for point in shape['points']:
                    total_x += point[0]
                    total_y += point[1]
                    point_count += 1
        
        if point_count > 0:
            center_x = total_x // point_count
            center_y = total_y // point_count
            return (center_x, center_y)
        
        return None

    def draw_center(self, center_pos):
        """отрисовка центра выделенных фигур"""
        if not center_pos or not self.show_center:
            return
        
        x, y = int(center_pos[0]), int(center_pos[1])
        
        # перекрестие
        cross_size = 10
        pygame.draw.line(self.screen, CENTER_COLOR, 
                        (x - cross_size, y), (x + cross_size, y), 2)
        pygame.draw.line(self.screen, CENTER_COLOR, 
                        (x, y - cross_size), (x, y + cross_size), 2)
        
        # окружность вокруг центра
        pygame.draw.circle(self.screen, CENTER_COLOR, (x, y), 15, 2)
        
        # координаты центра
        coord_text = self.small_font.render(
            f"({x}, {y})", True, CENTER_COLOR)
        text_rect = coord_text.get_rect(center=(x, y - 25))
        
        # фон для текста
        pygame.draw.rect(self.screen, (255, 255, 255, 200), 
                        text_rect.inflate(10, 5))
        pygame.draw.rect(self.screen, CENTER_COLOR, 
                        text_rect.inflate(10, 5), 1)
        self.screen.blit(coord_text, text_rect)

    def handle_ui_click(self, pos):
        """обработка кликов по интерфейсу"""
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
            
        if self.ui_elements['center_button']['rect'].collidepoint(pos):
            self.show_center = not self.show_center
            self.update_ui_active_states()
            return True

        return False

    def handle_events(self):
        """обработка всех событий"""
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
                        indices_to_delete = sorted(self.selected_shape_indices, reverse=True)
                        for idx in indices_to_delete:
                            if idx < len(self.shapes):
                                del self.shapes[idx]
                        self.selected_shape_indices.clear()
                elif event.key == pygame.K_a:
                    self.selected_shape_indices = set(range(len(self.shapes)))
                elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.ctrl_pressed = True
                elif event.key == pygame.K_SPACE:
                    self.show_center = not self.show_center
                    self.update_ui_active_states()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.ctrl_pressed = False
                    # выделение фигуры
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # левая кнопка мыши
                    if not self.handle_ui_click(event.pos):
                        if event.pos[1] > 50:
                            clicked_shape_index = self.find_shape_at_point(event.pos)
                            
                            if clicked_shape_index != -1:
                                # кликнули на фигуру
                                if self.ctrl_pressed:
                                    # добавляем/убираем из выделения
                                    if clicked_shape_index in self.selected_shape_indices:
                                        self.selected_shape_indices.remove(clicked_shape_index)
                                    else:
                                        self.selected_shape_indices.add(clicked_shape_index)
                                else:
                                    # обычный клик
                                    if clicked_shape_index in self.selected_shape_indices:
                                        # начинаем перетаскивание всех выбранных фигур
                                        self.dragging_selected = True
                                        self.last_mouse_pos = event.pos
                                        self.drag_offsets.clear()
                                        for idx in self.selected_shape_indices:
                                            shape = self.shapes[idx]
                                            # для новой структуры с points
                                            if 'points' in shape:
                                                self.drag_offsets[idx] = (
                                                    shape['points'][0][0] - event.pos[0],
                                                    shape['points'][0][1] - event.pos[1]
                                                )
                                            else:
                                                # для обратной совместимости
                                                self.drag_offsets[idx] = (
                                                    shape['start'][0] - event.pos[0],
                                                    shape['start'][1] - event.pos[1]
                                                )
                                    else:
                                        # кликнули на другую фигуру
                                        self.selected_shape_indices = {clicked_shape_index}
                                        self.dragging_selected = False
                            else:
                                # кликнули в пустое место
                                if not self.ctrl_pressed:
                                    self.selected_shape_indices.clear()
                                
                                self.start_pos = event.pos
                                if self.ctrl_pressed:
                                    self.selecting = True
                                else:
                                    self.drawing = True
                                
                                self.last_pos = event.pos

                elif event.button == 3:  # правая кнопка мыши
                    # можно использовать для контекстного меню, пока ничего не делаем
                    pass

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.selecting and self.start_pos and self.start_pos != event.pos:
                        rect = (min(self.start_pos[0], event.pos[0]),
                               min(self.start_pos[1], event.pos[1]),
                               abs(self.start_pos[0] - event.pos[0]),
                               abs(self.start_pos[1] - event.pos[1]))
                        
                        found_indices = self.find_shapes_in_rect(rect)
                        if self.ctrl_pressed:
                            self.selected_shape_indices.update(found_indices)
                        else:
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
                    self.fixed_center = None  # сбрасываем фиксированный центр

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_selected and self.selected_shape_indices and self.last_mouse_pos:
                    # перетаскивание с использованием матрицы переноса
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    
                    matrix = self.translation_matrix(dx, dy)
                    
                    for idx in self.selected_shape_indices:
                        if idx < len(self.shapes):
                            self.apply_matrix_to_shape(self.shapes[idx], matrix)
                    
                    self.last_mouse_pos = event.pos
                    
                elif self.drawing or self.selecting:
                    self.last_pos = event.pos
                    if self.drawing:
                        self.update_preview()
                    elif self.selecting:
                        self.selection_rect = (
                            min(self.start_pos[0], self.last_pos[0]),
                            min(self.start_pos[1], self.last_pos[1]),
                            abs(self.start_pos[0] - self.last_pos[0]),
                            abs(self.start_pos[1] - self.last_pos[1])
                        )

            elif event.type == pygame.MOUSEWHEEL:
                if self.selected_shape_indices:
                    # Вычисляем центр один раз и фиксируем его для всей серии трансформаций
                    if self.fixed_center is None:
                        self.fixed_center = self.calculate_center()
                        print(f"Центр зафиксирован: {self.fixed_center}")  # для отладки
                    
                    if self.fixed_center:
                        cx, cy = self.fixed_center
                        
                        T1 = self.translation_matrix(-cx, -cy)
                        T2 = self.translation_matrix(cx, cy)
                        
                        keys = pygame.key.get_pressed()
                        
                        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                            # масштабирование
                            scale_factor = 1 + event.y * 0.1
                            S = self.scale_matrix(scale_factor)
                            # Правильный порядок: сначала T1, потом S, потом T2
                            matrix = self.multiply_matrices(T2,
                                     self.multiply_matrices(S, T1))
                        else:
                            # поворот
                            angle = event.y * 0.1
                            R = self.rotation_matrix(angle)
                            # Правильный порядок: сначала T1, потом R, потом T2
                            matrix = self.multiply_matrices(T2,
                                     self.multiply_matrices(R, T1))
                        
                        for idx in self.selected_shape_indices:
                            self.apply_matrix_to_shape(self.shapes[idx], matrix)
                else:
                    # если ничего не выделено, меняем толщину
                    self.thickness += event.y
                    self.thickness = max(1, min(10, self.thickness))
                    self.update_ui_active_states()

        return True

    def update_preview(self):
        """обновление предпросмотра фигуры"""
        self.preview_surface.fill((0, 0, 0, 0))
        if self.start_pos and self.last_pos and self.drawing:
            if self.last_pos[1] > 50:
                # создаем временные точки для предпросмотра
                if self.current_tool == 'rectangle':
                    points = self.create_rectangle_points(self.start_pos, self.last_pos)
                else:
                    points = self.create_triangle_points(self.start_pos, self.last_pos)
                
                preview_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(preview_surface, (*self.current_color, 128), points, self.thickness)
                self.preview_surface.blit(preview_surface, (0, 0))

    def draw_shapes(self):
        """отрисовка всех фигур"""
        for i, shape in enumerate(self.shapes):
            pygame.draw.polygon(self.screen,
                                shape['color'],
                                shape['points'],
                                shape['thickness'])
            
            # рисуем обводку выделения для выбранных фигур
            if i in self.selected_shape_indices:
                is_multi = len(self.selected_shape_indices) > 1
                self.draw_selection_highlight(shape, is_multi)

        # прямоугольник выделения
        if self.selecting and self.selection_rect:
            rect_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            rect_surface.fill((0, 0, 0, 0))
            pygame.draw.rect(rect_surface, (*SELECTION_COLOR, 64), 
                           self.selection_rect, 2)
            pygame.draw.rect(rect_surface, (*SELECTION_COLOR, 32), 
                           self.selection_rect, 0)
            self.screen.blit(rect_surface, (0, 0))
        
        # рисуем центр выделенных фигур (используем фиксированный центр, если он есть)
        if self.selected_shape_indices:
            if self.fixed_center is not None:
                self.draw_center(self.fixed_center)
            else:
                center = self.calculate_center()
                self.draw_center(center)

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
        """основной цикл программы"""
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