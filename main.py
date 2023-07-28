import sys
import re
import matplotlib.pyplot as plt
import matplotlib._path  # Hidden import

import seaborn as sns
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox
import matplotlib.dates as mdates
from matplotlib import font_manager
from matplotlib.dates import HourLocator, DateFormatter



class MyGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("sfm3 터치 Z 파싱")
        self.setGeometry(100, 100, 320, 240)

        btn_load = QPushButton("로그 불러오기", self)
        btn_load.setGeometry(60, 30, 200, 50)
        btn_load.clicked.connect(self.load_files)

        btn_parse = QPushButton("파싱하기", self)
        btn_parse.setGeometry(60, 90, 200, 50)
        btn_parse.clicked.connect(self.parse_data)

        btn_show_graphs = QPushButton("그래프 보여주기", self)
        btn_show_graphs.setGeometry(60, 150, 200, 50)
        btn_show_graphs.clicked.connect(self.show_graphs)

        # 창 크기를 고정합니다.
        self.setFixedSize(self.size())

        self.log_data = []

    def load_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_names, _ = QFileDialog.getOpenFileNames(self, "로그 파일 불러오기", "", "로그 파일 (*.log);;모든 파일 (*)", options=options)

        if file_names:
            self.log_data = []  # 기존 로그 데이터를 비웁니다.
            for file_name in file_names:
                with open(file_name, 'r') as file:
                    try:
                        line_number = 0  # 줄 번호를 추적합니다.
                        for line in file:
                            line_number += 1
                            # Use re.search() to find matching pattern in the line
                            match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+Head:\s+(\d+)\s+([\w\s]+)\s+Bl:(\d+)\s+Ar:(\d+)\s+CadID:(\d+)\s+(\w+)\s+PosX:(-?\d+\.\d+)\s+PosY:(-?\d+\.\d+)\s+TouchZ:(-?\d+\.\d+)', line)
                            if match:
                                datetime_str, head, data_type, bl, ar, cad_id, l0, pos_x, pos_y, touch_z = match.groups()
                                # Check if DataType is "Place"
                                if data_type.strip() == "Place":  # Strip to remove leading/trailing whitespaces
                                    self.log_data.append({
                                        "DateTime": datetime_str,
                                        "Head": int(head),
                                        "DataType": data_type.strip(),
                                        "PosX": float(pos_x),
                                        "PosY": float(pos_y),
                                        "TouchZ": float(touch_z)
                                    })
                    except Exception as e:
                        QMessageBox.warning(self, "파일 로드 에러", f"파일 로드 중 오류가 발생했습니다.\n파일: {file_name}\n줄 번호: {line_number}\n에러 메시지: {str(e)}", QMessageBox.Ok)
                        return

        if self.log_data:
            QMessageBox.information(self, "성공", "파일을 성공적으로 불러왔습니다.", QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "경고", "유효한 로그 데이터가 없습니다.", QMessageBox.Ok)


    def parse_log_data(self, log_line):
        pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+Head:\s+(\d+)\s+([\w\s]+)\s+Bl:(\d+)\s+Ar:(\d+)\s+CadID:(\d+)\s+(\w+)\s+PosX:(-?\d+\.\d+)\s+PosY:(-?\d+\.\d+)\s+TouchZ:\s*(-?\d+\.\d+)\s+100\s+Act\(gf\):\s*(-?\d+\.\d+)\s+Target\(gf\):\s*(-?\d+\.\d+)\s+Dbg:\s*(-?\d+\.\d+)\s+(\w+\d+\.\d+)\s+TouchTime:\s+(\d+)\s+\[(\d+)\]'
        match = re.match(pattern, log_line)
        if match:
            datetime_str, head, data_type, bl, ar, cad_id, l0, pos_x, pos_y, touch_z, act_gf, target_gf, dbg, c_value, touch_time1, touch_time2 = match.groups()
            # Check if DataType is "Place"
            if data_type.strip() in ("Place", "Place\n"):  # Strip to remove leading/trailing whitespaces
                return {
                    "DateTime": datetime_str,
                    "Head": int(head),
                    "DataType": data_type.strip(),
                    "PosX": float(pos_x),
                    "PosY": float(pos_y),
                    "TouchZ": float(touch_z),
                    "Act(gf)": float(act_gf),
                    "Target(gf)": float(target_gf),
                    "Dbg": float(dbg),
                    "CValue": c_value,
                    "TouchTime1": int(touch_time1),
                    "TouchTime2": int(touch_time2)
                }
        return None  

    def parse_data(self):
            if not self.log_data:
                QMessageBox.warning(self, "경고", "파싱할 로그 데이터가 없습니다.", QMessageBox.Ok)
                return

            QMessageBox.information(self, "파싱 성공", "파싱이 성공적으로 완료되었습니다.", QMessageBox.Ok)

            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "결과 파일을 어디에 저장하실래요?", "", "텍스트 파일 (*.txt);;모든 파일 (*)", options=options)

            if file_name:
                # Filter log_data to keep only the entries with DataType 'Place'
                filtered_data = [data for data in self.log_data if data["DataType"] == "Place"]

                with open(file_name, 'w') as file:
                    for data in filtered_data:
                        file.write(f"DateTime: {data['DateTime']}\t")
                        file.write(f"Head: {data['Head']}\t")
                        file.write(f"DataType: {data['DataType']}\t")
                        file.write(f"PosX: {data['PosX']}\t")
                        file.write(f"PosY: {data['PosY']}\t")
                        file.write(f"TouchZ: {data['TouchZ']}\n")    

    def show_graphs(self):
        if not self.log_data:
            QMessageBox.warning(self, "경고", "그래프를 보여줄 데이터가 없습니다.", QMessageBox.Ok)
            return

        sns.set(style="whitegrid")
        heads = set(data["Head"] for data in self.log_data)

            # Set the font for Korean characters in matplotlib
        font_path = "C:/Windows/Fonts/malgun.ttf"  # Change this path if needed
        font_manager.FontProperties(fname=font_path).get_name()
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=font_path).get_name()

        sns.set(style="whitegrid")
        heads = set(data["Head"] for data in self.log_data)

        def on_pick(event):
            ind = event.ind[0]
            data = sorted_data[ind]
            datetime_str = data["DateTime"]
            head = data["Head"]
            touch_z = data["TouchZ"]
            data_type = data["DataType"]
            tooltip_text = f"DateTime: {datetime_str}\nHead: {head}\nTouchZ: {touch_z:.4f}\nDataType: {data_type}"
            self.tooltip.set_text(tooltip_text)

        for head in heads:
            data_for_head = [data for data in self.log_data if data["Head"] == head]
            if data_for_head:
                # Convert datetime_str to datetime object and sort by datetime
                sorted_data = sorted(data_for_head, key=lambda x: mdates.datestr2num(x["DateTime"]))
                x_values = [mdates.datestr2num(data["DateTime"]) for data in sorted_data]
                y_values = [data["TouchZ"] for data in sorted_data]
                fig, ax = plt.subplots()
                ax.xaxis_date()  # Set x-axis to display dates
                ax.xaxis.set_major_locator(HourLocator(interval=6))  # Set interval to display 6 hours
                ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))  # Format for x-axis
                plt.xticks(rotation=45)
                sns.scatterplot(x=x_values, y=y_values, ax=ax)
                plt.title(f"Head: {head}의 분산형 그래프")
                plt.tight_layout()

                # Create a tooltip for displaying data on hover
                self.tooltip = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w"),
                                        arrowprops=dict(arrowstyle="->"))
                self.tooltip.set_visible(False)

                # Connect the pick event to the on_pick function
                fig.canvas.mpl_connect('pick_event', on_pick)

                plt.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_gui = MyGUI()
    my_gui.show()
    sys.exit(app.exec_())