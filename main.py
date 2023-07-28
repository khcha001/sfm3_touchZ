import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
import pandas as pd
import re
import matplotlib.pyplot as plt


class TouchZParserApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Touch Z 파서')
        self.setGeometry(100, 100, 320, 240)
        self.setFixedSize(320, 240)  # 창 크기를 고정

        layout = QVBoxLayout(self)

        self.btn_load_logs = QPushButton('(1) 로그불러오기', self)
        self.btn_load_logs.clicked.connect(self.load_logs)
        layout.addWidget(self.btn_load_logs)

        self.btn_parse = QPushButton('(2) 파싱하기', self)
        self.btn_parse.clicked.connect(self.parse_logs)
        layout.addWidget(self.btn_parse)

        self.btn_plot = QPushButton('(3) 그래프로 나타내기', self)
        self.btn_plot.clicked.connect(self.plot_graph)
        layout.addWidget(self.btn_plot)

        self.btn_exit = QPushButton('(4) 종료', self)
        self.btn_exit.clicked.connect(self.close)
        layout.addWidget(self.btn_exit)

        self.log_entries = []  # 불러온 로그들을 저장할 리스트를 생성합니다.

    def load_logs(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_paths, _ = QFileDialog.getOpenFileNames(self, "로그 파일 불러오기", "", "로그 파일 (*.log);;모든 파일 (*)", options=options)
        if file_paths:
            self.log_entries.clear()  # 이전에 불러온 로그들을 비웁니다.
            for file_path in file_paths:
                with open(file_path, 'r') as file:
                    log_data = file.read()

                    # 각 로그 라인을 줄바꿈을 기준으로 분리하여 파싱합니다.
                    log_lines = log_data.split('\n')
                    for log_line in log_lines:
                        log_info = self.parse_log_line(log_line)
                        if log_info:
                            self.log_entries.append(log_info)

            # 여러 .log 파일을 불러온 후에 메시지를 표시합니다.
            QMessageBox.information(self, "성공", "로그파일을 정상적으로 불러왔습니다.", QMessageBox.Ok)

    def parse_log_line(self, log_line):
        # 로그 라인을 파싱하는 로직을 작성합니다.
        log_info = {}
        try:
            if log_line:
                # 로그 라인을 파싱하는 로직을 작성합니다.
                time_end_idx = log_line.index('Head:')
                # Time의 값을 추출합니다. 초(sec)는 소수점 없이 표시합니다.
                time_value = log_line[:time_end_idx].strip()
                time_value = re.sub(r'\.\d+', '', time_value)  # 초(sec) 부분의 소수점을 없애기 위해 정규식을 사용합니다.
                log_info['Time'] = time_value

                head_start_idx = time_end_idx + len('Head:')
                head_end_idx = log_line.index('Place', head_start_idx)  # Head와 Place 사이의 값을 추출합니다.
                log_info['Head'] = log_line[head_start_idx:head_end_idx].strip()

                # Place, Flux, Pick 중 어느 것인지 구분값을 추출합니다.
                log_info['구분'] = log_line[head_end_idx:head_end_idx+5].strip()

                posx_start_idx = log_line.index('PosX:', head_end_idx) + len('PosX:')
                posx_end_idx = log_line.index('PosY:', posx_start_idx)  # PosX와 PosY 사이의 값을 추출합니다.
                log_info['PosX'] = log_line[posx_start_idx:posx_end_idx].strip()

                posy_start_idx = posx_end_idx + len('PosY:')
                posy_end_idx = log_line.index('TouchZ:', posy_start_idx)  # PosY와 TouchZ 사이의 값을 추출합니다.
                log_info['PosY'] = log_line[posy_start_idx:posy_end_idx].strip()

                touchz_start_idx = posy_end_idx + len('TouchZ:')
                # Touch Z의 값을 추출합니다. 소수 넷째 자리까지 포함하는 float 값입니다.
                touch_z_value = re.search(r'\d+\.\d{4}', log_line[touchz_start_idx:])
                if touch_z_value:
                    log_info['Touch Z'] = float(touch_z_value.group())
        except ValueError:
            # 파싱 중 에러가 발생한 경우 무시합니다.
            pass

        return log_info

    def save_to_excel(self, df):
        if df.empty:
            QMessageBox.warning(self, "경고", "파싱할 로그가 없습니다.", QMessageBox.Ok)
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "파싱 결과 저장", "", "Excel Files (*.xlsx)", options=options)

        if file_path:
            try:
                # DataFrame을 Excel 파일로 저장합니다.
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "성공", "파싱 결과를 저장했습니다.", QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, "에러", f"파일 저장 중 오류가 발생했습니다: {str(e)}", QMessageBox.Ok)


    def parse_logs(self):
        if not self.log_entries:
            QMessageBox.warning(self, "경고", "파싱할 로그가 없습니다. 먼저 로그를 불러와주세요.", QMessageBox.Ok)
            return

        # 파싱 결과를 pandas DataFrame으로 변환합니다.
        df = pd.DataFrame(self.log_entries)

        # Time 열에만 값이 있는 행들을 삭제합니다.
        df = df.dropna(subset=['Time'])

        # '구분' 열에 'Place'만 있는 행들을 남기고 나머지를 삭제합니다.
        df = df[df['구분'] == 'Place']

        # DataFrame을 Excel 파일로 저장합니다.
        self.save_to_excel(df)

    def plot_graph(self):
        if not self.log_entries:
            QMessageBox.warning(self, "경고", "데이터가 없습니다. 먼저 로그를 불러와주세요.", QMessageBox.Ok)
            return

        # 파싱 결과를 pandas DataFrame으로 변환합니다.
        df = pd.DataFrame(self.log_entries)

        # Time 열에만 값이 있는 행들을 삭제합니다.
        df = df.dropna(subset=['Time'])

        # '구분' 열에 'Place'만 있는 행들을 남기고 나머지를 삭제합니다.
        df = df[df['구분'] == 'Place']

        # Time 값을 datetime 형식으로 변환합니다.
        df['Time'] = pd.to_datetime(df['Time'], format='%Y/%m/%d %H:%M:%S')

        # 6시간 단위로 데이터를 그룹화합니다.
        df['Time'] = df['Time'].dt.floor('6H')

        # 그래프를 그리기 위해 Head를 숫자형으로 변환합니다.
        df['Head'] = df['Head'].astype(int)

        # 각 Head별로 분산형 그래프를 그립니다.
        colors = {1: 'red', 2: 'orange', 3: 'blue', 4: 'green'}
        for head, group in df.groupby('Head'):
            plt.scatter(group['Time'], group['Touch Z'], label=f'Head {head}', color=colors[head])

        plt.xlabel('Time')
        plt.ylabel('Touch Z')
        plt.title('Touch Z by Head')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TouchZParserApp()
    window.show()
    sys.exit(app.exec_())

