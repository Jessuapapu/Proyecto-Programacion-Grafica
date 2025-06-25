# 🏛️ San Jacinto Estate Simulation

## 📄 Abstract

This project is an educational 3D simulation of the historical Hacienda San Jacinto, built using Python, Pygame, and PyOpenGL. The project immerses users in a virtual recreation of the estate with dynamic lighting, real-time interaction, audio effects, and configurable gameplay. It was created as part of a university course in computer graphics programming.

## 🔑 Keywords

Python, Pygame, OpenGL, 3D Simulation, Game Development, Educational Project, Interactive Visualization, PyInstaller

## 👋 Introduction

The San Jacinto Estate Simulation allows users to explore a 3D environment inspired by the iconic Hacienda San Jacinto. Users interact through a menu-driven interface, and navigate the scene using keyboard or joystick. The system features a dynamic day/night cycle, environmental sounds, and a music controller.

Built by students in their third semester of computer systems engineering, this project demonstrates practical applications of game loops, rendering, OpenGL model loading, and sound management in Python.

## 👥 Authors

**Group 3T1-COMS**
- Jessua René Solís Juárez
- Kyrsa Jolieth Hernández Roque
- Vanessa de los Ángeles Mercado Ortega
- Alberth Hernan Izaguirre Espinoza

## 🖥️ Installation and Execution

### Run from Source

1. Install required packages:

```bash
pip install -r requirements.txt
```

2. Run the project:

```bash
python main.py
```

### Run as Executable (.exe)

To generate the Windows executable:

```bash
pyinstaller --onefile --windowed ^
--add-data "Recursos;Recursos" ^
--add-data "Audio;Audio" ^
--add-data "Clases;Clases" ^
--add-data "Escenas;Escenas" ^
--add-data "modelosObj;modelosObj" ^
main.py
```

Then run:

```
dist/main.exe
```

## 🎮 Controls

- WASD — Move
- Mouse / Right joystick — Look around
- Shift / Space — Descend / Ascend
- ESC — Exit
- Joystick — Supported

## 📦 Requirements

- Python 3.11 or 3.12
- Pygame ≥ 2.1
- PyOpenGL
- Pillow
- PyInstaller

## 🎵 Credits

- Horse model by evgeney24: https://sketchfab.com/evgeney24
- Background music: indian-pacific-271.mp3 (free for educational use)


## 💾 Download Executable

You can download the compiled Windows executable here: [San Jacinto Simulation - EXE](https://drive.google.com/file/d/1CX004NzGm6zUVJc810fFpszpNUxrGRRH/view?usp=sharing)

## 🎬 Project Demonstration

Watch the gameplay video here: [San Jacinto Simulation on YouTube](https://youtu.be/DkytB5v_UDQ)

## ⚖️ License

This project is licensed under both the **MIT License** and **Apache License 2.0** for educational purposes.

---

MIT License: [Open Source Initiative](https://opensource.org/licenses/MIT)  
Apache License 2.0: [Apache Foundation](https://www.apache.org/licenses/LICENSE-2.0)
