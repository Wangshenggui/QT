#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtWidgets
from untitled.py import Ui_Dialog  # 导入由 pyuic5 转换的 UI 类

def main():
    # 创建 Qt 应用
    app = QtWidgets.QApplication(sys.argv)

    # 创建 Dialog 窗口并设置 UI
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)

    # 显示界面
    Dialog.show()

    # 启动 Qt 应用的事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()