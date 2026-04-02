
from PyQt5.uic import loadUi
from PyQt5.QtGui import QTransform
import sys
#import tempfile
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QScrollArea, QVBoxLayout, QWidget,QFileDialog,QMessageBox, QSlider, QInputDialog,QListWidgetItem, QCheckBox,QComboBox,QTableWidget, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QWheelEvent, QKeyEvent
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsPixmapItem, QGraphicsView, QMainWindow,QStyle,QGraphicsRectItem,QGraphicsLineItem,QGraphicsTextItem,QGraphicsPolygonItem,QGraphicsEllipseItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QGraphicsProxyWidget
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap, QImage, QIcon,QPen,QBrush,QColor,QTransform,QFont,QPolygonF, QPainter
from PyQt5.QtCore import Qt, QPointF,QSize,QRectF
from PyQt5 import uic
from PyQt5.QtGui import QCursor
import cv2
import pyqtgraph as pg
import time
import shutil
import random
from sklearn.model_selection import train_test_split
from torchvision import transforms
from torchinfo import summary
import torch.optim as optim
from pypylon import pylon
from PIL import Image, ImageTk
import numpy as np
import os
from datetime import datetime
import multiprocessing
import csv
import ctypes
from io import BytesIO
from PyQt5.QtGui import QPixmap
import cvzone
from cvzone.Utils import putTextRect
import torch
from torch import nn
import torchvision
from torchvision import transforms
from ultralytics import YOLO
from tqdm import tqdm
import xml.etree.ElementTree as ET
import pandas as pd
from tqdm import tqdm
import threading
from pathlib import Path
from ctypes import *
import ctypes
import ast
import math

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, datasets
from torchvision.models import resnet18
import os
from PIL import Image
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

sys.path.append("MVSDK")
from IMVApi import *
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

from PyQt5.QtWidgets import QApplication

#sys.path.append(os.path.abspath("E:/Python_project/RunTime_Sofware"))

#
sys.path.append(os.path.abspath("E:/RunTime_Sofware"))

#import Deep_Learning_Sevice
import Deep_Learning_Tool

from Deep_Learning_Tool import DEEP_LEARNING_SEGMENTATION,DEEP_LEARNING_CLASSIFICATION,UNSUPERVISED_DEEP_LEARNING,OCR_DEEP_LEARNING, DEEP_LEARNING_lOCATION

class CameraHandler:
    def __init__(self):
        self.cam = MvCamera()
        self.frame = IMV_Frame()
        self.is_open = False

    def initialize_camera(self):
        """Khởi tạo và mở kết nối camera"""
        deviceList = IMV_DeviceList()
        interfaceType = IMV_EInterfaceType.interfaceTypeAll
        #self.displayDeviceInfo(deviceList)
        # Liệt kê thiết bị
        MvCamera.IMV_EnumDevices(deviceList, interfaceType)
        self.cam.IMV_CreateHandle(IMV_ECreateHandleMode.modeByIndex, byref(c_void_p(int(0))))
        self.cam.IMV_Open()
        # self.cam.IMV_SetEnumFeatureSymbol("TriggerSource","Software")  
        # self.cam.IMV_SetEnumFeatureSymbol("TriggerSelector","FrameStart")  
        # self.cam.IMV_SetEnumFeatureSymbol("TriggerMode","Off")  
        self.cam.IMV_SetEnumFeatureSymbol("ShutterMode", "Global")# Global_Shutter
        self.cam.IMV_SetIntFeatureValue("StreamBufferCount", 1)
        self.cam.IMV_StartGrabbing()
        self.is_open = True
        print("Camera opened successfully.")

    def configure_camera(self):
        """Cấu hình các tham số cơ bản cho camera"""
        if not self.is_open:
            raise RuntimeError("Camera not open.")
        
        self.cam.IMV_SetEnumFeatureSymbol("LineSelector", "Line0")
        self.cam.IMV_SetEnumFeatureSymbol("LineSource", "UserOutput0")
        self.cam.IMV_SetEnumFeatureSymbol("LineSelector", "Line0")# khai bao out 
        self.cam.IMV_SetEnumFeatureSymbol("UserOutputSelector", "UserOutput0")
        print("Camera configured successfully.")
    def io_camera(self,status):
        self.cam.IMV_SetEnumFeatureSymbol("LineSelector", "Line1")
        line_status = c_bool(0)
        self.cam.IMV_GetBoolFeatureValue("LineStatus", line_status)
        line_status = line_status.value

        UserOutputValue = c_bool(0)
        self.cam.IMV_SetBoolFeatureValue("UserOutputValue", status)
        self.cam.IMV_GetBoolFeatureValue("UserOutputValue", UserOutputValue)
        line_status_out0 = UserOutputValue.value
        #print("Status out:", line_status_out0)
        
        return line_status,line_status_out0
    def io_camera2(self):
        self.cam.IMV_SetEnumFeatureSymbol("LineSelector", "Line1")
        line_status = c_bool(0)
        self.cam.IMV_GetBoolFeatureValue("LineStatus", line_status)
        line_status = line_status.value
        
        return line_status       
    def set_exposure_time(self, exposure_time):
        """Thay đổi thời gian phơi sáng của camera"""
        exposure_time_value = exposure_time
        ret = self.cam.IMV_SetDoubleFeatureValue("ExposureTime", exposure_time_value)
        if ret != IMV_OK:
            raise RuntimeError("can't change exposure time.")
        print(f"Exposure time set to {exposure_time}.")

    def capture_frame(self):
        """Chụp và xử lý khung hình"""
        self.cam.IMV_ClearFrameBuffer()  # xóa hết anh trong buffer   
        if self.cam.IMV_GetFrame(self.frame, 1000) == 0:
            img =self.frame_to_opencv(self.frame)
            nRet = self.cam.IMV_ReleaseFrame(self.frame)
            if IMV_OK != nRet:
                print("Release frame failed! ErrorCode[%d]\n", nRet)
            return img
        else:
            return None

    def frame_to_opencv(self, frame):
        """Chuyển đổi khung hình sang định dạng OpenCV"""
        stPixelConvertParam = IMV_PixelConvertParam()
        
        # Xác định kích thước buffer
        nDstBufSize = frame.frameInfo.width * frame.frameInfo.height * 3
        pDstBuf = (c_ubyte * nDstBufSize)()
        memset(byref(stPixelConvertParam), 0, sizeof(stPixelConvertParam))
        
        # Thiết lập thông số chuyển đổi
        stPixelConvertParam.nWidth = frame.frameInfo.width
        stPixelConvertParam.nHeight = frame.frameInfo.height
        stPixelConvertParam.ePixelFormat = frame.frameInfo.pixelFormat
        stPixelConvertParam.pSrcData = frame.pData
        stPixelConvertParam.nSrcDataLen = frame.frameInfo.size
        stPixelConvertParam.pDstBuf = pDstBuf
        stPixelConvertParam.nDstBufSize = nDstBufSize
        stPixelConvertParam.eDstPixelFormat = IMV_EPixelType.gvspPixelBGR8
        
        # Thực hiện chuyển đổi
        nRet = self.cam.IMV_PixelConvert(stPixelConvertParam)
        if nRet != IMV_OK:
            print("Image conversion failed!")
            return None
        # Chuyển đổi buffer thành OpenCV image
        rgbBuff = c_buffer(b'\0', nDstBufSize)
        memmove(rgbBuff, stPixelConvertParam.pDstBuf, nDstBufSize)
        colorByteArray = bytearray(rgbBuff)
        return np.array(colorByteArray).reshape(stPixelConvertParam.nHeight, stPixelConvertParam.nWidth, 3)

    def release_camera(self):
        """Dừng hoạt động và giải phóng camera"""
        if self.is_open:
            self.cam.IMV_StopGrabbing()
            self.cam.IMV_Close()
            self.cam.IMV_DestroyHandle()

            print("Camera released successfully.")


