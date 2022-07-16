from pygame import color as pg_color
from pygame import rect as pg_rect
from pygame import font as pg_font
from pygame import transform as pg_transform
from pygame import display as pg_disp
from pygame import init as pg_init
from pygame import mixer as pg_mixer
from pygame import BLEND_RGBA_MULT
from os import path as os_path
from subprocess import run as s_run

from numpy import array

from librosa import frames_to_time
from librosa.onset import onset_backtrack, onset_detect, onset_strength
from librosa import load as l_load
from librosa.beat import tempo as l_tempo

from utils import (
    concatenateAudio,

)
from common import (
    BLANK_AUDIO,
    FONT2,
    GAME_OVER_SOUND,
    LONG_NOTE_MINIMUM_DURATION,
    PAD_Y_POS,
    PAUSE_BACKGROUND, 
    SPEED_MULTIPLIER,
    LARGE_NOTE_SCORE,
    LARGE_NOTE_SPRITE,
    SMALL_NOTE_SCORE,
    SMALL_NOTE_SPRITE,
    RESTART_BTN,
    RESUME_BTN,
    INFO_BTN,
    HELP_BTN,
    WIN_W,
    MENU_TITLE,
    WIN_H,
    MAIN_MENU_BG,
    PAD_SPRITE,
    PAUSE_TEXT,
    EXIT_BTN,
    WHITE_TEXT,
    RESUME_COUNTDOWN_SPRITES,
    PAUSE_BACKGROUND,
    HIT_FX_SPRITE,
    MISS_FX_SPRITE,
    LOW_HP_WARNING_FX,
    FAILED_SCREEN_TITLE,
    BACKGROUND_IMAGE
)

from customTypes import (
    HitState
)

pg_init()
pg_disp.init()

class AudioAnalyzer():
    def __init__(self, fileName: str) -> None:

        self.fileName = fileName
        self.noteStartList = []
        self.smallNotesList = []
    def loadIntoLibrosa(self):
        print("Loading song...")
        # import files
        
        # song name
        self.songName = os_path.basename(self.fileName)
        # convert if not wav
        print("The song's file type is not WAV. Converting...")
        if not self.fileName.endswith(".wav"):
            s_run(args=['./ffmpeg.exe', '-i', self.fileName, "temp.wav"])
            self.fileName = "temp.wav"
        print("Converting finished!")
        # append file:
        concatenateAudio([BLANK_AUDIO, self.fileName])
        self.fileName = "temp2.wav"
        # load into librosa
        self.soundData, self.sampleRate = l_load(self.fileName)
        self.oenv = onset_strength(y=self.soundData, sr=self.sampleRate)

        return self.songName
    def calcBPM(self):
        
        bpm = float(l_tempo(y=self.soundData, sr=self.sampleRate))
        return bpm
    
    def detectNotes(self):

        print("Generating notes...")
        self.noteStartList = onset_detect(y=self.soundData, sr=self.sampleRate, normalize=True, backtrack=True)
        self.noteEndList = onset_backtrack(self.noteStartList, self.oenv)
        
        self.noteStartList: array = frames_to_time(self.noteStartList, sr=self.sampleRate)
        #self.noteStartList: tuple = tuple(map(numberRounding,list(self.noteStartList)))

        self.noteEndList: array = frames_to_time(self.noteEndList, sr=self.sampleRate)
        #self.noteEndList: tuple = tuple(map(numberRounding,list(self.noteEndList)))
        self.noteEndList = tuple(self.noteEndList)
        self.noteStartList = tuple(self.noteStartList)
        return (self.noteStartList)
    
    def detectSmallNotes(self):
        

        bpm = self.calcBPM()
        noteLength = 15/bpm
        smallNotesList= [] 
        for i in range(len(self.noteStartList) - 1):
            noteDuration = self.noteEndList[i + 1] - self.noteStartList[i]
            smallNoteGroup = []
            if noteDuration >= LONG_NOTE_MINIMUM_DURATION:
                t = self.noteStartList[i]
                while t < self.noteEndList[i + 1] - 60 / bpm:
                    t += noteLength
                    smallNoteGroup.append(t)
            smallNotesList.append(smallNoteGroup)
        return smallNotesList


class BaseNote():
    def update(self, bpm, fps):
        
        self.y += PAD_Y_POS / ((1 / SPEED_MULTIPLIER) / bpm) / fps

class LargeNote(BaseNote):
    def __init__(self, x, y):
        
        self.x = x
        self.y = y
        self.image = LARGE_NOTE_SPRITE
        self.rect = pg_rect.Rect(14, 14, 52, 52)
        

class SmallNote(BaseNote):
    def __init__(self, x, y):
        
        self.x = x
        self.y = y
        self.image = SMALL_NOTE_SPRITE
        self.rect = self.image.get_rect()
    
