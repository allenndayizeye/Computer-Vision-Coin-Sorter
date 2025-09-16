# Computer-Vision-Coin-Sorter
An automated coin classification and sorting system using a Raspberry Pi, Python, and OpenCV.

# Computer Vision Coin Sorter

[![Project Demo Video](https://img.youtube.com/vi/3zV9kLuA_2Y/maxresdefault.jpg)](https://youtu.be/3zV9kLuA_2Y)

This project is a fully automated coin classification and sorting machine. It uses a Raspberry Pi 5 and a camera to capture an image of a coin, leverages Google's Gemini Vision AI for robust image recognition (by Value, Mint, or Year), and then actuates a custom-built mechanical system to sort the coin into the appropriate bin.

### Key Features
* Automated sorting by **Value**, **Mint Mark**, or **Year** based on user selection.
* Utilizes the OpenCV library for image preprocessing to detect the coin.
* Integrates Google's Gemini Vision API for highly accurate, real-time classification.
* Custom-designed mechanical sorting system using stepper motors.
* User-friendly interface with an I2C LCD screen and physical buttons for mode selection.

### Technologies Used
* **Hardware:** Raspberry Pi 5, Pi Camera Module, Stepper Motors, I2C LCD Display, Buttons
* **Software:** Python, OpenCV, Google Generative AI API, gpiozero, RPLCD

### Setup and Installation
1.  Clone the repository to your local machine:
    ```
    git clone [https://github.com/](https://github.com/)[your-username]/[your-repo-name].git
    ```
2.  Navigate into the project directory:
    ```
    cd [your-repo-name]
    ```
3.  (Recommended) Create and activate a virtual environment:
    ```
    python -m venv venv
    source venv/bin/activate 
    ```
    *(Use `.\venv\Scripts\activate` on Windows)*

4.  Install the required Python libraries using the `requirements.txt` file:
    ```
    pip install -r requirements.txt
    ```

### Usage
1.  Ensure all hardware is connected correctly to the Raspberry Pi's GPIO pins.
2.  Run the main script from the terminal:
    ```
    python coin_sorter.py
    ```
    *(Replace `coin_sorter.py` with the actual name of your Python file)*

3.  Use the physical buttons on the device to select a sorting mode and follow the prompts on the LCD screen.
