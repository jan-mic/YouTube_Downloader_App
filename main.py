import os
import subprocess
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QLabel, QTextEdit, QLineEdit, QFrame, QWidget, \
    QComboBox, QPushButton, QFileDialog, QProgressBar
from pytubefix import YouTube
import platform


class YtDownloaderApp(QWidget):

    window_title = "Youtube Downloader"

    label_youtube_url = "YouTube URL"
    label_type_and_quality_selection = "Type / Quality"
    label_progress = "Progress Bar"
    label_download = "Download"
    label_download_completed = "File Downloaded!"

    yt_default_filename = ''
    stream_type = None
    extension_info = None

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.window_title)
        self.setFixedSize(490, 110)
        self.center()

        #YT URL
        self.add_label(self.label_youtube_url, 10, 10)
        self.youtube_url = QLineEdit(self)
        self.youtube_url.setGeometry(120, 10, 360, 20)
        self.youtube_url.textChanged.connect(self.update_stream_selection)

        #stream selection
        self.add_label(self.label_type_and_quality_selection, 10, 40)
        self.stream_selection = QComboBox(self)
        self.stream_selection.setGeometry(120, 40, 360, 20)
        self.stream_selection.addItem("Select Stream")

        # separator
        self.add_separator(70)

        #progress label
        self.add_label(self.label_progress, 10, 80)

        # progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(120, 80, 100, 20)
        self.progress_bar.setValue(0)

        #download completed
        self.label_download = QLabel(self.label_download_completed, self)
        self.label_download.move(235, 80)
        self.label_download.setStyleSheet("font-size: 14px;")
        self.label_download.hide()

        #download
        self.button_download = QPushButton("Download", self)
        self.button_download.setGeometry(380, 78, 100, 23)
        self.button_download.setStyleSheet("font-size: 13px")
        self.button_download.clicked.connect(self.file_download)

        self.show()

    def center(self):
        qr = self.frameGeometry()  # Get the geometry of the main window
        cp = QDesktopWidget().availableGeometry().center()  # Get the center point of the screen
        qr.moveCenter(cp)  # Move the center of the window geometry to the center point
        self.move(qr.topLeft())  # Move the top-left point of the window to match the geometry

    def add_label(self, text, x, y):
        label = QLabel(text, self)
        label.move(x, y)
        label.setStyleSheet("font-size: 16px;")

    def add_separator(self, y):
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setGeometry(10, y, 470, 2)

    def file_download(self):
        url = self.youtube_url.text()
        selected_stream_info = self.stream_selection.currentText()
        self.label_download.hide()

        if not url or selected_stream_info == "Select Stream":
            print("URL or Stream not selected")
            return

        try:
            yt = YouTube(url, on_progress_callback=self.on_progress)
            selected_stream = self.get_selected_stream(yt, selected_stream_info)
            self.stream_type = selected_stream.type
            file_path = self.get_file_path(selected_stream)

            if file_path:
                directory = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)

                if selected_stream.type == 'video':
                    if self.extension_info == "mp4":
                        audio_stream = yt.streams.filter(type='audio', file_extension='mp4').order_by('abr').desc().first()
                    else:
                        audio_stream = yt.streams.filter(type='audio', file_extension='webm').order_by('abr').desc().first()

                    video_file = selected_stream.download(output_path=directory, filename=file_name, filename_prefix="video_")
                    audi_file = audio_stream.download(output_path=directory, filename=file_name, filename_prefix="audio_")

                    self.merge_video_audio(video_file, audi_file, file_path)

                    os.remove(video_file)
                    os.remove(audi_file)

                    self.progress_bar.setValue(100)
                    self.label_download.show()
                    print("Download completed!")

                if selected_stream.type == 'audio':
                    selected_stream.download(output_path=directory, filename=file_name)
                    self.progress_bar.setValue(100)
                    self.label_download.show()
                    print("Download completed!")

            else:
                print("Download failed!")

        except Exception as e:
            print(f"Error: {e}")

    def get_file_path(self, selected_stream):
        options = QFileDialog.Options()
        file_extension = selected_stream.subtype
        self.extension_info = file_extension

        file_filter = file_extension.upper() + " Files (*." + file_extension + ");;All Files (*)"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", self.yt_default_filename + '.' + file_extension, file_filter, options=options)
        return file_path

    # def get_ffmpeg_path(self):
    #     # Jeśli jest zapakowany, użyj wbudowanej ścieżki
    #     if getattr(sys, 'frozen', False):
    #         return os.path.join(sys._MEIPASS, "ffmpeg", "ffmpeg.exe")  # Dla Windows
    #     else:
    #         return os.path.join(os.getcwd(), "ffmpeg", "ffmpeg.exe")  # Dla normalnego środowiska

    # def get_ffmpeg_path(self):
    #     ffmpeg_file = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    #
    #     if getattr(sys, 'frozen', False):
    #         return os.path.join(sys._MEIPASS, "ffmpeg", ffmpeg_file)
    #     else:
    #         return os.path.join(os.path.dirname(__file__), "ffmpeg", ffmpeg_file)
    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            ffmpeg_file = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
            return os.path.join(sys._MEIPASS, "ffmpeg", ffmpeg_file)
        else:
            ffmpeg_file = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
            return os.path.join(os.path.dirname(__file__), "ffmpeg", ffmpeg_file)

    def merge_video_audio(self, video_file, audio_file, file_path):
        #ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "ffmpeg.exe")
        ffmpeg_path = self.get_ffmpeg_path()
        #command = f'"{ffmpeg_path}" -i "{video_file}" -i "{audio_file}" -c copy "{file_path}" -y'
        command = [
            ffmpeg_path,
            "-i", video_file,
            "-i", audio_file,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            "-b:a", "192k",
            file_path,
            "-y"
        ]


        # subprocess.run(command, shell=True)
        subprocess.run(command, stdout=subprocess.DEVNULL)

    def get_selected_stream(self, yt, selected_stream_info):
        for stream in yt.streams.fmt_streams:
            if self.format_stream_description(stream) == selected_stream_info:
                return stream
        return None

    def format_stream_description(self, stream):
        if stream.type == "video":
            return self.video_info_format(stream)
        elif stream.type == "audio":
            return self.audio_info_format(stream)
        else:
            return "Unknown stream"

    def video_info_format(self, stream):
        return f"{stream.mime_type} - {stream.resolution} - {stream.video_codec} - {round(stream.filesize/1000000, 2)} MB"

    def audio_info_format(self, stream):
        return f"{stream.mime_type} - {stream.abr} - {round(stream.filesize / 1000000, 2)} MB"

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining

        if self.stream_type == "video":
            if stream.type == "video":
                download_progress = int((bytes_downloaded / total_size) * 85)
                self.progress_bar.setValue(download_progress)
            else:
                download_progress = int((bytes_downloaded / total_size) * 14)
                self.progress_bar.setValue(85 + download_progress)
        else:
            download_progress = int((bytes_downloaded / total_size) * 100)
            self.progress_bar.setValue(download_progress)

    def update_stream_selection(self):
        url = self.youtube_url.text()
        if not url:
            return

        try:
            yt = YouTube(url)
            self.yt_default_filename = yt.title
            self.stream_selection.clear()

            #add videos to list
            streams = yt.streams.filter(only_video=True).order_by('resolution').desc()
            for stream in streams:
                stream_label = self.video_info_format(stream)
                self.stream_selection.addItem(stream_label)

            # add audios to list
            streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
            for stream in streams:
                stream_label = self.audio_info_format(stream)
                self.stream_selection.addItem(stream_label)

        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    yt_downloader_app = YtDownloaderApp()
    sys.exit(app.exec_())



