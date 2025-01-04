#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import sys
sys.path.append('/home/wheeltec/QT/src/qt_node/src')  # 将文件路径加入到 sys.path
from PyQt5 import QtWidgets, QtGui, QtCore # 正确导入 QtGui
from untitled import Ui_Dialog  # 导入由 pyuic5 转换的 UI 类

class MyDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置UI

        # 设置 listView 的排列方向为水平
        self.listView.setFlow(QtWidgets.QListView.LeftToRight)  # 水平排列

        # 设置 listView 为单行显示
        self.listView.setViewMode(QtWidgets.QListView.IconMode)  # 使用图标模式显示

        # 连接 spinBox 的值变化事件
        self.spinBox.valueChanged.connect(self.update_listview)

    def update_listview(self):
        # 获取 spinBox 的值
        value = self.spinBox.value()

        # 创建 listView 的模型
        model = QtGui.QStandardItemModel(self.listView)

        # 根据 spinBox 的值更新 listView 的内容
        for i in range(value):
            # 创建每一项，项名为 "房间 1", "房间 2", ...
            item = QtGui.QStandardItem(f"房间 {i + 1}")
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 设置文本居中显示
            model.appendRow(item)

        # 设置 listView 的模型
        self.listView.setModel(model)


def main():
    # 创建 Qt 应用
    app = QtWidgets.QApplication(sys.argv)

    # 创建 Dialog 窗口并设置 UI
    dialog = MyDialog()

    # 显示界面
    dialog.show()

    # 启动 Qt 应用的事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()