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

## 📋 Description

**PonLab** is a professional desktop application developed in Python that allows simulation, design, and analysis of Passive Optical Networks (PON). The tool provides an intuitive and powerful graphical interface for fiber optic infrastructure design, with advanced **Artificial Intelligence (RL)** functionalities, **integrated SDN controller**, real-time visualization, and network performance analysis with intelligent optimization algorithms.

### 🤖 **Innovation in AI and Software Defined Networks**

PonLab integrates cutting-edge technologies for automatic PON network optimization:

- **🧠 Reinforcement Learning (Smart-RL)**: Internal RL agent that learns and optimizes bandwidth allocation
- **🌐 SDN Controller**: Centralized control system for dynamic network management
- **🚀 Smart-RL-SDN Hybrid Algorithm**: Revolutionary combination of RL and SDN for maximum performance

## ✨ Main Features

### 🎨 **Interface and Visualization**

- **Advanced Interactive Canvas**: Workspace with infinite zoom, smooth pan, and intuitive navigation
- **Professional Coordinate System**: Configurable grid with visible origin and precise measurements
- **Map Visualization**: Integration with geographic maps for real equipment location
- **Customizable Themes**: Full support for light and dark themes with professional styles
- **Splash Screen**: Loading screen with initialization progress
- **Adaptive Interface**: Resizable and configurable panels

### 🔧 **Device Management**

- **Complete PON Devices**: Support for OLT (Optical Line Terminal) and ONU (Optical Network Unit)
- **Intuitive Drag & Drop**: Drag devices from side panel to canvas
- **Visual Management**: Professional SVG icons and detailed graphical representation
- **Real-Time Information**: Information panel with device coordinates and data
- **Selection and Manipulation**: Multiple selection, movement, and device configuration
- **Configurable Properties**: Detailed configuration for each device

### 🔗 **Connection System**

- **Advanced Connection Mode**: Activation with `L` key to connect devices
- **Visual Connections**: Fiber optic lines with automatic distance labels
- **Intelligent Management**: Creation, deletion, and modification of connections
- **Distance Calculation**: Automatic measurement of distances between devices
- **Connection Validation**: System that prevents invalid connections

### 🧪 **Advanced Simulation System with AI**

- **Integrated PON Simulator**: Advanced simulation engine for PON networks
- **🤖 Intelligent DBA Algorithms**:
  - **FCFS** - First Come First Served (basic algorithm)
  - **Priority** - Priority-based
  - **RL-DBA** - Classic Reinforcement Learning DBA
  - **SDN** - Software Defined Network with centralized control
  - **Smart-RL** - Intelligent internal RL (no external dependencies) ⭐
  - **Smart-RL-SDN** - RL + SDN hybrid algorithm ⭐⭐
- **🧠 Internal RL Agent**: Completely autonomous system with learning policies
- **🌐 SDN Dashboard**: Real-time metrics panel (Ctrl+D)
- **⚖️ Fairness Analysis**: Jain index and automatic equity metrics
- **Predefined Scenarios**: Automatic configuration for different traffic scenarios
- **Real-Time Simulation**: Simulation execution with configurable time (1-120 seconds)
- **Hybrid Architecture**: Event-driven simulation system with precise time control

### 📊 **Visualization and Analysis with AI**

- **Interactive Graphics**: Complete visualization system with matplotlib
- **🤖 Real-Time RL Metrics**: Monitoring of RL agent decisions
- **🌐 Integrated SDN Dashboard**: SDN control panel with advanced metrics (Ctrl+D)
- **⚖️ Automatic Fairness Analysis**: Automatic calculation of Jain index
- **📈 Intelligent Metrics**: Analysis of delay, throughput, buffer occupancy, utilization
- **Results Window**: Automatic popup with graphics upon simulation completion
- **Graphics Export**: Automatic saving in PNG, PDF, SVG formats
- **🧠 RL Performance Analysis**: Visualization of agent policies and decisions
- **Simulation History**: Tracking and comparison of results
- **Log Panel**: Real-time event system with filters

### 💾 **Project Management**

- **Native .pon Format**: Own file system for PON topologies
- **Intelligent Auto-save**: Automatic saving in temporary folder
- **Load and Save**: Complete project import and export
- **Change History**: Tracking of modifications and project states
- **Change Detection**: Notification of unsaved work
- **Results Export**: Saving of simulation metrics and graphics

### ⌨️ **Controls and Navigation**

