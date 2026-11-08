import streamlit as st
import av
import threading

from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase,
    WebRtcMode
)

from streamlit_autorefresh import st_autorefresh
from livesignmate1 import SignMateRecognizer


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Signmate AI",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# 2. THEME AND WEBSITE STYLING
# =========================================================

st.html("""
<style>
:root {
    --navy: #17243A;
    --navy-deep: #0B1424;
    --navy-soft: #26364D;
    --silver: #AEBBCB;
    --silver-light: #D0D8E2;
    --silver-pale: #E7ECF2;
    --platinum: #E9EDF2;
    --surface: #F7F9FC;
    --text: #17243A;
    --muted-text: #716A64;
}

.stApp {
    background: var(--platinum);
    color: var(--text);
}

.block-container {
    padding-top: 1.7rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

/* Elegant charcoal masthead */
.st-key-main_header {
    background: linear-gradient(125deg, #0B1424 0%, #1C2B42 58%, #314158 100%);
    padding: 48px 30px 42px;
    border-radius: 22px;
    border: 1px solid rgba(196,124,80,.8);
    border-top: 4px solid var(--silver);
    margin-bottom: 26px;
    text-align: center;
    box-shadow: 0 16px 38px rgba(28,25,23,.16);
    position: relative;
    overflow: hidden;
}

.st-key-main_header h1 {
    color: #F0F3F7 !important;
    font-family: Georgia, 'Times New Roman', serif !important;
    font-size: clamp(2.3rem, 5vw, 3.5rem) !important;
    font-weight: 700 !important;
    letter-spacing: 3px;
    margin-bottom: 8px !important;
}

.st-key-main_header h2,
.st-key-main_header h3,
.st-key-main_header p {
    color: #E9EEF5 !important;
}

.st-key-main_header p {
    color: #C5CFDC !important;
    font-size: 1rem;
    letter-spacing: .3px;
}

/* Typography and section rhythm */
h1, h2, h3, h4 {
    color: var(--navy) !important;
}

h2, h3 {
    font-family: Georgia, 'Times New Roman', serif !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #3B485A;
    line-height: 1.72;
}

/* Navigation tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 7px;
    background: #DCE3EC;
    border: 1px solid #BFCAD8;
    padding: 8px;
    border-radius: 14px;
}

.stTabs [data-baseweb="tab"] {
    height: 46px;
    border-radius: 10px;
    color: #45536A;
    font-weight: 650;
    padding-left: 15px;
    padding-right: 15px;
    transition: all .2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(196,124,80,.13);
    color: #52647D;
}

.stTabs [aria-selected="true"] {
    background: var(--navy) !important;
    color: #F0F3F7 !important;
    box-shadow: 0 3px 9px rgba(32,35,38,.18);
}

.stTabs [data-baseweb="tab-highlight"] {
    background: var(--silver) !important;
}

/* Light editorial cards */
.info-card {
    background: var(--surface);
    border: 1px solid #D4DDE8;
    border-left: 4px solid var(--silver);
    border-radius: 15px;
    padding: 23px 22px;
    min-height: 148px;
    margin-bottom: 15px;
    box-shadow: 0 7px 20px rgba(55,43,35,.055);
    transition: transform .2s ease, box-shadow .2s ease;
}

.info-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 11px 24px rgba(55,43,35,.09);
}

.info-card h3 {
    color: #40536E !important;
    margin-top: 0;
    margin-bottom: 9px;
    font-family: Georgia, 'Times New Roman', serif !important;
    font-size: 1.18rem;
}

.info-card p {
    color: #536176;
    line-height: 1.68;
    margin-bottom: 0;
}

.workflow-step {
    background: var(--surface);
    border: 1px solid #C8D2DF;
    border-top: 3px solid var(--silver);
    border-radius: 14px;
    padding: 21px 13px;
    text-align: center;
    min-height: 125px;
    box-shadow: 0 5px 15px rgba(55,43,35,.05);
}

.workflow-step strong {
    color: #40536E;
    display: block;
    margin-bottom: 8px;
    letter-spacing: .5px;
}

.workflow-step span {
    color: #536176;
    font-size: 14px;
}

/* Copper action buttons */
.stButton > button {
    background: linear-gradient(135deg, #AEBBCB, #D0D8E2) !important;
    color: #26364D !important;
    border: 1px solid #687A92 !important;
    border-radius: 11px !important;
    font-weight: 750 !important;
    padding: 12px 22px !important;
    min-height: 45px;
    box-shadow: 0 5px 13px rgba(145,82,48,.16);
    transition: all .2s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #D0D8E2, #D0D8E2) !important;
    color: #0B1424 !important;
    border-color: #40536E !important;
    transform: translateY(-1px);
    box-shadow: 0 7px 16px rgba(145,82,48,.22);
}

.stButton > button:focus {
    box-shadow: 0 0 0 3px rgba(196,124,80,.24) !important;
}

/* Camera frame */
[data-testid="stVideo"],
[data-testid="stCameraInput"] {
    border: 2px solid var(--silver) !important;
    border-radius: 16px !important;
    overflow: hidden;
    box-shadow: 0 8px 22px rgba(32,35,38,.10);
}

/* Prediction and confidence panels */
.st-key-prediction_card {
    background: linear-gradient(145deg, #F7F9FC, #E9EEF5);
    border: 1px solid #AEBBCB;
    border-top: 4px solid var(--silver);
    border-radius: 17px;
    padding: 22px;
    text-align: center;
    margin-top: 13px;
    box-shadow: 0 8px 20px rgba(55,43,35,.08);
}

.st-key-prediction_card h1 {
    color: #52647D !important;
    font-family: Georgia, 'Times New Roman', serif !important;
    font-size: 3.7rem !important;
    font-weight: 800 !important;
}

.st-key-confidence_card {
    background: #F7F9FC !important;
    border: 1px solid #D4DDE8 !important;
    border-left: 4px solid var(--silver) !important;
    border-radius: 16px !important;
    padding: 19px !important;
    margin-top: 14px !important;
    box-shadow: 0 6px 17px rgba(55,43,35,.06);
}

.st-key-confidence_card p {
    color: #40536E !important;
    font-size: 15px !important;
    font-weight: 750 !important;
}

.st-key-confidence_card h2 {
    color: var(--navy) !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}

/* Alerts, progress, separators and captions */
[data-testid="stAlert"] {
    border-radius: 12px;
    border-color: #C8D2DF;
}

[data-testid="stProgressBar"] > div > div {
    background: var(--silver) !important;
}

hr {
    border-color: #B8C4D2 !important;
}

[data-testid="stCaptionContainer"] {
    color: var(--muted-text) !important;
}

/* Footer returns to the dark brand colour */
.st-key-main_footer {
    background: linear-gradient(120deg, #0B1424, #26364D);
    color: #E9EEF5;
    border: 1px solid #687A92;
    border-top: 3px solid var(--silver);
    border-radius: 16px;
    padding: 23px;
    margin-top: 32px;
    text-align: center;
    box-shadow: 0 10px 24px rgba(28,25,23,.13);
}

.st-key-main_footer p {
    color: #D0D8E2 !important;
}

.st-key-main_footer small {
    color: #E9EEF5 !important;
}

/* Make the layout comfortable on smaller screens */
@media (max-width: 700px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .st-key-main_header { padding: 34px 16px; }
    .st-key-main_header h1 { letter-spacing: 1.5px; }
    .stTabs [data-baseweb="tab"] { padding-left: 9px; padding-right: 9px; }
}
</style>
""")


