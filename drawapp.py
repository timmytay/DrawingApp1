import pygame
import sys
import os
from datetime import datetime

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (255, 255, 255)
DEFAULT_COLOR = (0, 0, 0)
DEFAULT_THICKNESS = 2

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
        pygame.display.set_caption("трофим (в8)")
        pygame.display.set_caption("трофим (в8)")

        self.shapes = []
        self.current_tool = 'rectangle'
        self.current_color = COLORS['BLACK']
        self.thickness = DEFAULT_THICKNESS
        self.drawing = False
        self.start_pos = None
        self.last_pos = None
        self.preview_surface = None

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
            'rect': pygame.Rect(0, tool_y, 130, 30),
            'type': 'rectangle',
            'text': 'прямоугольник',
            'active': True
        })

        ui['tools'].append({
            'rect': pygame.Rect(130, tool_y, 130, 30),
            'type': 'triangle',
            'text': 'треугольник',
            'active': False
        })

        color_x = 280
        for i, (color_name, color_value) in enumerate(COLORS.items()):
            ui['colors'].append({
                'rect': pygame.Rect(color_x + i * 40, tool_y, 30, 30),
                'color': color_value,
                'name': color_name,
                'active': color_value == self.current_color
            })

        ui['thickness_slider'] = {
            'rect': pygame.Rect(570, tool_y + 10, 100, 6),
            'handle_rect': pygame.Rect(
                570 + int((self.thickness - 1) / (10 - 1) * (100 - 8)),
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

        help_text = self.small_font.render("r - прямоугольник | t - треугольник | c - очистить | s - сохранить", True,
                                           (80, 80, 80))
        self.screen.blit(help_text, (10, SCREEN_HEIGHT - 25))

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
                elif event.key == pygame.K_s:
                    self.save_image()
                elif event.key == pygame.K_ESCAPE:
                    self.drawing = False
                    self.start_pos = None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.handle_ui_click(event.pos):
                        if event.pos[1] > 50:
                            self.drawing = True
                            self.start_pos = event.pos
                            self.last_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.drawing:
                    if self.start_pos and self.start_pos != event.pos:
                        end_pos = event.pos
                        if end_pos[1] > 50:
                            self.add_shape(self.start_pos, end_pos)
                    self.drawing = False
                    self.start_pos = None
                    self.preview_surface.fill((0, 0, 0, 0))

            elif event.type == pygame.MOUSEMOTION:
                if self.drawing:
                    self.last_pos = event.pos
                    self.update_preview()

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
        for shape in self.shapes:
            self.draw_shape(self.screen,
                            shape['type'],
                            shape['start'],
                            shape['end'],
                            shape['color'],
                            shape['thickness'])

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
                (0, 50, SCREEN_WIDTH, SCREEN_HEIGHT - 50 - 30)  # Вычитаем 30 пикселей для инструкции внизу
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