- **Complete Keyboard Shortcuts**: More than 15 shortcuts for quick navigation
- **Mouse Controls**: Pan with middle button, zoom with wheel, selection with click
- **Intelligent Navigation**: Auto-centering, view reset, and device focus
- **Simulation Panel**: Quick access with Ctrl+N to simulation system
- **🌐 SDN Dashboard**: Direct access with Ctrl+D to SDN control panel

### 🌍 **Multilanguage System**

- **5 Complete Languages**: Spanish, English, French, Portuguese, German
- **660+ Translation Keys**: Complete UI translation in all languages
- **Dynamic Language Switching**: Change language without restarting application
- **Matplotlib Integration**: Charts and graphics translated according to selected language
- **Consistent Messages**: All dialogs, errors, and notifications translated

### 🤖 **Artificial Intelligence and Software Defined Networks**

#### **🧠 Smart-RL System (Reinforcement Learning)**

- **Internal RL Agent**: Completely autonomous system without external dependencies
- **Intelligent Policies**:
  - `prioritize_low_buffer` - Prioritizes ONUs with low buffers
  - `balance_throughput` - Balances throughput among users
  - `minimize_delay` - Minimizes average latency
  - `fairness_factor` - Guarantees equity in allocation
- **Adaptive Learning**: Agent improves its decisions with each simulation
- **Internal Q-Table**: Reinforcement learning system with Q-table
- **Dynamic Optimization**: Automatic parameter adjustment based on performance

#### **🌐 Integrated SDN Controller**

- **OLT_SDN**: Specialized SDN controller for PON networks
- **Centralized Control**: Unified management of all network devices
- **Real-Time Metrics**: Continuous monitoring of:
  - Latency per ONU
  - Aggregate throughput
  - Buffer levels
  - Link utilization
  - Fairness Index (Jain)
- **Interactive Dashboard**: Visual panel accessible with Ctrl+D
- **Dynamic Policies**: Automatic implementation of network policies

#### **🚀 Smart-RL-SDN Hybrid Algorithm**

- **Revolutionary Integration**: Combines the best of RL and SDN
- **Two-Layer Architecture**:
  - **RL Layer**: Makes intelligent allocation decisions
  - **SDN Layer**: Implements and monitors decisions
- **Intelligent Feedback**: SDN informs RL about performance
- **Continuous Optimization**: System improves automatically with each cycle
- **Combined Metrics**: Complete analysis of both systems

## 🛠️ Technologies and Architecture

### **Technology Stack**

- **Python 3.8+**: Main language with modern support
- **PyQt5**: Professional GUI framework
- **PyQtWebEngine**: Web engine for interactive maps (optional)
- **Matplotlib**: Library for scientific graphics and visualization
- **NumPy**: Numerical computing for data analysis
- **🤖 Stable-Baselines3**: Advanced Reinforcement Learning framework
- **🧠 PyTorch**: Deep learning engine for RL algorithms
- **🌐 Gymnasium**: Standard environments for RL (OpenAI Gym)
- **📊 Pandas**: Analysis and manipulation of simulation data
- **🔬 Scikit-learn**: Complementary machine learning algorithms
- **JSON**: Configuration storage format
- **SVG**: Vector graphics for device icons

## 📦 Installation and Configuration

### **Prerequisites**

- Python 3.8+ (Recommended: Python 3.11+)
- Git to clone the repository
- pip (Python package manager)

### **Quick Installation**

1. **Clone the repository:**

   ```bash
   git clone https://github.com/alex-itico/PonLab.git
   cd PonLab
   ```

2. **Create virtual environment (Recommended):**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### **Installation with Conda (Alternative)**

```bash
# Create conda environment
conda create -n ponlab python=3.11
conda activate ponlab

# Install PyQt5
conda install -c conda-forge pyqt

# Clone and run
git clone https://github.com/alex-itico/PonLab.git
cd PonLab
python main.py
```

## 🎮 User Manual

### **🚀 Quick Start**

1. **Run the application** with `python main.py`
2. **Drag devices** from the side panel to the canvas
3. **Connect devices** by pressing `L` and selecting two devices
4. **Navigate** using `C` (center), `R` (reset), mouse wheel (zoom)
5. **Save your project** with `Ctrl+S`

### **⌨️ Complete Keyboard Shortcuts**

