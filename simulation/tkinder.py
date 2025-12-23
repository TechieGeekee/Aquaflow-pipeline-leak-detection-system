import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from datetime import datetime

# Firebase imports - with graceful fallback
try:
    import firebase_admin
    from firebase_admin import credentials, db
    from firebase_admin.exceptions import FirebaseError
    FIREBASE_AVAILABLE = True
    print("Firebase library loaded successfully")
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Firebase library not available. Running in offline mode.")

class WaterSystemGUI:

    def start_firebase_listener(self):
        """Safe Firebase listener that runs in a background thread."""
        if not self.firebase_initialized:
            print("Firebase not initialized, listener not started.")
            return

        print("Starting Firebase listener...")

        def listener_loop():
            while True:
                try:
                    data = self.firebase_ref.get()
                    if data:
                        # You can process incoming Firebase values here
                        pass
                except Exception as e:
                    print("Firebase listener error:", e)
                
                time.sleep(2)  # poll every 2 seconds

        threading.Thread(target=listener_loop, daemon=True).start() 

    def __init__(self, root):
        self.root = root
        self.root.title("WATER SYSTEM SIMULATION WITH FIREBASE")
        # CHANGED: Increased height from 600 to 900 to fit all controls
        self.root.geometry("1000x900") 
        self.root.configure(bg='white')
        # Active leak states (leaks with water flowing)
        self.active_leaks = {}
        
        # Firebase configuration
        self.firebase_initialized = False
        self.firebase_ref = None
        self.last_update_time = 0
        self.update_interval = 2  # seconds
        
        # Initialize system states
        # TAP states: True = open (water flowing), False = closed (no water)
        self.tap_states = {
            "TAP1": False,  # Initially closed
            "TAP2": False,
            "TAP3": False,
            "TAP4": False,
            "TAP5": False
        }
        
        # Pipe leak states: True = has leak, False = no leak
        self.pipe_leaks = {
            "TANK-S1": False,
            "S1-S2": False,
            "S2-VALVE_A": False,
            "VALVE_A-S3": False,
            "S3-TAP1": False,
            "VALVE_A-S4": False,
            "S4-TAP2": False,
            "VALVE_A-S5": False,
            "S5-JUNCTION_E": False,
            "JUNCTION_E-S6": False,
            "S6-TAP3": False,
            "JUNCTION_E-S7": False,
            "S7-TAP4": False,
            "JUNCTION_E-S8": False,
            "S8-TAP5": False
        }
        
        # Valve states: True = open (water can flow), False = closed (no water)
        self.valve_states = {
            "TANK_VALVE": True,  # Tank valve initially open
            "VALVE_A": True      # Valve A initially open
        }
        
        # Water flow status for each pipe
        self.water_flow = {}
        
        # Initialize sensor values
        self.ph_value = tk.DoubleVar(value=7.0)
        self.turbidity_value = tk.DoubleVar(value=5.0)
        self.salinity_value = tk.DoubleVar(value=0.5)
        self.flow_value = tk.DoubleVar(value=2.5)
        self.water_level_value = tk.IntVar(value=49)
        
        # Firebase status
        self.firebase_status_var = tk.StringVar(value="Firebase: Checking...")
        
        # Variables for scroll region
        self.canvas_width = 1200
        self.canvas_height = 800
        
        # Setup GUI
        self.setup_gui()
        
        # Setup Firebase - with error handling
        self.setup_firebase_safe()
        
        # Start Firebase listener thread if initialized
        if self.firebase_initialized:
            self.start_firebase_listener()
    
    def setup_gui(self):
        # Main container with two columns
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left column for controls (1/3 of width)
        left_frame = tk.Frame(main_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Right column for visualization (2/3 of width)
        right_frame = tk.Frame(main_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Setup left panel
        self.setup_control_panel(left_frame)
        
        # Setup right panel with scrollable canvas
        self.setup_scrollable_visualization_panel(right_frame)
    
    def setup_control_panel(self, parent):
        # Title with Firebase status
        title_frame = tk.Frame(parent, bg='white')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame, 
            text="WATER SYSTEM SIMULATION",
            font=('Helvetica', 18, 'bold'),
            bg='white',
            fg='#1a5a99'
        )
        title_label.pack()
        
        # Firebase status label
        self.firebase_status_label = tk.Label(
            title_frame,
            textvariable=self.firebase_status_var,
            font=('Helvetica', 10),
            bg='white',
            fg='#666666'
        )
        self.firebase_status_label.pack(pady=(5, 0))
        
        # SENSOR CONTROLS section
        sensor_frame = tk.LabelFrame(
            parent,
            text="SENSOR CONTROLS",
            font=('Helvetica', 12, 'bold'),
            bg='white',
            fg='#1a5a99',
            bd=2,
            relief=tk.GROOVE,
            padx=15,
            pady=15
        )
        sensor_frame.pack(fill=tk.X, pady=(0, 20))
        
        # pH Sensor
        ph_frame = tk.Frame(sensor_frame, bg='white')
        ph_frame.pack(fill=tk.X, pady=5)
        
        # pH label and value display
        ph_label_frame = tk.Frame(ph_frame, bg='white')
        ph_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            ph_label_frame,
            text="pH Sensor",
            font=('Helvetica', 11, 'bold'),
            bg='white'
        ).pack(side=tk.LEFT)
        
        self.ph_display = tk.Label(
            ph_label_frame,
            text="7.0",
            font=('Helvetica', 11, 'bold'),
            bg='white',
            fg='#1a5a99',
            width=6
        )
        self.ph_display.pack(side=tk.RIGHT)
        
        # pH slider with min/max labels and slider label
        ph_slider_frame = tk.Frame(ph_frame, bg='white')
        ph_slider_frame.pack(fill=tk.X)
        
        # Min value label
        min_label = tk.Label(
            ph_slider_frame,
            text="7.0",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        min_label.pack(side=tk.LEFT)
        
        # Max value label - PACKED RIGHT FIRST
        max_label = tk.Label(
            ph_slider_frame,
            text="7.8",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        max_label.pack(side=tk.RIGHT)

        # pH slider
        ph_slider = tk.Scale(
            ph_slider_frame,
            from_=0,
            to=14,
            orient=tk.HORIZONTAL,
            variable=self.ph_value,
            resolution=0.1,
            length=200,
            bg='white',
            fg='#1a5a99',
            troughcolor='#e6f2ff',
            highlightbackground='white',
            showvalue=False,
            command=self.update_ph_display
        )
        ph_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # pH slider range label
        ph_range_label = tk.Label(
            ph_frame,
            text="pH Scale (0-14)",
            font=('Helvetica', 9),
            bg='white',
            fg='#666666'
        )
        ph_range_label.pack(pady=(5, 0))
        
        # Turbidity Sensor
        turb_frame = tk.Frame(sensor_frame, bg='white')
        turb_frame.pack(fill=tk.X, pady=15)
        
        # Turbidity label and value display
        turb_label_frame = tk.Frame(turb_frame, bg='white')
        turb_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            turb_label_frame,
            text="Turbidity Sensor",
            font=('Helvetica', 11, 'bold'),
            bg='white'
        ).pack(side=tk.LEFT)
        
        self.turb_display = tk.Label(
            turb_label_frame,
            text="5.0",
            font=('Helvetica', 11, 'bold'),
            bg='white',
            fg='#1a5a99',
            width=6
        )
        self.turb_display.pack(side=tk.RIGHT)
        
        # Turbidity slider with min/max labels and slider label
        turb_slider_frame = tk.Frame(turb_frame, bg='white')
        turb_slider_frame.pack(fill=tk.X)
        
        # Min value label
        turb_min_label = tk.Label(
            turb_slider_frame,
            text="5.0",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        turb_min_label.pack(side=tk.LEFT)

        # Max value label - PACKED RIGHT FIRST
        turb_max_label = tk.Label(
            turb_slider_frame,
            text="5.5",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        turb_max_label.pack(side=tk.RIGHT)
        
        # Turbidity slider
        turb_slider = tk.Scale(
            turb_slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.turbidity_value,
            resolution=0.1,
            length=200,
            bg='white',
            fg='#1a5a99',
            troughcolor='#e6f2ff',
            highlightbackground='white',
            showvalue=False,
            command=self.update_turbidity_display
        )
        turb_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Turbidity slider range label
        turb_range_label = tk.Label(
            turb_frame,
            text="NTU (Nephelometric Turbidity Units)",
            font=('Helvetica', 9),
            bg='white',
            fg='#666666'
        )
        turb_range_label.pack(pady=(5, 0))
        
        # Salinity Sensor
        sal_frame = tk.Frame(sensor_frame, bg='white')
        sal_frame.pack(fill=tk.X, pady=15)
        
        # Salinity label and value display
        sal_label_frame = tk.Frame(sal_frame, bg='white')
        sal_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            sal_label_frame,
            text="Salinity Sensor",
            font=('Helvetica', 11, 'bold'),
            bg='white'
        ).pack(side=tk.LEFT)
        
        self.sal_display = tk.Label(
            sal_label_frame,
            text="0.5",
            font=('Helvetica', 11, 'bold'),
            bg='white',
            fg='#1a5a99',
            width=6
        )
        self.sal_display.pack(side=tk.RIGHT)
        
        # Salinity slider with min/max labels and slider label
        sal_slider_frame = tk.Frame(sal_frame, bg='white')
        sal_slider_frame.pack(fill=tk.X)
        
        # Min value label
        sal_min_label = tk.Label(
            sal_slider_frame,
            text="0.5",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        sal_min_label.pack(side=tk.LEFT)
        
        # Max value label - PACKED RIGHT FIRST
        sal_max_label = tk.Label(
            sal_slider_frame,
            text="0.5",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        sal_max_label.pack(side=tk.RIGHT)

        # Salinity slider
        sal_slider = tk.Scale(
            sal_slider_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.salinity_value,
            resolution=0.01,
            length=200,
            bg='white',
            fg='#1a5a99',
            troughcolor='#e6f2ff',
            highlightbackground='white',
            showvalue=False,
            command=self.update_salinity_display
        )
        sal_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Salinity slider range label
        sal_range_label = tk.Label(
            sal_frame,
            text="g/L (grams per liter)",
            font=('Helvetica', 9),
            bg='white',
            fg='#666666'
        )
        sal_range_label.pack(pady=(5, 0))
        
        # Flow Sensor
        flow_frame = tk.Frame(sensor_frame, bg='white')
        flow_frame.pack(fill=tk.X, pady=(15, 5))
        
        # Flow label and value display
        flow_label_frame = tk.Frame(flow_frame, bg='white')
        flow_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            flow_label_frame,
            text="Flow Sensor",
            font=('Helvetica', 11, 'bold'),
            bg='white'
        ).pack(side=tk.LEFT)
        
        self.flow_display = tk.Label(
            flow_label_frame,
            text="2.5",
            font=('Helvetica', 11, 'bold'),
            bg='white',
            fg='#1a5a99',
            width=6
        )
        self.flow_display.pack(side=tk.RIGHT)
        
        # Flow slider with min/max labels and slider label
        flow_slider_frame = tk.Frame(flow_frame, bg='white')
        flow_slider_frame.pack(fill=tk.X)
        
        # Min value label
        flow_min_label = tk.Label(
            flow_slider_frame,
            text="0.0",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        flow_min_label.pack(side=tk.LEFT)

        # Max value label - PACKED RIGHT FIRST
        flow_max_label = tk.Label(
            flow_slider_frame,
            text="10.0",
            font=('Helvetica', 10),
            bg='white',
            width=4
        )
        flow_max_label.pack(side=tk.RIGHT)
        
        # Flow slider
        flow_slider = tk.Scale(
            flow_slider_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.flow_value,
            resolution=0.1,
            length=200,
            bg='white',
            fg='#1a5a99',
            troughcolor='#e6f2ff',
            highlightbackground='white',
            showvalue=False,
            command=self.update_flow_display
        )
        flow_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Flow slider range label
        flow_range_label = tk.Label(
            flow_frame,
            text="L/min (liters per minute)",
            font=('Helvetica', 9),
            bg='white',
            fg='#666666'
        )
        flow_range_label.pack(pady=(5, 0))
        
        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill=tk.X, pady=20)
        
        # WATER LEVEL CONTROL section
        water_level_frame = tk.LabelFrame(
            parent,
            text="WATER LEVEL CONTROL",
            font=('Helvetica', 12, 'bold'),
            bg='white',
            fg='#1a5a99',
            bd=2,
            relief=tk.GROOVE,
            padx=15,
            pady=15
        )
        water_level_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Water level percentage display
        level_display_frame = tk.Frame(water_level_frame, bg='white')
        level_display_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.water_level_label = tk.Label(
            level_display_frame,
            text="49%",
            font=('Helvetica', 24, 'bold'),
            bg='white',
            fg='#1a5a99'
        )
        self.water_level_label.pack()
        
        # Water level slider with min/max labels
        water_slider_frame = tk.Frame(water_level_frame, bg='white')
        water_slider_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Min label (0%)
        tk.Label(
            water_slider_frame,
            text="0%",
            font=('Helvetica', 10),
            bg='white',
            width=4
        ).pack(side=tk.LEFT)

        # Max label (100%) - MOVED UP and PACKED RIGHT to ensure it stays visible
        tk.Label(
            water_slider_frame,
            text="100%",
            font=('Helvetica', 10),
            bg='white',
            width=4
        ).pack(side=tk.RIGHT)
        
        # Water level slider - PACKED LAST with Fill/Expand
        water_slider = tk.Scale(
            water_slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.water_level_value,
            length=250,
            bg='white',
            fg='#1a5a99',
            troughcolor='#e6f2ff',
            highlightbackground='white',
            showvalue=False,
            sliderlength=20,
            width=15,
            command=self.update_water_level_display
        )
        water_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Water level slider label
        water_slider_label = tk.Label(
            water_level_frame,
            text="Adjust Tank Water Level",
            font=('Helvetica', 9),
            bg='white',
            fg='#666666'
        )
        water_slider_label.pack(pady=(5, 0))
        
        # Separator
        separator2 = ttk.Separator(parent, orient='horizontal')
        separator2.pack(fill=tk.X, pady=20)
        
        # VALVE CONTROL section
        valve_frame = tk.LabelFrame(
            parent,
            text="VALVE CONTROLS",
            font=('Helvetica', 12, 'bold'),
            bg='white',
            fg='#1a5a99',
            bd=2,
            relief=tk.GROOVE,
            padx=15,
            pady=15
        )
        valve_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Tank Valve Control
        tank_valve_frame = tk.Frame(valve_frame, bg='white')
        tank_valve_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            tank_valve_frame,
            text="Tank Valve:",
            font=('Helvetica', 11, 'bold'),
            bg='white',
            fg='#1a5a99'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        # Create a frame for the button with fixed size
        tank_button_frame = tk.Frame(tank_valve_frame, bg='white')
        tank_button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tank_valve_button = tk.Button(
            tank_button_frame,
            text="OPEN",
            font=('Helvetica', 11, 'bold'),
            bg='#0066cc',  # BLUE BACKGROUND
            fg='white',    # WHITE TEXT
            activebackground='#004499',  # DARKER BLUE WHEN PRESSED
            activeforeground='white',    # WHITE TEXT WHEN PRESSED
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=3,
            command=self.toggle_tank_valve
        )
        self.tank_valve_button.pack()
        
        # Valve A Control
        valve_a_frame = tk.Frame(valve_frame, bg='white')
        valve_a_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            valve_a_frame,
            text="Valve A:",
            font=('Helvetica', 11, 'bold'),
            bg='white',
            fg='#1a5a99'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        # Create a frame for the button with fixed size
        valve_a_button_frame = tk.Frame(valve_a_frame, bg='white')
        valve_a_button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.valve_a_button = tk.Button(
            valve_a_button_frame,
            text="OPEN",
            font=('Helvetica', 11, 'bold'),
            bg='#0066cc',  # BLUE BACKGROUND
            fg='white',    # WHITE TEXT
            activebackground='#004499',  # DARKER BLUE WHEN PRESSED
            activeforeground='white',    # WHITE TEXT WHEN PRESSED
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=3,
            command=self.toggle_valve_a
        )
        self.valve_a_button.pack()
        
        # Instructions for valve controls
        valve_instructions = tk.Label(
            valve_frame,
            text="Click buttons to open/close valves",
            font=('Helvetica', 9),
            bg='white',
            fg='#666666'
        )
        valve_instructions.pack(pady=(10, 0))
        
        # Firebase Control Section (only if Firebase is available)
        if FIREBASE_AVAILABLE:
            firebase_frame = tk.LabelFrame(
                parent,
                text="FIREBASE CONTROLS",
                font=('Helvetica', 12, 'bold'),
                bg='white',
                fg='#1a5a99',
                bd=2,
                relief=tk.GROOVE,
                padx=15,
                pady=15
            )
            firebase_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Firebase control buttons
            firebase_buttons_frame = tk.Frame(firebase_frame, bg='white')
            firebase_buttons_frame.pack(fill=tk.X, pady=5)
            
            # Send data button
            send_button = tk.Button(
                firebase_buttons_frame,
                text="Send Data to Firebase",
                font=('Helvetica', 10, 'bold'),
                bg='#4CAF50',
                fg='white',
                width=20,
                command=self.send_all_data_to_firebase
            )
            send_button.pack(side=tk.LEFT, padx=(0, 10))
            
            # Check leak status button
            check_leak_button = tk.Button(
                firebase_buttons_frame,
                text="Check Leak Status",
                font=('Helvetica', 10, 'bold'),
                bg='#FF9800',
                fg='white',
                width=15,
                command=self.check_leak_status
            )
            check_leak_button.pack(side=tk.RIGHT)
        
        # Instructions
        instructions_frame = tk.Frame(parent, bg='white')
        instructions_frame.pack(fill=tk.X, pady=10)
        
        instructions = tk.Label(
            instructions_frame,
            text="1. Click on TAPs to open/close them\n2. Click on pipes to add/remove leaks\n3. Open/Close valves using control buttons" +
                 ("\n4. Use Firebase to sync data in real-time" if FIREBASE_AVAILABLE else ""),
            font=('Helvetica', 10),
            bg='white',
            fg='#666666',
            justify=tk.LEFT
        )
        instructions.pack(anchor='w')
    
    def setup_scrollable_visualization_panel(self, parent):
        # Create a frame for the canvas and scrollbars
        canvas_frame = tk.Frame(parent, bg='white')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create vertical scrollbar
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create horizontal scrollbar
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(
            canvas_frame, 
            bg='white',
            highlightthickness=0,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            scrollregion=(0, 0, self.canvas_width, self.canvas_height)
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)    # Linux scroll down
        
        # Bind click events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Draw the initial water system
        self.calculate_water_flow()
        self.draw_water_system()
    
    def setup_firebase_safe(self):
        """Initialize Firebase connection safely"""
        if not FIREBASE_AVAILABLE:
            self.firebase_status_var.set("Firebase: Library not installed")
            self.firebase_status_label.config(fg='#666666')
            print("Running in offline mode - Firebase library not installed")
            return
        
        try:
            # Check for service account key
            service_account_paths = [
                'serviceAccountKey.json',
                'firebase-key.json',
                'key.json',
                './config/serviceAccountKey.json'
            ]
            
            service_account_path = None
            for path in service_account_paths:
                if os.path.exists(path):
                    service_account_path = path
                    print(f"Found service account key: {path}")
                    break
            
            if service_account_path:
                # Initialize with service account
                cred = credentials.Certificate(service_account_path)
                
                # Try to get database URL from environment or use default
                database_url = os.environ.get('FIREBASE_DB_URL', 
                                            'https://aterleak2-default-rtdb.firebaseio.com/')
                
                firebase_admin.initialize_app(cred, {
                    'databaseURL': database_url
                })
                
                self.firebase_ref = db.reference('/water_system')
                self.firebase_initialized = True
                self.firebase_status_var.set("Firebase: Connected ✓")
                self.firebase_status_label.config(fg='#4CAF50')
                print(f"Firebase initialized successfully with URL: {database_url}")
                
                # Send initial data
                self.send_all_data_to_firebase()
                
            else:
                # No service account found
                self.firebase_status_var.set("Firebase: No service account key")
                self.firebase_status_label.config(fg='#FF9800')
                print("No Firebase service account key found. Running in offline mode.")
                
                # Create mock Firebase for offline mode
                self.create_mock_firebase()
                
        except Exception as e:
            self.firebase_status_var.set("Firebase: Connection failed")
            self.firebase_status_label.config(fg='#FF0000')
            print(f"Firebase setup error: {e}")
            
            # Create mock Firebase for offline mode
            self.create_mock_firebase()
    
    def create_mock_firebase(self):
        """Create a mock Firebase object for offline mode"""
        class MockFirebaseRef:
            def __init__(self):
                self.data = {}
                print("Created mock Firebase for offline mode")
            
            def get(self):
                return self.data
            
            def set(self, data):
                self.data = data
                print("Mock Firebase: Data saved (offline mode)")
            
            def child(self, path):
                return self
            
            def update(self, data):
                self.data.update(data)
                print(f"Mock Firebase: Data updated (offline mode)")
        
        self.firebase_ref = MockFirebaseRef()
        self.firebase_initialized = False
    
    def _on_mousewheel(self, event):
        # Handle mouse wheel scrolling
        if event.num == 5 or event.delta == -120:  # Scroll down
            self.canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta == 120:   # Scroll up
            self.canvas.yview_scroll(-1, "units")
    
    def calculate_water_flow(self):
        """Calculate water flow through pipes and determine active leaks"""
        # Reset all water flow status
        for pipe_id in self.pipe_leaks.keys():
            self.water_flow[pipe_id] = False
        
        # Reset active leaks detection
        self.active_leaks = {}
        
        # Check if water can flow from tank (tank valve must be open and water level > 0)
        water_available = self.valve_states["TANK_VALVE"] and self.water_level_value.get() > 0
        
        if not water_available:
            # Send water flow status even when no flow
            if self.firebase_initialized:
                self.send_water_flow_to_firebase()
            return  # No water flow if tank valve is closed or empty
        
        # Water flow path calculation
        # Tank -> S1
        self.water_flow["TANK-S1"] = True
        
        # S1 -> S2
        self.water_flow["S1-S2"] = True
        
        # S2 -> VALVE_A
        self.water_flow["S2-VALVE_A"] = True
        
        # From VALVE_A (only if valve A is open)
        if self.valve_states["VALVE_A"]:
            # VALVE_A -> S3 -> TAP1
            self.water_flow["VALVE_A-S3"] = True
            if self.tap_states["TAP1"]:
                self.water_flow["S3-TAP1"] = True
            
            # VALVE_A -> S4 -> TAP2
            self.water_flow["VALVE_A-S4"] = True
            if self.tap_states["TAP2"]:
                self.water_flow["S4-TAP2"] = True
            
            # VALVE_A -> S5 -> JUNCTION_E
            self.water_flow["VALVE_A-S5"] = True
            self.water_flow["S5-JUNCTION_E"] = True
            
            # From JUNCTION_E to other taps
            # JUNCTION_E -> S6 -> TAP3
            self.water_flow["JUNCTION_E-S6"] = True
            if self.tap_states["TAP3"]:
                self.water_flow["S6-TAP3"] = True
            
            # JUNCTION_E -> S7 -> TAP4
            self.water_flow["JUNCTION_E-S7"] = True
            if self.tap_states["TAP4"]:
                self.water_flow["S7-TAP4"] = True
            
            # JUNCTION_E -> S8 -> TAP5
            self.water_flow["JUNCTION_E-S8"] = True
            if self.tap_states["TAP5"]:
                self.water_flow["S8-TAP5"] = True
        
        # Calculate active leaks (leaks with water flow)
        self.calculate_active_leaks()
        
        # Send water flow status after calculation
        if self.firebase_initialized:
            self.send_water_flow_to_firebase()
            self.send_active_leaks_to_firebase()

    def calculate_active_leaks(self):
        """Calculate which leaks are active (water flowing through leaking pipes)"""
        self.active_leaks = {}
        
        for pipe_id, has_leak in self.pipe_leaks.items():
            if has_leak and self.water_flow.get(pipe_id, False):
                # This is an active leak (water flowing through a leaking pipe)
                self.active_leaks[pipe_id] = True
            else:
                self.active_leaks[pipe_id] = False

    def send_active_leaks_to_firebase(self):
        """Send active leak status to Firebase"""
        if not self.firebase_initialized:
            return
            
        try:
            active_leaks_data = {pipe: int(is_active) for pipe, is_active in self.active_leaks.items()}
            self.firebase_ref.child('active_leaks').set(active_leaks_data)
            print(f"Active leaks sent to Firebase: {active_leaks_data}")
            
        except Exception as e:
            print(f"Error sending active leaks to Firebase: {e}")
    
    def draw_water_system(self):
        canvas = self.canvas
        canvas.delete("all")
        
        # Scale down the entire diagram
        scale_factor = 0.7  # You can adjust this value
        
        # Calculate positions for the expanded layout
        tank_x = 80 * scale_factor  # Changed from 100
        tank_y = 250 * scale_factor  # Changed from 300
        tank_width = 100 * scale_factor  # Changed from 120
        tank_height = 150 * scale_factor  # Changed from 200
        
        # Draw the tank with water
        tank_color = '#e6f2ff'
        tank_outline = '#1a5a99'
        
        # Tank outline
        canvas.create_rectangle(
            tank_x, tank_y, 
            tank_x + tank_width, tank_y + tank_height,
            outline=tank_outline, width=3, fill=tank_color,
            tags=("tank", "clickable")
        )
        
        # Draw water in tank based on water level
        water_level = self.water_level_value.get()
        water_height = tank_height * (water_level / 100)
        water_y = tank_y + tank_height - water_height
        
        water_color = '#66b3ff' if water_level > 0 else '#cccccc'
        
        canvas.create_rectangle(
            tank_x, water_y, 
            tank_x + tank_width, tank_y + tank_height,
            outline='', fill=water_color,
            tags=("water", "clickable")
        )
        
        # Draw water level percentage inside tank
        canvas.create_text(
            tank_x + tank_width/2, tank_y + tank_height/2,
            text=f"{water_level}%",
            font=('Helvetica', 16, 'bold'),
            fill='#1a5a99',
            tags=("water_level_display", "clickable")
        )
        
        # Tank label above the tank
        canvas.create_text(
            tank_x + tank_width/2, tank_y - 25,
            text="TANK",
            font=('Helvetica', 14, 'bold'),
            fill='#1a5a99',
            tags=("tank_label", "clickable")
        )
        
        # Draw tank valve indicator
        tank_valve_color = '#0066cc' if self.valve_states["TANK_VALVE"] else '#ff3333'
        tank_valve_text = "OPEN" if self.valve_states["TANK_VALVE"] else "CLOSED"
        
        canvas.create_rectangle(
            tank_x + tank_width/2 - 25, tank_y + tank_height + 20,
            tank_x + tank_width/2 + 25, tank_y + tank_height + 50,
            outline='#1a5a99', width=2, fill=tank_valve_color,
            tags=("tank_valve", "clickable")
        )
        
        canvas.create_text(
            tank_x + tank_width/2, tank_y + tank_height + 35,
            text="Tank\nValve",
            font=('Helvetica', 8, 'bold'),
            fill='white',
            tags=("tank_valve_label", "clickable")
        )
        
        # Position nodes with sensor nodes between all pipelines
        # Position nodes with sensor nodes between all pipelines
        current_x = tank_x + tank_width + 80 * scale_factor  # Changed from +100
        base_y = tank_y + tank_height/2

        # Reduce horizontal spacing
        s1_x = current_x
        s1_y = base_y
        current_x += 120 * scale_factor  # Changed from 150

        s2_x = current_x
        s2_y = base_y
        current_x += 120 * scale_factor  # Changed from 150

        # Reduce valve spacing
        valve_a_x = current_x
        valve_a_y = base_y
        current_x += 120 * scale_factor  # Changed from 150
        
        # Create TAP positions
        tap_positions = []
        
        # TAP1 - from valve A via sensor S3 (top left)
        tap1_x = valve_a_x - 150
        tap1_y = valve_a_y - 150
        tap_positions.append((tap1_x, tap1_y, "TAP1"))
        
        # TAP2 - from valve A via sensor S4 (bottom left)
        tap2_x = valve_a_x - 150
        tap2_y = valve_a_y + 150
        tap_positions.append((tap2_x, tap2_y, "TAP2"))
        
        # JUNCTION E - from valve A via sensor S5
        junction_e_x = valve_a_x + 250
        junction_e_y = valve_a_y
        
        # TAP3 - from junction E via sensor S6 (top right)
        tap3_x = junction_e_x + 200
        tap3_y = junction_e_y - 120
        tap_positions.append((tap3_x, tap3_y, "TAP3"))
        
        # TAP4 - from junction E via sensor S7 (middle right)
        tap4_x = junction_e_x + 200
        tap4_y = junction_e_y
        tap_positions.append((tap4_x, tap4_y, "TAP4"))
        
        # TAP5 - from junction E via sensor S8 (bottom right)
        tap5_x = junction_e_x + 200
        tap5_y = junction_e_y + 120
        tap_positions.append((tap5_x, tap5_y, "TAP5"))
        
        # Sensor nodes between valve A and TAPs
        sensor_positions = []
        
        # Sensor S3 - between valve A and TAP1
        s3_x = (valve_a_x + tap1_x) / 2
        s3_y = (valve_a_y + tap1_y) / 2
        sensor_positions.append((s3_x, s3_y, "S3"))
        
        # Sensor S4 - between valve A and TAP2
        s4_x = (valve_a_x + tap2_x) / 2
        s4_y = (valve_a_y + tap2_y) / 2
        sensor_positions.append((s4_x, s4_y, "S4"))
        
        # Sensor S5 - between valve A and junction E
        s5_x = (valve_a_x + junction_e_x) / 2
        s5_y = (valve_a_y + junction_e_y) / 2
        sensor_positions.append((s5_x, s5_y, "S5"))
        
        # Sensor nodes between junction E and TAPs
        s6_x = (junction_e_x + tap3_x) / 2
        s6_y = (junction_e_y + tap3_y) / 2
        sensor_positions.append((s6_x, s6_y, "S6"))
        
        s7_x = (junction_e_x + tap4_x) / 2
        s7_y = (junction_e_y + tap4_y) / 2
        sensor_positions.append((s7_x, s7_y, "S7"))
        
        s8_x = (junction_e_x + tap5_x) / 2
        s8_y = (junction_e_y + tap5_y) / 2
        sensor_positions.append((s8_x, s8_y, "S8"))
        
        # Draw all sensor nodes (S1-S8)
        sensor_nodes = [
            (s1_x, s1_y, "S1"),
            (s2_x, s2_y, "S2"),
            (s3_x, s3_y, "S3"),
            (s4_x, s4_y, "S4"),
            (s5_x, s5_y, "S5"),
            (s6_x, s6_y, "S6"),
            (s7_x, s7_y, "S7"),
            (s8_x, s8_y, "S8")
        ]
        
        for sensor_x, sensor_y, sensor_name in sensor_nodes:
            canvas.create_oval(
                sensor_x - 20, sensor_y - 20,
                sensor_x + 20, sensor_y + 20,
                outline='#1a5a99', width=2, fill='#ccffff',
                tags=(f"node_{sensor_name}", "sensor", "clickable")
            )
            
            canvas.create_text(
                sensor_x, sensor_y,
                text=sensor_name,
                font=('Helvetica', 10, 'bold'),
                fill='#1a5a99',
                tags=(f"node_{sensor_name}_label", "clickable")
            )
        
        # Draw Valve A
        valve_a_color = '#0066cc' if self.valve_states["VALVE_A"] else '#ff3333'
        points = [
            valve_a_x, valve_a_y - 30,  # top
            valve_a_x + 30, valve_a_y,  # right
            valve_a_x, valve_a_y + 30,  # bottom
            valve_a_x - 30, valve_a_y   # left
        ]
        canvas.create_polygon(
            points,
            outline='#1a5a99', width=3, fill=valve_a_color,
            tags=("node_VALVE_A", "valve", "clickable")
        )
        
        canvas.create_text(
            valve_a_x, valve_a_y,
            text="VALVE A",
            font=('Helvetica', 10, 'bold'),
            fill='white',
            tags=("node_VALVE_A_label", "clickable")
        )
        
        # Draw Junction E
        canvas.create_rectangle(
            junction_e_x - 40, junction_e_y - 25,
            junction_e_x + 40, junction_e_y + 25,
            outline='#1a5a99', width=3, fill='#ccffcc',
            tags=("node_JUNCTION_E", "junction", "clickable")
        )
        
        canvas.create_text(
            junction_e_x, junction_e_y,
            text="JUNCTION E",
            font=('Helvetica', 10, 'bold'),
            fill='#1a5a99',
            tags=("node_JUNCTION_E_label", "clickable")
        )
        
        # Store node positions for click detection
        self.node_areas = {}
        self.tap_areas = {}
        
        # Draw all TAP nodes with appropriate colors
        for tap_x, tap_y, tap_name in tap_positions:
            # Determine tap color: RED if open, GREEN if closed
            tap_color = '#ff3333' if self.tap_states[tap_name] else '#00cc66'
            
            canvas.create_rectangle(
                tap_x - 35, tap_y - 20,
                tap_x + 35, tap_y + 20,
                outline='#1a5a99', width=3, fill=tap_color,
                tags=(f"node_{tap_name}", "tap", "clickable")
            )
            
            canvas.create_text(
                tap_x, tap_y,
                text=tap_name,
                font=('Helvetica', 11, 'bold'),
                fill='white',
                tags=(f"node_{tap_name}_label", "clickable")
            )
            
            # Store tap area for click detection
            self.tap_areas[tap_name] = {
                'x': tap_x, 'y': tap_y,
                'width': 70, 'height': 40
            }
        
        # Store sensor node areas for click detection
        for sensor_x, sensor_y, sensor_name in sensor_nodes:
            self.node_areas[sensor_name] = {
                'x': sensor_x, 'y': sensor_y,
                'radius': 20
            }
        
        # Store other node areas
        self.node_areas["TANK"] = {'x': tank_x + tank_width/2, 'y': tank_y + tank_height/2, 'radius': 50}
        self.node_areas["VALVE_A"] = {'x': valve_a_x, 'y': valve_a_y, 'radius': 30}
        self.node_areas["JUNCTION_E"] = {'x': junction_e_x, 'y': junction_e_y, 'width': 80, 'height': 50}
        
        # Draw pipes with current states
        self.pipe_areas = {}
        
        # Define all pipes with their coordinates
        pipes = [
            # Main pipeline from tank
            (tank_x + tank_width, tank_y + tank_height/2, s1_x - 20, s1_y, "TANK-S1", "Tank to S1"),
            (s1_x + 20, s1_y, s2_x - 20, s2_y, "S1-S2", "S1 to S2"),
            (s2_x + 20, s2_y, valve_a_x - 30, valve_a_y, "S2-VALVE_A", "S2 to Valve A"),
            
            # Branches from Valve A
            (valve_a_x, valve_a_y - 30, s3_x, s3_y, "VALVE_A-S3", "Valve A to S3"),
            (s3_x, s3_y, tap1_x + 35, tap1_y, "S3-TAP1", "S3 to TAP1"),
            
            (valve_a_x, valve_a_y + 30, s4_x, s4_y, "VALVE_A-S4", "Valve A to S4"),
            (s4_x, s4_y, tap2_x + 35, tap2_y, "S4-TAP2", "S4 to TAP2"),
            
            (valve_a_x + 30, valve_a_y, s5_x, s5_y, "VALVE_A-S5", "Valve A to S5"),
            (s5_x, s5_y, junction_e_x - 40, junction_e_y, "S5-JUNCTION_E", "S5 to Junction E"),
            
            # Branches from Junction E
            (junction_e_x + 40, junction_e_y - 15, s6_x, s6_y, "JUNCTION_E-S6", "Junction E to S6"),
            (s6_x, s6_y, tap3_x - 35, tap3_y, "S6-TAP3", "S6 to TAP3"),
            
            (junction_e_x + 40, junction_e_y, s7_x, s7_y, "JUNCTION_E-S7", "Junction E to S7"),
            (s7_x, s7_y, tap4_x - 35, tap4_y, "S7-TAP4", "S7 to TAP4"),
            
            (junction_e_x + 40, junction_e_y + 15, s8_x, s8_y, "JUNCTION_E-S8", "Junction E to S8"),
            (s8_x, s8_y, tap5_x - 35, tap5_y, "S8-TAP5", "S8 to TAP5")
        ]
        
        # Draw all pipes
        for x1, y1, x2, y2, pipe_id, label in pipes:
            self.draw_pipe(x1, y1, x2, y2, pipe_id, label)
        
        # Add legend
        self.add_legend()
        
        # Update scroll region based on actual content
        self.update_scroll_region()
    
    def draw_pipe(self, x1, y1, x2, y2, pipe_id, label):
        canvas = self.canvas
        
        # Determine pipe color based on water flow and leaks
        if self.water_flow.get(pipe_id, False):
            # Water is flowing through this pipe
            if self.pipe_leaks[pipe_id]:
                # Pipe has a leak and water is flowing - ACTIVE LEAK
                color = '#ff3333'  # Red for active leak
                leak_color = '#ff0000'  # Bright red for active leak indicator
            else:
                # Pipe is intact with water flow
                color = '#0099ff'  # Light blue for normal water flow
        else:
            # No water flow
            if self.pipe_leaks[pipe_id]:
                # Pipe has leak but no water - INACTIVE LEAK
                color = '#ff9900'  # Orange for inactive leak
                leak_color = '#ff9900'  # Orange for inactive leak indicator
            else:
                # Normal pipe without water
                color = '#cccccc'  # Gray for inactive pipe
        
        width = 8
        
        # Draw the pipe
        pipe = canvas.create_line(
            x1, y1, x2, y2,
            width=width, fill=color, capstyle=tk.ROUND,
            tags=(f"pipe_{pipe_id}", "pipe", "clickable")
        )
        
        # Add leak indicator if pipe has a leak
        if self.pipe_leaks[pipe_id]:
            # Calculate midpoint for leak indicator
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # Determine leak indicator color and size based on activity
            if self.active_leaks.get(pipe_id, False):
                # Active leak (water flowing) - larger, brighter indicator
                leak_size = 12
                fill_color = '#ff6666'
                outline_color = '#ff0000'
            else:
                # Inactive leak (no water flow) - smaller, dimmer indicator
                leak_size = 8
                fill_color = '#ffcc99'
                outline_color = '#ff9900'
            
            canvas.create_oval(
                mid_x - leak_size, mid_y - leak_size,
                mid_x + leak_size, mid_y + leak_size,
                outline=outline_color, width=2, fill=fill_color,
                tags=(f"leak_{pipe_id}", "leak", "clickable")
            )
        
        # Store pipe coordinates for click detection
        self.pipe_areas[pipe_id] = {
            'id': pipe,
            'x1': x1, 'y1': y1,
            'x2': x2, 'y2': y2,
            'width': width
        }
    
    def add_legend(self):
        legend_x = self.canvas_width - 250
        legend_y = 50
        
        # Legend box
        self.canvas.create_rectangle(
            legend_x - 15, legend_y - 15,
            legend_x + 235, legend_y + 220,
            outline='#cccccc', fill='#f9f9f9', width=2
        )
        
        # Legend title
        self.canvas.create_text(
            legend_x + 110, legend_y + 10,
            text="SYSTEM LEGEND",
            font=('Helvetica', 11, 'bold'),
            fill='#1a5a99'
        )
        
        # Active leak indicator (bright red)
        self.canvas.create_oval(
            legend_x + 10, legend_y + 55,
            legend_x + 25, legend_y + 70,
            outline='#ff0000', width=2, fill='#ff6666'
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 62,
            text="Active Leak (Water Flowing)",
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
        
        # Inactive leak indicator (orange)
        self.canvas.create_oval(
            legend_x + 10, legend_y + 77,
            legend_x + 20, legend_y + 87,
            outline='#ff9900', width=2, fill='#ffcc99'
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 82,
            text="Inactive Leak (No Water)",
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
        
        # Pipe with water flow (blue)
        self.canvas.create_line(
            legend_x, legend_y + 35,
            legend_x + 40, legend_y + 35,
            width=8, fill='#0099ff'
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 35,
            text="Water Flowing",
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
        
        # Tap open (red)
        self.canvas.create_rectangle(
            legend_x + 10, legend_y + 100,
            legend_x + 30, legend_y + 120,
            outline='#1a5a99', width=2, fill='#ff3333'
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 110,
            text="Tap Open (Water Flowing)",
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
        
        # Tap closed (green)
        self.canvas.create_rectangle(
            legend_x + 10, legend_y + 125,
            legend_x + 30, legend_y + 145,
            outline='#1a5a99', width=2, fill='#00cc66'
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 135,
            text="Tap Closed (No Water)",
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
        
        # Sensor node
        self.canvas.create_oval(
            legend_x + 10, legend_y + 150,
            legend_x + 30, legend_y + 170,
            outline='#1a5a99', width=2, fill='#ccffff'
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 160,
            text="Sensor Node",
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
        
        # Firebase status indicator
        firebase_color = '#4CAF50' if self.firebase_initialized else '#FF9800'
        firebase_text = "Firebase Connected" if self.firebase_initialized else "Firebase: Offline Mode"
        
        self.canvas.create_oval(
            legend_x + 10, legend_y + 175,
            legend_x + 30, legend_y + 195,
            outline='#1a5a99', width=2, fill=firebase_color
        )
        self.canvas.create_text(
            legend_x + 100, legend_y + 185,
            text=firebase_text,
            font=('Helvetica', 10),
            fill='#333333',
            anchor='w'
        )
    
    def update_scroll_region(self):
        # Get the bounding box of all items on the canvas
        bbox = self.canvas.bbox("all")
        if bbox:
            # Add some padding around the content
            padding = 50
            self.canvas.configure(scrollregion=(
                bbox[0] - padding, 
                bbox[1] - padding, 
                bbox[2] + padding, 
                bbox[3] + padding
            ))
    
    def on_canvas_click(self, event):
        # Get the canvas coordinates considering scroll position
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # First check if a TAP was clicked
        for tap_name, area in self.tap_areas.items():
            if (abs(canvas_x - area['x']) <= area['width']/2 and 
                abs(canvas_y - area['y']) <= area['height']/2):
                # Toggle tap state
                self.tap_states[tap_name] = not self.tap_states[tap_name]
                self.calculate_water_flow()
                self.draw_water_system()
                
                # Send tap states to Firebase
                self.send_tap_states_to_firebase()
                return
        
        # Check if a pipe was clicked (for adding/removing leaks)
        for pipe_id, coords in self.pipe_areas.items():
            if self.point_near_line(canvas_x, canvas_y, 
                                   coords['x1'], coords['y1'], 
                                   coords['x2'], coords['y2'], 
                                   coords['width'] * 2):
                # Toggle leak state for this pipe
                self.pipe_leaks[pipe_id] = not self.pipe_leaks[pipe_id]
                self.calculate_water_flow()
                self.draw_water_system()
                
                # Send leak states to Firebase
                self.send_leak_states_to_firebase()
                return
        
        # Check if tank valve was clicked
        tank_valve_x = 100 + 60  # tank_x + tank_width/2
        tank_valve_y = 300 + 200 + 35  # tank_y + tank_height + 35
        if (abs(canvas_x - tank_valve_x) <= 25 and 
            abs(canvas_y - tank_valve_y) <= 15):
            self.toggle_tank_valve()
            # toggle_tank_valve() already calls send_valve_status_to_firebase()
            return
        
        # Check if valve A was clicked
        valve_a_x = 100 + 120 + 100 + 150 + 150  # Calculated position
        valve_a_y = 300 + 100  # tank_y + tank_height/2
        if (abs(canvas_x - valve_a_x) <= 30 and 
            abs(canvas_y - valve_a_y) <= 30):
            self.toggle_valve_a()
            # toggle_valve_a() already calls send_valve_status_to_firebase()
            return
    
    def point_near_line(self, px, py, x1, y1, x2, y2, tolerance):
        # Calculate distance from point to line segment
        import math
        
        # Line vector
        line_vec_x = x2 - x1
        line_vec_y = y2 - y1
        
        # Point vector from line start
        point_vec_x = px - x1
        point_vec_y = py - y1
        
        # Length squared of line
        line_len_sq = line_vec_x * line_vec_x + line_vec_y * line_vec_y
        
        # Dot product
        dot = point_vec_x * line_vec_x + point_vec_y * line_vec_y
        
        # Calculate projection fraction
        if line_len_sq != 0:
            t = max(0, min(1, dot / line_len_sq))
        else:
            t = 0
        
        # Find closest point on line segment
        closest_x = x1 + t * line_vec_x
        closest_y = y1 + t * line_vec_y
        
        # Calculate distance from point to closest point on line
        dist_x = px - closest_x
        dist_y = py - closest_y
        distance = math.sqrt(dist_x * dist_x + dist_y * dist_y)
        
        return distance <= tolerance
    
    def toggle_tank_valve(self):
        self.valve_states["TANK_VALVE"] = not self.valve_states["TANK_VALVE"]
        
        # Update button text and color
        if self.valve_states["TANK_VALVE"]:
            self.tank_valve_button.config(text="OPEN", bg='#0066cc', fg='white')
        else:
            self.tank_valve_button.config(text="CLOSED", bg='#ff3333', fg='white')
        
        # Recalculate water flow and redraw
        self.calculate_water_flow()
        self.draw_water_system()
        
        # Send update to Firebase
        self.send_valve_status_to_firebase()
        # Also send water flow status since it changed
        self.send_water_flow_to_firebase()
    
    def toggle_valve_a(self):
        self.valve_states["VALVE_A"] = not self.valve_states["VALVE_A"]
        
        # Update button text and color
        if self.valve_states["VALVE_A"]:
            self.valve_a_button.config(text="OPEN", bg='#0066cc', fg='white')
        else:
            self.valve_a_button.config(text="CLOSED", bg='#ff3333', fg='white')
        
        # Recalculate water flow and redraw
        self.calculate_water_flow()
        self.draw_water_system()
        
        # Send update to Firebase
        self.send_valve_status_to_firebase()
        # Also send water flow status since it changed
        self.send_water_flow_to_firebase()
    
    def send_valve_status_to_firebase(self):
        """Send only valve status to Firebase"""
        if not self.firebase_initialized:
            return
            
        try:
            valve_data = {
                'TANK_VALVE': int(self.valve_states["TANK_VALVE"]),
                'VALVE_A': int(self.valve_states["VALVE_A"])
            }
            
            self.firebase_ref.child('valves').set(valve_data)
            print(f"Valve status sent to Firebase: {valve_data}")
            
        except Exception as e:
            print(f"Error sending valve status to Firebase: {e}")
    
    def send_tap_states_to_firebase(self):
        """Send current tap states to Firebase"""
        if not self.firebase_initialized:
            return
            
        try:
            taps_data = {tap: int(state) for tap, state in self.tap_states.items()}
            self.firebase_ref.child('taps').set(taps_data)
            print(f"Tap states sent to Firebase: {taps_data}")
            
        except Exception as e:
            print(f"Error sending tap states to Firebase: {e}")
    
    def send_leak_states_to_firebase(self):
        """Send current pipe leak states to Firebase"""
        if not self.firebase_initialized:
            return
            
        try:
            leaks_data = {pipe: int(has_leak) for pipe, has_leak in self.pipe_leaks.items()}
            self.firebase_ref.child('leaks').set(leaks_data)
            print(f"Leak states sent to Firebase: {leaks_data}")
            
        except Exception as e:
            print(f"Error sending leak states to Firebase: {e}")
    
    def send_water_flow_to_firebase(self):
        """Send current water flow status to Firebase"""
        if not self.firebase_initialized:
            return
            
        try:
            flow_data = {pipe: int(flow) for pipe, flow in self.water_flow.items()}
            self.firebase_ref.child('water_flow').set(flow_data)
            print(f"Water flow status sent to Firebase")
            
        except Exception as e:
            print(f"Error sending water flow to Firebase: {e}")
    
    def send_all_data_to_firebase(self):
        """Send all current data to Firebase"""
        if not self.firebase_initialized:
            messagebox.showinfo("Info", "Firebase is not connected. Running in offline mode.")
            return
            
        try:
            # Calculate active leaks before sending
            self.calculate_active_leaks()
            
            # Prepare data
            data = {
                'timestamp': datetime.now().isoformat(),
                'sensors': {
                    'pH': float(self.ph_value.get()),
                    'turbidity': float(self.turbidity_value.get()),
                    'salinity': float(self.salinity_value.get()),
                    'flow': float(self.flow_value.get())
                },
                'water_level': int(self.water_level_value.get()),
                'valves': {
                    'TANK_VALVE': int(self.valve_states["TANK_VALVE"]),
                    'VALVE_A': int(self.valve_states["VALVE_A"])
                },
                'taps': {tap: int(state) for tap, state in self.tap_states.items()},
                'leaks': {pipe: int(has_leak) for pipe, has_leak in self.pipe_leaks.items()},
                'active_leaks': {pipe: int(is_active) for pipe, is_active in self.active_leaks.items()},
                'water_flow': {pipe: int(flow) for pipe, flow in self.water_flow.items()}
            }
            
            # Send to Firebase
            self.firebase_ref.set(data)
            
            # Update status
            self.firebase_status_var.set("Firebase: Data Sent ✓")
            self.firebase_status_label.config(fg='#4CAF50')
            
            print("All data sent to Firebase")
            
            # Reset status after 2 seconds
            self.root.after(2000, lambda: self.firebase_status_var.set("Firebase: Connected ✓"))
            
        except Exception as e:
            self.firebase_status_var.set("Firebase: Send Error")
            self.firebase_status_label.config(fg='#FF0000')
            print(f"Error sending to Firebase: {e}")
    
    def check_leak_status(self):
        """Check and report ACTIVE leak status (only leaks with water flow)"""
        # Calculate active leaks first
        self.calculate_active_leaks()
        
        active_leak_count = sum(1 for is_active in self.active_leaks.values() if is_active)
        total_leak_count = sum(1 for has_leak in self.pipe_leaks.values() if has_leak)
        
        if active_leak_count > 0:
            active_leaking_pipes = [pipe for pipe, is_active in self.active_leaks.items() if is_active]
            message = f"Found {active_leak_count} ACTIVE leaks (water flowing):\n" + "\n".join(active_leaking_pipes)
            if total_leak_count > active_leak_count:
                message += f"\n\nNote: {total_leak_count - active_leak_count} additional leaks detected but inactive (no water flow)"
            messagebox.showinfo("Leak Status", message)
        else:
            if total_leak_count > 0:
                message = f"No active leaks detected.\n{total_leak_count} leaks found but inactive (no water flow through them)"
            else:
                message = "No leaks detected at all!"
            messagebox.showinfo("Leak Status", message)
        
        # Also send to Firebase
        self.detect_and_report_leaks()

    def detect_and_report_leaks(self):
        """Detect leaks and report to Firebase - only active leaks are reported"""
        try:
            # Calculate active leaks first
            self.calculate_active_leaks()
            
            active_leak_count = sum(1 for is_active in self.active_leaks.values() if is_active)
            total_leak_count = sum(1 for has_leak in self.pipe_leaks.values() if has_leak)
            
            leak_report = {
                'timestamp': datetime.now().isoformat(),
                'total_pipes': len(self.pipe_leaks),
                'total_leaks': total_leak_count,
                'active_leaks': [],
                'active_leak_count': active_leak_count,
                'inactive_leaks': [],
                'inactive_leak_count': total_leak_count - active_leak_count
            }
            
            # Find all pipes with leaks and categorize them
            for pipe_id, has_leak in self.pipe_leaks.items():
                if has_leak:
                    if self.active_leaks.get(pipe_id, False):
                        leak_report['active_leaks'].append(pipe_id)
                    else:
                        leak_report['inactive_leaks'].append(pipe_id)
            
            # Send leak report to Firebase if connected
            if self.firebase_initialized:
                self.firebase_ref.child('leak_report').set(leak_report)
                print(f"Leak report sent to Firebase: Active={active_leak_count}, Total={total_leak_count}")
            else:
                print(f"Leak report (offline): Active={active_leak_count}, Total={total_leak_count}")
                    
        except Exception as e:
            print(f"Error detecting leaks: {e}")
    
    def update_ph_display(self, value):
        # Update pH display with formatted value
        ph_value = float(value)
        self.ph_display.config(text=f"{ph_value:.1f}")
        
        # Send sensor data to Firebase
        self.send_sensor_data_to_firebase()
    
    def update_turbidity_display(self, value):
        # Update turbidity display with formatted value
        turb_value = float(value)
        self.turb_display.config(text=f"{turb_value:.1f}")
        
        # Send sensor data to Firebase
        self.send_sensor_data_to_firebase()
    
    def update_salinity_display(self, value):
        # Update salinity display with formatted value
        sal_value = float(value)
        self.sal_display.config(text=f"{sal_value:.2f}")
        
        # Send sensor data to Firebase
        self.send_sensor_data_to_firebase()
    
    def update_flow_display(self, value):
        # Update flow display with formatted value
        flow_value = float(value)
        self.flow_display.config(text=f"{flow_value:.1f}")
        
        # Send sensor data to Firebase
        self.send_sensor_data_to_firebase()
    
    def send_sensor_data_to_firebase(self):
        """Send sensor data to Firebase"""
        if not self.firebase_initialized:
            return
            
        try:
            sensor_data = {
                'pH': float(self.ph_value.get()),
                'turbidity': float(self.turbidity_value.get()),
                'salinity': float(self.salinity_value.get()),
                'flow': float(self.flow_value.get())
            }
            
            self.firebase_ref.child('sensors').set(sensor_data)
            print(f"Sensor data sent to Firebase: {sensor_data}")
            
        except Exception as e:
            print(f"Error sending sensor data to Firebase: {e}")
    
    def update_water_level_display(self, value=None):
        # Update water level label
        water_level = self.water_level_value.get()
        self.water_level_label.config(text=f"{water_level}%")
        
        # Recalculate water flow and redraw
        self.calculate_water_flow()
        self.draw_water_system()
        
        # Send water level to Firebase
        if self.firebase_initialized:
            try:
                self.firebase_ref.child('water_level').set(water_level)
                print(f"Water level sent to Firebase: {water_level}%")
            except Exception as e:
                print(f"Error sending water level to Firebase: {e}")

def main():
    root = tk.Tk()
    app = WaterSystemGUI(root)
    
    # Handle window resizing
    def on_resize(event):
        # Update the canvas scroll region when window is resized
        app.update_scroll_region()
    
    root.bind("<Configure>", on_resize)
    
    root.mainloop()

if __name__ == "__main__":
    main()