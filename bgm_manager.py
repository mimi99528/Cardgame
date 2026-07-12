"""
BGM管理系统
提供背景音乐的加载、播放、切换和循环功能
使用 streaming 模式加载MP3以节省内存，手动循环因为streaming不支持loop参数
"""
import arcade
from pathlib import Path


class BgmManager:
    """BGM管理器（单例模式）- 管理所有背景音乐的播放和切换"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._sounds: dict[str, arcade.Sound] = {}
        self._current_player = None
        self._current_track: str | None = None
        self._volume: float = 0.5
        self._bgm_dir = Path(__file__).parent / "assets" / "bgm"

        self._preload()

    def _preload(self):
        """预加载所有BGM文件（streaming模式，不占用大量内存）"""
        tracks = {
            "intro": self._bgm_dir / "intro.mp3",
            "village": self._bgm_dir / "village.mp3",
            "battle1": self._bgm_dir / "battle1.mp3",
        }
        for name, path in tracks.items():
            if path.exists():
                try:
                    self._sounds[name] = arcade.Sound(str(path), streaming=True)
                    print(f"[BGM] 已加载: {name}")
                except Exception as e:
                    print(f"[BGM] 加载失败 {name}: {e}")
            else:
                print(f"[BGM] 文件不存在: {path}")

    def play_bgm(self, track_name: str, volume: float = None):
        """切换到指定BGM（同一首不重复播放）"""
        if volume is None:
            volume = self._volume

        if self._current_track == track_name and self._is_playing():
            return

        self._stop_current()

        if track_name not in self._sounds:
            print(f"[BGM] 未找到曲目: {track_name}")
            return

        try:
            self._current_player = self._sounds[track_name].play(volume=volume)
            self._current_track = track_name
            print(f"[BGM] 播放: {track_name}")
        except Exception as e:
            print(f"[BGM] 播放失败 {track_name}: {e}")

    def _stop_current(self):
        """停止当前播放"""
        if self._current_player:
            try:
                arcade.stop_sound(self._current_player)
            except Exception:
                pass
        self._current_player = None
        self._current_track = None

    def _is_playing(self) -> bool:
        """检查当前播放器是否活跃"""
        if self._current_player is None:
            return False
        try:
            return self._current_player.playing
        except Exception:
            return False

    def on_update(self, dt: float):
        """每帧调用 - streaming模式下不支持loop，手动检测并重新播放"""
        if self._current_track is None or self._current_player is None:
            return
        try:
            if not self._current_player.playing and self._current_track in self._sounds:
                self._current_player = self._sounds[self._current_track].play(
                    volume=self._volume
                )
        except Exception:
            pass

    def set_volume(self, volume: float):
        """设置音量 (0.0 ~ 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        if self._current_player:
            try:
                self._current_player.volume = self._volume
            except Exception:
                pass

    def stop(self):
        """停止BGM"""
        self._stop_current()