| Shortcut | Function                | Description                                      |
| -------- | ----------------------- | ------------------------------------------------ |
| `L`      | **Connection Mode**     | Enable/disable mode to connect devices           |
| `C`      | **Center View**         | Centers view at origin (0, 0)                    |
| `R`      | **Reset View**          | Restores zoom and centers view                   |
| `Escape` | **Cancel**              | Cancels operations in progress                   |
| `Ctrl+P` | **Components Panel**    | Show/hide device panel                           |
| `Ctrl+G` | **Grid**                | Show/hide grid and origin                        |
| `Ctrl+I` | **Info Panel**          | Show/hide information panel                      |
| `Ctrl+N` | **Simulation Panel**    | Show/hide simulation panel                       |
| `Ctrl+D` | **🌐 SDN Dashboard**    | Opens SDN dashboard in real-time ⭐              |
| `Ctrl+T` | **🤖 RL Panel**         | Access RL configuration panel ⭐                 |
| `Ctrl+S` | **Save**                | Saves current project                            |
| `Ctrl+O` | **Open**                | Opens existing project                           |
| `Delete` | **Delete**              | Deletes selected devices/connections             |

### **🖱️ Mouse Controls**

| Action                   | Function                                |
| ------------------------ | --------------------------------------- |
| **Left Click**           | Select devices/elements                 |
| **Right Click**          | Context menu with options               |
| **Middle Button + Drag** | Pan (move view)                         |
| **Mouse Wheel**          | Zoom in/out                             |
| **Drag & Drop**          | Move devices, drag from panel           |

### **🔧 Advanced Features**

#### **NetPONPy Simulation System**

- **Integrated Simulation**: PON simulation panel with complete controls
- **Temporal Configuration**: Customizable simulation duration control
- **Automatic Execution**: Simulation system with optimized parameters
- **Real-Time Results**: Immediate visualization of results

#### **PON Metrics Visualization**

- **Interactive Graphics**: Matplotlib graphics integrated in interface
- **Real-Time Metrics**: Continuous monitoring of network parameters
- **Popup Window**: Expanded visualization of graphics and results
- **Detailed Analysis**: Performance metrics and advanced statistics

#### **Device Management**

- **Add Devices**: Drag OLT/ONU from side panel
- **Move Devices**: Select and drag devices on canvas
- **Detailed Information**: Information panel shows coordinates and data
- **Multiple Selection**: Hold Ctrl to select multiple devices

#### **Connection System**

- **Create Connections**: Press `L`, then select two devices
- **Distance Labels**: Connections show distance automatically
- **Validation**: System prevents invalid connections
- **Visual Management**: Connections with differentiated colors and styles

#### **Navigation and View**

- **Infinite Zoom**: Zoom in as much as needed without limits
- **Smooth Navigation**: Fluid pan with natural inertia
- **Intelligent Centering**: `C` centers at origin, `R` completely resets
- **Real-Time Coordinates**: See mouse coordinates in real-time

#### **Theme System**

- **Interchangeable Themes**: Full support for light and dark themes
- **QSS Integration**: All components respect selected theme
- **Persistence**: Selected theme maintained between sessions
- **Universal Compatibility**: All panels and windows support themes

#### **🌍 Language System**

- **5 Languages Available**: Spanish, English, French, Portuguese, German
- **Easy Switching**: Menu Help → Language → Select your language
- **Complete Translation**: All UI elements, dialogs, and messages
- **Persistent Configuration**: Language preference saved automatically
- **Chart Translation**: Matplotlib graphics adapted to selected language

## 📁 Detailed Project Structure

