from ctypes import c_long
from ctypes import py_object
from ctypes import pythonapi
from inspect import isclass
import os
import re
from time import sleep
from io import BytesIO
from threading import Thread

import pygame.mixer
import wx
import wx.lib.buttons as buttons
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from PIL import Image


class main_frame(wx.Frame):
    def __init__(self):
        """
        构造
        """
        pygame.mixer.init()
        self.music = pygame.mixer.music
        self.current_song = 0
        self.current_time = 0
        self.current_idx = 0
        self.volume = 1.0

        if not os.path.exists('./Music'):
            os.makedirs('./Music')
        if not os.path.exists('./Album'):
            os.makedirs('./Album')
        if not os.path.exists('./Lyrics'):
            os.makedirs('./Lyrics')

        self.music_folder = './Music/'
        self.album_folder = './Album/'
        self.lyrics_folder = './Lyrics/'
        self.music_files = []
        self.music_title_list = []
        self.artist_list = []
        self.album_list = []
        self.length_list = []

        wx.Frame.__init__(self, None, wx.ID_ANY, 'YAMP _by Wenti-D_', size=(1200, 800), style=wx.DEFAULT_FRAME_STYLE ^ (wx.MAXIMIZE_BOX | wx.RESIZE_BORDER))
        self.SetBackgroundColour((255, 255, 255))
        self.Bind(wx.EVT_CLOSE, self.exiting)
        self.Center(wx.BOTH)
        self.icon = wx.Icon('./assets/icon.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.draw_list_title_panel()
        self.draw_list_panal()
        self.draw_current_title()
        self.draw_line()
        self.draw_album_cover()
        self.draw_current_song_info()
        self.draw_lyrics_panel()
        self.draw_control_panel()

    def draw_list_title_panel(self):
        """
        左侧标题
        """
        self.list_title_panel = wx.Panel(self, pos=(0, 0), size=(380, 60))
        self.list_title_panel.SetBackgroundColour((233, 233, 233))

        self.list_title_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.list_title_font.SetPointSize(15)

        self.title_text = wx.StaticText(self.list_title_panel, wx.ID_ANY, "本地音乐", pos=(20, 20))

        self.title_text.SetOwnForegroundColour((0, 0, 0))
        self.title_text.SetOwnFont(self.list_title_font)
    
    def time_formatting(self, time):
        """
        格式化时间显示
        """
        if time % 60 < 10:
            the_length = str(int(time) // 60) + ":0" + str(int(time) % 60)
        else:
            the_length = str(int(time) // 60) + ":" + str(int(time) % 60)
        return the_length

    def draw_list_panal(self):
        """
        左侧列表
        """
        self.get_local_music()

        self.music_num = len(self.music_files)
        
        self.list_panel = wx.Panel(self, pos=(0, 60), size=(380, 701))
        self.list_panel.SetBackgroundColour((233, 233, 233))

        self.list_scroll = wx.ScrolledWindow(self.list_panel, wx.ID_ANY, pos=(0, 0), size=(381, 700))
        self.list_scroll.SetScrollbars(0, 8, 380, self.music_num * 5)

        self.in_the_list = 0
        if self.music_num == 0:
            no_song_text = wx.StaticText(self.list_panel, wx.ID_ANY, '这里什么也没有……', pos=(130, 300))
        
        for music_idx in range(self.music_num):
            self.music_panel = wx.Panel(self.list_scroll, 8 * music_idx + 1, pos=(0, music_idx * 40), size=(380, 40))
            self.music_panel.SetBackgroundColour((233, 233, 233))
            self.music_title_panel = wx.Panel(self.music_panel, 8 * music_idx + 2, pos=(30, 12), size=(160, 20))
            self.music_artist_panel = wx.Panel(self.music_panel, 8 * music_idx + 3, pos=(210, 12), size=(87, 20))
            self.music_length_panel = wx.Panel(self.music_panel, 8 * music_idx + 4, pos=(300, 12), size=(50, 20))
            self.music_title_panel.SetDoubleBuffered(True)
            self.music_artist_panel.SetDoubleBuffered(True)
            self.music_length_panel.SetDoubleBuffered(True)

            the_length = self.time_formatting(self.length_list[music_idx])

            self.music_title_text = wx.StaticText(self.music_title_panel, 8 * music_idx + 5, self.music_title_list[music_idx], pos=(0, 0), size=(250, 20))
            self.music_artist_text = wx.StaticText(self.music_artist_panel, 8 * music_idx + 6, self.artist_list[music_idx], pos=(0, 0), size=(100, 20))
            self.music_length_text = wx.StaticText(self.music_length_panel, 8 * music_idx + 7, the_length, pos=(0, 0), size=(50, 20), style=wx.ALIGN_RIGHT)

            wx.FindWindowById(8 * music_idx + 1).Bind(wx.EVT_ENTER_WINDOW, lambda evt="a", i=8 * music_idx + 1: self.enter_music_list('a', i))
            for j in range(2,8):
                wx.FindWindowById(8 * music_idx + j).Bind(wx.EVT_ENTER_WINDOW, self.inner_music_list)
                wx.FindWindowById(8 * music_idx + j).Bind(wx.EVT_LEAVE_WINDOW, self.outer_music_list)
            wx.FindWindowById(8 * music_idx + 1).Bind(wx.EVT_LEAVE_WINDOW, lambda evt="a", i=8 * music_idx + 1: self.leave_music_list('a', i))
            for j in range(1, 8):
                wx.FindWindowById(8 * music_idx + j).Bind(wx.EVT_LEFT_DCLICK, lambda evt="a", i=music_idx: self.play_song('a',i))

    def enter_music_list(self, evt, i):
        wx.FindWindowById(i).SetBackgroundColour((255, 255, 255))
        self.list_panel.Refresh()
    
    def inner_music_list(self, evt):
        self.in_the_list = 1

    def outer_music_list(self, evt):
        self.in_the_list = 0

    def leave_music_list(self, evt, i):
        if self.in_the_list == 0:
            wx.FindWindowById(i).SetBackgroundColour((233, 233, 233))
        self.list_panel.Refresh()

    def draw_line(self):
        """
        嗯……画线
        """
        self.line_panel_l = wx.Panel(self.list_title_panel, pos=(20, 59), size=(333, 1))
        self.line_panel_l.SetOwnBackgroundColour((136, 136, 136))
        self.line_panel_r = wx.Panel(self, pos=(410, 70), size=(695, 2))
        self.line_panel_r.SetOwnBackgroundColour((40, 170, 255))
    
    def draw_current_title(self):
        """
        右侧标题
        """
        self.current_title_panel = wx.Panel(self, pos=(380, 0), size=(820, 70))

        self.play_now_text = wx.StaticText(self.current_title_panel, wx.ID_ANY, "正在播放", pos=(40, 15))
        try:
            self.play_now_font = wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT, False, "微软雅黑 Light")
        except:
            self.play_now_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            self.play_now_font.SetPointSize(24)
            self.play_now_font.SetWeight(wx.FONTWEIGHT_LIGHT)

        self.play_now_text.SetOwnForegroundColour((0, 0, 0))
        self.play_now_text.SetOwnFont(self.play_now_font)

    def draw_album_cover(self):
        """
        专辑封面显示
        """
        self.album_cover_panal = wx.Panel(self, pos=(400, 72), size=(250, 238))
        self.album_cover = wx.StaticBitmap(self.album_cover_panal, wx.ID_ANY, wx.Bitmap('./assets/default_album.png', wx.BITMAP_TYPE_ANY), pos=(45, 35))

    def draw_current_song_info(self):
        """
        当前歌曲信息显示
        """
        self.current_song_info_panel = wx.Panel(self, pos=(650, 72), size=(430, 238))

        self.current_song_title_text = wx.StaticText(self.current_song_info_panel, wx.ID_ANY, "不放点歌吗", pos=(50, 85))
        self.current_song_artist_text = wx.StaticText(self.current_song_info_panel, wx.ID_ANY, "真的不放点歌吗", pos=(50, 135))
        self.current_song_album_text = wx.StaticText(self.current_song_info_panel, wx.ID_ANY, "确定不放点歌吗", pos=(50, 163))

        self.song_title_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.song_title_font.SetPointSize(15)
        self.song_title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.song_other_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.song_other_font.SetPointSize(11)
        
        self.current_song_title_text.SetOwnFont(self.song_title_font)
        self.current_song_artist_text.SetOwnFont(self.song_other_font)
        self.current_song_album_text.SetOwnFont(self.song_other_font)

        self.current_song_artist_text.SetOwnForegroundColour((90, 90, 90))
        self.current_song_album_text.SetOwnForegroundColour((90, 90, 90))

    def draw_lyrics_panel(self):
        """
        歌词面板
        """
        self.lyrics_panel = wx.Panel(self, pos=(410, 320), size=(700, 350))

        for i in range(5):
            self.line_panel = wx.Panel(self.lyrics_panel, id=8 * i + 8, pos=(0, 70 * i), size=(700, 70))
            self.line_panel.SetDoubleBuffered(True)
        
        self.line1_text_up = wx.StaticText(wx.FindWindowById(8), 48, "", pos=(0, 10), size=(700, 19), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line1_text_down = wx.StaticText(wx.FindWindowById(8), 56, "", pos=(0, 29), size=(700, 15), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line2_text_up = wx.StaticText(wx.FindWindowById(16), 64, "", pos=(0, 10), size=(700, 19), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line2_text_down = wx.StaticText(wx.FindWindowById(16), 72, "", pos=(0, 29), size=(700, 15), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line3_text_up = wx.StaticText(wx.FindWindowById(24), 80, "", pos=(0, 10), size=(700, 22), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line3_text_down = wx.StaticText(wx.FindWindowById(24), 88, "", pos=(0, 32), size=(700, 15), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line4_text_up = wx.StaticText(wx.FindWindowById(32), 96, "", pos=(0, 10), size=(700, 19), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line4_text_down = wx.StaticText(wx.FindWindowById(32), 104, "", pos=(0, 29), size=(700, 15), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line5_text_up = wx.StaticText(wx.FindWindowById(40), 112, "", pos=(0, 10), size=(700, 19), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.line5_text_down = wx.StaticText(wx.FindWindowById(40), 120, "", pos=(0, 29), size=(700, 15), style=wx.ALIGN_CENTER_HORIZONTAL)

        self.up_font_center = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.up_font_center.SetPointSize(12)
        self.up_font_center.SetWeight(wx.FONTWEIGHT_BOLD)
        self.down_font_center = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.down_font_center.SetPointSize(11)
        self.down_font_center.SetWeight(wx.FONTWEIGHT_BOLD)
        self.up_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.up_font.SetPointSize(10)
        self.down_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.down_font.SetPointSize(9)

        for i in (1,2,4,5):
            wx.FindWindowById(8 * (4 + 2 * i)).SetOwnForegroundColour((135, 135, 135))
            wx.FindWindowById(8 * (4 + 2 * i)).SetOwnFont(self.up_font)
            wx.FindWindowById(8 * (5 + 2 * i)).SetOwnForegroundColour((135, 135, 135))
            wx.FindWindowById(8 * (5 + 2 * i)).SetOwnFont(self.down_font)

        self.line3_text_up.SetOwnFont(self.up_font_center)
        self.line3_text_down.SetOwnFont(self.down_font_center)

    def lyrics_parsing(self):
        """
        歌词处理
        """
        self.current_lyrics_lines = []
        self.offset = 0.0
        if self.music_files[self.current_idx].endswith(".mp3"):
            lyrics_file_name = self.lyrics_folder + self.music_files[self.current_idx][:-4] + ".lrc"
        if self.music_files[self.current_idx].endswith(".flac"):
            lyrics_file_name = self.lyrics_folder + self.music_files[self.current_idx][:-5] + ".lrc"
        try:
            with open(lyrics_file_name, "r", encoding="utf-8") as lyrics_file:
                for lines in lyrics_file.readlines():
                    if re.match(r'\[offset', lines):
                        if re.search(r'[+-]?[0-9]+', lines):
                            self.offset = float(re.search(r'[+-]?[0-9]+', lines).group()) / 1000
                        else:
                            self.offset = 0.0
                    if re.match(r'\[[0-9]{2}:[0-9]{2}.[0-9]{2}\]', lines) != None:
                        time = float(lines[1:3]) * 60 + float(lines[4:6]) + float(lines[7:9]) / 100
                        content = lines[10:].strip()
                        self.current_lyrics_lines.append([time, content])
        except:
            self.current_lyrics_lines.append([0.0, '暂无歌词或纯音乐'])
        if self.current_lyrics_lines[0][0] != 0.0:
            self.current_lyrics_lines.insert(0, [0.0, ''])

    def lyrics_display(self):
        """
        歌词显示
        """
        idx = 0
        content = 5 * ['']
        org = 5 * ['']
        trans = 5 * ['']
        double_line = 5 * [0]
        while self.music.get_busy() or self.current_time != 0:
            self.current_time = self.music.get_pos()
            the_current_time = self.current_time / 1000
            the_time = self.current_lyrics_lines[idx][0]
            if idx == 0:
                content[0] = content[1] = ''
                content[2] = self.current_lyrics_lines[idx][1]
                try:
                    content[3] = self.current_lyrics_lines[idx + 1][1]
                    content[4] = self.current_lyrics_lines[idx + 2][1]
                except:
                    content[3] = content[4] = ''
            elif idx == 1:
                content[0] = ''
                for i in range(1,5):
                    content[i] = self.current_lyrics_lines[idx + i - 2][1]
            else:
                for i in range(5):
                    try:
                        content[i] = self.current_lyrics_lines[idx + i - 2][1]
                    except:
                        content[i] =''
            for i in range(5):
                if content[i].find(' // ') != -1:
                    org[i] = content[i].split(' // ')[0]
                    trans[i] = content[i].split(' // ')[1]
                    double_line[i] = 1
                else:
                    double_line[i] = 0
            if the_time - the_current_time - self.offset <= .006:
                for i in range(5):
                    if double_line[i]:
                        wx.FindWindowById(16 * (i + 3)).SetLabelText(org[i])
                        wx.FindWindowById(16 * (i + 3) + 8).SetLabelText(trans[i])
                    else:
                        wx.FindWindowById(16 * (i + 3)).SetLabelText(content[i])
                        wx.FindWindowById(16 * (i + 3) + 8).SetLabelText('')
                self.lyrics_panel.Refresh()
                if content[2] == '暂无歌词或纯音乐' or idx == len(self.current_lyrics_lines) - 1:
                    break
                else:
                    idx += 1
            sleep(.002)

    def get_local_music(self):
        """
        获取 ./Music/ 目录下的音乐信息
        """
        self.music_files.clear()
        self.music_title_list.clear()
        self.artist_list.clear()
        self.length_list.clear()

        for files in os.listdir(self.music_folder):
            if files.endswith('.mp3') or files.endswith('.flac'):
                self.music_files.append(files)
        for files in self.music_files:
            if files.endswith('.mp3'):
                song = MP3(self.music_folder + files)
                try:
                    title = song.tags["TIT2"].text[0]
                except:
                    self.music_title_list.append(files[:-4])
                else:
                    self.music_title_list.append(title)
                try:
                    artist = song.tags["TPE1"].text[0]
                except:
                    self.artist_list.append('未知艺术家')
                else:
                    self.artist_list.append(artist)
                try:
                    album = song.tags["TALB"].text[0]
                except:
                    self.album_list.append('未知专辑')
                else:
                    self.album_list.append(album)
                length = song.info.length
                self.length_list.append(length)
                self.collect_cover_mp3(files)
                self.collect_lyrics_mp3(files)
            if files.endswith('.flac'):
                song = FLAC(self.music_folder + files)
                try:
                    title = song.tags['TITLE'][0]
                except:
                    self.music_title_list.append(files[:-5])
                else:
                    self.music_title_list.append(title)
                try:
                    artist = song.tags['ARTIST'][0]
                except:
                    self.artist_list.append('未知艺术家')
                else:
                    self.artist_list.append(artist)
                try:
                    album = song.tags['ALBUM'][0]
                except:
                    self.album_list.append('未知专辑')
                else:
                    self.album_list.append(album)
                length = song.info.length
                self.length_list.append(length)
                self.collect_cover_flac(files)
                self.collect_lyrics_flac(files)

    def collect_cover_mp3(self, filename):
        """
        获取MP3内嵌专辑封面并保存缩略图于 ./Album/
        """
        song = MP3(self.music_folder + filename)
        try:
            album = song.tags["TALB"].text[0]
            if not (os.path.exists(self.music_folder + album + '.png') or album == None):
                picture = song.tags.get("APIC:").data
                album_pict = Image.open(BytesIO(picture))
                album_pict.thumbnail((200, 200), resample=Image.BICUBIC)
                album_pict.save(self.album_folder + album.replace('/','-') + '.png', 'png')
        except:
            pass
    
    def collect_cover_flac(self, filename):
        """
        获取FLAC内嵌专辑封面并保存缩略图于 ./Album/
        """
        song = FLAC(self.music_folder + filename)
        try:
            album = song.tags['ALBUM'][0]
            if not os.path.exists(self.music_folder + album + '.png'):
                picture = song.pictures[0].data
                album_pict = Image.open(BytesIO(picture))
                album_pict.thumbnail((200, 200), resample=Image.BICUBIC)
                album_pict.save(self.album_folder + album.replace('/','-') + '.png', 'png')
        except:
            pass

    def collect_lyrics_mp3(self, filename):
        """
        获取 mp3 文件内嵌歌词并保存至 ./Lyrics/
        """
        try:
            song = MP3(self.music_folder + filename)
            lyrics = song.tags.get("USLT::XXX")
            if not (lyrics == None or os.path.exists(self.lyrics_folder + filename[:-4] + '.lrc')):
                file = open(self.lyrics_folder + filename[:-4] + '.lrc', "w", encoding='utf-8', newline="")
                file.writelines(str(lyrics))
                file.close()
        except:
            pass

    def collect_lyrics_flac(self, filename):
        """
        获取 flac 文件内嵌歌词并保存至 ./Lyrics/
        """
        song = FLAC(self.music_folder + filename)
        try:
            lyrics = song.tags["LYRICS"][0]
            if not os.path.exists(self.lyrics_folder + filename[:-5] + '.lrc'):
                file = open(self.lyrics_folder + filename[:-5] + ".lrc", "w", encoding="utf-8", newline="")
                file.writelines(str(lyrics))
                file.close()
        except:
            pass

    def draw_control_panel(self):
        """
        控制器面板
        """
        self.control_panel = wx.Panel(self, pos=(410, 680), size=(700, 81))

        self.time_text_l = wx.StaticText(self.control_panel, wx.ID_ANY, '-', pos=(79,10), size=(40,-1), style=wx.ALIGN_RIGHT)
        self.time_text_slash = wx.StaticText(self.control_panel, wx.ID_ANY, '/', pos=(120,10), size=(6,-1))
        self.time_text_r = wx.StaticText(self.control_panel, wx.ID_ANY, '-', pos=(126,10), size=(40,-1))
        self.play_pause_button = buttons.GenBitmapButton(self.control_panel, wx.ID_ANY, wx.Bitmap("./assets/play.png", wx.BITMAP_TYPE_ANY), pos=(330, 0), size=(40, 40))
        self.previous_button = buttons.GenBitmapButton(self.control_panel, wx.ID_ANY, wx.Bitmap("./assets/previous.png", wx.BITMAP_TYPE_ANY), pos=(280, 5), size=(30, 30))
        self.next_button = buttons.GenBitmapButton(self.control_panel, wx.ID_ANY, wx.Bitmap("./assets/next.png", wx.BITMAP_TYPE_ANY), pos=(390, 5), size=(30, 30))
        self.circle_button = buttons.GenBitmapToggleButton(self.control_panel, wx.ID_ANY, wx.Bitmap("./assets/circle.png", wx.BITMAP_TYPE_ANY), pos=(230, 5), size=(31, 31))
        self.circle_button.SetBitmapSelected(wx.Bitmap("./assets/circle_pressed.png", wx.BITMAP_TYPE_ANY))
        self.volume_bitmap = wx.StaticBitmap(self.control_panel, wx.ID_ANY, wx.Bitmap('./assets/volume.png', wx.BITMAP_TYPE_ANY), pos=(515,7))
        self.volume_slider = wx.Slider(self.control_panel, wx.ID_ANY, 100, 0, 100, pos=(540,7), size=(150,-1), style=wx.SL_BOTH|wx.SL_HORIZONTAL)

        self.play_pause_button.SetBezelWidth(0)
        self.previous_button.SetBezelWidth(0)
        self.next_button.SetBezelWidth(0)
        self.circle_button.SetBezelWidth(0)

        self.play_pause_button.Bind(wx.EVT_BUTTON, self.play_pause)
        self.previous_button.Bind(wx.EVT_BUTTON, self.previous_song)
        self.next_button.Bind(wx.EVT_BUTTON, self.next_song)
        self.volume_slider.Bind(wx.EVT_SLIDER, self.change_volume)

    def play_song(self, evt, i):
        """
        播放指定索引的音乐
        """
        if self.music_num == 0:
            return ""
        self.current_song = 1
        self.current_idx = i
        try:
            stop_thread(self.lyric_display_thread)
        except:
            pass
        try:
            stop_thread(self.list_circle_thread)
        except:
            pass
        self.play_pause_button.SetBitmapLabel(wx.Bitmap("./assets/pause.png", wx.BITMAP_TYPE_ANY))
        self.music.load(self.music_folder + self.music_files[i])
        self.music.play(loops=1, start=0.0)
        self.lyrics_parsing()

        self.current_song_title_text.SetLabelText(self.music_title_list[i])
        self.current_song_artist_text.SetLabelText(self.artist_list[i])
        self.current_song_album_text.SetLabelText(self.album_list[i])
        if self.album_list[i] == '未知专辑':
            self.album_cover.SetBitmap(wx.Bitmap('./assets/default_album.png', wx.BITMAP_TYPE_ANY))
        else:
            self.album_cover.SetBitmap(wx.Bitmap(self.album_folder + self.album_list[i].replace('/','-') + '.png', wx.BITMAP_TYPE_ANY))
        self.time_text_r.SetLabelText(self.time_formatting(self.length_list[i]))

        for j in range(self.music_num):
            for k in (5, 6, 7):
                wx.FindWindowById(8 * j + k).SetOwnForegroundColour((0, 0, 0))
        for k in (5, 6, 7):
            wx.FindWindowById(8 * i + k).SetOwnForegroundColour((40, 170, 255))
        self.Refresh()

        self.lyric_display_thread = Thread(target=self.lyrics_display)
        self.lyric_display_thread.start()
        self.list_circle_thread = Thread(target=self.list_circle)
        self.list_circle_thread.start()

    def play_pause(self, evt):
        """
        播放/暂停按钮
        """
        if self.music.get_busy() or self.current_time != 0:
            if self.current_song:
                self.music.pause()
                self.current_song = 0
                self.play_pause_button.SetBitmapLabel(wx.Bitmap("./assets/play.png", wx.BITMAP_TYPE_ANY))
            else:
                self.music.unpause()
                self.current_song = 1
                self.play_pause_button.SetBitmapLabel(wx.Bitmap("./assets/pause.png", wx.BITMAP_TYPE_ANY))
        else:
            self.play_song('a', 0)

    def previous_song(self, evt):
        """
        上一首
        """
        try:
            stop_thread(self.lyric_display_thread)
        except:
            pass
        try:
            stop_thread(self.list_circle_thread)
        except:
            pass
        if self.current_idx == 0:
            self.play_song('a', len(self.music_title_list) - 1)
        else:
            self.play_song('a', self.current_idx - 1)

    def next_song(self, evt):
        """
        下一首
        """
        try:
            stop_thread(self.lyric_display_thread)
        except:
            pass
        try:
            stop_thread(self.list_circle_thread)
        except:
            pass
        if self.current_idx == len(self.music_title_list) - 1:
            self.play_song('a', 0)
        else:
            self.play_song('a', self.current_idx + 1)

    def list_circle(self):
        """
        列表循环播放
        """
        while self.music.get_busy() or self.current_time != 0:
            current_time = self.music.get_pos() / 1000
            self.time_text_l.SetLabelText(self.time_formatting(current_time))
            sleep(.2)
            if current_time > (self.length_list[self.current_idx] - .4): break
        if self.circle_button.GetValue():
            self.next_song('a')
        else:
            self.play_pause_button.SetBitmapLabel(wx.Bitmap("./assets/play.png", wx.BITMAP_TYPE_ANY))
            self.control_panel.Refresh()
        self.time_text_l.SetLabelText(self.time_formatting(0))

    def change_volume(self, evt):
        """
        音量调节
        """
        widget = evt.GetEventObject()
        value = widget.GetValue()
        self.volume = float(value / 100)
        self.music.set_volume(self.volume)

    def exiting(self, evt):
        """
        退出时的操作
        """
        try:
            stop_thread(self.lyric_display_thread)
        except:
            pass
        try:
            stop_thread(self.list_circle_thread)
        except:
            pass
        self.Destroy()


'''
下面这俩是用来结束线程的
来自 https://blog.csdn.net/smallsmallmouse/article/details/89155529
要不然线程会越来越多无法停止
'''

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = c_long(tid)
    if not isclass(exctype):
        exctype = type(exctype)
    res = pythonapi.PyThreadState_SetAsyncExc(tid, py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


if __name__ == "__main__":
    app = wx.App()
    frame = main_frame()
    frame.Show()
    app.MainLoop()
