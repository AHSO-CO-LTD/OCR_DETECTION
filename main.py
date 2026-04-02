# ===== SAFE IMPORT ZONE for PyInstaller =====
# Đảm bảo PyInstaller đóng gói đầy đủ dependencies, kể cả khi các module đã mã hoá thành .pyd

# --- Core system ---
import os, sys, re, math, time, random, threading, multiprocessing, csv, shutil, datetime, pathlib, io, ast, yaml, ctypes, subprocess, psutil

# --- Data & AI ---
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data
import torchvision
from torchvision import datasets, transforms, models
from sklearn.model_selection import train_test_split
from torchinfo import summary
from ultralytics import YOLO
import tqdm  # dùng cho thanh tiến trình

# --- Communication / PLC / Database ---
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import pymodbus
import pymcprotocol
import pymysql
from pymysql.err import MySQLError

# --- Windows API (Single Instance) ---
import win32event
import win32api
import winerror


# --- Image / Vision ---
import cv2
import cvzone
from cvzone.Utils import putTextRect
from PIL import Image, ImageTk
from pypylon import pylon

# --- GUI (PyQt5 + PyQtGraph) ---
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg

# --- XML / ETC ---
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ===== END SAFE IMPORT ZONE =====



# Lấy thư mục chứa file main.py hoặc main.exe
if getattr(sys, 'frozen', False):
    # Đang chạy trong EXE (PyInstaller)
    base_path = os.path.dirname(sys.executable)
else:
    # Đang chạy Python bình thường
    base_path = os.path.dirname(os.path.abspath(__file__))

module_path = os.path.join(base_path, "lib")
sys.path.append(module_path)
import StackUI
from StackUI import StackedWidget


if __name__ == '__main__':
    # QUAN TRỌNG: Phải có dòng này khi đóng EXE để tránh spawn vô hạn processes
    multiprocessing.freeze_support()

    # Kiểm tra single instance bằng Mutex
    # Tạo mutex với tên unique cho app này
    mutex = win32event.CreateMutex(None, False, 'Global\\AHSO_DRB_OCR_AI_Metalcore')
    last_error = win32api.GetLastError()

    if last_error == winerror.ERROR_ALREADY_EXISTS:
        # Đã có instance đang chạy
        sys.exit(0)

    app = QtWidgets.QApplication(sys.argv)
    window = StackedWidget()
    window.setCurrentIndex(0)
    window.showFullScreen()
    sys.exit(app.exec_())