```
PonLab/
├── 📄 main.py                    # 🚀 Main entry point
├── 📄 requirements.txt           # 📦 Project dependencies
├── 📄 SHORTCUTS.md              # ⌨️ Complete shortcut guide
├── 📄 README.md                 # 📖 Main documentation (Spanish)
├── 📄 README_EN.md              # 📖 English documentation
├── 📄 .gitignore               # 🚫 Files ignored by Git
│
├── 📁 core/                     # ⚙️ Main business logic (REORGANIZED)
│   ├── 📄 __init__.py
│   ├── 📁 devices/             # 📱 Device management
│   │   ├── 📄 __init__.py
│   │   ├── 📄 device.py        # 🔧 Base device class
│   │   ├── 📄 device_manager.py # 📱 Device manager
│   │   └── 📄 device_types.py  # 🏭 Device factory
│   ├── 📁 connections/         # 🔗 Connection system
│   │   ├── 📄 __init__.py
│   │   ├── 📄 connection.py    # 🔗 Base connection class
│   │   ├── 📄 connection_manager.py # 🔗 Connection manager
│   │   ├── 📄 connection_points.py # 📍 Connection points
│   │   ├── 📄 pon_connection.py # 🌐 Specific PON connections
│   │   └── 📄 pon_link.py      # 🔌 PON links
│   ├── 📁 pon/                 # 🌐 Specific PON components
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pon_adapter.py   # 🔄 Main PON adapter
│   │   ├── 📄 pon_olt.py       # 🔴 Optical Line Terminal
│   │   ├── 📄 pon_onu.py       # 🔵 Optical Network Unit
│   │   └── 📄 pon_types.py     # 📋 PON types and constants
│   ├── 📁 algorithms/          # 🧮 DBA and scheduling algorithms
│   │   ├── 📄 __init__.py
│   │   ├── 📄 upstream_scheduler.py # ⬆️ Upstream scheduler
│   │   ├── 📄 pon_dba.py       # 🎯 Main DBA algorithms
│   │   └── 📄 pon_dba_cycle.py # 🔄 DBA cycle management
│   ├── 📁 simulation/          # 🎯 Simulation engines
│   │   ├── 📄 __init__.py
│   │   ├── 📄 simulation_manager.py # 🎮 Main manager
│   │   ├── 📄 pon_orchestrator.py # 🎼 PON orchestrator
│   │   ├── 📄 pon_simulator.py    # 🔬 Main simulator
│   │   ├── 📄 pon_event_simulator.py # ⚡ Event simulator
│   │   ├── 📄 pon_cycle_simulator.py # 🔄 Cycle simulator
│   │   └── 📄 pon_netsim.py       # 🌐 Network simulator
│   ├── 📁 events/              # ⚡ Discrete event system
│   │   ├── 📄 __init__.py
│   │   ├── 📄 event_queue.py   # 📋 Event queue
│   │   ├── 📄 pon_event.py     # ⚡ Base PON events
│   │   ├── 📄 pon_event_olt.py # 🔴 Hybrid OLT events
│   │   └── 📄 pon_event_onu.py # 🔵 Hybrid ONU events
│   ├── 📁 data/                # 📊 Data structures
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pon_queue.py     # 📋 PON queues
│   │   ├── 📄 pon_request.py   # 📤 PON requests
│   │   └── 📄 project_manager.py # 📁 Project manager
│   └── 📁 utilities/           # 🛠️ Utility functions
│       ├── 📄 __init__.py
│       ├── 📄 pon_traffic.py   # 🚦 Traffic generation
│       ├── 📄 pon_random.py    # 🎲 Random variables
│       └── 📄 helpers.py       # 🔧 Auxiliary functions
│
├── 📁 ui/                       # 🎨 Interface components
│   ├── 📄 __init__.py
│   ├── 📄 main_window.py       # 🏢 Main window
│   ├── 📄 canvas.py            # 🎨 Main drawing canvas
│   ├── 📄 sidebar_panel.py     # 📋 Device side panel
│   ├── 📄 netponpy_sidebar.py  # 🧪 NetPONPy simulation panel
│   ├── 📄 integrated_pon_test_panel.py # 🔬 Integrated simulator panel
│   ├── 📄 pon_simulation_results_panel.py # 📊 Results panel
│   ├── 📄 graphics_popup_window.py # 🖼️ Graphics popup window
│   ├── 📄 log_panel.py         # 📋 Event log panel
│   ├── 📄 map_view.py          # 🗺️ Map view (MapBox)
│   └── 📄 splash_screen.py     # 🎬 Loading screen
│
├── 📁 utils/                    # 🛠️ Utilities and helpers
│   ├── 📄 __init__.py
│   ├── 📄 config_manager.py    # ⚙️ Configuration manager
│   ├── 📄 constants.py         # 📊 Application constants
│   ├── 📄 helpers.py           # 🔧 Auxiliary functions
│   ├── 📄 resource_manager.py  # 📦 Resource manager
│   └── 📄 validators.py        # ✅ Validators
│
├── 📁 resources/               # 🎨 Graphic resources and assets
│   ├── 📁 devices/            # 📱 Device icons
│   │   ├── 🔴 olt_icon.svg    # OLT icon (Optical Terminal)
│   │   └── 🔵 onu_icon.svg    # ONU icon (Optical Network Unit)
│   ├── 📁 icons/              # 🖼️ Application icons
│   │   ├── 📄 app_icon.ico    # Main Windows icon
│   │   ├── 📄 app_icon.png    # PNG icon
│   │   ├── 📄 app_icon.svg    # Vector icon
│   │   ├── 📄 app_icon_16x16.png
│   │   ├── 📄 app_icon_32x32.png
│   │   ├── 📄 app_icon_64x64.png
│   │   └── 📄 app_icon_128x128.png
│   ├── 📁 images/             # 🖼️ Additional images
│   ├── 📁 styles/             # 🎨 CSS style files
│   │   ├── 📄 dark_theme.qss  # Dark theme
│   │   └── 📄 light_theme.qss # Light theme
│   └── 📁 translations/       # 🌍 Translation files
│       ├── 📄 es_ES.json      # Spanish (Spain)
│       ├── 📄 en_US.json      # English (US)
│       ├── 📄 fr_FR.json      # French (France)
│       ├── 📄 pt_BR.json      # Portuguese (Brazil)
│       └── 📄 de_DE.json      # German (Germany)
│
└── 📁 temp/                    # 🗂️ Temporary files (auto-generated)
    └── 📄 autosave_*.pon      # 💾 Project auto-save
```

