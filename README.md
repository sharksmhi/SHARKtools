# SHARKtools
SHARKtools is a Python 3 GUI plugin-application originaly developed to work with in-situ data from ferrybox and fixed platforms.
Graphics by tkinter. 

Note: We are currently updating the description of this project. Information below refers to the original development and is not up to date! 

¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤¤


### Preparations and requirements 
Application uses basemap for showing maps. The module requires Microsoft Visual C++ for python which can be a bit tricky to install if you want to run the program in a viritual environment (recomended). Here follows a step by step guide on the prefered way to setup all requirements needed to run the program on Windows (not tested for other platforms). The guide assumes the user has no prior experience of Python. 

#### Download Pyhton and application
- Download Python 3.6 based on your system here: https://www.python.org/downloads/release/python-367/. We recomend you install under C:\Pyhton36 and DONT add pyhton to PATH. 
- Create a directory where you want to install GISMOtoolbox 
- From this directory open a cmd console (you will get this option if you hold down SHIFT and right click) 
- Create a virtual environment by typing (this will create a virtual environment in the folder venv36): 

      C:\Python36\python.exe -m venv venv36 
      
Download the the latest versions of gismo_gui_tkinter and sharkpylib here: 

      https://github.com/sharksmhi/gismo_gui_tkinter/releases/latest
      https://github.com/sharksmhi/sharkpylib/releases/latest

Unzip and rename (remove version number)

You should now have three folders (venv36, gismo_gui_tkinter and sharkpylib). 
- Copy the folder sharkpylib to gimso_gui_tkinter/libs 

#### Install required packages 
- Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/ and download the following packages based on your operating system. Make sure you download packages for python36 (the packages filenames should contain cp36): 
      **pyproj, basemap** 
      
- From the command line type (from the directory where you have your three folders): 

      venv36\Scripts\activate 
      
  This will activate the newly created virtual environment. 

- Now install the two packages by typing: 

      pip install <path to downloaded pyproj-file>
      
      pip install <path to downloaded basemap-file> 
      
- We also need to install some other required packages by typing: 

      pip install -r gismo_gui_tkinter/requirements.txt 
      
### Run GISMOtoolbox 
Run the application via the command line: 
- Activate environment: 

      venv36\Scripts\activate 
      
- Run:

      python gismo_gui_tkinter\main.py 

      
