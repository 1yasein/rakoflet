from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Line, InstructionGroup
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.config import Config
from kivy.utils import platform
import random
import math

# منع الخروج عند الضغط على زر الهاتف الخلفي
Config.set('kivy', 'exit_on_escape', '0')

# تخصيص مظهر النوافذ
Window.clearcolor = (0.1, 0.1, 0.1, 1)

class FancyButton(Button):
    """زر مخصص بمظهر فاخر"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = 24
        self.bold = True
        self.size_hint = (None, None)
        self.height = 60
        self.width = 200
        
        with self.canvas.before:
            Color(0.2, 0.6, 0.2, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            
        self.bind(pos=self.update_rect, size=self.update_rect)
        
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        
    def on_press(self):
        anim = Animation(background_color=(0.3, 0.8, 0.3, 0.5), duration=0.1)
        anim.start(self)
        
    def on_release(self):
        anim = Animation(background_color=(0, 0, 0, 0), duration=0.3)
        anim.start(self)

class SnakeGame(Widget):
    # خصائص اللعبة
    score = NumericProperty(0)
    high_score = NumericProperty(0)
    snake_size = NumericProperty(20)
    snake_speed = NumericProperty(10)
    game_over = BooleanProperty(False)
    particles = ListProperty([])
    control_pad = ObjectProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.snake = []
        self.food = []
        self.direction = "right"
        self.next_direction = "right"
        self.touch_start = None
        self.paused = False
        self.is_mobile = platform in ('android', 'ios')  # تحديد إذا كان الجهاز جوالاً أم لا
        self.grow = False  # متغير لتحديد إذا كان الثعبان يحتاج للنمو
        
        # بدء اللعبة
        self.reset_game()
        
        # جدولة تحديث اللعبة
        self.update_event = Clock.schedule_interval(self.update, 1.0 / self.snake_speed)
        
        # خلفية متحركة
        self.setup_background()
        
        # ربط حدث لوحة المفاتيح
        Window.bind(on_key_down=self.on_key_down)
        
    def setup_background(self):
        """إعداد خلفية متحركة مع تأثيرات جذابة"""
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'pos': [random.randint(0, int(self.width)), random.randint(0, int(self.height))],
                'size': random.randint(2, 8),
                'speed': random.uniform(0.5, 2.0),
                'color': [random.random()*0.2, random.random()*0.2, 0.3 + random.random()*0.3, 0.5]
            })
        
    def update_particles(self, dt):
        """تحديث حركة الجزيئات"""
        for particle in self.particles:
            particle['pos'][1] -= particle['speed']
            if particle['pos'][1] < 0:
                particle['pos'][1] = self.height
                particle['pos'][0] = random.randint(0, int(self.width))
        
    def reset_game(self):
        """إعادة تعيين اللعبة"""
        self.snake = []
        self.food = []
        self.direction = "right"
        self.next_direction = "right"
        self.game_over = False
        self.score = 0
        self.paused = False
        self.grow = False
        
        # إنشاء الثعبان الابتدائي
        start_x = self.width // 2
        start_y = self.height // 2
        for i in range(3):
            self.snake.append([start_x - i * self.snake_size, start_y])
            
        # إنشاء الطعام الأول
        self.create_food()
        
    def create_food(self):
        """إنشاء طعام في مكان عشوائي"""
        while True:
            x = random.randint(2, (int(self.width) - self.snake_size * 2) // self.snake_size) * self.snake_size
            y = random.randint(2, (int(self.height) - self.snake_size * 2) // self.snake_size) * self.snake_size
            
            # التأكد من أن الطعام ليس على الثعبان
            if [x, y] not in self.snake:
                self.food = [x, y]
                break
                
    def update(self, dt):
        """تحديث حالة اللعبة"""
        if self.game_over or self.paused:
            return
            
        # تحديث اتجاه الثعبان
        self.direction = self.next_direction
        
        # حفظ رأس الثعبان الحالي
        head = self.snake[0][:]
        
        # تحريك رأس الثعبان بناءً على الاتجاه
        if self.direction == "up":
            head[1] += self.snake_size
        elif self.direction == "down":
            head[1] -= self.snake_size
        elif self.direction == "left":
            head[0] -= self.snake_size
        elif self.direction == "right":
            head[0] += self.snake_size
            
        # التحقق من الاصطدام بالجدران
        if (head[0] < 0 or head[0] >= self.width or 
            head[1] < 0 or head[1] >= self.height):
            self.end_game()
            return
            
        # التحقق من الاصطدام بالنفس
        if head in self.snake[1:]:  # تجاهل الرأس عند المقارنة
            self.end_game()
            return
            
        # إضافة الرأس الجديد
        self.snake.insert(0, head)
        
        # التحقق من أكل الطعام - الإصلاح هنا!
        head_x, head_y = head
        food_x, food_y = self.food
        distance = math.sqrt((head_x - food_x)**2 + (head_y - food_y)**2)
        
        if distance < self.snake_size:  # إذا كان الرأس قريباً من الطعام
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
            self.create_food()
            self.grow = True  # الثعبان يحتاج للنمو
            self.food_effect()  # تأثير عند أكل الطعام
        else:
            # إزالة الذيل إذا لم يؤكل الطعام ولم يكن الثعبان بحاجة للنمو
            if not self.grow:
                self.snake.pop()
            else:
                self.grow = False  # تم النمو، نعيد القيمة
            
        # تحديث الجزيئات
        self.update_particles(dt)
        
        # إعادة الرسم
        self.draw()
            
    def food_effect(self):
        """تأثير خاص عند أكل الطعام"""
        # إضافة جزيئات تأثير مؤقتة
        for _ in range(10):
            self.particles.append({
                'pos': [self.food[0] + random.randint(-10, 10), self.food[1] + random.randint(-10, 10)],
                'size': random.randint(3, 10),
                'speed': random.uniform(1.0, 3.0),
                'color': [1, 0.5, 0.2, 1],
                'lifetime': 10  # عدد التحديثات قبل إزالة الجزيء
            })
        
    def end_game(self):
        """إنهاء اللعبة وعرض النتيجة"""
        self.game_over = True
        
        # عرض نافذة النهاية
        self.show_game_over()
        
    def show_game_over(self):
        """عرض نافذة نهاية اللعبة"""
        modal = ModalView(size_hint=(0.8, 0.6), background_color=(0, 0, 0, 0.7))
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # عنوان النافذة
        title = Label(text='Game Over', font_size=40, color=(1, 0.2, 0.2, 1), bold=True)
        
        # عرض النقاط
        score_label = Label(text=f'Score: {self.score}', font_size=30, color=(1, 1, 1, 1))
        high_score_label = Label(text=f'High Score: {self.high_score}', font_size=30, color=(1, 1, 1, 1))
        
        # أزرار التحكم
        btn_layout = BoxLayout(size_hint_y=0.4, spacing=10)
        restart_btn = FancyButton(text='Restart', on_press=self.restart_game)
        menu_btn = FancyButton(text='Main Menu', on_press=self.to_main_menu)
        
        btn_layout.add_widget(restart_btn)
        btn_layout.add_widget(menu_btn)
        
        layout.add_widget(title)
        layout.add_widget(score_label)
        layout.add_widget(high_score_label)
        layout.add_widget(btn_layout)
        
        modal.add_widget(layout)
        modal.open()
        
    def restart_game(self, instance):
        """إعادة تشغيل اللعبة"""
        try:
            if instance and hasattr(instance, 'parent'):
                instance.parent.parent.parent.dismiss()
        except:
            pass
        self.reset_game()
        
    def to_main_menu(self, instance):
        """العودة إلى القائمة الرئيسية"""
        try:
            if instance and hasattr(instance, 'parent'):
                instance.parent.parent.parent.dismiss()
        except:
            pass
        App.get_running_app().show_main_menu()
        
    def toggle_pause(self):
        """تبديل حالة الإيقاف المؤقت"""
        self.paused = not self.paused
        
    def on_touch_down(self, touch):
        """معالجة لمس الشاشة"""
        if self.game_over:
            return super().on_touch_down(touch)
            
        # إذا كان على جوال، نتعامل مع اللمس للتحكم
        if self.is_mobile:
            self.touch_start = touch.pos
        return super().on_touch_down(touch)
        
    def on_touch_move(self, touch):
        """معالجة حركة اللمس"""
        if self.game_over or not self.touch_start:
            return super().on_touch_move(touch)
            
        # إذا كان على جوال، نتعامل مع اللمس للتحكم
        if self.is_mobile:
            # حساب اتجاه السحب
            dx = touch.x - self.touch_start[0]
            dy = touch.y - self.touch_start[1]
            
            # نحتاج حركة كافية لتغيير الاتجاه
            if abs(dx) < 20 and abs(dy) < 20:
                return super().on_touch_move(touch)
                
            # تحديد الاتجاه بناءً على الحركة الأكبر
            if abs(dx) > abs(dy):
                if dx > 0 and self.direction != "left":
                    self.next_direction = "right"
                elif dx < 0 and self.direction != "right":
                    self.next_direction = "left"
            else:
                if dy > 0 and self.direction != "down":
                    self.next_direction = "up"
                elif dy < 0 and self.direction != "up":
                    self.next_direction = "down"
                    
            self.touch_start = touch.pos
            
        return super().on_touch_move(touch)
        
    def on_touch_up(self, touch):
        """معالجة رفع الإصبع"""
        self.touch_start = None
        return super().on_touch_up(touch)
    
    def on_key_down(self, window, key, *args):
        """معالجة ضغطات لوحة المفاتيح (للكمبيوتر)"""
        if not self.is_mobile and not self.game_over:
            if key == 273 or key == 119:  # سهم أعلى أو W
                if self.direction != "down":
                    self.next_direction = "up"
            elif key == 274 or key == 115:  # سهم أسفل أو S
                if self.direction != "up":
                    self.next_direction = "down"
            elif key == 275 or key == 100:  # سهم يمين أو D
                if self.direction != "left":
                    self.next_direction = "right"
            elif key == 276 or key == 97:  # سهم يسار أو A
                if self.direction != "right":
                    self.next_direction = "left"
            elif key == 32:  # مفتاح المسافة
                self.toggle_pause()
            return True
        return False
        
    def on_size(self, *args):
        """عند تغيير حجم الويدجت"""
        if hasattr(self, 'snake') and self.snake:
            self.reset_game()
            
    def draw(self):
        """رسم اللعبة"""
        self.canvas.clear()
        with self.canvas:
            # رسم الخلفية والجزيئات
            Color(0.05, 0.05, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            for particle in self.particles:
                Color(*particle['color'])
                Ellipse(pos=particle['pos'], size=(particle['size'], particle['size']))
            
            # رسم الطعام
            Color(1, 0.2, 0.2, 1)
            Ellipse(pos=(self.food[0], self.food[1]), 
                   size=(self.snake_size, self.snake_size))
            
            # رسم الثعبان
            for i, segment in enumerate(self.snake):
                # تدرج اللون من الرأس إلى الذيل
                if i == 0:  # الرأس
                    Color(0.2, 0.8, 0.2, 1)
                else:
                    # تدرج اللون
                    color_val = max(0.3, 0.8 - (i / len(self.snake)) * 0.5)
                    Color(0.2, color_val, 0.2, 1)
                
                # رسم جزء الثعبان
                Ellipse(pos=(segment[0], segment[1]), 
                       size=(self.snake_size, self.snake_size))
                        
            # رسم الحدود
            Color(0.3, 0.3, 0.5, 1)
            Line(rectangle=(0, 0, self.width, self.height), width=1.5)
            
            # رسم النقاط
            Color(0.2, 0.2, 0.2, 0.8)
            Rectangle(pos=(10, self.height - 40), size=(160, 30))
            Color(1, 1, 1, 1)
            
            # إذا كانت اللعبة متوقفة، عرض رسالة الإيقاف
            if self.paused:
                Color(0, 0, 0, 0.7)
                Rectangle(pos=(0, 0), size=self.size)
                Color(1, 1, 1, 1)

class MainMenu(BoxLayout):
    """القائمة الرئيسية للعبة"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [20, 50, 20, 50]
        self.spacing = 30
        
        # عنوان اللعبة
        title = Label(text='SNAKE GAME', font_size=50, color=(0.2, 0.8, 0.2, 1), 
                     bold=True, size_hint_y=0.4)
        
        # أزرار القائمة
        btn_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.6)
        
        start_btn = FancyButton(text='Start Game', size_hint_y=None, height=80)
        start_btn.bind(on_press=self.start_game)
        
        exit_btn = FancyButton(text='Exit', size_hint_y=None, height=80)
        exit_btn.bind(on_press=self.exit_game)
        
        btn_layout.add_widget(start_btn)
        btn_layout.add_widget(exit_btn)
        
        self.add_widget(title)
        self.add_widget(btn_layout)
        
        # تعيين خلفية للقائمة الرئيسية
        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            
        self.bind(size=self.update_bg, pos=self.update_bg)
        
    def update_bg(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
        
    def start_game(self, instance):
        """بدء اللعبة"""
        App.get_running_app().show_game()
        
    def exit_game(self, instance):
        """خروج من اللعبة"""
        App.get_running_app().stop()

class SnakeApp(App):
    """التطبيق الرئيسي"""
    def build(self):
        # منع الخروج عند الضغط على زر الرجوع
        Window.bind(on_keyboard=self.on_key)
        
        # النافذة الرئيسية
        self.root_layout = BoxLayout(orientation='vertical')
        
        # عرض القائمة الرئيسية أولاً
        self.show_main_menu()
        
        return self.root_layout
        
    def on_key(self, window, key, *args):
        """معالجة أزرار الهاتف ولوحة المفاتيح"""
        if key == 27:  # زر الرجوع
            # إذا كنا في اللعبة، نعود للقائمة الرئيسية
            if hasattr(self, 'game') and self.game in self.root_layout.children:
                self.show_main_menu()
                return True  # منع الخروج
            # إذا كنا في القائمة الرئيسية، نطلب تأكيد الخروج
            else:
                self.confirm_exit()
                return True
        return False
        
    def confirm_exit(self):
        """نافذة تأكيد الخروج"""
        modal = ModalView(size_hint=(0.7, 0.4), background_color=(0, 0, 0, 0.7))
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        title = Label(text='Exit Game?', font_size=30, color=(1, 1, 1, 1))
        btn_layout = BoxLayout(spacing=10)
        
        yes_btn = FancyButton(text='Yes', size_hint_x=0.5)
        yes_btn.bind(on_press=lambda x: self.stop())
        
        no_btn = FancyButton(text='No', size_hint_x=0.5)
        no_btn.bind(on_press=lambda x: modal.dismiss())
        
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        
        layout.add_widget(title)
        layout.add_widget(btn_layout)
        
        modal.add_widget(layout)
        modal.open()
        
    def show_game(self):
        """عرض شاشة اللعبة"""
        self.root_layout.clear_widgets()
        self.game = SnakeGame()
        self.game.size = self.root_layout.size
        self.root_layout.add_widget(self.game)
        
        # جدولة الرسم
        Clock.schedule_interval(lambda dt: self.game.draw(), 1.0/60)
        
    def show_main_menu(self):
        """عرض القائمة الرئيسية"""
        self.root_layout.clear_widgets()
        self.main_menu = MainMenu()
        self.root_layout.add_widget(self.main_menu)

if __name__ == '__main__':
    SnakeApp().run()