## 🚀 Advanced Technical Features

### **🎯 Performance and Optimization**

- **Efficient Rendering**: Canvas optimized for thousands of devices
- **Memory Management**: Automatic resource cleanup and garbage collection
- **Lazy Loading**: Progressive resource loading for fast startup
- **Intelligent Auto-save**: Automatic saving without interruptions

### **🔒 Robustness and Reliability**

- **Error Handling**: Robust exception capture and handling system
- **Data Validation**: Complete validation of inputs and formats
- **Failure Recovery**: Auto-recovery from temporary files
- **Automatic Backup**: Automatic project backup system

### **🎨 Customization and Extensibility**

- **Theme System**: Completely customizable themes (light/dark)
- **Persistent Configuration**: All preferences saved automatically
- **Modular Architecture**: Easy extension and addition of new features
- **Internal API**: Event and signal system for component communication

### **🔧 Usage Guides for RL and SDN Features**

#### **🤖 Usage Guide: Smart-RL System**

1. **🚀 Smart-RL Quick Start**:

   - Configure your PON topology (OLT + ONUs)
   - Go to RL panel (Ctrl+T) for advanced configurations
   - Select **"Smart-RL"** algorithm in simulation panel
   - Run simulation and observe automatic optimization!

2. **⚙️ Advanced Configuration**:
   - **Learning Policies**: Adjust internal policy factors
   - **Learning Rate**: Control agent learning speed
   - **Exploration vs Exploitation**: Configure balance between exploring new strategies and using known ones

#### **🌐 Usage Guide: SDN Controller**

1. **📊 Real-Time SDN Dashboard**:

   - Press `Ctrl+D` to open SDN dashboard
   - Visualize real-time metrics during simulation
   - Observe: latency per ONU, throughput, fairness, buffer levels

2. **🎛️ Centralized Control**:
   - Select **"SDN"** algorithm for pure SDN control
   - OLT_SDN controller automatically manages network
   - Fairness metrics calculated automatically with Jain index

#### **🚀 Usage Guide: Smart-RL-SDN Hybrid Algorithm**

1. **💫 Best of Both Worlds**:

   - Select **"Smart-RL-SDN"** algorithm for maximum performance
   - RL agent makes intelligent decisions
   - SDN controller implements them and provides feedback
   - Observe continuous optimization in dashboard

2. **📈 Results Analysis**:
   - Compare results between different algorithms
   - Analyze fairness and performance metrics
   - Export automatically generated graphics

---

## 🤖 **Artificial Intelligence and Advanced Optimization**

### **🧠 Smart-RL System Features**

PonLab incorporates a **completely internal Reinforcement Learning system** that requires no additional external dependencies:

#### **🎯 Implemented Intelligent Policies**

- **`prioritize_low_buffer`** (Factor: 0.7): Prioritizes ONUs with buffers near saturation
- **`balance_throughput`** (Factor: 0.6): Balances throughput among all users
- **`minimize_delay`** (Factor: 0.8): Optimizes to reduce average latency
- **`fairness_factor`** (Factor: 0.5): Guarantees equitable resource distribution

#### **🔄 Learning Mechanism**

- **Internal Q-Table**: Reinforcement learning system with discrete states
- **Dynamic Observation**: Continuous network state analysis (buffer levels, requests, throughput)
- **Intelligent Actions**: Bandwidth allocation decisions based on multiple policies
- **Continuous Adaptation**: Agent improves its decisions with each simulation cycle

#### **📊 RL Metrics and Analysis**

