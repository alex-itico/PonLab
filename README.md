# 🚀 PonLab - Passive Optical Network Simulator

<div align="center">

![PonLab Logo](resources/icons/app_icon_512x512.png)

_An advanced desktop application for simulation, design, and analysis of PON fiber optic networks_

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![RL](https://img.shields.io/badge/Reinforcement%20Learning-Smart--RL-ff6b6b.svg)](https://github.com/alex-itico/PonLab)
[![SDN](https://img.shields.io/badge/SDN-Controller-4ecdc4.svg)](https://github.com/alex-itico/PonLab)
[![Version](https://img.shields.io/badge/Version-2.1.0-brightgreen.svg)](releases)
[![Languages](https://img.shields.io/badge/Languages-5-blue.svg)](resources/translations)

**🌍 Available Languages:** 🇪🇸 Español | 🇺🇸 English | 🇫🇷 Français | 🇧🇷🇵🇹 Português | 🇩🇪 Deutsch

**🎯 Developed by:** Alex Aravena Tapia • Jesús Chaffe González • Eduardo Maldonado Zamora • Jorge Barrios Núñez

</div>

---

## 📑 Table of Contents

- [Description](#-description)
- [Main Features](#-main-features)
- [AI and SDN Architecture](#-ai-and-sdn-architecture)
- [Installation](#-installation-and-configuration)
- [Quick Start Guide](#-quick-start-guide)
- [Project Structure](#-project-structure)
- [Use Cases](#-use-cases-and-applications)
- [Authors](#-authors)

---

## �📋 Description

**PonLab** is a professional desktop application developed in Python that enables simulation, design, and analysis of Passive Optical Networks (PON). The tool features an intuitive graphical interface for fiber optic infrastructure design with advanced **Artificial Intelligence (RL)**, **integrated SDN controller**, real-time visualization, and intelligent optimization algorithms for network performance analysis

## ✨ Main Features

### 🎨 **Interface, Themes & Navigation**

- **Advanced Interactive Canvas**: Infinite zoom, smooth pan, intuitive navigation with real-time coordinates
- **Professional Coordinate System**: Configurable grid with visible origin and precise measurements
- **Customizable Themes**: Full support for light/dark themes with QSS integration and persistent configuration
- **Map Integration**: Geographic visualization for real equipment location (MapBox)
- **Adaptive Panels**: Resizable and configurable interface with splash screen

### 🔧 **Device & Connection Management**

- **Complete PON Devices**: OLT (Optical Line Terminal) and ONU (Optical Network Unit) with SVG icons
- **Intuitive Drag & Drop**: Seamless device placement from side panel to canvas
- **Advanced Connection Mode**: Press `L` to connect devices with automatic distance calculation
- **Visual Management**: Real-time information panel with coordinates, multiple selection support
- **Smart Validation**: System prevents invalid connections and configurations

### 🧪 **Intelligent Simulation System**

- **Integrated PON Simulator**: Advanced event-driven simulation engine with precise time control
- **🤖 DBA Algorithms**: FCFS, Priority, RL-DBA, SDN, Smart-RL ⭐, Smart-RL-SDN ⭐⭐
- **Configurable Scenarios**: Predefined traffic patterns with customizable simulation time (1-120s)
- **Real-Time Dashboard**: SDN metrics panel (Ctrl+D) with continuous monitoring
- **Fairness Analysis**: Automatic Jain index calculation and equity metrics

### 📊 **Visualization & Analysis**

- **Interactive Graphics**: Complete matplotlib integration with real-time RL metrics
- **Performance Monitoring**: Delay, throughput, buffer occupancy, link utilization analysis
- **Auto-Export**: Automatic saving of results in PNG, PDF, SVG formats
- **Simulation History**: Track and compare multiple execution results
- **Event Log Panel**: Real-time system events with filtering capabilities

### 🌍 **Multilanguage System**

- **5 Complete Languages**: Spanish, English, French, Portuguese, German
- **660+ Translation Keys**: Complete UI, dialogs, matplotlib charts, and error messages
- **Dynamic Switching**: Change language without restarting (Help → Language)
- **Persistent Configuration**: Language preference saved automatically

### 💾 **Project Management**

- **Native .pon Format**: Proprietary file system for complete PON topologies
- **Intelligent Auto-save**: Automatic backup in temporary folder with change detection
- **Complete Import/Export**: Full project state preservation with modification tracking

---

## 🤖 AI and SDN Architecture

### **🧠 Smart-RL System (Reinforcement Learning)**

PonLab features a **completely internal RL agent** requiring no external dependencies:

**Intelligent Policies:**
- `prioritize_low_buffer` (0.7) - Prioritizes ONUs near buffer saturation
- `balance_throughput` (0.6) - Balances throughput distribution
- `minimize_delay` (0.8) - Optimizes average latency
- `fairness_factor` (0.5) - Guarantees equitable resource allocation

**Learning Mechanism:**
- Internal Q-Table with discrete state space
- Dynamic network observation (buffer levels, requests, throughput)
- Adaptive policy improvement with each simulation cycle
- Real-time decision tracking and performance analysis

### **🌐 SDN Controller (OLT_SDN)**

**Centralized Control:**
- Unified management with global network state visibility
- Dynamic policy implementation and continuous monitoring
- Real-time metrics: latency per ONU, aggregate throughput, buffer occupancy, link utilization, Jain index

**Interactive Dashboard (Ctrl+D):**
- Live visualization of all network metrics
- Automated fairness calculations
- Historical performance tracking

### **🚀 Smart-RL-SDN Hybrid Algorithm**

**Revolutionary Two-Layer Architecture:**

1. **RL Decision Layer**: Smart-RL analyzes global state and makes intelligent allocation decisions
2. **SDN Implementation Layer**: OLT_SDN executes decisions and provides performance feedback
3. **Intelligent Feedback Loop**: Continuous optimization based on real-time results

**Advantages:**
- 🎯 RL Precision + ⚡ SDN Speed
- 🔄 Adaptability to traffic pattern changes
- 📊 Complete dual-system metrics analysis
- 🚀 Optimal performance combining flexibility and control

**Quick Start:**
- Select algorithm in simulation panel (Ctrl+N)
- Configure policies in RL panel (Ctrl+T)
- Monitor in SDN dashboard (Ctrl+D)
- Compare results across algorithms

---

## 🛠️ Technologies and Architecture

**Technology Stack:**
- **Python 3.8+** with PyQt5, PyQtWebEngine, Matplotlib, NumPy
- **AI/ML**: Stable-Baselines3, PyTorch, Gymnasium, Scikit-learn
- **Data**: Pandas for analysis, JSON for configuration
- **Graphics**: SVG vector icons, QSS themes

**Architecture:**
- Modular design with separated concerns (core, ui, utils)
- Event-driven simulation with precise timing
- Signal-based component communication
- Efficient rendering for thousands of devices

---

## 📦 Installation and Configuration

### **Prerequisites**

- Python 3.8+ (Recommended: Python 3.11+)
- Git, pip package manager

### **Quick Installation**

```bash
# Clone repository
git clone https://github.com/alex-itico/PonLab.git
cd PonLab

# Create virtual environment (Recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/MacOS

# Install dependencies and run
pip install -r requirements.txt
python main.py
```

### **Conda Alternative**

```bash
conda create -n ponlab python=3.11
conda activate ponlab
conda install -c conda-forge pyqt
git clone https://github.com/alex-itico/PonLab.git
cd PonLab
python main.py
```

---

## 🎮 Quick Start Guide

### **⚡ 5-Step Quick Start**

1. **Launch**: `python main.py`
2. **Add Devices**: Drag OLT/ONU from side panel
3. **Connect**: Press `L`, select two devices
4. **Navigate**: `C` (center), `R` (reset), wheel (zoom)
5. **Save**: `Ctrl+S`

### **⌨️ Essential Shortcuts**

| Shortcut | Function             | Description                          |
| -------- | -------------------- | ------------------------------------ |
| `L`      | Connection Mode      | Enable/disable connection mode       |
| `C` / `R`| Center / Reset View  | Navigation controls                  |
| `Ctrl+N` | Simulation Panel     | Open simulation controls             |
| `Ctrl+D` | SDN Dashboard        | Real-time SDN metrics ⭐             |
| `Ctrl+T` | RL Panel             | RL configuration ⭐                  |
| `Ctrl+S` | Save                 | Save current project                 |
| `Ctrl+G` | Grid Toggle          | Show/hide grid                       |
| `Delete` | Delete               | Remove selected items                |

### **🖱️ Mouse Controls**

- **Left Click**: Select devices/elements
- **Right Click**: Context menu
- **Middle + Drag**: Pan view
- **Wheel**: Zoom in/out
- **Drag & Drop**: Move devices

### **🔧 Common Workflows**

**Simulation Setup:**
1. Configure PON topology (OLT + ONUs)
2. Open simulation panel (Ctrl+N)
3. Select algorithm (Smart-RL-SDN recommended)
4. Set duration and execute
5. View results in popup window

**RL/SDN Monitoring:**
1. Start simulation with Smart-RL or SDN algorithm
2. Open SDN dashboard (Ctrl+D) for live metrics
3. Configure policies in RL panel (Ctrl+T)
4. Compare algorithm performance

**Language Change:**
- Help → Language → Select preferred language
- Interface updates immediately

---

## 📁 Project Structure

```
PonLab/
├── 📄 main.py                    # Main entry point
├── 📄 requirements.txt           # Project dependencies
├── 📄 README.md / README_EN.md   # Documentation
│
├── 📁 core/                      # Business logic
│   ├──  devices/              # Device management (OLT, ONU)
│   ├── 📁 connections/          # Connection system
│   ├── � pon/                  # PON-specific components
│   ├── 📁 algorithms/           # DBA and scheduling
│   ├──  simulation/           # Simulation engines
│   ├── � events/               # Event-driven system
│   ├── 📁 data/                 # Data structures
│   └──  utilities/            # Helper functions
│
├── 📁 ui/                        # Interface components
│   ├── 📄 main_window.py        # Main window
│   ├── 📄 canvas.py             # Drawing canvas
│   ├── 📄 netponpy_sidebar.py   # Simulation panel
│   ├── 📄 graphics_popup_window.py # Results visualization
│   └── 📄 splash_screen.py      # Loading screen
│
├── 📁 utils/                     # Utilities
│   ├── 📄 config_manager.py     # Configuration
│   ├── 📄 constants.py          # Application constants
│   └── 📄 resource_manager.py   # Resource handling
│
└── 📁 resources/                 # Assets
    ├── 📁 devices/              # Device SVG icons
    ├── 📁 icons/                # Application icons
    ├── 📁 styles/               # QSS themes (light/dark)
    └── 📁 translations/         # Language JSON files (5 languages)
```

---

## 📚 Use Cases and Applications

### **🎓 Academic Research**
- Custom DBA algorithm simulation and comparative analysis
- Reinforcement Learning research for optical networks
- Development of new bandwidth allocation policies

### **� Industrial Development**
- PON network prototyping before deployment
- Existing network configuration optimization
- Capacity analysis and growth planning

### **📖 Education and Training**
- PON network concepts demonstration
- DBA algorithms practical teaching
- AI/SDN applied to networks workshops

---

## � Technical Features

### **Performance**
- Efficient canvas rendering for thousands of devices
- Automatic memory management and garbage collection
- Progressive resource loading for fast startup

### **Robustness**
- Comprehensive error handling and validation
- Auto-recovery from temporary files
- Automatic project backup system

### **Extensibility**
- Modular architecture for easy feature addition
- Internal API with event/signal system
- Plugin-ready design

---

## 📄 License

Academic and research purposes. Contact authors for licensing information.

---

## 👥 Authors

- **Alex Aravena Tapia** - Lead Developer
- **Jesús Chaffe González** - Core Algorithms
- **Eduardo Maldonado Zamora** - UI/UX Design
- **Jorge Barrios Núñez** - Network Architecture

**Repository**: [github.com/alex-itico/PonLab](https://github.com/alex-itico/PonLab)

---

## 📝 Version History

### **v2.1.0** (Current)
✨ Complete multilanguage support (5 languages: ES, EN, FR, PT, DE)
📊 660+ translation keys covering entire application
🎨 Translated matplotlib charts and UI components
📖 English README for international visibility

### **v2.0.0**
🤖 Smart-RL system implementation
🌐 SDN controller integration
🚀 Smart-RL-SDN hybrid algorithm
📊 Advanced metrics dashboard with Jain fairness index

### **v1.0.0**
🎨 Initial graphical interface
🔧 Basic device and connection management
🧪 PON simulation integration

---

<div align="center">

**Made with ❤️ for the PON networks and AI community**

_PonLab - Connecting the future of optical networks with intelligent technology_

</div>
