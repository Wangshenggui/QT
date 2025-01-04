#!/usr/bin/env python3
# -*- coding: utf-8 -*- 
import sys
sys.path.append('/home/wheeltec/QT/src/qt_node/src')  # 将文件路径加入到 sys.path
import socket
import threading
import rospy
from geometry_msgs.msg import Point
from std_msgs.msg import Int32, Int8
from PyQt5 import QtWidgets, QtGui, QtCore
from untitled2 import Ui_Dialog
import select
import json
import serial  # 导入串口库

class MyDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置UI

        # 存储点击的房间数据
        self.selected_rooms = []

        # 房间的数据字典，每个房间都有一个 (x, y, z) 坐标
        self.room_data = {
            1: (-3.29, 63.1, 0),  # room1 数据 (x, y, z)
            2: (5.65, -0.355, 0),  # room2 数据 (x, y, z)
            3: (-3.29, -40.4, 0),  # room3 数据 (x, y, z)
            4: (-3.29, 40.2, 0)   # room4 数据 (x, y, z)
        }

        # 初始化 ROS 节点
        rospy.init_node('room_data_publisher', anonymous=True)
        self.publisher = rospy.Publisher('/room_data_topic', Point, queue_size=10)  # 创建一个发布者

        # 订阅 'arrive' 话题，接收房间号信息
        self.arrive_subscriber = rospy.Subscriber('/arrive', Int32, self.arrive_callback)

        # 初始化当前房间号和火灾状态
        self.current_room = None  # 当前发生火灾的房间号
        self.fire_status = False   # 火灾状态，False 表示没有火灾，True 表示有火灾
        self.first_fire_received = False  # 标记是否接收到第一次 "fire": 1 的消息

        # 连接房间按钮的点击事件
        self.room1.clicked.connect(lambda: self.select_room(1))
        self.room2.clicked.connect(lambda: self.select_room(2))
        self.r00m3.clicked.connect(lambda: self.select_room(3))
        self.room4.clicked.connect(lambda: self.select_room(4))

        # 连接执行按钮的点击事件
        self.pushButton.clicked.connect(self.publish_data)

        # 初始化 QStandardItemModel 用来显示数据
        self.model = QtGui.QStandardItemModel()

        # 确保 list_view 是 QListView
        if isinstance(self.list_view, QtWidgets.QListView):
            self.list_view.setModel(self.model)  # 将 model 设置给 QListView
        else:
            print("Error: 'list_view' is not a QListView!")

        # 初始化两个 QLabel，用于显示不同的状态
        self.room_detection_label = QtWidgets.QLabel(self)  # 创建 QLabel 用于显示正在检测房间
        self.room_detection_label.setGeometry(10, 10, 400, 30)  # 设置位置和大小
        self.room_detection_label.setAlignment(QtCore.Qt.AlignCenter)  # 设置文本居中
        self.room_detection_label.setText("等待火灾状态...")  # 默认文本

        self.fire_status_label = QtWidgets.QLabel(self)  # 创建 QLabel 用于显示火灾状态
        self.fire_status_label.setGeometry(10, 50, 400, 30)  # 设置不同位置，避免重叠
        self.fire_status_label.setAlignment(QtCore.Qt.AlignCenter)  # 设置文本居中
        self.fire_status_label.setText("等待火灾状态...")  # 默认文本

        # 初始化串口连接 (通过 PySerial)
        self.serial_port_ama0 = '/dev/ttyCH343USB1'  # 原串口设备（保持不变）
        self.serial_port_usb1 = '/dev/ttyCH343USB2'  # 新增串口 ttyUSB1
        self.baudrate = 115200  # 设置波特率

        # 打开原串口（ttyAMA0）
        try:
            self.ser_ama0 = serial.Serial(self.serial_port_ama0, self.baudrate, timeout=1)
            print(f"串口 {self.serial_port_ama0} 已连接.")
        except Exception as e:
            print(f"无法打开串口 {self.serial_port_ama0}: {e}")
            self.ser_ama0 = None

        # 打开串口（ttyUSB1）
        try:
            self.ser_usb1 = serial.Serial(self.serial_port_usb1, self.baudrate, timeout=1)
            print(f"串口 {self.serial_port_usb1} 已连接.")
        except Exception as e:
            print(f"无法打开串口 {self.serial_port_usb1}: {e}")
            self.ser_usb1 = None

        # 存储TCP连接的套接字
        self.client_sockets = []

        # 启动 TCP 服务器线程
        self.server_thread = threading.Thread(target=self.start_tcp_server, args=('0.0.0.0', 5000))
        self.server_thread.daemon = True
        self.server_thread.start()

        # 添加电话号码输入框 (QLineEdit)
        self.phone_input = QtWidgets.QLineEdit(self)  # 创建输入框
        self.phone_input.setGeometry(100, 600, 200, 30)  # 设置位置和大小
        self.phone_input.setPlaceholderText("请输入电话号码")  # 提示文本

        # 添加发送按钮
        self.send_button = QtWidgets.QPushButton(self)  # 创建按钮
        self.send_button.setGeometry(320, 600, 100, 30)  # 设置位置和大小
        self.send_button.setText("发送电话")  # 按钮文本
        self.send_button.clicked.connect(self.save_phone_number)  # 按钮点击事件

        # 初始化电话号码字段
        self.saved_phone_number = None  # 用于保存用户输入的电话号码

    def save_phone_number(self):
        """
        记录用户输入的电话号码
        """
        self.saved_phone_number = self.phone_input.text()
        print(f"已保存电话号码: {self.saved_phone_number}")

    def arrive_callback(self, msg):
        """
        处理接收到的 arrive 数据，更新当前正在检测的房间号。
        """
        self.current_room = msg.data
        print(f"当前房间号: {self.current_room}")
        self.update_room_detection()

    def fire_callback(self, msg):
        """
        处理接收到的火灾信息，更新火灾状态。
        """
        try:
            fire_data = json.loads(msg.data.decode())  # 解析收到的数据
            print(f"接收到的火灾数据: {fire_data}")  # 调试输出
            
            if "fire" in fire_data and fire_data["fire"] == 1:
                if not self.first_fire_received:
                    # 忽略第一次收到的火灾数据
                    self.first_fire_received = True
                    print("忽略第一次火灾消息")
                    return  # 忽略后续处理
                self.fire_status = True
            else:
                self.fire_status = False

            self.update_fire_status()  # 更新火灾状态显示
            
            # 如果发生火灾，发送 AT 命令
            if self.fire_status:
                self.trigger_at_command()  # 当火灾发生时，发送 AT 命令

        except json.JSONDecodeError:
            print("无法解析 fire 数据")

    def update_room_detection(self):
        """
        根据当前房间号更新显示的房间信息
        """
        if self.current_room == 1:
            self.room_detection_label.setText("正在检测房间1")
        elif self.current_room is not None:
            self.room_detection_label.setText(f"正在检测房间{self.current_room - 1}")
        else:
            self.room_detection_label.setText("等待火灾状态...")

    def update_fire_status(self):
        """
        根据火灾状态更新火灾提示信息
        """
        if self.current_room is not None:
            if self.fire_status:
                self.fire_status_label.setText("火灾发生！立即疏散！")
                if self.ser_usb1:
                    self.send_room_to_usb1()  # 发送房间号到 ttyUSB1
            else:
                self.fire_status_label.setText("暂无火灾")
        else:
            self.fire_status_label.setText("等待火灾状态...")

    def send_room_to_usb1(self):
        """
        当火灾发生时，通过 ttyUSB1 发送房间号
        """
        if self.ser_usb1 and self.current_room is not None:
            try:
                at_command = f'room={self.current_room}\r\n'  # 构造 AT 命令
                print(f"{at_command}")
                self.ser_usb1.write(at_command.encode())  # 发送 AT 命令
                self.ser_usb1.flush()  # 确保缓冲区数据已经发送
                print(f"已向串口 {self.serial_port_usb1} 发送房间号: {at_command}")
            except Exception as e:
                print(f"发送命令时发生错误: {e}")

    def trigger_at_command(self):
        """
        发送 AT 命令以拨打指定的电话号码
        """
        if self.saved_phone_number:
            at_command = f'AT+Call={self.saved_phone_number}\r\n'  # 构造 AT 命令
            print(f"发送命令: {at_command}")  # 调试打印 AT 命令
            
            if self.ser_ama0:
                try:
                    self.ser_ama0.write(at_command.encode())  # 发送 AT 命令
                    print(f"命令已发送到串口: {at_command}")
                    response = self.ser_ama0.readline()  # 读取串口响应
                    print(f"串口返回: {response.decode()}")  # 打印串口返回
                except Exception as e:
                    print(f"发送 AT 命令时发生错误: {e}")
            else:
                print("串口未连接，无法发送 AT 命令")
        else:
            print("电话号码未保存，无法发送 AT 命令")

    def select_room(self, room_number):
        """
        每次点击房间按钮时，将该房间的 (x, y, z) 数据加入或移除列表
        """
        if room_number not in self.selected_rooms:
            self.selected_rooms.append(room_number)
            print(f"Room {room_number} selected, data: {self.room_data[room_number]}")
        else:
            self.selected_rooms.remove(room_number)
            print(f"Room {room_number} deselected, data removed")

        # 更新 list_view 中的内容
        self.update_show_list()

    def update_show_list(self):
        """
        更新 list_view 中的列表，显示所有已选中的房间
        """
        self.model.clear()  # 清空当前的列表

        # 将选中的房间数据添加到模型中
        for room in self.selected_rooms:
            room_name = f"Room {room}: {self.room_data[room]}"
            item = QtGui.QStandardItem(room_name)
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 设置文本居中显示
            self.model.appendRow(item)

    def publish_data(self):
        """
        点击 'execute' 按钮时，将选中的房间数据发布出去
        """
        selected_data = [self.room_data[room] for room in self.selected_rooms]

        if selected_data:
            print("Publishing data for selected rooms:")

            # 构建消息字符串，首先添加帧头
            frame_header = 1999  # 帧头为 1999
            frame_footer = 2999  # 帧尾为 2999

            # 构建数据部分，将每个房间的 (x, y, z) 格式化成字符串并拼接
            message_data = []
            for data in selected_data:
                # 将数据 (x, y, z) 转换为字符串并添加到列表中
                message_data.append(f"{data[0]} {data[1]} {data[2]}")

            # 拼接完整的消息（帧头 + 数据 + 帧尾）
            full_message = f"{frame_header} " + " ".join(message_data) + f" {frame_footer}"

            # 打印完整的消息（用于调试）
            print(f"Sending message: {full_message}")

            # 发布帧头
            point_header = Point()
            point_header.x = frame_header
            self.publisher.publish(point_header)

            # 发布数据部分（每个房间数据） 
            for data in selected_data:
                point_msg = Point()
                point_msg.x = data[0]
                point_msg.y = data[1]
                point_msg.z = data[2]
                self.publisher.publish(point_msg)

            # 发布帧尾
            point_footer = Point()
            point_footer.x = frame_footer
            self.publisher.publish(point_footer)

            print("Data published to /room_data_topic.")
        else:
            print("No rooms selected, nothing to send.")

    def start_tcp_server(self, host='0.0.0.0', port=5000):
        """
        启动一个 TCP 服务器，监听指定的地址和端口
        """
        # 创建一个 TCP socket 对象
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setblocking(False)  # 设置为非阻塞模式
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"服务器启动，监听 {host}:{port} 端口...")

        # 使用 select 监听套接字
        inputs = [server_socket]
        
        # 初始化标志位，判断是否是第一次接收到消息
        first_message_received = False
        
        while True:
            # 使用 select 来监听
            readable, _, _ = select.select(inputs, [], [])
            
            for s in readable:
                if s is server_socket:
                    # 接受新的客户端连接
                    client_socket, client_address = server_socket.accept()
                    print(f"客户端 {client_address} 已连接")
                    inputs.append(client_socket)  # 将新的客户端套接字添加到 inputs 列表

                else:
                    # 接收客户端的数据
                    data = s.recv(1024)
                    if data:
                        try:
                            # 解析收到的数据
                            message = json.loads(data.decode())
                            print(f"接收到消息: {message}")
                            
                            # 如果是第一次接收到消息，则跳过处理
                            if not first_message_received:
                                first_message_received = True
                                print("忽略第一次接收到的消息")
                                continue  # 忽略这次消息，不进行后续处理

                            # 如果消息中包含火灾数据，进行相应处理
                            if "fire" in message and message["fire"] == 1:
                                self.fire_status = True
                                self.update_fire_status()
                                self.trigger_at_command()  # 触发 AT 命令
                        except json.JSONDecodeError:
                            print("无法解析 JSON 数据")
                    else:
                        # 客户端关闭连接
                        print(f"客户端 {s.getpeername()} 已断开连接")
                        inputs.remove(s)
                        s.close()

def main():
    # 创建 Qt 应用
    app = QtWidgets.QApplication(sys.argv)

    # 创建 Dialog 窗口并设置 UI
    dialog = MyDialog()

    # 显示界面
    dialog.show()  # 现在调用 show() 方法没有冲突了

    # 启动 Qt 应用的事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()