class Screen2(QMainWindow):
    error_signal2 = pyqtSignal(str)
    show_state_sig = pyqtSignal()
    show_Output = pyqtSignal()
    image_signal = pyqtSignal(object)  # Gửi ảnh (numpy array)
    def __init__(self):
        super(Screen2, self).__init__()
        loadUi("form_UI/screen2.ui", self)
        self.error_signal2.connect(self.show_error_message2)
        self.show_state_sig.connect(self.show_state)
        self.show_Output.connect(self.show_output_result)
        self.Bnt_Connect_Camera.clicked.connect(self.Connnect_Camera)
        self.image_signal.connect(self.load_image4)

        self.onMainFormLoad()
        self.Return_Fom1.triggered.connect(self.gotoScreen1)
        self.actionReturn_Form_Classification.triggered.connect(self.gotoScreen3)
        self.actionReturn_Form_Unsupervied.triggered.connect(self.gotoScreen4)
        self.actionForm_OCR.triggered.connect(self.gotoScreen5)
        self.actionLocation_Form.triggered.connect(self.gotoScreen6)

        
        self.Le_Exposure_Time.setText(str(self.exposure_time))
        self.comboBox_acceptance_threshold.setCurrentText(str(self.acceptance_threshold))
        self.DSpinBox_ZoomFacter.setValue(self.zoom_factor)
        self.Bnt_Quite.clicked.connect(self.exit_app)
        self.Bnt_Trigger.clicked.connect(self.Trigger_image)

        self.Bnt_Trigger_Continuous.clicked.connect(self.Trigger_Continous)
        self.actionLoad_Model_AI.triggered.connect(self.Load_Model)
        self.actionSave_Setting.triggered.connect(self.Save_Setting)
        self.radio_button.toggled.connect(self.handle_radio_button)
        self.actionDisconnect_Camera.triggered.connect(self.Disconnect_Camera)
        self.actionSelect_the_path_to_save_image.triggered.connect(self.select_save_path)
        self.actionOpen_Image.triggered.connect(self.Open_Image)
        self.Cb_Camera.setCurrentText(self.Camera_type)
        self.Action_Open.triggered.connect(self.open_file) # open folder
        self.image = None
        self.trigger_continous = True
        # Khởi tạo các luồng
        self.stop_threads= False #phải khởi tao trước khi khởi tạo luồng  
        self.lock_zoom_facter = True


        self.i=0
        self.Bnt_Trigger.setEnabled(False)
        self.Bnt_Trigger_Continuous.setEnabled(False)
        self.img_state= False
        self.open_model =False
        self.Button_is_clicked = False
        self.thickness2 =3
        self.previous_line_status =None
        self.result =None
        self.rotated_roi = None
        #self.save_path = ""
        self.camera_handler = CameraHandler()

        # Gán graphicsView từ UI vào
        self.graphicsView.setScene(QGraphicsScene(self))
        self.scene = self.graphicsView.scene()
        # Khởi tạo các thuộc tính
 
        # Kết nối các sự kiện vào methods của lớp này
        self.graphicsView.wheelEvent = self.wheelEvent


        record_folder = os.path.join(self.save_path, "Record")  # Tạo thư mục Record
        ok_folder = os.path.join(record_folder, "OK")
        ng_folder = os.path.join(record_folder, "NG")
        cropped_folder = os.path.join(record_folder, "Cropped")

        # Tạo thư mục Record trước, sau đó tạo các thư mục con bên trong
        os.makedirs(ok_folder, exist_ok=True)
        os.makedirs(ng_folder, exist_ok=True)
        os.makedirs(cropped_folder, exist_ok=True)
        ok_folder= ok_folder.replace("\\", "/")
        ng_folder= ng_folder.replace("\\", "/")
        cropped_folder= cropped_folder.replace("\\", "/")
        self.Camera_Trigger_Continous=False


        #self.SEGMENTATION_DEEPLEARING_TOOL =DEEP_LEARNING_SEGMENTATION()
        #self.Model_Seg = self.SEGMENTATION_DEEPLEARING_TOOL.Load_Model_Seg("best_seg.pt")
        #img3 = cv2.imread("Helix (2).png")
        #acceptance_threshold =0.2
        #Duplication_Threshold_Seg=0.2
        #img_graphic_Seg,boxes, scores,segmentation_contours_idx ,class_ids,text2 = self.SEGMENTATION_DEEPLEARING_TOOL.Prediction_Seg(img3,self.Model_Seg,acceptance_threshold,Duplication_Threshold_Seg)
        #boxes, scores,segmentation_contours_idx ,class_ids,text3 = self.SEGMENTATION_DEEPLEARING_TOOL.Prediction_Seg_None_Img(img3,self.Model_Seg,acceptance_threshold,Duplication_Threshold_Seg)
        #cv2.imwrite("img_graphic_Seg.bmp", img_graphic_Seg)

        #print("text2",text2)

        #self.CLASSIFICATION_DEEP_LEARNING_TOOL = DEEP_LEARNING_CLASSIFICATION()
        #self.Model3 = self.CLASSIFICATION_DEEP_LEARNING_TOOL.Load_Model_Cls("cake_cls.pt")
        #img4 = cv2.imread("Do (2).bmp")
        #img_graphic_Cls,Name_Cls1,Score_Cls1 = self.CLASSIFICATION_DEEP_LEARNING_TOOL.Prediction_Cls(img4,self.Model3)
        #Name_cls2,Score2 = self.CLASSIFICATION_DEEP_LEARNING_TOOL.Prediction_Cls_None_Img(img4,self.Model3)
        #print(Name_Cls1,Score_Cls1)
        #print(Name_cls2,Name_cls2)
        #cv2.imwrite("img_graphic_Cls.bmp", img_graphic_Cls)

       # self.UNSUPERVISED_DEEP_LEARNING_TOOL = UNSUPERVISED_DEEP_LEARNING()
        #self.Model_Uns = self.UNSUPERVISED_DEEP_LEARNING_TOOL.Load_Model_Uns("OCV5.th")
        #img = cv2.imread("NG (1).bmp")
        #self.acceptance_threshold_Uns=0.85
        #img_graphic_Uns,Name_cls_Uns1,Score_Uns1 =self.UNSUPERVISED_DEEP_LEARNING_TOOL.Prediction_UnS(img,self.Model_Uns,self.acceptance_threshold_Uns)
        #Name_cls_Uns2,Score_Uns2 =self.UNSUPERVISED_DEEP_LEARNING_TOOL.Prediction_UnS_None_Img(img,self.Model_Uns,self.acceptance_threshold_Uns)
        #cv2.imwrite("img_graphic_Uns.bmp", img_graphic_Uns)
        #print(Name_cls_Uns1,Score_Uns1)
        #print(Name_cls_Uns2,Score_Uns2)

        self.OCR_DEEP_LEARNING_TOOL=OCR_DEEP_LEARNING()
        self.Model_OCR= self.OCR_DEEP_LEARNING_TOOL.Load_Model_OCR("Ocr4.pt")
        #img_ocr = cv2.imread("NG (15).bmp")
        #acceptance_threshold_Ocr= 0.2
        #Duplication_Threshold_Ocr=0.4
        #row_threshold =20
        #img_graphic_Ocr,Box_Ocr1,Text1,_ = self.OCR_DEEP_LEARNING_TOOL.Prediction_OCR(img_ocr,self.Model_OCR,acceptance_threshold_Ocr,Duplication_Threshold_Ocr,row_threshold)
        #Box_Ocr2,Text2,Box_Point2 = self.OCR_DEEP_LEARNING_TOOL.Prediction_OCR_None_Img(img_ocr,self.Model_OCR,acceptance_threshold_Ocr,Duplication_Threshold_Ocr,row_threshold)
        #Box_Point1=[str(i),cx_str,cy_str,w_str,h_str,angle_deg_str ,confidence_str,label]
        #cv2.imwrite("img_graphic_OCR.bmp", img_graphic_Ocr)
        #print(Box_Ocr1)

        self.DEEP_LEARNING_lOCATION_TOOL =DEEP_LEARNING_lOCATION() 
        img_location = cv2.imread("OCR_DRB (308).bmp")
        self.Mode_Location = self.DEEP_LEARNING_lOCATION_TOOL.Load_Model_Loca("Location_OCR2.pth",img_location)# phải load trước khi preidiction
        acceptance_threshold_Loca= 0.2
        Duplication_Threshold_Loca=0.4
        img_graphic_Loca,Box_Point_Location1,=self.DEEP_LEARNING_lOCATION_TOOL.Prediction_Location(img_location,self.Mode_Location,acceptance_threshold_Loca,Duplication_Threshold_Loca)
        #Box_Point_Location2 =self.DEEP_LEARNING_lOCATION_TOOL.Prediction_Location_None_Img(img_location,self.Mode_Location,acceptance_threshold_Loca,Duplication_Threshold_Loca)
        self.i=0
        #cv2.imwrite("img_graphic_Loca2.bmp", img_graphic_Loca)
        # thong so Box_Point_Location2=[id,x,y,w,h,angle,score,[(x1),(x2),(x3),(x4)]]
       # for box in Box_Point_Location2:
            #ROI=box[7]
            #id =box[0]
            #angle = float(box[6])
            #images_ROI=self.DEEP_LEARNING_lOCATION_TOOL.Get_Rotation_Image(img_location,ROI,angle)
            #imag_Name =f"{id}_image.bmp"
            #label_\
            # cv2.imwrite(imag_Name , images_ROI)


    def crop_rotated_rect(self,image , x, y, w, h, angle, save_path):

        # Tạo RotatedRect
        rect = ((x, y), (w, h), angle)

        # Lấy ma trận biến đổi (xoay + dịch)
        box = cv2.boxPoints(rect)
        box = box.astype(np.int32)# trên 1.24 ver
        #box = np.int0(box)# dươi 1.24ver
        # Tạo ma trận xoay quanh tâm
        M = cv2.getRotationMatrix2D((x, y), angle, 1.0)
        # Xoay toàn bộ ảnh theo tâm
        rotated = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

        # Sau khi xoay, crop vùng cần thiết (tâm giữ nguyên)
        cropped = cv2.getRectSubPix(rotated, (int(w), int(h)), (x, y))
        # Lưu ảnh
        cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)# xoay ngược chiều kim đồng hồ 90
        #cropped = cv2.rotate(cropped, cv2.ROTATE_90_CLOCKWISE)# xoay cùng chiều kim đồng hồ 90
        #cv2.imwrite(save_path, cropped)
        return cropped,box


    def select_save_path(self):
        try:
            # Hàm chọn đường dẫn lưu ảnh
            folder_path = QFileDialog.getExistingDirectory(None, "Chọn đường dẫn lưu ảnh")
            if folder_path:
                self.save_path = folder_path
                # Kiểm tra và tạo thư mục "OK" và "NG" nếu không tồn tại
                record_folder = os.path.join(self.save_path, "Record")  # Tạo thư mục Record
                ok_folder = os.path.join(record_folder, "OK")
                ng_folder = os.path.join(record_folder, "NG")
                cropped_folder = os.path.join(record_folder, "Cropped")

                # Tạo thư mục Record trước, sau đó tạo các thư mục con bên trong
                os.makedirs(ok_folder, exist_ok=True)
                os.makedirs(ng_folder, exist_ok=True)
                os.makedirs(cropped_folder, exist_ok=True)
                ok_folder= ok_folder.replace("\\", "/")
                ng_folder= ng_folder.replace("\\", "/")
                cropped_folder= cropped_folder.replace("\\", "/")
                QMessageBox.information(None, "Thông báo", f"Đường dẫn được chọn: {cropped_folder}")
            else:
                QMessageBox.warning(None, "Thông báo", "Bạn chưa chọn đường dẫn!")
        except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
            self.error_signal2.emit(str(e))
            
    def handle_radio_button(self, checked):
        try:
            if checked:  # Nếu được tick
                self.Bnt_Trigger_Continuous.setEnabled(False)
                self.Bnt_Trigger.setEnabled(False)
                self.actionLoad_Model_AI.disconnect()
                self.actionSave_Setting.disconnect() 
                self.actionSelect_the_path_to_save_image.disconnect()          
                self.on_checked()
            else:  # Nếu không được tick
                self.stop_threads2 = True
                self.Bnt_Trigger_Continuous.setEnabled(True)
                self.Bnt_Trigger.setEnabled(True)
                self.actionLoad_Model_AI.triggered.connect(self.Load_Model)
                self.actionSave_Setting.triggered.connect(self.Save_Setting)

                self.actionSelect_the_path_to_save_image.triggered.connect(self.select_save_path)

        except Exception as e: 
            self.error_signal2.emit(str(e))
    def on_checked(self):
        self.stop_threads2 = False
        self.thread3 = threading.Thread(target=self.run_function_3)
        self.thread3.start()# bat sau chay luon
    def run_function_2(self):
        try:
            while not self.stop_threads:
                if not self.trigger_continous:
                    #print("threa1")
                    self.Trigger_image2()
                    time.sleep(0.002) 
        except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
            self.error_signal2.emit(str(e))
    def run_function_3(self):
        try:
            while not self.stop_threads2:
                    try:
                        selected_camera = self.Cb_Camera.currentText()
                        if selected_camera =='Basler':
                            self.cam.LineSelector.SetValue('Line1')  # Chọn Line 1
                            self.cam.LineMode.SetValue('Input')
                            self.cam.LineStatus.GetValue()  
                            line_status = self.cam.LineStatus.GetValue()
                            self.show_state_sig.emit()# HIỆN TRẠNG THÁI INPUT TRIGGER
                            if line_status and self.img_state:
                                if not self.previous_line_status : # khi doi trang thai ma xu ly anh xong
                                    #print(line_status)
                                    self.Trigger_image()
                            time.sleep(0.002)
                            self.previous_line_status = line_status 
                        if selected_camera =='Irayple':
                            line_status = self.camera_handler.io_camera2()
                            self.show_state_sig.emit()# HIỆN TRẠNG THÁI INPUT TRIGGER
                            if line_status and self.img_state:                               
                                if not self.previous_line_status : # khi doi trang thai ma xu ly anh xong
                                    #print(line_status)
                                    self.Trigger_image()
                            time.sleep(0.002)
                            self.previous_line_status = line_status                         
                    except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
                        self.error_signal2.emit(str(e))
                        self.stop_threads2 =True
        except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
            self.error_signal2.emit(str(e))
    def close_thread(self):
        try:
            self.stop_threads =True
            self.stop_threads2 = True
            self.camera_handler.release_camera()
            selected_camera = self.Cb_Camera.currentText()
            if selected_camera =='Basler':
                self.cam.StopGrabbing()
                self.cam.Close()  
                print("Basler Close")
        except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
            self.error_signal2.emit(str(e))
        #print("đã thoát luồng trong sreeen2 ")
    def Disconnect_Camera(self):
        try:
            selected_camera = self.Cb_Camera.currentText()
            self.stop_threads =True # dừng luồng trigger continous
            if selected_camera =='Basler':           
                self.cam.StopGrabbing()
                self.cam.Close()   
                self.Bnt_Connect_Camera.setText("Connect Camera") 
                self.Bnt_Connect_Camera.setStyleSheet(
                    "background-color: white;"       # Màu nền trắng
                    "color: black;"                  # Màu chữ đen
                    "font-size: 10pt;"               # Kích thước font chữ
                    "border: none;"                  # Không có viền (tùy chọn)
                    "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                        # Căn chữ giữa cả ngang và dọc
                )  
                self.Bnt_Trigger.setEnabled(False)  
                self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                self.Bnt_Trigger_Continuous.setEnabled(False)
                self.stop_threads =True
            elif selected_camera =='Irayple': 
                self.camera_handler.release_camera()
                self.Bnt_Connect_Camera.setText("Connect Camera") 
                self.Bnt_Connect_Camera.setStyleSheet(
                    "background-color: white;"       # Màu nền trắng
                    "color: black;"                  # Màu chữ đen
                    "font-size: 10pt;"               # Kích thước font chữ
                    "border: none;"                  # Không có viền (tùy chọn)
                    "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                        # Căn chữ giữa cả ngang và dọc
                )  
                self.Bnt_Trigger.setEnabled(False)  
                self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                self.Bnt_Trigger_Continuous.setEnabled(False)
                self.stop_threads =True
        except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
            self.error_signal2.emit(str(e))
    def show_error_message2(self, error_message):
        # Hiển thị hộp thoại lỗi với nội dung từ error_message
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(f"An error occurred: {error_message}")
        msg_box.exec()
    def show_state(self):
        selected_camera = self.Cb_Camera.currentText()
        if selected_camera =='Basler':
            self.cam.LineSelector.SetValue('Line1')  # Chọn Line 1
            self.cam.LineMode.SetValue('Input')
            self.cam.LineStatus.GetValue()  
            line_status = self.cam.LineStatus.GetValue()
            if line_status:
                self.La_Input.setStyleSheet("""
                QLabel {
                    border: 1px solid black;
                    color: black; 
                    background-color: rgb(0, 255, 0);  /* green */
                    border-radius: 8px;
                    font: 700 12pt "Arial";
                }
                """)
            else:
                self.La_Input.setStyleSheet("""
                QLabel {
                    border: 1px solid black;
                    color: black; 
                    background-color: rgb(255, 255, 255);  
                    border-radius: 8px;
                    font: 700 12pt "Arial";
                }
                                            """) 
        if selected_camera =='Irayple':
            line_status = self.camera_handler.io_camera2()
            if line_status:
                self.La_Input.setStyleSheet("""
                QLabel {
                    border: 1px solid black;
                    color: black; 
                    background-color: rgb(0, 255, 0);  /* green */
                    border-radius: 8px;
                    font: 700 12pt "Arial";
                }
                """)
            else:
                self.La_Input.setStyleSheet("""
                QLabel {
                    border: 1px solid black;
                    color: black; 
                    background-color: rgb(255, 255, 255);  
                    border-radius: 8px;
                    font: 700 12pt "Arial";
                }
                                            """) 

    def show_output_result(self):
        try:
            if self.img_state:
                selected_camera = self.Cb_Camera.currentText()
                if selected_camera =='Basler':
                    # Đặt màu nền thành xanh (True)
                    self.La_OutPut.setStyleSheet("""
                    QLabel {
                        border: 1px solid black;
                        color: black; 
                        background-color: rgb(0, 255, 0);  /* xanh */
                        border-radius: 8px;
                        font: 700 12pt "Arial";
                    }
                    """)
                    # Đặt output thành True
                    self.cam.UserOutputValue.SetValue(True)
                    # Hủy Timer cũ nếu tồn tại
                    if hasattr(self, 'timer_output') and self.timer_output.isActive():
                        self.timer_output.stop()
                    if hasattr(self, 'timer_color') and self.timer_color.isActive():
                        self.timer_color.stop()
                    # Tạo Timer để reset UserOutputValue thành False sau 500ms
                    self.timer_output = QTimer()
                    self.timer_output.setSingleShot(True)
                    self.timer_output.timeout.connect(lambda: self.cam.UserOutputValue.SetValue(False))
                    self.timer_output.start(1000)  # Reset output False sau 1000ms

                    # Tạo Timer khác để chuyển màu về trắng sau 1 giây
                    self.timer_color = QTimer()
                    self.timer_color.setSingleShot(True)
                    self.timer_color.timeout.connect(lambda: self.La_OutPut.setStyleSheet("""
                        QLabel {
                            border: 1px solid black;
                            color: black; 
                            background-color: rgb(255, 255, 255);  /* trắng */
                            border-radius: 8px;
                            font: 700 12pt "Arial";
                        }
                    """))
                    self.timer_color.start(1000)  # Reset màu sau 1 giây
                if selected_camera =='Irayple':   
                    # Đặt màu nền thành xanh (True)
                    self.La_OutPut.setStyleSheet("""
                    QLabel {
                        border: 1px solid black;
                        color: black; 
                        background-color: rgb(0, 255, 0);  /* xanh */
                        border-radius: 8px;
                        font: 700 12pt "Arial";
                    }
                    """)
                    # Đặt output thành True
                    self.camera_handler.io_camera(True)# xuất điên áp âm lên chân số 4 cam 
                    # Hủy Timer cũ nếu tồn tại
                    if hasattr(self, 'timer_output') and self.timer_output.isActive():
                        self.timer_output.stop()
                    if hasattr(self, 'timer_color') and self.timer_color.isActive():
                        self.timer_color.stop()
                    # Tạo Timer để reset UserOutputValue thành False sau 500ms
                    self.timer_output = QTimer()
                    self.timer_output.setSingleShot(True)
                    self.timer_output.timeout.connect(lambda: self.camera_handler.io_camera(False))
                    self.timer_output.start(1000)  # Reset output sau 500ms

                    # Tạo Timer khác để chuyển màu về trắng sau 1 giây
                    self.timer_color = QTimer()
                    self.timer_color.setSingleShot(True)
                    self.timer_color.timeout.connect(lambda: self.La_OutPut.setStyleSheet("""
                        QLabel {
                            border: 1px solid black;
                            color: black; 
                            background-color: rgb(255, 255, 255);  /* trắng */
                            border-radius: 8px;
                            font: 700 12pt "Arial";
                        }
                    """))
                    self.timer_color.start(1000)  # Reset màu sau 1 giây   
        except Exception as e:  # Bắt và xử lý ngoại lệ cho bất kỳ lỗi nào xảy ra
            self.error_signal2.emit(str(e))
    def Connnect_Camera(self):
        try:
            selected_camera = self.Cb_Camera.currentText()
            if selected_camera =='Basler':
                # khai bao camera 
                #self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
                self.maxCamerasToUse = 1
                self.converter = pylon.ImageFormatConverter()
                self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
                self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
                self.camera_on = False 
                self.tlFactory = pylon.TlFactory.GetInstance()
                self.devices = self.tlFactory.EnumerateDevices()

                self.camera = pylon.InstantCameraArray(min(len(self.devices), self.maxCamerasToUse))
                self.cam = pylon.InstantCamera(self.tlFactory.CreateDevice(self.devices[0]))
                self.cam.Open()
                self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                self.cam.ExposureTimeAbs.SetValue(self.exposure_time)
                self.cam.LineSelector.SetValue('Line1')  # Chọn Line 1
                self.cam.LineMode.SetValue('Input')
                self.cam.LineStatus.GetValue()                        
                grab_result = self.cam.RetrieveResult(4000, pylon.TimeoutHandling_ThrowException)
                if grab_result.GrabSucceeded():
                    img = self.converter.Convert(grab_result).GetArray()  
                    self.img2 =img
                    self.Bnt_Connect_Camera.setText("Connected") 
                    self.Bnt_Connect_Camera.setStyleSheet(
                        "background-color: green;"       # Màu nền xanh
                        "color: black;"                  # Màu chữ đen
                        "font-size: 10pt;"               # Kích thước font chữ
                        "border: none;"                  # Không có viền (tùy chọn)
                        "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                        # Căn chữ giữa cả ngang và dọc
                    )   
                    self.Bnt_Trigger.setEnabled(True)    
                    self.Bnt_Trigger_Continuous.setEnabled(True)
                    self.img_state= True  
            if selected_camera =='Irayple':
                self.camera_handler.initialize_camera()
                self.camera_handler.configure_camera()    
                img=self.camera_handler.capture_frame()  
                if img is not None:
                    self.Bnt_Connect_Camera.setText("Connected") 
                    self.Bnt_Connect_Camera.setStyleSheet(
                        "background-color: green;"       # Màu nền xanh
                        "color: black;"                  # Màu chữ đen
                        "font-size: 10pt;"               # Kích thước font chữ
                        "border: none;"                  # Không có viền (tùy chọn)
                        "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                        # Căn chữ giữa cả ngang và dọc
                    )   
                    self.Bnt_Trigger.setEnabled(True)    
                    self.Bnt_Trigger_Continuous.setEnabled(True)
                    self.img_state= True       
        except  Exception as e:
            self.error_signal2.emit(str(e))

    def AI_Test(self,img):# cho camera basler
        try:           
            self.cam.LineSelector.SetValue('Out1')# Pin 4 
            self.cam.LineMode.SetValue('Output')# set pin 4 is output 
            model=self.model
            self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
            img2 =img
            image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
            self.image=image
            self.image_height,self.image_width,_=image.shape
            height2, width2, channels = image.shape                              
            results = model(img2)
            for result in results:
                boxes = result.boxes.xyxy
                scores = result.boxes.conf
                label =result.boxes.cls    # cls, (N, 1)
                if len(boxes) > 0:
                    self.result =False
                    segmentation_contours_idx = [np.array(seg, dtype=np.int32) for seg in result.masks.xy]
                    class_ids = np.array(result.boxes.cls.cpu(), dtype="int")
                    for box, score, seg,class_id in zip(boxes, scores,segmentation_contours_idx ,class_ids):
                        x1, y1, x2, y2 = box
                        confidence = score.item()
                        class_id = class_id.item()
                        class_name = result.names.get(class_id, 'Unknown')
                        text = f"{class_name}:{confidence:.1f}"
                        seg = seg + np.array([0, 0])# thêm tọa độ của ROI (Roi_x1 và Roi_y1) vào contour seg để chuyển đổi tọa độ về tọa độ trên ảnh gốc
                        
                        if confidence > self.acceptance_threshold:
                                text2 ="NG"
                                cv2.putText(img, text2, (20,180), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 0, 255), 15)
                                x1, y1, x2, y2 = box[:4]
                                if self.checkBox.isChecked():
                                    cv2.putText(img, text, (int(x2)+5, int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), self.thickness2)
                                if self.checkBox_2.isChecked():
                                    cv2.fillPoly(img, [seg], (0,0,255))#dien day foly gon
                                if self.checkBox_4.isChecked():
                                    cv2.polylines(img, [seg], True, (0, 0, 255), 4)

                    self.cam.UserOutputValue.SetValue(True)  # Đặt trạng thái của Out1 là True
                    self.show_Output.emit()# câp nhật tín hiệu ở một sự kiện mà không sử dụng chung luồng đang xử lý  hoặc  luồng UI
                else:
                    text2 ="OK"
                    self.result =True
                    cv2.putText(img, text2, (20,180), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 255, 0), 15)
                    self.cam.UserOutputValue.SetValue(False)  # Đặt trạng thái của Out1 là True
                    self.show_Output.emit()# câp nhật tín hiệu ở một sự kiện mà không sử dụng chung luồng đang xử lý  hoặc  luồng UI
        except  Exception as e:
            self.error_signal2.emit(str(e))
    def AI_Test2(self,img):# cho camera irayple
        try:           
            model=self.model
            self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
            img2 =img
            image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
            self.image=image
            self.image_height,self.image_width,_=image.shape
            #height2, width2, channels = image.shape                              
            results = model(img2)
            for result in results:
                boxes = result.boxes.xyxy
                scores = result.boxes.conf
                label =result.boxes.cls    # cls, (N, 1)
                if len(boxes) > 0:
                    self.result =False
                    segmentation_contours_idx = [np.array(seg, dtype=np.int32) for seg in result.masks.xy]
                    class_ids = np.array(result.boxes.cls.cpu(), dtype="int")
                    #label2 =  class_id.item()
                    for box, score, seg,class_id in zip(boxes, scores,segmentation_contours_idx ,class_ids):
                        x1, y1, x2, y2 = box
                        confidence = score.item()
                        class_id = class_id.item()
                        class_name = result.names.get(class_id, 'Unknown')
                        text = f"{class_name}:{confidence:.1f}"
                        seg = seg + np.array([0, 0])# thêm tọa độ của ROI (Roi_x1 và Roi_y1) vào contour seg để chuyển đổi tọa độ về tọa độ trên ảnh gốc
                        if confidence > self.acceptance_threshold:
                                text2 ="NG"
                                cv2.putText(img, text2, (20,180), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 0, 255), 15)
                                x1, y1, x2, y2 = box[:4]
                                if self.checkBox.isChecked():
                                    cv2.putText(img, text, (int(x2)+5, int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), self.thickness2)
                                if self.checkBox_2.isChecked():
                                    cv2.fillPoly(img, [seg], (0,0,255))#dien day foly gon
                                if self.checkBox_4.isChecked():
                                    cv2.polylines(img, [seg], True, (0, 0, 255), 4)
                                
                    self.camera_handler.io_camera(True)# xuất điên áp âm lên chân số 4 cam 
                    self.show_Output.emit()# câp nhật tín hiệu ở một sự kiện mà không sử dụng chung luồng đang xử lý  hoặc  luồng UI

                else:
                    text2 ="OK"
                    self.result =True
                    self.camera_handler.io_camera(False) # ngắt điên áp âm lên chân số 4 cam 
                    cv2.putText(img, text2, (20,180), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 255, 0), 15)
                    self.show_Output.emit()# câp nhật tín hiệu ở một sự kiện mà không sử dụng chung luồng đang xử lý  hoặc  luồng UI
        except  Exception as e:
            self.error_signal2.emit(str(e))

    def gotoScreen1(self):
        widget.setCurrentIndex(0)  # Move back to MainWindow in the stack
        if not widget.isFullScreen():  # Only resize if not in fullscreen mode
            widget.setSizeBasedOnForm()
    def gotoScreen3(self):
        widget.setCurrentIndex(2)  # Move back to MainWindow in the stack
        if not widget.isFullScreen():  # Only resize if not in fullscreen mode
            widget.setSizeBasedOnForm()
    def gotoScreen4(self):
        widget.setCurrentIndex(3)  # Move back to MainWindow in the stack
        if not widget.isFullScreen():  # Only resize if not in fullscreen mode
            widget.setSizeBasedOnForm()
    def gotoScreen5(self):
        widget.setCurrentIndex(4)  # Move to Screen2 in the stack
        if not widget.isFullScreen():  # Only resize if not in fullscreen mode
            widget.setSizeBasedOnForm()
    def gotoScreen6(self):
        widget.setCurrentIndex(5)  # Move to Screen2 in the stack
        if not widget.isFullScreen():  # Only resize if not in fullscreen mode
            widget.setSizeBasedOnForm()

    def onMainFormLoad(self):
        self.loadSettings()

    def loadSettings(self):
        try:

            filename = 'savesetting.csv'
            with open(filename, 'r') as csvfile:
                reader = csv.reader(csvfile)
                row = next(reader)  # Đọc dòng đầu tiên
                # Gán giá trị vào biến
                self.acceptance_threshold = float(row[0])
                self.exposure_time  = int(row[1]) 
                self.zoom_factor    = float(row[2]) 
                self.model_path     = str(row[3])  
                self.Camera_type    = str(row[4])
                self.save_path      = str(row[5])

                self.model = YOLO(self.model_path)
                img = np.zeros((160, 200, 3), dtype=np.uint8)#tao ra mot anh 
                image2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.model(image2)
            transform = QTransform()
            transform.scale(self.zoom_factor, self.zoom_factor)  # Phóng to gấp 2 lần theo cả hai chiều
            self.graphicsView.setTransform(transform)
            print("Settings loaded successfully.")
        except  Exception as e:
            self.error_signal2.emit(str(e))
            exit()
    def ChecK_Value(self):
        try:
            self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
            self.zoom_factor = self.DSpinBox_ZoomFacter.value()
            self.exposure_time         = int(self.Le_Exposure_Time.text())
            self.Camera_type = str(self.Cb_Camera.currentText())

            return True
        except ValueError as e:  
            self.error_signal.emit(str(e))
            return False
                
    def Save_Setting(self):
        try:
            value= self.ChecK_Value()
            if value:
                transform = QTransform()
                transform.scale(self.zoom_factor, self.zoom_factor)  # Phóng to gấp 2 lần theo cả hai chiều
                self.graphicsView.setTransform(transform)
                filename = 'savesetting.csv'
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # Ghi giá trị vào dòng
                    writer.writerow([self.acceptance_threshold,self.exposure_time,self.zoom_factor,self.model_path,self.Camera_type,self.save_path])   
        except  Exception as e:
            self.error_signal2.emit(str(e))

    def extract_key(self,file_name):
        match = re.match(r"(.+?)\s*\((\d+)\)", file_name)
        if match:
            name_part = match.group(1).strip().lower()
            number_part = int(match.group(2))
            return (name_part, number_part)
        else:
            return (file_name.lower(), 0)
        
    def open_file(self):
        # Mở hộp thoại để chọn thư mục
        try:
            folder_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh")
            if folder_path:
                # Đọc tất cả các ảnh trong thư mục
                self.foldel_images =folder_path

                image_list = []
                files = sorted(os.listdir(folder_path), key=self.extract_key)
                for file_name in files:
                    file_path = os.path.join(folder_path, file_name)
                    # Kiểm tra xem file có phải là ảnh không (đuôi jpg, png, ...)
                    if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        image = cv2.imread(file_path)
                        if image is not None:
                            image_list.append(image)
                            self.image_3 = image
                            height, width, _ = image.shape
                            self.height = height
                            self.width = width
                
                # Kiểm tra xem danh sách ảnh có trống không
                if not image_list:
                    raise ValueError("Thư mục không chứa ảnh hợp lệ.")
                
                self.open_folder_images = True
                # Tạo một ảnh màu trắng với kích thước như ảnh đầu tiên
                self.white_image = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
                self.La_Munber_Image.setText(str(len(image_list)))
                self.display_images_in_scroll_area(folder_path)
        except ValueError as e:  
            self.error_signal.emit(str(e))
    def display_images_in_scroll_area(self, folder_path):
        # Tạo widget để chứa ảnh
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Đọc tất cả các ảnh trong thư mục và sắp xếp theo kích thước (từ nhỏ đến lớn)
        images_fomr3 = []
        files = sorted(os.listdir(folder_path), key=self.extract_key)
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                image = cv2.imread(file_path)
                if image is not None:
                    height, width, _ = image.shape
                    images_fomr3.append((file_name, image, width * height))  # Thêm tên ảnh, ảnh và kích thước vào danh sách

        # Sắp xếp danh sách ảnh theo kích thước từ bé đến lớn
        images_fomr3.sort(key=lambda x: x[2])

        # Hiển thị từng ảnh trong QLabel và thêm vào layout
        for file_name, image, _ in images_fomr3:
            image_copy=image.copy()
            height,width,_=image_copy.shape
            scale = height/width
           # width_img =int(100*scale)
            height_img = int(235*scale)

            resized_image = cv2.resize(image, (235 ,height_img))
            label = QLabel(self)
            label.setObjectName(file_name)
            qimage = self.convert_cv_qt(resized_image)
            pixmap = QPixmap.fromImage(qimage)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Thêm khung viền đen
            label.setStyleSheet("border: 4px solid green;")
            
            # Lưu thông tin file và hình ảnh dưới dạng thuộc tính của QLabel
            label.image_form3 = image_copy  # Gán ảnh vào QLabel
            label.file_name_form3  = file_name  # Gán tên file vào QLabel

        # Tạo hàm xử lý sự kiện cho từng label
            label.mousePressEvent = lambda event, lbl=label: self.label_clicked_form3(lbl)
            # Thêm QLabel vào layout
            layout.addWidget(label)
        # Đặt widget vào ScrollArea
        self.scrollArea_2.setWidget(widget)

    def convert_cv_qt(self, cv_img):
        """Chuyển đổi ảnh OpenCV sang QImage để hiển thị trong QLabel"""
        height, width, channel = cv_img.shape
        bytes_per_line = channel * width
        qimg = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        return qimg.rgbSwapped()  # Đảo màu RGB sang BGR
    def label_clicked_form3(self, label):
        try:
            """Hàm này sẽ được gọi khi nhấn vào ảnh"""
            if not self.Camera_Trigger_Continous:
                for item in self.scene.items():
                    if isinstance(item, QGraphicsRectItem):
                        self.scene.removeItem(item)
                    if isinstance(item, QGraphicsPolygonItem):
                        self.scene.removeItem(item)
                    if isinstance(item, QGraphicsLineItem):
                        self.scene.removeItem(item)
                    if isinstance(item, QGraphicsTextItem):
                        self.scene.removeItem(item)                 
                image = label.image_form3   # Truy xuất ảnh từ QLabel
                file_name = label.file_name_form3   # Truy xuất tên file từ QLabel

                if hasattr(self, 'file_name'):
                        self.previous_file_name = self.file_name
                        #print(self.previous_file_name)
                self.file_name=file_name
                image_copy2      =image.copy()
                image_copy3      =image.copy() 
                self.image_copy4 =image.copy()         
                self.image_copy2 =image_copy2
                self.image7      =image_copy2      
                # Lấy tên file ảnh (không bao gồm phần mở rộng)
                self.Labe_file_name.setText(str(self.file_name))
                # Kết nối combobox để gán tên đối tượng cho ảnh
                label_text = None

                width,hieght,_=image_copy3.shape
                x=int((width/20)*15)
                y=int((hieght/20)*1)
                font_string =int(width/550)
                thickness =int(width/190)
                # Nếu có nhãn, vẽ nhãn lên ảnh
                image_copy4=image_copy3.copy()

                #arr,boxes, scores,segmentation_contours_idx ,class_ids,text2 = self.SEGMENTATION_DEEPLEARING_TOOL.Prediction(image_copy3)
                
                #Name_cls,Score =self.UNSUPERVISED_DEEP_LEARNING_TOOL.Prediction_None_Img(image_copy3)
                #self.acceptance_threshold_Uns=0.85
                #Name_cls_Uns2,Score_Uns2 =self.UNSUPERVISED_DEEP_LEARNING_TOOL.Prediction_UnS_None_Img(image_copy3,self.Model_Uns,self.acceptance_threshold_Uns)                    
                #print(Name_cls_Uns2,Score_Uns2)
                start_time= time.time()
                acceptance_threshold_Loca= 0.2
                Duplication_Threshold_Loca=1.0
                img_graphic_Loca,Box_Point_Location1,=self.DEEP_LEARNING_lOCATION_TOOL.Prediction_Location(image_copy4,self.Mode_Location,acceptance_threshold_Loca,Duplication_Threshold_Loca)
                for box in Box_Point_Location1:
                    _,x,y,w,h,angle,_,_  =box  
                    self.i=self.i+1           
                    img_Name =f"{self.i}_OCR.bmp"
                    img_crop,box=self.crop_rotated_rect(image_copy4 , int(x), int(y), 400, 700, int(angle), img_Name)
                    acceptance_threshold_Ocr= 0.2
                    Duplication_Threshold_Ocr=0.4
                    row_threshold =20
                    _,Text2,_ = self.OCR_DEEP_LEARNING_TOOL.Prediction_OCR_None_Img(img_crop,self.Model_OCR,acceptance_threshold_Ocr,Duplication_Threshold_Ocr,row_threshold)
                    #print(box)
                    #print(Text2)
                    OCR_Text=Text2
                    text_item3 = QGraphicsTextItem(OCR_Text)# show test Ai
                    text_item3.setDefaultTextColor(QColor(255, 255, 0))
                    font = QFont()
                    font.setPointSize(int(width / 80))
                    text_item3.setFont(font)
                    text_item3.setPos(int(x),int(y))
                    text_item3.setRotation(0)
                    #self.scene.addItem(text_item3)  
                    text_item3.setZValue(1)  # Đảm bảo text luôn nằm trên ảnh
                    self.scene.addItem(text_item3)  
                    # Tạo polygon
                    points = [QPointF(p[0], p[1]) for p in box]
                    polygon = QPolygonF(points)
                    # Tạo đối tượng đồ họa
                    box_item = QGraphicsPolygonItem(polygon)
                    pen5 = QPen(QColor(0, 255, 0))  # Màu xanh lá cây
                    # Tạo viền dày 8px với màu xanh
                    pen5.setWidth(int(width/140))  # Độ dày viền
                    box_item.setPen(pen5)
                    box_item.setZValue(1)  # Đảm bảo text luôn nằm trên ảnh
                    # Thêm vào scene
                    self.scene.addItem(box_item)                   


                end_time = time.time()
                self.load_image3(img_graphic_Loca)
                
                height, width, _ = image_copy3.shape
                image_dimension = f"{height} x {width}"
                self.Label_Dimention_Images.setText(image_dimension)
                processing_time = (end_time - start_time)*1000
                processing_time = f"{processing_time:.1f}ms"
                self.La_cycle_time.setText(processing_time)

        except Exception as e:
            self.error_signal2.emit(str(e))
    def Load_Model(self):
        try:
            model_path2, _ = QFileDialog.getOpenFileName(
            None,  # Không cần truyền đối tượng QWidget ở đây
            "choose model",
            "",
            "Model files (*.pt);;All Files (*)"
            )
            if model_path2 and self.img_state:
                self.model_path = model_path2  
                self.model = YOLO(self.model_path)
                img = np.zeros((160, 200, 3), dtype=np.uint8)#tao ra mot anh 
                image2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self.model(image2)
                
            else:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"Please trigger an image file before selecting a Model!")
                msg_box.exec()  
        except Exception as e:
            self.error_signal2.emit(str(e))

    
    def Trigger_Continous(self):
        try:
            if not self.Button_is_clicked:
                # Chỉ thay đổi màu nền mà không ảnh hưởng đến font chữ
                self.stop_threads = False

                
                self.thread2 = threading.Thread(target=self.run_function_2)
                self.thread2.start()# bat sau chay luon
                self.Bnt_Trigger_Continuous.setStyleSheet("background-color: green; font-size: 10pt;")
                self.Button_is_clicked = True  # Cập nhật trạng thái
                self.trigger_continous = False
                self.lock_zoom_facter = False
                self.Bnt_Trigger.setEnabled(False)
            else:
                # Xóa màu nền để trở về trạng thái mặc định mà không thay đổi font chữ
                self.Camera_Trigger_Continous=False
                self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                self.Button_is_clicked = False  # Cập nhật trạng thái
                self.trigger_continous = True
                self.stop_threads = True
                self.lock_zoom_facter = True
                self.Bnt_Trigger.setEnabled(True)
        except Exception as e:
            self.error_signal2.emit(str(e))

    def Trigger_image(self):# cho xu ly AI#  su ly anh don camera 
            try:
                for item in self.scene.items():
                    if isinstance(item, QGraphicsRectItem):
                        self.scene.removeItem(item)
                    if isinstance(item, QGraphicsPolygonItem):
                        self.scene.removeItem(item)
                    if isinstance(item, QGraphicsLineItem):
                        self.scene.removeItem(item)
                    if isinstance(item, QGraphicsTextItem):
                        self.scene.removeItem(item)  
                selected_camera = self.Cb_Camera.currentText()
                i= 0
                if selected_camera =='Basler':
                    start_time = time.time()
                    self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
                    self.exposure_time = int(self.Le_Exposure_Time.text())
                    self.cam.ExposureTimeAbs.SetValue(self.exposure_time)
                    grab_result = self.cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if grab_result.GrabSucceeded():
                        img = self.converter.Convert(grab_result).GetArray()  
                        img_save = img.copy()
                        img2= img
                        #img2 =cv2.resize(img  , (1280,1280), interpolation=cv2.INTER_LINEAR)
                        if self.model_path:
                            self.AI_Test(img2)
                        height,width,_ = img2.shape
                        end_time = time.time()
                        processing_time = (end_time - start_time)*1000
                        processing_time = f"{processing_time:.1f} ms"
                        self.image_signal.emit(img)
                        self.La_cycle_time.setText(processing_time)
                        image_dimension = f"{height} x {width}"
                        self.Label_Dimention_Images.setText(image_dimension)
                        if self.save_path  and self.checkBox_5.isChecked():
                            # Tạo tên file dựa trên thời gian hiện tại
                            current_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")  # Định dạng: ngày_tháng_năm_giờ_phút_giây
                            image_name = f"{current_time}.jpg"  # Thêm đuôi .jpg
                            ok_folder = os.path.join(self.save_path, "OK")
                            image_path = os.path.join(ok_folder, image_name)

                            record = os.path.join(self.save_path, "Record")       
                            ok_folder = os.path.join(record, "OK")
                            ng_folder = os.path.join(record, "NG")
                            ok_folder = ok_folder.replace("\\", "/")
                            ng_folder = ng_folder.replace("\\", "/")


                            if self.result and self.Cb_Save_image_Mode.currentText() == "Both":
                                image_name = f"OK_{current_time}.bmp"  
                                image_path = os.path.join(ok_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            elif  not self.result and self.Cb_Save_image_Mode.currentText() == "Both":
                                image_name = f"NG_{current_time}.bmp"  
                                image_path = os.path.join(ng_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            elif self.result and self.Cb_Save_image_Mode.currentText() == "OK":
                                image_name = f"OK_{current_time}.bmp"  
                                image_path = os.path.join(ok_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            elif  not self.result and self.Cb_Save_image_Mode.currentText() == "NG":
                                image_name = f"NG_{current_time}.bmp"  
                                image_path = os.path.join(ng_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            if self.save_path  and self.checkBox_within_template.isChecked() or self.checkBox_Template.isChecked() and self.rotated_roi is not None:
                                img2= self.Get_ROI3(img)   
                        self.image7= img.copy()
                        end_time = time.time()
                        processing_time = (end_time - start_time)*1000
                        processing_time = f"{processing_time:.1f} ms"
                        #self.setImage(img2) 
                        self.load_image2(img2)
                        self.La_cycle_time.setText(processing_time)
                        image_dimension = f"{height} x {width}"
                        self.Label_Dimention_Images.setText(image_dimension) 
                        grab_result.Release()# giả phóng buffer
   

                    else:
                        self.Bnt_Connect_Camera.setText("Connect Camera") 
                        self.Bnt_Connect_Camera.setStyleSheet(
                            "background-color: white;"       # Màu nền xanh
                            "color: black;"                  # Màu chữ đen
                            "font-size: 10pt;"               # Kích thước font chữ
                            "border: none;"                  # Không có viền (tùy chọn)
                            "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                            # Căn chữ giữa cả ngang và dọc
                        )   
                        self.Bnt_Trigger.setEnabled(False)  
                        self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                        self.Bnt_Trigger_Continuous.setEnabled(False)   
                if selected_camera =='Irayple':# trigger OCR test
                    start_time = time.time()
                    self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
                    self.exposure_time = float(self.Le_Exposure_Time.text())
                    #self.camera_handler.set_exposure_time(self.exposure_time) 
                    img=self.camera_handler.capture_frame()
                    if img is not None:  
                        img2= img
                        img_save = img.copy()
                        image_copy4= img.copy()
                        height,width,_ = img2.shape
                        if self.model_path:
                            #self.AI_Test2(img2)
                            print("sssss")
                            acceptance_threshold_Loca= 0.2
                            Duplication_Threshold_Loca=1.0
                            img_graphic_Loca,Box_Point_Location1,=self.DEEP_LEARNING_lOCATION_TOOL.Prediction_Location(image_copy4,self.Mode_Location,acceptance_threshold_Loca,Duplication_Threshold_Loca)
                            for box in Box_Point_Location1:
                                _,x,y,w,h,angle,_,_  =box  
                                self.i=self.i+1           
                                img_Name =f"{self.i}_OCR.bmp"
                                img_crop,box=self.crop_rotated_rect(image_copy4 , int(x), int(y), 400, 700, int(angle), img_Name)
                                acceptance_threshold_Ocr= 0.2
                                Duplication_Threshold_Ocr=0.4
                                row_threshold =20
                                _,Text2,_ = self.OCR_DEEP_LEARNING_TOOL.Prediction_OCR_None_Img(img_crop,self.Model_OCR,acceptance_threshold_Ocr,Duplication_Threshold_Ocr,row_threshold)
                                #print(box)
                                print(Text2)
                                OCR_Text=Text2
                                text_item3 = QGraphicsTextItem(OCR_Text)# show test Ai
                                text_item3.setDefaultTextColor(QColor(255, 255, 0))
                                font = QFont()
                                font.setPointSize(int(width / 80))
                                text_item3.setFont(font)
                                text_item3.setPos(int(x),int(y))
                                text_item3.setRotation(0)
                                #self.scene.addItem(text_item3)  
                                text_item3.setZValue(1)  # Đảm bảo text luôn nằm trên ảnh
                                self.scene.addItem(text_item3)  
                                # Tạo polygon
                                points = [QPointF(p[0], p[1]) for p in box]
                                polygon = QPolygonF(points)
                                # Tạo đối tượng đồ họa
                                box_item = QGraphicsPolygonItem(polygon)
                                pen5 = QPen(QColor(0, 255, 0))  # Màu xanh lá cây
                                # Tạo viền dày 8px với màu xanh
                                pen5.setWidth(int(width/140))  # Độ dày viền
                                box_item.setPen(pen5)
                                box_item.setZValue(1)  # Đảm bảo text luôn nằm trên ảnh
                                # Thêm vào scene
                                self.scene.addItem(box_item)                              

                        if self.save_path  and self.checkBox_5.isChecked():
                            # Tạo tên file dựa trên thời gian hiện tại
                            current_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")  # Định dạng: ngày_tháng_năm_giờ_phút_giây
                            image_name = f"{current_time}.jpg"  # Thêm đuôi .jpg
                            ok_folder = os.path.join(self.save_path, "OK")
                            image_path = os.path.join(ok_folder, image_name)
                            record = os.path.join(self.save_path, "Record")  

                            ok_folder = os.path.join(record, "OK")
                            ng_folder = os.path.join(record, "NG")
                            ok_folder = ok_folder.replace("\\", "/")
                            ng_folder = ng_folder.replace("\\", "/")

                            if self.result and self.Cb_Save_image_Mode.currentText() == "Both":
                                image_name = f"OK_{current_time}.bmp"  
                                image_path = os.path.join(ok_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            elif  not self.result and self.Cb_Save_image_Mode.currentText() == "Both":
                                image_name = f"NG_{current_time}.bmp"  
                                image_path = os.path.join(ng_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            elif self.result and self.Cb_Save_image_Mode.currentText() == "OK":
                                image_name = f"OK_{current_time}.bmp"  
                                image_path = os.path.join(ok_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            elif  not self.result and self.Cb_Save_image_Mode.currentText() == "NG":
                                image_name = f"NG_{current_time}.bmp"  
                                image_path = os.path.join(ng_folder, image_name)
                                cv2.imwrite(image_path, img_save)
                            if self.save_path  and self.checkBox_within_template.isChecked() or self.checkBox_Template.isChecked() and self.rotated_roi is not None:
                                img2= self.Get_ROI3(img)   
                        self.image7= img.copy()
                        end_time = time.time()
                        processing_time = (end_time - start_time)*1000
                        processing_time = f"{processing_time:.1f} ms"
                        #self.setImage(img2) 
                        self.image_signal.emit(img_graphic_Loca)
                        self.La_cycle_time.setText(processing_time)
                        image_dimension = f"{height} x {width}"
                        self.Label_Dimention_Images.setText(image_dimension)    

                    else:
                        self.camera_handler.release_camera()
                        self.Bnt_Connect_Camera.setText("Connect Camera") 
                        self.Bnt_Connect_Camera.setStyleSheet(
                            "background-color: white;"       # Màu nền xanh
                            "color: black;"                  # Màu chữ đen
                            "font-size: 10pt;"               # Kích thước font chữ
                            "border: none;"                  # Không có viền (tùy chọn)
                            "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                            # Căn chữ giữa cả ngang và dọc
                        )   
                        self.Bnt_Trigger.setEnabled(False)  
                        self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                        self.Bnt_Trigger_Continuous.setEnabled(False)
            except Exception as e:
                self.error_signal2.emit(str(e))
                self.stop_threads=True

                self.Bnt_Connect_Camera.setText("Connect Camera") 
                self.Bnt_Connect_Camera.setStyleSheet(
                    "background-color: white;"       # Màu nền xanh
                    "color: black;"                  # Màu chữ đen
                    "font-size: 10pt;"               # Kích thước font chữ
                    "border: none;"                  # Không có viền (tùy chọn)
                    "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                      # Căn chữ giữa cả ngang và dọc
                )   
                self.Bnt_Trigger.setEnabled(False)  
                self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                self.Button_is_clicked = False  # Cập nhật trạng thái
                self.Bnt_Trigger_Continuous.setEnabled(False)
    
    def Trigger_image2(self):# cho continous
            try:
                self.Camera_Trigger_Continous=True
                selected_camera = self.Cb_Camera.currentText()
                i= 0
                if selected_camera =='Basler':
                    start_time = time.time()
                    self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
                    self.exposure_time = int(self.Le_Exposure_Time.text())
                    self.cam.ExposureTimeAbs.SetValue(self.exposure_time)
                    grab_result = self.cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if grab_result.GrabSucceeded():
                        img = self.converter.Convert(grab_result).GetArray()  
                        img2= img
                        height,width,_ = img2.shape
                        end_time = time.time()
                        processing_time = (end_time - start_time)*1000
                        processing_time = f"{processing_time:.1f} ms"
                        self.image_signal.emit(img)
                        self.La_cycle_time.setText(processing_time)
                        image_dimension = f"{height} x {width}"
                        self.Label_Dimention_Images.setText(image_dimension)
                if selected_camera =='Irayple':
                    start_time = time.time()
                    self.acceptance_threshold = float(self.comboBox_acceptance_threshold.currentText())
                    self.exposure_time = float(self.Le_Exposure_Time.text())
                    #self.camera_handler.set_exposure_time(self.exposure_time) 
                    img=self.camera_handler.capture_frame()
                    if img is not None:  
                        img2= img
                        height,width,_ = img2.shape
                        end_time = time.time()
                        processing_time = (end_time - start_time)*1000
                        processing_time = f"{processing_time:.1f} ms"
                        self.image_signal.emit(img)  # Gửi ảnh về GUI thread
                        #self.load_image2(img2) 
                        self.La_cycle_time.setText(processing_time)
                        image_dimension = f"{height} x {width}"
                        self.Label_Dimention_Images.setText(image_dimension)
                    else:
                        self.camera_handler.release_camera()
            except Exception as e:
                self.error_signal2.emit(str(e))
                self.stop_threads=True

                self.Bnt_Connect_Camera.setText("Connect Camera") 
                self.Bnt_Connect_Camera.setStyleSheet(
                    "background-color: white;"       # Màu nền trắng
                    "color: black;"                  # Màu chữ đen
                    "font-size: 10pt;"               # Kích thước font chữ
                    "border: none;"                  # Không có viền (tùy chọn)
                    "padding: 10px;"                 # Tạo khoảng cách đều xung quanh để căn giữa dọc
                      # Căn chữ giữa cả ngang và dọc
                )   
                self.Bnt_Trigger.setEnabled(False)  
                self.Bnt_Trigger_Continuous.setStyleSheet("background-color: none; font-size: 10pt;")
                self.Button_is_clicked = False  # Cập nhật trạng thái
                self.Bnt_Trigger_Continuous.setEnabled(False)


    # Hàm chuyển đổi QPixmap sang numpy array
    def qpixmap_to_cv2(self,qpixmap):
        try:
            qimage = qpixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            width = qimage.width()
            height = qimage.height()
            ptr = qimage.bits()
            ptr.setsize(qimage.sizeInBytes())
            arr = np.array(ptr).reshape(height, width, 4)  # RGBA
            return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        # Hàm vẽ icon lên ảnh tại vị trí mong muốn
        except Exception as e:
            self.error_signal2.emit(str(e))
     
    def Open_Image(self):
        try:
            # Mở hộp thoại để chọn ảnh
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter("Images (*.png *.jpg *.bmp)")
            if file_dialog.exec():
                # Lấy đường dẫn tệp ảnh được chọn
                file_path = file_dialog.selectedFiles()[0]

                # Đọc ảnh bằng OpenCV
                img = cv2.imread(file_path)
                self.image7 = img.copy()
                height,width,_ = img.shape
                image_dimension = f"{height} x {width}"
                self.Label_Dimention_Images.setText(image_dimension)
                self.load_image2(img)
        except Exception as e:
            self.error_signal2.emit(str(e))

    def load_image2(self,img):
        try:
            transform = QTransform()
            transform.scale(self.zoom_factor, self.zoom_factor)  # Phóng to gấp 2 lần theo cả hai chiều
            self.graphicsView.setTransform(transform)

            img6 =img
            self.image =img6
            if img6 is None:
                return  
            # OpenCV sử dụng BGR, nhưng PyQt cần RGB. Chuyển đổi từ BGR sang RGB.
            img_rgb = cv2.cvtColor(img6, cv2.COLOR_BGR2RGB)
            # Chuyển đổi NumPy array sang QImage
            height, width, channels = img_rgb.shape
            bytes_per_line = channels * width
            qimage = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            # Chuyển QImage thành QPixmap
            self.pixmap = QPixmap.fromImage(qimage)
            # Tạo QGraphicsPixmapItem để hiển thị ảnh
            self.item = QGraphicsPixmapItem(self.pixmap)
            self.scene.clear()  # Xóa các mục cũ trong scene
            self.scene.addItem(self.item)

            # Điều chỉnh kích thước scene cho phù hợp với kích thước ảnh
            self.scene.setSceneRect(0, 0, self.pixmap.width(), self.pixmap.height())
        except Exception as e:
            self.error_signal2.emit(str(e))
    def load_image4(self,img):
        try:
            # Sử dụng OpenCV để đọc ảnh
            self.image = img
            if img is None:
                return  
            # OpenCV sử dụng BGR, nhưng PyQt cần RGB. Chuyển đổi từ BGR sang RGB.
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # Chuyển đổi NumPy array sang QImage
            height, width, channels = img_rgb.shape
            bytes_per_line = channels * width
            qimage = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            # Chuyển QImage thành QPixmap
            self.pixmap = QPixmap.fromImage(qimage)

            # Nếu self.item đã tồn tại thì update lại ảnh cho nó, không cần clear scene
            if hasattr(self, 'item') and self.item is not None:
                self.item.setPixmap(self.pixmap)
            else:
                self.item = QGraphicsPixmapItem(self.pixmap)
                self.scene.addItem(self.item)
            # Điều chỉnh kích thước scene cho phù hợp với kích thước ảnh
            self.scene.setSceneRect(0, 0, self.pixmap.width(), self.pixmap.height())


        except Exception as e:
            self.error_signal2.emit(str(e))
    def load_image3(self, img):
        try:
            # Sử dụng OpenCV để đọc ảnh
            self.image = img
            if img is None:
                return  
            # OpenCV sử dụng BGR, nhưng PyQt cần RGB. Chuyển đổi từ BGR sang RGB.
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # Chuyển đổi NumPy array sang QImage
            height, width, channels = img_rgb.shape
            bytes_per_line = channels * width
            qimage = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            # Chuyển QImage thành QPixmap
            self.pixmap = QPixmap.fromImage(qimage)

            # Nếu self.item đã tồn tại thì update lại ảnh cho nó, không cần clear scene
            if hasattr(self, 'item') and self.item is not None:
                self.item.setPixmap(self.pixmap)
            else:
                self.item = QGraphicsPixmapItem(self.pixmap)
                self.scene.addItem(self.item)
            # Điều chỉnh kích thước scene cho phù hợp với kích thước ảnh
            self.scene.setSceneRect(0, 0, self.pixmap.width(), self.pixmap.height())


        except Exception as e:
            self.error_signal2.emit(str(e))



    def points_to_rect(self,points):
        rect = cv2.minAreaRect(np.array(points, dtype=np.float32))  # (center, (w,h), angle)
        return rect

    def wheelEvent(self, event):
        try:
            # Hàm thu phóng khi dùng chuột
            # Lấy giá trị scale hiện tại của QGraphicsView
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if self.image is not None :
                    current_scale = self.graphicsView.transform().m11()
                    current_scale = round(current_scale, 2)  # Làm tròn đến 2 chữ số thập phân
                    print(current_scale)
                    factor = 0.9
                    if  0.15 < current_scale < 50.0:
                        if event.angleDelta().y() < 0:
                            factor = 1 / factor
                        self.graphicsView.scale(factor, factor)
                    if current_scale == 0.15 and event.angleDelta().y() < 0:
                        factor = 1 / factor
                        self.graphicsView.scale(factor, factor)
                    if current_scale == 50.92 and event.angleDelta().y() > 0:
                        self.graphicsView.scale(factor, factor)
        except Exception as e:
            self.error_signal2.emit(str(e))
    def exit_app(self):
        self.camera_handler.release_camera()
        self.Save_Setting()
        QtWidgets.QApplication.quit()  # Thoát ứng dụng
    def closeEvent(self):
            # Khi cửa sổ đóng, dừng các luồng
            self.stop_threads = False
            self.stop_training= True
            # if self.thread1.is_alive():
            #     self.thread1.join()
            print("All threads stopped and program is exiting")
            sys.exit()

class MyWidget(QtWidgets.QStackedWidget):
    def __init__(self):
        super(MyWidget, self).__init__()
        self.fullscreen = True  # Biến để theo dõi trạng thái full màn hình
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F1:  # Check if F1 is pressed
            if self.fullscreen:
                self.showNormal()  # Exit fullscreen and return to normal size
                self.setSizeBasedOnForm()  # Set size based on the current form
            else:
                self.showFullScreen()  # Return to fullscreen mode
                self.setSizeBasedOnForm() 
            self.fullscreen = not self.fullscreen  # Đổi trạng thái full màn hình

    def setSizeBasedOnForm(self):
        current_index = self.currentIndex()
        #print(current_index )
        if current_index == 0:  # MainWindow
            widget.setFixedHeight(1200)  # Set the desired window height
            widget.setFixedWidth(1920)   # Set the desired window width 

if __name__ == "__main__": 
    multiprocessing.freeze_support()#chong dong bang
    app = QApplication(sys.argv)
    widget = MyWidget()
    # Create instances of MainWindow, Screen2, and Screen3

    screen2 = Screen2()
    # Add instances to QStackedWidget

    widget.addWidget(screen2)
    # Set Form 1 (MainWindow) as the initial screen
    widget.setCurrentIndex(0)
    # Display full screen
    widget.showFullScreen()
    # Đảm bảo gọi closeEvent khi thoát ứng dụng
    def on_exit():
        screen2.close_thread()# thoát luồng trong form2 
        screen2.closeEvent()  # Gọi phương thức close để kích hoạt closeEvent
        sys.exit(1)
    app.aboutToQuit.connect(on_exit)
    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error while exiting: {e}")
        on_exit()
        sys.exit(1)