# =========================================================
# 3. SIGNMATE VIDEO PROCESSOR
#    Recognition logic retained from your original code.
# =========================================================

class SignMateVideoProcessor(VideoProcessorBase):

    def __init__(self):
        self.lock = threading.Lock()
        self.recognizer = SignMateRecognizer()
        print("SignMate AI loaded successfully!")

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")

        try:
            with self.lock:
                image = self.recognizer.process_frame(image)

        except Exception as error:
            print("Processing error:", error)

        return av.VideoFrame.from_ndarray(
            image,
            format="bgr24"
        )

    def start_prediction(self):
        with self.lock:
            self.recognizer.start_prediction()
            print("Prediction started!")

    def get_status(self):
        with self.lock:
            return {
                "state": self.recognizer.state,
                "prediction": str(self.recognizer.predicted_letter),
                "confidence": float(self.recognizer.confidence),
                "frames": len(self.recognizer.sequence)
            }


# =========================================================
# 4. WEBSITE HEADER
# =========================================================

with st.container(key="main_header"):
    st.title("🤟 SIGNMATE AI")
    st.subheader("Smart Sign Language Recognition System")
    st.write(
        "Bridging communication through intelligent "
        "hand gesture recognition."
    )


# =========================================================
# 5. WEBSITE NAVIGATION
# =========================================================

home_tab, about_tab, features_tab, process_tab, tech_tab, live_tab, team_tab = st.tabs([
    "Home",
    "About",
    "Features",
    "How It Works",
    "Technology",
    "Live Recognition",
    "Our Team"
])


# =========================================================
# 6. HOME
# =========================================================