class MainMenu():
    def __init__(self) -> None:
        
        
        # images
        self.playBtn = pg_transform.smoothscale(RESUME_BTN, (200, 200))
        self.aboutBtn = pg_transform.smoothscale(INFO_BTN, (50, 50))
        self.helpBtn = pg_transform.smoothscale(HELP_BTN, (50, 50))

        # positions
        self.titlePos = ((WIN_W - MENU_TITLE.get_width()) / 2, 40)
        self.playBtnPos = ((WIN_W - self.playBtn.get_width()) / 2, 240)
        self.aboutBtnPos = (30, WIN_H - 20 - self.aboutBtn.get_height())
        self.helpBtnPos = (60 + self.aboutBtn.get_width(), WIN_H - 20 - self.helpBtn.get_height())

        # rects
        self.titleRect = MENU_TITLE.get_rect()
        self.playBtnRect = self.playBtn.get_rect()
        self.aboutBtnRect = self.aboutBtn.get_rect()
        self.helpBtnRect = self.helpBtn.get_rect()

        # set rect coords
        self.titleRect.topleft = self.titlePos
        self.playBtnRect.topleft = self.playBtnPos
        self.aboutBtnRect.topleft = self.aboutBtnPos
        self.helpBtnRect.topleft = self.helpBtnPos

    def show(self, window):
        

        window.blit(MAIN_MENU_BG, (0, 0))
        window.blit(self.playBtn, self.playBtnPos)
        window.blit(self.aboutBtn, self.aboutBtnPos)
        window.blit(self.helpBtn, self.helpBtnPos)
        window.blit(MENU_TITLE, self.titlePos)

class Pad():
    def __init__(self, x, y):

        self.x = x
        self.y = y
        self.image = PAD_SPRITE
        self.rect = self.image.get_rect()
    def render(self, window):
        self.rect.topleft = (self.x, self.y)
        window.blit(self.image, (self.x, self.y))

class PauseMenu():
    def __init__(self) -> None:
        self.font = pg_font.Font(FONT2, 28)


        # images 
        self.image = pg_transform.scale(PAUSE_TEXT, (400, 90))
        self.resumeBtn = pg_transform.scale(RESUME_BTN, (128, 128))
        self.restartBtn = pg_transform.scale(RESTART_BTN, (128, 128))
        self.exitBtn = pg_transform.scale(EXIT_BTN, (128, 128))
        
        # texts
        self.resumeBtnText = self.font.render("Resume [ESC]", True, WHITE_TEXT)
        self.restartBtnText = self.font.render("Restart [R]", True , WHITE_TEXT)
        self.exitBtnText = self.font.render("Exit [E]", True, WHITE_TEXT)

        # rects
        self.rect = self.image.get_rect()
        self.resumeBtnRect = self.resumeBtn.get_rect()
        self.restartBtnRect = self.restartBtn.get_rect()
        self.exitBtnRect = self.exitBtn.get_rect()

        # positions
        self.pos = ((WIN_W - self.image.get_width()) / 2, 30)
        self.resumeBtnPos = (((WIN_W / 3) - self.resumeBtn.get_width()) / 2, 300)
        self.restartBtnPos = ((WIN_W / 3) + ((WIN_W / 3) - self.restartBtn.get_width()) / 2, 300)
        self.exitBtnPos = ((WIN_W / 3) * 2 + ((WIN_W / 3) - self.exitBtn.get_width()) / 2, 300)
        self.resumeBtnTextPos = (((WIN_W / 3) - self.resumeBtnText.get_width()) / 2, 500)
        self.restartBtnTextPos = ((WIN_W / 3) + ((WIN_W / 3) - self.restartBtnText.get_width()) / 2, 500)
        self.exitBtnTextPos = ((WIN_W / 3) * 2 + ((WIN_W / 3) - self.exitBtnText.get_width()) / 2, 500)

        # update rects' positions
        self.resumeBtnRect.topleft = self.resumeBtnPos
        self.restartBtnRect.topleft = self.restartBtnPos
        self.exitBtnRect.topleft = self.exitBtnPos

    def show(self, window) -> None:
        window.blit(self.image, self.pos)
        window.blit(self.resumeBtn, self.resumeBtnPos)
        window.blit(self.restartBtn, self.restartBtnPos)
        window.blit(self.exitBtn, self.exitBtnPos)
        window.blit(self.restartBtnText, self.restartBtnTextPos)
        window.blit(self.resumeBtnText, self.resumeBtnTextPos)
        window.blit(self.exitBtnText, self.exitBtnTextPos)


