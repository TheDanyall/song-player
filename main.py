from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.text import Label as CoreLabel
from kivy.core.text import LabelBase
import pygame
import os
from mutagen.mp3 import MP3


class SimpleImageButton(ButtonBehavior, Image):
    def __init__(self, show_circle=True, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (dp(60), dp(60)))
        kwargs.setdefault('allow_stretch', True)
        kwargs.setdefault('color', (1, 1, 1, 0.9))
        super().__init__(**kwargs)
        
        self.show_circle = show_circle
        if show_circle:
            with self.canvas.before:
                Color(1, 1, 1, 0.2)
                self.circle_bg = RoundedRectangle(
                    size=(self.width+dp(20), self.height+dp(20)), 
                    pos=(self.x-dp(10), self.y-dp(10)), 
                    radius=[(self.width+dp(20))/2]
                )
        self.bind(pos=self.update_circle_pos, size=self.update_circle_pos)
    
    def update_circle_pos(self, *args):
        if hasattr(self, 'circle_bg'):
            self.circle_bg.pos = (self.x-dp(10), self.y-dp(10))
            self.circle_bg.size = (self.width+dp(20), self.height+dp(20))

class BackgroundImage(BoxLayout):
    def __init__(self, source, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.rect = Rectangle(source=source, size=Window.size)
        self.bind(size=self._update_rect)
        Window.bind(size=self._update_rect)
    
    def _update_rect(self, *args): 
        self.rect.size = Window.size

class MyMusicPlayer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        pygame.init()
        pygame.mixer.init()
        
        self.song_list = ["music1.mp3", "music2.mp3"]
        self.current_song_number = 0
        self.user_is_dragging = False
        self.is_playing_now = False
        self.song_duration = 0
        self.last_position = 0
        
        self.add_widget(BackgroundImage(source='background.jpg'))
        
        main_content = BoxLayout(orientation="vertical")
        buttons_panel = BoxLayout(orientation='vertical', size_hint=(1, 1), 
                                padding=dp(30), spacing=dp(20))
        
        # لیبل نام آهنگ با فونت بولد و رنگ آبی
        self.song_name_label = Label(
            text="No Song Selected",
            font_size=dp(18),
            color=(0, 0.7, 1, 1),  # آبی روشن
            bold=True,  # فونت بولد
            # font_name='BoldFont',  # اگر فونت اختصاصی ثبت کردید
            size_hint=(1, None),
            height=dp(30)
        )
        self.song_progress = Slider(min=0, max=100, value=0, size_hint=(1, None), 
                                  height=dp(8), value_track_color=[1, 1, 1, 0.8],
                                  value_track=True, cursor_size=[dp(20), dp(20)])
        
        time_labels = BoxLayout(size_hint=(1, None), height=dp(20))
        
        # لیبل زمان جاری با فونت بولد و رنگ آبی
        self.current_position_label = Label(
            text="0:00",
            font_size=dp(14),  # کمی بزرگتر
            color=(0, 0.7, 1, 1),  # آبی روشن
            bold=True,  # فونت بولد
            # font_name='BoldFont'  # اگر فونت اختصاصی ثبت کردید
        )
        
        # لیبل زمان کل با فونت بولد و رنگ آبی
        self.total_time_label = Label(
            text="0:00",
            font_size=dp(14),  # کمی بزرگتر
            color=(0, 0.7, 1, 1),  # آبی روشن
            bold=True,  # فونت بولد
            # font_name='BoldFont',  # اگر فونت اختصاصی ثبت کردید
            halign='right'
        )
        
        time_labels.add_widget(self.current_position_label)
        time_labels.add_widget(self.total_time_label)
        
        main_buttons = BoxLayout(size_hint=(1, None), height=dp(80), spacing=dp(40),
                               padding=[dp(60), 0, dp(60), 0])
        
        self.play_button = SimpleImageButton(source='play.png', on_press=self.play_or_pause, size=(dp(80), dp(80)))
        prev_button = SimpleImageButton(source='previous.png', on_press=self.previous_song, 
                                      size=(dp(20), dp(20)), show_circle=False)
        next_button = SimpleImageButton(source='next.png', on_press=self.next_song, 
                                      size=(dp(20), dp(20)), show_circle=False)
        
        for btn in [prev_button, self.play_button, next_button]:
            btn.size_hint_x = 0.5 if btn != self.play_button else 1
            main_buttons.add_widget(btn)
        
        for widget in [self.song_name_label, self.song_progress, time_labels, main_buttons]:
            buttons_panel.add_widget(widget)
        
        main_content.add_widget(buttons_panel)
        self.add_widget(main_content)
        
        self.song_progress.bind(
            on_touch_down=self.slider_pressed,
            on_touch_move=self.slider_moved,
            on_touch_up=self.slider_released
        )
        Clock.schedule_interval(self.update_song_position, 0.1)
    
    def slider_pressed(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.user_is_dragging = True
            self.last_position = instance.value
    
    def slider_moved(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.user_is_dragging:
            self.current_position_label.text = self.time_format(instance.value)
            self.last_position = instance.value
    
    def slider_released(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.user_is_dragging:
            self.go_to_position(self.last_position)
            self.user_is_dragging = False
    
    def go_to_position(self, position):
        try:
            pygame.mixer.music.set_pos(position)
        except:
            was_playing = self.is_playing_now
            pygame.mixer.music.stop()
            pygame.mixer.music.play(start=position)
            if not was_playing: 
                pygame.mixer.music.pause()
        
        self.song_progress.value = position
        self.current_position_label.text = self.time_format(position)
    
    def time_format(self, seconds): 
        return f"{int(seconds//60)}:{int(seconds%60):02d}"
    
    def play_or_pause(self, instance):
        if self.is_playing_now: 
            self.pause_song()
        else: 
            self.play_song()
    
    def play_song(self):
        if not self.song_list: 
            return
        try:
            pygame.mixer.music.load(self.song_list[self.current_song_number])
            pygame.mixer.music.play()
            self.play_button.source = 'pause.png'
            self.is_playing_now = True
            self.show_song_info()
            self.song_duration = self.get_duration()
            self.song_progress.max = self.song_duration
            self.total_time_label.text = self.time_format(self.song_duration)
            self.song_progress.value = 0
        except Exception as e: 
            print(f"Error: {e}")
    
    def pause_song(self):
        pygame.mixer.music.pause()
        self.play_button.source = 'play.png'
        self.is_playing_now = False
    
    def next_song(self, instance):
        self.current_song_number = (self.current_song_number + 1) % len(self.song_list)
        if self.is_playing_now:
            self.play_song()
        else:
            self.show_song_info()
    
    def previous_song(self, instance):
        self.current_song_number = (self.current_song_number - 1) % len(self.song_list)
        if self.is_playing_now:
            self.play_song()
        else:
            self.show_song_info()
    
    def update_song_position(self, dt):
        if not self.user_is_dragging and self.is_playing_now:
            current_time = pygame.mixer.music.get_pos() / 1000
            if current_time <= self.song_duration:
                self.song_progress.value = current_time
                self.current_position_label.text = self.time_format(current_time)
            if current_time >= self.song_duration - 0.1: 
                self.next_song(None)
    
    def get_duration(self):
        try: 
            return MP3(self.song_list[self.current_song_number]).info.length
        except Exception as e: 
            print("Error:", e)
            return 100
    
    def show_song_info(self):
        if not self.song_list: 
            return
        name = os.path.splitext(self.song_list[self.current_song_number])[0]
        self.song_name_label.text = name
        self.song_duration = self.get_duration()
        self.song_progress.max = self.song_duration
        self.total_time_label.text = self.time_format(self.song_duration)
        self.song_progress.value = 0
        self.current_position_label.text = "0:00"

class MusicPlayerApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Window.size = (360, 640)
        return MyMusicPlayer()

if __name__ == "__main__":
    MusicPlayerApp().run()