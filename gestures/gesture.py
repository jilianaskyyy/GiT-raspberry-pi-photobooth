# mediapie and open cv

# 4 different functions: 
#   ✌️ 3 fingers	Start a 3-second countdown
#   🖐️ Open hand	 Start a 5-second countdown
#   👍 Thumbs up	Confirm/select photo
#   ✊ Close fist   Retake photo

import cv2
import mediapipe as mp
import math


class GestureDetector:

    def __init__(self):
        """
        Initialise MediaPipe Hands.

        MediaPipe Hands detects a hand in an image and gives us
        21 landmark points for that hand.
        """

        # Create the MediaPipe Hands object
        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,                # video frames, not unrelated photographs
            max_num_hands=1,                        # only detect 1 hand
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # Used to draw the hand skeleton on the camera frame
        self.mp_draw = mp.solutions.drawing_utils


    def process_frame(self, frame):    # camera take in pictures in BGR, ASK if display will be in BGR or greyscale. ASK 
        """
        Send one camera frame to MediaPipe.

        Parameters:
            frame: an OpenCV camera frame (BGR format)

        Returns:
            hand_landmarks: the detected hand landmarks
            handedness: whether the hand is Left or Right
        """

        # OpenCV normally gives us images in BGR format.
        # MediaPipe expects RGB images.
        # Convert frame from BGR to RGB 
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)          

        # Process the image using MediaPipe
        results = self.hands.process(rgb_frame)

        # If no hand is detected, return None
        if not results.multi_hand_landmarks:
            return None, None

        # Get the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]

        # Get whether MediaPipe thinks it is a Left or Right hand
        handedness = results.multi_handedness[0].classification[0].label

        return hand_landmarks, handedness


    def is_finger_extended(self, landmarks, finger):
        """
        Determine whether a finger is extended.

        MediaPipe gives us coordinates for different joints
        of each finger.

        For the four fingers (index, middle, ring, pinky),
        we compare the fingertip with the PIP joint.

        If the fingertip is above the PIP joint,
        we consider the finger extended.

        Returns:
            True  -> finger is extended
            False -> finger is folded
        """

        # MediaPipe landmark IDs:
        #
        # Index:
        #   PIP = 6
        #   TIP = 8
        #
        # Middle:
        #   PIP = 10
        #   TIP = 12
        #
        # Ring:
        #   PIP = 14
        #   TIP = 16
        #
        # Pinky:
        #   PIP = 18
        #   TIP = 20

        finger_landmarks = {
            "index": (6, 8),
            "middle": (10, 12),
            "ring": (14, 16),
            "pinky": (18, 20)
        }

        pip_id, tip_id = finger_landmarks[finger]

        pip = landmarks.landmark[pip_id]
        tip = landmarks.landmark[tip_id]

        # MediaPipe's y-coordinate increases as we move DOWN.
        #
        # Therefore:
        # tip.y < pip.y
        #
        # means the fingertip is above the PIP joint.
        return tip.y < pip.y


    def is_thumb_extended(self, landmarks):
        """
        Determine whether the thumb is extended.

        The thumb is different from the other four fingers,
        so we use the distance between the thumb tip and
        the index finger MCP joint.

        This is a simple first version and may need tuning
        after testing with the actual camera.
        """

        thumb_tip = landmarks.landmark[4]
        index_mcp = landmarks.landmark[5]

        distance = math.sqrt(
            (thumb_tip.x - index_mcp.x) ** 2 +
            (thumb_tip.y - index_mcp.y) ** 2
        )

        # If the thumb tip is sufficiently far away from
        # the index finger base, we treat it as extended.
        return distance > 0.12


    def get_finger_states(self, landmarks):
        """
        Check the state of all five fingers.

        Returns a dictionary such as:

        {
            "thumb": True,
            "index": True,
            "middle": True,
            "ring": False,
            "pinky": False
        }

        True  = extended
        False = folded
        """

        return {
            "thumb": self.is_thumb_extended(landmarks),

            "index": self.is_finger_extended(
                landmarks, "index"
            ),

            "middle": self.is_finger_extended(
                landmarks, "middle"
            ),

            "ring": self.is_finger_extended(
                landmarks, "ring"
            ),

            "pinky": self.is_finger_extended(
                landmarks, "pinky"
            )
        }


    def is_three_fingers(self, fingers):
        """
        Check whether exactly THREE fingers are extended.

        This means we are not looking for one specific
        combination such as index + middle + ring.

        Any combination of exactly three extended fingers
        can potentially be recognised.

        Example:

        True, True, True, False, False
        = 3 fingers

        False, True, True, True, False
        = 3 fingers

        True, False, True, False, True
        = 3 fingers
        """

        number_of_extended_fingers = sum(fingers.values())

        return number_of_extended_fingers == 3


    def is_open_hand(self, fingers):
        """
        Check whether all five fingers are extended.

        Example:

        thumb  = True
        index  = True
        middle = True
        ring   = True
        pinky  = True

        Therefore this is an open hand.
        """

        return all(fingers.values())


    def is_fist(self, fingers):
        """
        Check whether all five fingers are folded.

        This is NOT currently one of your required gestures,
        but it is useful as a test gesture.
        """

        return not any(fingers.values())


    def is_thumbs_up(self, landmarks, fingers):
        """
        Check for a thumbs-up gesture.

        For thumbs-up:
        - Thumb should be extended
        - Other four fingers should be folded
        """

        other_fingers_folded = (
            not fingers["index"]
            and not fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
        )

        if not fingers["thumb"] or not other_fingers_folded:
            return False

        thumb_tip = landmarks.landmark[4]
        thumb_mcp = landmarks.landmark[2]

        # Thumb tip should be ABOVE the thumb MCP joint.
        # Remember: smaller y = higher on the image.
        return thumb_tip.y < thumb_mcp.y


    # def is_thumbs_down(self, landmarks, fingers):
    #     """
    #     Check for a thumbs-down gesture.

    #     For thumbs-down:
    #     - Thumb should be extended
    #     - Other four fingers should be folded
    #     - Thumb tip should be BELOW the thumb MCP joint
    #     """

    #     other_fingers_folded = (
    #         not fingers["index"]
    #         and not fingers["middle"]
    #         and not fingers["ring"]
    #         and not fingers["pinky"]
    #     )

    #     if not fingers["thumb"] or not other_fingers_folded:
    #         return False

    #     thumb_tip = landmarks.landmark[4]
    #     thumb_mcp = landmarks.landmark[2]

    #     # Thumb tip should be BELOW the thumb MCP joint.
    #     return thumb_tip.y > thumb_mcp.y


    def classify_gesture(self, landmarks):
        """
        Convert the detected finger positions into
        one of our recognised gesture names.

        IMPORTANT:
        This function ONLY identifies the gesture.

        It does NOT:
        - start the countdown
        - take a photo
        - confirm a photo
        - retake a photo

        It simply answers:
        "What gesture is the user making?"
        """

        fingers = self.get_finger_states(landmarks)

        # Check the more specific gestures first.

        if self.is_thumbs_up(landmarks, fingers):
            return "THUMBS_UP"

        if self.is_fist(landmarks, fingers):
            return "IS_FIST"

        # Check exactly 3 extended fingers.
        if self.is_three_fingers(fingers):
            return "THREE_FINGERS"

        # Check all 5 fingers.
        if self.is_open_hand(fingers):
            return "OPEN_HAND"

        # Nothing matched.
        return None


    def detect_gesture(self, frame):
        """
        Main function that your teammate will call.

        Input:
            camera frame

        Output:
            gesture name or None
        """

        landmarks, handedness = self.process_frame(frame)

        # No hand detected
        if landmarks is None:
            return None

        # Identify the gesture
        gesture = self.classify_gesture(landmarks)

        return gesture