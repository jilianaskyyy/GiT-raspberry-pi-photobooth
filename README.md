# Raspberry Pi Photobooth

An interactive photobooth built using a Raspberry Pi, camera, display and thermal printer. Users can control the photobooth using hand gestures to take, review and print photos without needing a computer.

## Description

The Raspberry Pi Photobooth is a standalone photo-taking system designed to provide a simple and interactive experience for users. The system uses a Raspberry Pi connected to a camera, display and thermal printer. A camera preview is displayed on screen while MediaPipe is used to detect hand gestures as controls. Users can use gestures to start different countdowns, capture photos, confirm or retake photos, and complete the photo session. After capturing four photos, the selected photos can be printed using a thermal printer. The system can also upload the photos and generate a QR code so users can scan and access their digital photos.

## Getting Started

### Dependencies

The following hardware and software are required to run the project.

**Hardware**

* Raspberry Pi
* Raspberry Pi Camera Module or compatible camera
* LCD/display
* Pi Hut Thermal Printer
* MicroSD card
* Stable power supply
* Internet connection for photo uploading and QR code generation

**Software**

* Raspberry Pi OS
* Python 3
* OpenCV
* MediaPipe
* Git
* Required Python libraries listed in `requirements.txt`

### Installing

1. **Clone the repository onto the Raspberry Pi.**

```bash
git clone <repository-url>
```

2. **Navigate into the project folder.**

```bash
cd <project-folder>
```

3. **Install the required Python dependencies.**

```bash
pip install -r requirements.txt
```

4. **Connect the camera, display and thermal printer to the Raspberry Pi.**

5. **Configure the required settings**, such as:

* Camera settings
* Printer settings
* Photo upload settings
* QR code settings

6. **Make sure the Raspberry Pi has the required permissions** to access the camera and printer.

## Executing program

1. **Navigate to the project directory.**

```bash
cd <project-folder>
```

2. **Start the photobooth program.**

```bash
python3 main.py
```

3. **The camera preview will appear** on the connected display.

4. **Use the supported hand gestures** to control the photobooth.

### Gesture Controls

| **Gesture**        | **Action**                 |
| ------------------ | -------------------------- |
| ✌️ **3 fingers**   | Start a 3-second countdown |
| 🖐️ **Open hand**  | Start a 5-second countdown |
| 👍 **Thumbs up**   | Confirm/select photo       |
| 👎 **Thumbs down** | Retake photo               |

5. **The photobooth captures a total of four photos.**

6. **Review the captured photos** and use the gestures to confirm or retake them.

7. **Print the confirmed photos** using the thermal printer.

8. **Upload the photos digitally** using the configured photo upload service.

9. **Scan the displayed QR code** to access the digital photos.

## Help

### Camera is not detected

Check that the camera is properly connected and enabled on the Raspberry Pi.

```bash
libcamera-hello
```

If the camera does not appear, check the camera connection and Raspberry Pi camera configuration.

### Hand gestures are not detected

Make sure the user's hand is clearly visible to the camera and that there is sufficient lighting. Avoid covering the hand or standing too far away from the camera.

### Thermal printer is not printing

Check that:

* The printer is powered on.
* The printer is properly connected to the Raspberry Pi.
* Thermal paper is inserted correctly.
* The printer configuration matches the connection being used.

### Photos are not uploading

Check that the Raspberry Pi has an active internet connection and that the photo upload service is correctly configured.

## Authors

**Raspberry Pi Photobooth Project Team**

* Yu Yao
* Gui Ru
* Jiliana
* Francesca

## License

This project is currently developed as a student project.

## Acknowledgments

* Raspberry Pi documentation and community
* MediaPipe for hand gesture detection
* OpenCV for camera and image processing
* Pi Hut for the thermal printer hardware
* Python community and documentation
* GitHub for version control and collaboration