with home_tab:
    st.subheader("Welcome to Signmate AI")
    st.write(
        "Signmate AI is an intelligent sign language recognition "
        "system that uses artificial intelligence to identify hand "
        "gestures through a live camera feed and display the recognized sign."
    )

    st.html("""
    <div class="info-card">
        <h3>Communication through technology</h3>
        <p>
            Signmate AI aims to make digital communication more accessible
            by using hand gesture recognition to support communication
            between sign language users and others.
        </p>
    </div>
    """)

    st.markdown("### Explore the website")
    home_col1, home_col2, home_col3 = st.columns(3)

    with home_col1:
        st.html("""
        <div class="info-card">
            <h3>Learn about the project</h3>
            <p>Discover the purpose and objectives behind Signmate AI.</p>
        </div>
        """)

    with home_col2:
        st.html("""
        <div class="info-card">
            <h3>Explore the features</h3>
            <p>Understand the main capabilities of the recognition system.</p>
        </div>
        """)

    with home_col3:
        st.html("""
        <div class="info-card">
            <h3>Try the recognition system</h3>
            <p>Open Live Recognition to use the camera-based demonstration.</p>
        </div>
        """)

    st.info("Select **Live Recognition** in the navigation above to try Signmate AI.")


# =========================================================
# 7. ABOUT
# =========================================================

with about_tab:
    st.subheader("About Signmate AI")

    st.write(
        "Signmate AI is a smart sign language recognition project "
        "developed to support more accessible communication. The system "
        "uses computer vision and machine learning techniques to analyse "
        "hand gestures captured through a camera."
    )

    st.markdown("### Our purpose")
    st.html("""
    <div class="info-card">
        <h3>Making communication more accessible</h3>
        <p>
            The purpose of Signmate AI is to explore how artificial
            intelligence can help recognize sign language gestures and
            present the predicted signs in a simple text format.
        </p>
    </div>
    """)

    st.markdown("### Project objectives")
    st.html("""
    - Recognize hand gestures using a camera.
    - Process hand movements and extract useful features.
    - Use a trained machine learning model to predict signs.
    - Display the recognized output clearly.
    - Create a simple and user-friendly interface.
    """)


# =========================================================
# 8. FEATURES
# =========================================================

with features_tab:
    st.subheader("Key Features")
    st.write("Explore the main capabilities of the Signmate AI system.")

    feature_col1, feature_col2 = st.columns(2)

    with feature_col1:
        st.html("""
        <div class="info-card">
            <h3>📷 Live Camera Input</h3>
            <p>Uses a live camera feed to capture hand gestures for recognition.</p>
        </div>
        <div class="info-card">
            <h3>✋ Hand Gesture Detection</h3>
            <p>Analyses hand landmarks to represent the position of the hand.</p>
        </div>
        <div class="info-card">
            <h3>🤖 AI-Based Prediction</h3>
            <p>Uses a trained machine learning model to predict the sign from extracted features.</p>
        </div>
        """)

    with feature_col2:
        st.html("""
        <div class="info-card">
            <h3>⚡ Real-Time Processing</h3>
            <p>Processes camera frames continuously while the recognition session is active.</p>
        </div>
        <div class="info-card">
            <h3>🔤 Text Output</h3>
            <p>Displays the recognized sign as a prediction on the website.</p>
        </div>
        <div class="info-card">
            <h3>📊 Confidence Display</h3>
            <p>Shows the confidence value returned by the recognition model.</p>
        </div>
        """)


# =========================================================
# 9. HOW IT WORKS
# =========================================================

