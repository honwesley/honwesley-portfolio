"""All portfolio content lives here. Edit, then run:  python3 _build/build.py
Each project becomes its own page at projects/<slug>.html.

Fields
  slug, title, short (one line for the tile), when, year, org, role, status
  cats      filter categories (see CATEGORIES)
  tools     list of tools/tech
  cover     image used on the tile and as the page hero (assets/img/...)
  images    [(file, alt), ...] gallery; the first three also cycle on the tile hover
  video     optional mp4 in assets/video
  summary   opening paragraph
  sections  [{"h": heading, "p": text | "list": [...] | "ol": [(bold, text)] | "dl": [(term, text)]}]
  impact    optional highlighted result line
  docs      [(label, file in assets/docs)]
  size      tile size on the projects grid: "xl", "l" or "m"
  sim       True to embed the live Pendubot simulation on the page
"""

CATEGORIES = [
    ("power", "Power electronics"),
    ("controls", "Controls"),
    ("embedded", "Embedded"),
    ("pcb", "PCB design"),
    ("mech", "Mechanical"),
    ("course", "Coursework"),
]

PROJECTS = [
    dict(
        slug="pendubot", title="Underactuated Pendubot", size="xl", sim=True,
        short="Two links, one motor. Balancing the free link through the dynamics of the driven one.",
        when="2026", year="2026", status="In progress",
        cats=["controls", "mech", "embedded", "pcb"],
        tools=["MATLAB", "Simulink", "Embedded C++", "PID", "LQR", "NMPC", "Fuzzy control"],
        cover="pendubot-sketch.jpg",
        images=[("pendubot-sketch.jpg", "Hand sketch of the Pendubot: controller electronics, motor, encoder and the two-link plant"),
                ("pendubot-plant.jpg", "Plant diagram of the two links with joint angles and centers of mass"),
                ("pendubot-block.jpg", "Closed-loop block diagram: controller, plant, disturbance and state estimate")],
        summary="The shoulder is driven and the elbow swings free, so the controller has to balance the passive link entirely through the dynamics of the active one. I'm building it to compare four control strategies on the same hardware.",
        sections=[
            {"h": "The design", "list": [
                "Two equal 6061-T6 aluminum links, each 11 in long, 2 in wide and 1/4 in thick, with masses and inertias taken from CAD.",
                "Direct drive with link 1 bolted to the motor shaft and no gearbox, which removes backlash at the joint that matters most.",
                "Absolute encoders on both joints. Encoder 2 rides on link 1 through a flexible coupling so it doesn't side-load its bearings.",
                "A custom motor-control PCB running a real-time control loop in embedded C++.",
                "Nonlinear equations of motion and a state-space model, simulated in MATLAB/Simulink before any hardware runs."]},
            {"h": "Test plan", "ol": [
                ("Stabilization.", "Start hanging down and compare settling time, overshoot, steady-state error and oscillation."),
                ("Disturbance rejection.", "Apply a repeatable impulse and measure peak deflection, recovery time and motor torque."),
                ("Robustness.", "Add mass to a link and see which controller copes with the model being wrong."),
                ("Compute cost.", "Execution time, jitter and processor load: PID and LQR against NMPC.")]},
            {"h": "Designing for failure", "p": "Hanging down is the stable rest state, so cutting power is safe. The danger is the fall: link 2 has no rotation limit and can swing hard, and a runaway controller can wind up link 1's encoder cable. The plan: a software limit on link 1, cable strain relief and a cutoff when balance is lost."},
        ],
        docs=[("Mathematical modeling", "pendubot-modeling.pdf"), ("State space and controllers", "pendubot-state-space.pdf")],
    ),
    dict(
        slug="dc-microgrid-nmpc", title="Nonlinear MPC for a DC microgrid", size="l",
        short="Holding a shared DC bus steady through constant-power load steps with four boost converters.",
        when="June 2026 to present", year="2026", org="Power Electronics and Energy Conversion Lab, UCLA", role="Undergraduate researcher",
        cats=["power", "controls", "pcb"],
        tools=["MATLAB", "Simulink", "LTspice", "KiCad", "Oscilloscopes", "Differential probes", "Electronic loads"],
        cover="peec-pcb-3d.jpg",
        images=[("peec-pcb-3d.jpg", "3D render of the four-phase boost converter PCB with bulk capacitors"),
                ("peec-simulink.jpg", "Simulink model of four boost converters on a shared DC bus with the NMPC"),
                ("peec-pcb-layout.jpg", "PCB layout of the boost converter board")],
        summary="Constant power loads are destabilizing: when the bus voltage dips, the load draws more current to hold its power, which pulls the voltage down further. I designed a nonlinear model predictive controller that sets the duty cycles of several parallel boost converters to hold a shared DC bus at its reference through large load steps.",
        sections=[
            {"h": "Building the model up in stages", "ol": [
                ("One averaged converter with a CPL.", "Verified the steady state: duty cycle 0.669, zero state derivatives."),
                ("Open loop.", "Fixed duty cycle, then a 5 kW to 8 kW load step to watch the bus sag."),
                ("Simple duty controller.", "Used to confirm the plant behaves before adding anything clever."),
                ("Nonlinear MPC.", "Cost, state and output functions written by hand."),
                ("Four converters, one bus.", "States are every inductor current plus bus voltage, inputs are every duty cycle, and the cost adds current sharing."),
                ("Switching models.", "Averaged converters replaced with MOSFET, diode and PWM models and compared against the averaged version.")]},
            {"h": "Constraints the controller respects", "list": [
                "Duty cycle between 0.05 and 0.90.",
                "Inductor current within its maximum.",
                "Bus voltage between its minimum and maximum."]},
            {"h": "The board", "p": "Four boost stages, each with a current sensor feeding the controller, which runs the optimization and drives the MOSFET PWM. An external supply comes in through a buck and an LDO for the logic rails, with low-pass filtering on the power lines. The boost stages sit on one edge, the supply in the bottom left and the controller in the bottom right. I did the bring-up with scopes, differential probes and electronic loads, chasing gate ringing, conduction losses and VDS switching transients."},
        ],
        impact="The bus recovers to its reference in under 0.1 s after load steps, and often under 20 ms in the switching-model simulation.",
        docs=[("Board schematic", "peec-boost-schematic.pdf")],
    ),
    dict(
        slug="actuator-testbench", title="eCVT actuator testbench", size="l",
        short="A hardware-in-the-loop rig that finds shifter failures on the bench instead of on race day.",
        when="Aug 2025 to May 2026", year="2025", org="UCLA Bruin Racing Baja SAE", role="Electronics project lead",
        cats=["controls", "embedded", "mech"],
        tools=["ODrive", "CAN", "I2C", "Raspberry Pi", "PID tuning", "Root-cause analysis"],
        cover="testbench-model.jpg",
        images=[("testbench-model.jpg", "Actuator testbench on an aluminum extrusion frame"),
                ("testbench-shifter.jpg", "Continuous gear shifter mechanism"),
                ("testbench-wiring.jpg", "Motor and encoder wiring"),
                ("testbench-model-2.jpg", "Second view of the testbench assembly"),
                ("testbench-electronics.jpg", "Controllers, Raspberry Pi and wiring on the bench"),
                ("testbench-schematic.jpg", "Testbench schematic sheet")],
        summary="A standalone rig to test the car's electronic CVT actuator under controlled, repeatable loads before it ever goes into the vehicle.",
        sections=[
            {"h": "How it works", "list": [
                "A primary motor drives the shifter while a second motor applies a controllable load. Both run on ODrive controllers over CAN and I2C.",
                "Feedback comes from an encoder, optical limit switches and a gear tooth sensor, logged alongside ODrive telemetry on a Raspberry Pi.",
                "Bring-up went in steps: signal validation, then baseline tests, then stress tests over many cycles.",
                "Pass criteria: repeatable shifts, stable under load, no stalling."]},
            {"h": "What broke, and the fix", "dl": [
                ("Missed gear-tooth pulses", "The sensor gap was wrong. Re-setting it brought the signal back."),
                ("Fine at no load, failing under load", "The motor didn't have the torque for realistic shifting loads, and the bench proved we needed more."),
                ("Trusting the controller's own numbers", "Added an external encoder so we could compare commanded input against actual output.")]},
            {"h": "Why it mattered", "p": "It moved validation earlier, so failures turned up before race day. It gave the electronics and powertrain teams one shared platform for PID tuning and debugging."},
        ],
        impact="Contributed to a 51.4% improvement in our Baja competition event performance.",
        docs=[("Testbench schematic", "actuator-testbench-schematic.pdf")],
    ),
    dict(
        slug="signet", title="SIGNET robotic arm", size="m",
        short="A 6-DOF arm that mirrors my arm and a vision model that reads ASL.",
        when="May 2026 to present", year="2026", status="In progress",
        cats=["embedded", "controls", "mech"],
        tools=["ESP32", "Embedded C++", "PyTorch", "OpenCV", "MediaPipe", "KiCad", "Onshape"],
        cover="signet-hand.jpg",
        images=[("signet-hand.jpg", "Render of SIGNET's 3D-printed left hand"),
                ("signet-cad.jpg", "Renders of SIGNET's printed hand, forearm shell and wrist joint")],
        summary="A teleoperated 6-DOF arm that copies the motion of my own arm, paired with a vision model that recognizes American Sign Language gestures.",
        sections=[
            {"h": "Hardware and firmware", "list": [
                "ESP32 controllers with servo and BLDC drivers, IMUs and encoder feedback for multi-axis joint tracking.",
                "Distributed embedded C++ firmware across I2C and UART buses, with PID trajectory control.",
                "Hand, forearm and joints modeled in Onshape and 3D printed; boards in KiCad."]},
            {"h": "Vision", "list": [
                "Custom PyTorch and OpenCV models trained on more than 10,000 self-collected multimodal samples covering 26 ASL gestures.",
                "Real-time gesture recognition through a MediaPipe pipeline."]},
            {"h": "Still learning", "p": "Inverse kinematics for the joint targets, plus tighter motor control. A full build log is coming."},
        ],
        impact="Under 50 ms control latency and 80% fewer telemetry faults.",
    ),
    dict(
        slug="baja-daq", title="Baja controls and DAQ board", size="m",
        short="One board to log what the car is doing, timestamped and synchronized.",
        when=None, year="2025", org="UCLA Bruin Racing Baja SAE", role="Electronics project lead",
        cats=["pcb", "embedded"],
        tools=["ESP32-S3", "CAN", "UART", "I2C/SPI", "Op-amp front ends", "Raspberry Pi"],
        cover="daq-board.jpg",
        images=[("daq-board.jpg", "Assembled DAQ board mounted in the vehicle"),
                ("daq-schematic.jpg", "DAQ board schematic sheet"),
                ("baja-power.jpg", "Vehicle power block diagram from the 48 V battery"),
                ("baja-controls.jpg", "Controls schematic sheet")],
        summary="A central data acquisition and controls board, so powertrain and controls could tune from data instead of guesses.",
        sections=[
            {"h": "What's on the board", "list": [
                "ESP32-S3 controls and DAQ PCB, architected from dev-board schematics.",
                "CAN transceivers, sensor inputs and actuator driver interfaces.",
                "Op-amp stages to scale and filter analog sensors into ADC range.",
                "IMU and GPS over I2C/SPI, plus an RTC for timestamped logs.",
                "Custom UART firmware feeding a Raspberry Pi logging pipeline for real-time telemetry.",
                "A structured connector pinout so sensors can be added without rewiring the harness."]},
            {"h": "Why it mattered", "p": "It turned vehicle behavior into measurable data the electronics, powertrain and controls teams could share, and it's a platform new sensors can plug into."},
        ],
        docs=[("DAQ schematic", "baja-daq-schematic.pdf")],
    ),
    dict(
        slug="buck-boost", title="Buck–boost power stage study", size="m",
        short="Smaller, lower-power 3.3 V rail from a single Li-ion cell, and a plan to prove it.",
        when="October 2026 to present", year="2026", org="Emergence of Communication Lab, UCLA", role="Undergraduate researcher",
        cats=["power"],
        tools=["TPS63060", "TPS63802", "Power analyzer", "Electronic load", "Thermal camera"],
        cover="eoc-buckboost.jpg",
        images=[("eoc-buckboost.jpg", "Comparison of the TPS63060 and TPS63802 buck-boost regulators")],
        summary="The board needs a regulated 3.3 V rail from a single-cell Li-ion battery (2.9 to 4.2 V). I evaluated whether a newer regulator could shrink the power stage without giving anything up.",
        sections=[
            {"h": "Current versus proposed", "dl": [
                ("Input range", "TPS63060: 2.5–12 V. TPS63802: 1.3–5.5 V, which covers the whole cell range."),
                ("Footprint", "9 mm² down to 6 mm²."),
                ("Quiescent current", "30 µA down to 11 µA."),
                ("Reference inductor", "1 µH down to 0.47 µH.")]},
            {"h": "How I'd validate it", "list": [
                "Emulate the battery with a current-limited supply at 2.9, 3.3, 3.7 and 4.2 V.",
                "Sweep the load from idle through nominal to maximum with an electronic load.",
                "Capture load-step undershoot, overshoot and settling on the scope.",
                "Measure efficiency, ripple and switching spikes.",
                "Check inductor peak current against Isat, and IC and inductor temperatures."]},
        ],
        impact="Decision rule: choose the smallest power stage that meets every limit at minimum input voltage and maximum load, not just the smallest inductor.",
        docs=[("Characterization plan", "buck-boost-characterization.pdf")],
    ),
    dict(
        slug="heater-control-pcb", title="Heater and thermistor control PCB", size="m",
        short="A Raspberry Pi HAT that drives three heaters and reads three thermistors.",
        when="November 2026 to present", year="2026", org="Ozcan Lab, UCLA", role="Undergraduate researcher",
        cats=["pcb", "power", "embedded"],
        tools=["KiCad", "ADS1115", "TPS56837", "AP2114H", "MOSFET switching"],
        cover="ozcan-pcb.jpg",
        images=[("ozcan-pcb.jpg", "Board layout rendered from the KiCad file: front copper in gold, back copper in blue")],
        summary="Powers three heaters and up to four LEDs from a Raspberry Pi. Heater A is a 10 × 10 mm pad held at 95 °C. Heaters B and C are 20 × 40 mm pads run at 40 to 95 °C.",
        sections=[
            {"h": "How it works", "list": [
                "GPIO-driven MOSFETs switch each heater. A pin set high at 3.3 V pulls the MOSFET to ground and current flows.",
                "An ADS1115 ADC reads three thermistors and reports to the Pi over I2C.",
                "A TPS56837 buck converts 15 V to 5.1 V for the Pi and LEDs, and an AP2114H LDO makes 3.3 V for heater A.",
                "Headers for a TLC LED driver, with the LEDs mounted off-board."]},
            {"h": "Revisions from design review", "list": [
                "Added an RC filter and ESD clamp diode to each thermistor input.",
                "Widened the Pi's 5 V trace to at least 2 mm and rerouted it around Q3, which it had been running through.",
                "Fixed a reversed MOSFET (Q4) and moved the heater pin from GPIO 29 to 13.",
                "Upsized the TVS to an SMBJ18A, changed the thermistor connectors, and corrected the mounting holes to 2.7 mm.",
                "Kept two layers, with extra decoupling to hold down voltage spikes."]},
        ],
    ),
    dict(
        slug="lumos", title="LUMOS", size="m",
        short="A 48-LED display with an ESP32, two LED drivers and a printed enclosure.",
        when=None, year="2026", org="Personal build",
        cats=["embedded", "pcb", "mech"],
        tools=["ESP32", "TLC5947", "3D printing", "DB25 harness"],
        cover="lumos.jpg",
        images=[("lumos.jpg", "LUMOS in its 3D-printed enclosure")],
        summary="A 48-LED display driven by an ESP32 through two TLC5947 constant-current drivers, with brightness and button controls. It runs from an AA pack through a 5 V buck.",
        sections=[
            {"h": "Build", "list": [
                "Two TLC5947 drivers with IREF resistors setting LED current.",
                "Six AA cells (9 V nominal) into a 5 V, 2 A buck, with bulk and decoupling capacitors.",
                "A pot for brightness, three pushbuttons and a power switch, all on terminal blocks.",
                "A DB25 cable harness between the board and the display."]},
            {"h": "Enclosure fit testing", "ol": [
                ("v0.", "LED and M3 screw fit only. The M3 hole was too big and the LED hole too small."),
                ("v1.", "Added the pot, switch and button cutouts. The pushbutton fit was perfect; the others needed adjusting."),
                ("v2.", "Updated all the fits, then printed the display, holder and cover.")]},
        ],
        impact="Total BOM under $50.",
    ),
    dict(
        slug="supermileage-ui", title="Supermileage driver UI board", size="m",
        short="The driver's control panel and a node on the car's CAN bus.",
        when=None, year="2025", org="Bruin Supermileage SAE", role="KiCad UI PCB team lead",
        cats=["pcb", "embedded", "power"],
        tools=["KiCad", "ESP32", "CAN", "MOSFET/relay drivers", "I2C display"],
        cover="smv-schematic.jpg",
        images=[("smv-schematic.jpg", "Supermileage UI board schematic"),
                ("smv-block.jpg", "UI board block diagram")],
        summary="A central driver interface for lights, horn, wipers, ignition and kill switch. It also serves as a communication node on the vehicle's CAN network.",
        sections=[
            {"h": "Design", "list": [
                "An ESP32 handles GPIO inputs, CAN, and Bluetooth for logging and configuration.",
                "Driver inputs have signal conditioning and debouncing.",
                "MOSFET and relay outputs switch the 12 V loads.",
                "Reverse-polarity and fuse protection, plus 12 V to 5 V and 3.3 V conversion.",
                "An I2C LCD/OLED and indicator LEDs give the driver feedback."]},
            {"h": "Leading the team", "p": "Directed bring-up, component selection, power distribution and electrical interface reviews across the mechanical subteams."},
        ],
        docs=[("Schematic", "supermileage-ui-schematic.pdf")],
    ),
    dict(
        slug="brewbird", title="Brewbird flow sensing", size="m",
        short="Accurate water volume for a brewing machine with a pulse-output flow sensor.",
        when=None, year="2025", org="Brewbird", role="Intern project",
        cats=["embedded"],
        tools=["ESP32", "KiCad", "Signal conditioning", "Calibration"],
        cover="brewbird-schematic.jpg",
        images=[("brewbird-schematic.jpg", "Flow sensor and ESP32 schematic in KiCad"),
                ("brewbird-sensor.jpg", "Sensor signal chain: pull-up, RC filter and ESD into the MCU"),
                ("brewbird-placement.jpg", "System placement: tank, pump, flow sensor, heater, brew")],
        summary="Integrated a flow sensor into the fluid path to measure dispensed water and make brews repeatable, within the machine's thermal and pressure limits.",
        sections=[
            {"h": "Decisions", "dl": [
                ("Thermal limit", "The sensor is rated to 60 °C, so it sits before the heater. Placement mattered as much as the circuit."),
                ("Noisy pulses", "The open-collector output needed a pull-up, RC filtering and careful routing before it was usable."),
                ("Air bubbles", "Bubbles throw off the readings, so the system needs a priming routine and correct mounting."),
                ("Pump and power noise", "Fixed with routing strategy and filtering.")]},
            {"h": "Measurement", "p": "Pulse counts convert to volume through a K-factor, calibrated and validated against known volumes. The same data flags blockages and faults."},
        ],
    ),
    dict(
        slug="go-kart", title="Verstappenmobiel electric go-kart", size="xl",
        short="A 36 V, two-motor kart with Ackermann steering and an F1-style wheel.",
        when=None, year="2025", org="Team of six",
        cats=["embedded", "mech"],
        tools=["Arduino", "ESC", "OLED", "Perfboard", "Soldering"],
        cover="kart-car.jpg", video="kart-lap.mp4", poster="kart-lap-poster.jpg",
        images=[("kart-car.jpg", "The finished go-kart"),
                ("kart-soldering.jpg", "Soldering the perfboard controller"),
                ("kart-box.jpg", "Electronics enclosure behind the seat"),
                ("kart-wiring.jpg", "Wiring the controller on the breadboard"),
                ("kart-arduino.jpg", "Testing the microcontroller"),
                ("kart-block.jpg", "Electrical block diagram")],
        summary="A team-built electric kart. I worked on the electronics.",
        sections=[
            {"h": "Electronics", "list": [
                "An ESC powered by a 36 V battery drives both motors: speed, direction and braking.",
                "A potentiometer at the end of the steering rod measures steering angle.",
                "An OLED on the F1-inspired steering wheel shows steering angle and speed.",
                "The microcontroller and wiring are soldered onto perfboard and sealed in a box behind the seat."]},
            {"h": "Chassis", "p": "Designed for 50/50 left-right weight, ideally 40/60 front-rear. The front wheels mount above the chassis to center the weight, and the seat position came from measuring our drivers."},
        ],
    ),
    dict(
        slug="greenglide", title="Project GreenGlide", size="m",
        short="Sensors and embedded feedback to make shared e-scooters safer.",
        when=None, year="2025", org="With Vlasi Pagonis and Joseph Gitonga",
        cats=["embedded", "pcb"],
        tools=["Microcontrollers", "Proximity and motion sensing", "Data analysis"],
        cover="greenglide-1.jpg",
        images=[("greenglide-1.jpg", "Sensor prototype on the scooter"),
                ("greenglide-2.jpg", "Prototype with lighting mounted on the deck"),
                ("greenglide-3.jpg", "Prototype electronics close up"),
                ("greenglide-4.jpg", "Lighting test"),
                ("greenglide-schematic.jpg", "GreenGlide schematic")],
        summary="Exploring how sensors and real-time embedded code can reduce collisions and instability for e-scooter riders and pedestrians in dense cities.",
        sections=[
            {"h": "Goals", "list": [
                "Better situational awareness and collision avoidance through real-time sensing and feedback.",
                "Usage and environment data to understand accident patterns.",
                "One hardware and software architecture that is reliable in real time.",
                "Cheap enough for commercial and shared scooter fleets."]},
        ],
        docs=[("Schematics", "greenglide-schematic.pdf")],
    ),
    dict(
        slug="ee141-cpl-control", title="Feedback control of a constant power load", size="l",
        short="Linearize, design, then see what the nonlinear plant does to your controller.",
        when="March 2026", year="2026", org="EC ENGR 141, Principles of Feedback Control",
        cats=["controls", "power", "course"],
        tools=["MATLAB", "Simulink", "State space", "PID control"],
        cover="ee141-voltage.jpg",
        images=[("ee141-voltage.jpg", "Nonlinear closed-loop capacitor voltage settling to reference"),
                ("ee141-circuit.jpg", "Source, L-R-C network and constant power load"),
                ("ee141-simulink.jpg", "Simulink model of the nonlinear plant with the controller"),
                ("ee141-current.jpg", "Nonlinear closed-loop inductor current")],
        summary="A DC source feeds a constant power load through an L-R-C network. The CPL adds a P/v term that makes the plant nonlinear and pushes it toward instability.",
        sections=[
            {"h": "Approach", "ol": [
                ("Model.", "Nonlinear state space with inductor current and capacitor voltage as states."),
                ("Linearize.", "About the equilibrium operating point, then derive the transfer function and check stability."),
                ("Design.", "A controller for settling under 0.05 s with no overshoot."),
                ("Stress it.", "Run the same controller on the full nonlinear plant with saturation limits on voltage and current.")]},
            {"h": "What it showed", "p": "The gap between the linear and nonlinear responses, and how much a CPL's negative incremental resistance erodes stability margin. This is the same problem I now work on at the lab at a larger scale."},
        ],
        docs=[("Report", "ee141-cpl-control.pdf")],
    ),
    dict(
        slug="ece131a-detection", title="Distributed detection in Gaussian noise", size="l",
        short="How many noisy sensors does it take to get the error rate under 10⁻³?",
        when="June 2026", year="2026", org="ECE 131A extra credit project",
        cats=["course"],
        tools=["MATLAB", "Monte Carlo simulation", "Hypothesis testing"],
        cover="ece131-threshold.jpg",
        images=[("ece131-threshold.jpg", "Error probability against the modified sensor threshold"),
                ("ece131-error.jpg", "Error probability against number of sensors, Gaussian and binary"),
                ("ece131-cost.jpg", "Cost comparison of full-precision and binary sensors")],
        summary="Detecting a signal of amplitude 0.5 with many sensors in Gaussian noise. I compared full-precision sensors against cheaper one-bit sensors and optimized the decision threshold.",
        sections=[
            {"h": "Results", "dl": [
                ("Full-precision sensors", "39 sensors reach an error probability of 8.97 × 10⁻⁴, under the 10⁻³ target. A Monte Carlo run of about 220,000 trials confirmed it."),
                ("Binary sensors", "61 one-bit sensors needed for the same target, also checked by simulation."),
                ("Cost trade-off", "Compared total cost at each target error rate to find where cheaper binary sensors win."),
                ("Threshold tuning", "Optimizing a modified threshold (γ ≈ −0.81) lowered the error with a fixed sensor count.")]},
        ],
        docs=[("Report", "ece131a-distributed-detection.pdf")],
    ),
]