- **Decision Count**: Tracking of number of decisions made
- **Policy Performance**: Analysis of each policy's performance
- **Learning Progress**: Visualization of learning progress
- **State Space Analysis**: Analysis of explored state space

### **🌐 Integrated SDN System**

#### **🎛️ OLT_SDN Controller**

- **Centralized Control**: Single control point for entire PON network
- **Global View**: Complete knowledge of all ONU states
- **Dynamic Policies**: Automatic implementation of network rules
- **Continuous Monitoring**: Constant performance metrics collection

#### **📈 Advanced SDN Metrics**

- **Latency per ONU**: Individual delay measurement for each terminal
- **Aggregate Throughput**: Measurement of total network performance
- **Buffer Occupancy**: Real-time buffer level monitoring
- **Link Utilization**: Analysis of fiber link utilization
- **Jain Fairness Index**: Automatic calculation of equity index

#### **🚀 Smart-RL-SDN Hybrid Algorithm**

**Revolutionary Architecture** combining the best of both worlds:

1. **RL Decision Layer**: Smart-RL agent analyzes global state and makes intelligent decisions
2. **SDN Implementation Layer**: SDN controller implements decisions and monitors results
3. **Intelligent Feedback**: SDN provides performance metrics to RL agent
4. **Continuous Optimization**: System continuously self-optimizes based on results

#### **💡 Hybrid Approach Advantages**

- **🎯 RL Precision**: Intelligent decisions based on learning
- **⚡ SDN Speed**: Fast implementation and real-time monitoring
- **🔄 Adaptability**: Ability to adapt to changes in traffic patterns
- **📊 Complete Analysis**: Detailed metrics from both systems
- **🚀 Optimal Performance**: Combines RL flexibility with precise SDN control

---

## 📚 **Use Cases and Applications**

### **🎓 Academic Research**

- Simulation of custom DBA algorithms
- Research in Reinforcement Learning for optical networks
- Comparative performance analysis of algorithms
- Development of new bandwidth allocation policies

### **🏢 Industrial Development**

- PON network prototyping before deployment
- Optimization of existing network configurations
- Capacity analysis and growth planning
- Evaluation of new control algorithms

### **📖 Education and Training**

- Teaching of PON network concepts
- Practical demonstration of DBA algorithms
- Training in Artificial Intelligence applied to networks
- SDN and network control workshops

---

## 🤝 **Contributing**

We welcome contributions! If you want to contribute to PonLab:

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. Open a **Pull Request**

### **Contribution Guidelines**

- Follow PEP 8 style for Python code
- Add tests for new functionalities
- Update documentation as needed
- Maintain compatibility with Python 3.8+
- Ensure all tests pass before submitting PR

---

## 📄 **License**

This project is under development for academic and research purposes. Please contact the authors for information about licensing and usage.

---

## 👥 **Authors and Contact**

### **Development Team**

- **Alex Aravena Tapia** - Lead Developer
- **Jesús Chaffe González** - Core Algorithms
- **Eduardo Maldonado Zamora** - UI/UX Design
- **Jorge Barrios Núñez** - Network Architecture

### **Contact**

- **GitHub Repository**: [https://github.com/alex-itico/PonLab](https://github.com/alex-itico/PonLab)
- **Email**: [contact information]

---

## 🙏 **Acknowledgments**

- Thanks to the Python and PyQt5 communities for their excellent tools
- Thanks to the Reinforcement Learning and SDN research communities
- Special thanks to all contributors and testers

---

## 📝 **Version History**

### **Version 2.1.0** (Current)
- ✨ Added complete multilanguage support (5 languages)
- 🌍 Spanish, English, French, Portuguese, German translations
- 🎨 Translated matplotlib charts and all UI components
- 📊 660+ translation keys covering entire application
- 🔧 Improved language switching system
- 📖 Created English README for international visibility

### **Version 2.0.0**
- 🤖 Implementation of Smart-RL system
- 🌐 Integration of SDN controller
- 🚀 Development of Smart-RL-SDN hybrid algorithm
- 📊 Advanced metrics dashboard
- ⚖️ Automatic fairness analysis with Jain index

### **Version 1.0.0**
- 🎨 Initial graphical interface
- 🔧 Basic device management
- 🔗 Connection system
- 🧪 PON simulation integration

---

<div align="center">

**Made with ❤️ for the PON networks and Artificial Intelligence community**

_PonLab - Connecting the future of optical networks with intelligent technology_

</div>