with process_tab:
    st.subheader("How Signmate AI Works")
    st.write(
        "The system follows a sequence of steps to convert a hand gesture "
        "captured by the camera into a predicted sign."
    )

    steps = [
        ("01", "Camera Input", "The camera captures the user's hand gesture."),
        ("02", "Hand Detection", "MediaPipe detects hand landmarks."),
        ("03", "Feature Extraction", "Landmark coordinates are prepared as model inputs."),
        ("04", "AI Prediction", "The trained machine learning model predicts the sign."),
        ("05", "Text Display", "The predicted sign and confidence are displayed.")
    ]

    for number, heading, description in steps:
        st.markdown(
            f"""
            <div class="info-card">
                <h3>{number} · {heading}</h3>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# 10. TECHNOLOGY STACK
# =========================================================

with tech_tab:
    st.subheader("Technology Stack")
    st.write("The following technologies are used in the Signmate AI project.")

    tech_col1, tech_col2 = st.columns(2)

    with tech_col1:
        st.html("""
        <div class="info-card">
            <h3>Python</h3>
            <p>Used as the main programming language for the recognition system.</p>
        </div>
        <div class="info-card">
            <h3>MediaPipe</h3>
            <p>Used for hand landmark detection and feature extraction.</p>
        </div>
        <div class="info-card">
            <h3>Random Forest</h3>
            <p>Used as the machine learning model for sign prediction.</p>
        </div>
        """)

    with tech_col2:
        st.html("""
        <div class="info-card">
            <h3>Streamlit</h3>
            <p>Used to build the interactive web application interface.</p>
        </div>
        <div class="info-card">
            <h3>Streamlit-WebRTC</h3>
            <p>Connects the browser camera stream to the video-processing component.</p>
        </div>
        <div class="info-card">
            <h3>OpenCV</h3>
            <p>Supports image and video frame processing in the recognition pipeline.</p>
        </div>
        """)


# =========================================================
# 11. LIVE SIGN RECOGNITION
# =========================================================

# =========================================================
# 11. LIVE SIGN RECOGNITION
# =========================================================

with live_tab:

    st.subheader("📷 Live Sign Detection")
    st.write("Position your hand in front of the camera.")

    left, right = st.columns([1.5, 1], gap="large")

    with left:

        ctx = webrtc_streamer(
            key="signmate-final-test",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=SignMateVideoProcessor,
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True,
            rtc_configuration={
                "iceServers": [
                    {
                        "urls": [
                            "stun:stun.l.google.com:19302"
                        ]
                    }
                ]
            }
        )

        st.caption(
            "Allow camera permission when your browser requests it."
        )

    with right:

        st.subheader("💬 Translation Output")

        start_button = st.button(
            "▶ Start Prediction",
            use_container_width=True
        )

        if start_button:

            if ctx.video_processor is not None:
                ctx.video_processor.start_prediction()
                st.success("Prediction started! Show your hand.")

            else:
                st.warning("Please start the camera first.")

    st.divider()

    # Automatically refresh only the recognition status.
    @st.fragment(run_every="1s")
    def render_recognition_status():

        st.subheader("Recognition Status")

        if ctx.video_processor is not None:

            try:

                data = ctx.video_processor.get_status()

                state = data["state"]
                prediction = data["prediction"]
                confidence = data["confidence"]
                frames = data["frames"]

                status_messages = {
                    "READY": "Ready to start",
                    "WAITING_HAND": "Show your hand",
                    "COUNTDOWN": "Get ready! Hold your sign",
                    "RECORDING": "Recognizing your sign...",
                    "RESULT": "Recognition completed"
                }

                st.info(status_messages.get(state, state))

                valid_prediction = (
                    prediction.strip().lower()
                    not in ("none", "", "null")
                )

                if valid_prediction:

                    with st.container(key="prediction_card"):

                        st.markdown("**RECOGNIZED SIGN**")
                        st.markdown(f"# {prediction}")

                    with st.container(key="confidence_card"):

                        st.markdown("**RECOGNITION CONFIDENCE**")
                        st.markdown(f"## {confidence:.2f}%")

                else:

                    st.info("Your recognized sign will appear here.")

                    with st.container(key="confidence_card"):

                        st.markdown("**RECOGNITION CONFIDENCE**")
                        st.markdown("## Waiting for prediction...")

                if state == "RECORDING":

                    st.progress(
                        min(frames / 20, 1.0),
                        text=f"Recording: {frames}/20 frames"
                    )

            except Exception as error:

                st.error(
                    f"Unable to retrieve prediction: {error}"
                )

        else:

            st.info("Start the camera to begin recognition.")

    render_recognition_status()

    # Usage and limitations note
    st.markdown("""
    <div class="info-card" style="margin-top:18px;">
        <h3>Usage &amp; Limitations</h3>
        <p><strong>Usage:</strong> Allow camera access, keep your hand clearly visible in the camera frame,
        use a well-lit environment, and hold a supported sign steadily while recognition runs.</p>
        <p><strong>Limitations:</strong> Recognition is limited to the signs/classes included in the
        model's training data. Results may vary with lighting, camera quality, hand position,
        movement and background conditions. This prototype is intended for demonstration and
        learning; it may not interpret every sign or replace a qualified sign-language interpreter.</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 12. OUR TEAM
# =========================================================

with team_tab:
    st.subheader("Our Team")
    st.write(
        "Signmate AI was developed through teamwork, collaboration "
        "and the shared goal of exploring AI-powered sign recognition."
    )

    team_members = [
        "T.K. Nithila",
        "Akshara Geeta Probhu",
        "G. Bhuvaneswari",
        "B. Dharshini",
        "Shankara Narayanan S",
        "V. Sudhish"
    ]

    team_columns = st.columns(3)

    for index, member in enumerate(team_members):
        with team_columns[index % 3]:
            st.markdown(
                f"""
                <div class="info-card" style="min-height: 85px; text-align:center;">
                    <h3>{member}</h3>
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# 13. FOOTER
# =========================================================

st.divider()

with st.container(key="main_footer"):
    st.markdown("**SIGNMATE AI**")
    st.caption(
        "Smart Assistive Technology | "
        "Innovation • Accessibility • Inclusion"
    )