class PauseCountdown():
    def __init__(self) -> None:

        self.font = pg_font.Font(FONT2, 28)
        self.countdownText = self.font.render("Game will start in...", True, WHITE_TEXT)
        self.countdownTextRect = self.countdownText.get_rect()
        self.countdownTextPos = ((WIN_W - self.countdownTextRect.width) / 2, 50)
        self.i = 0
    def countdown(self, window) -> None:

        self.image = RESUME_COUNTDOWN_SPRITES[int(self.i / 40)]
        self.rect = self.image.get_rect()
        self.x = int((WIN_W - self.rect.width) / 2)
        self.y = 90
        window.blit(PAUSE_BACKGROUND, (0, 0))
        window.blit(self.countdownText, self.countdownTextPos)
        window.blit(self.image, (self.x, self.y))
            
class Effect():
    def __init__(self, window, x, y, t, padX = None) -> None:
        self.img = 0
        self.alpha = 255
        self.t = t
        self.x = x
        self.y = y
        self.padX = padX
    def update(self):

        if self.alpha > 0:
            
            if self.t == HitState.Hit:
                self.img = HIT_FX_SPRITE
            elif self.t == HitState.Miss:
                self.img = MISS_FX_SPRITE
            self.img = self.img.convert_alpha()
            self.img.fill((255, 255, 255, self.alpha), None, BLEND_RGBA_MULT)
            self.alpha -= 20


class LowHPWarning():
    def __init__(self) -> None:

        self.image = LOW_HP_WARNING_FX
        self.alpha = 255
        self.glowing = True
        self.hidden = False
    def update(self):
        if self.hidden:
            self.alpha = 255
            self.hidden = False

        if self.alpha >= 255:           
            self.glowing = False
        elif self.alpha <= 150:
            self.glowing = True
        
        if self.glowing:
            self.alpha += 18
        elif not self.glowing:
            self.alpha -= 18
    def hide(self):
        self.alpha = 0
        self.hidden = True
        
    def render(self, window):
        self.i = self.image.copy()
        self.i.fill((255, 255, 255, self.alpha), None, BLEND_RGBA_MULT)
        window.blit(self.i, (0, 0))

class ScoreDisp():
    def __init__(self, t) -> None:
        self.alpha = 255
        self.t = t

    def show(self):

        if self.alpha > 0:
            if self.t == "SmallNote":
                self.img = SMALL_NOTE_SCORE
            elif self.t == "LargeNote":
                self.img = LARGE_NOTE_SCORE
            self.rect = self.img.get_rect()
            self.img = self.img.convert_alpha()
            self.img.fill((255, 255, 255, self.alpha), None, BLEND_RGBA_MULT)
            self.alpha -= 20

class FailedScreen():
    def __init__(self) -> None:
        # fonts
        font = pg_font.Font(FONT2, 28)

        # buttons
        self.retryBtn = pg_transform.smoothscale(RESTART_BTN, (200, 200))
        self.exitBtn = pg_transform.smoothscale(EXIT_BTN, (200, 200))

        # texts
        self.retryTxt = font.render("Retry", True, WHITE_TEXT)
        self.exitTxt = font.render("Exit", True, WHITE_TEXT)

        # rects
        self.retryBtnRect = self.retryBtn.get_rect()
        self.exitBtnRect = self.exitBtn.get_rect()

        # positions
        self.retryBtnPos = ((WIN_W / 2 - self.retryBtn.get_width()) / 2, 230)
        self.exitBtnPos = ((WIN_W / 2) + (WIN_W /2 - self.exitBtn.get_width()) / 2, 230)
        self.titlePos = ((WIN_W - FAILED_SCREEN_TITLE.get_width()) / 2, 30)

        self.retryTxtPos = ((WIN_W / 2 - self.retryTxt.get_width()) / 2, self.retryBtn.get_height() + 260)
        self.exitTxtPos = ((WIN_W / 2) + (WIN_W / 2 - self.exitTxt.get_width()) / 2, self.exitBtn.get_height() + 260)
        # update rect pos
        self.retryBtnRect.topleft = self.retryBtnPos
        self.exitBtnRect.topleft = self.exitBtnPos

        # audio
        self.sound = pg_mixer.Sound(GAME_OVER_SOUND)

        # is audio played?
        self.audioPlayed = False
    def show(self, window):
        window.blit(BACKGROUND_IMAGE, (0, 0))
        window.blit(PAUSE_BACKGROUND, (0, 0))
        window.blit(FAILED_SCREEN_TITLE, self.titlePos)
        window.blit(self.retryBtn, self.retryBtnPos)
        window.blit(self.exitBtn, self.exitBtnPos)
        window.blit(self.exitTxt, self.exitTxtPos)
        window.blit(self.retryTxt, self.retryTxtPos)

    def playAudio(self):
        if not self.audioPlayed:
            self.sound.play(loops=0)
            self.audioPlayed = True
    