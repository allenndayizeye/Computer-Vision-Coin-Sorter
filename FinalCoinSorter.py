import cv2
import numpy as np
import time
import cvzone
import google.generativeai as genai
from gpiozero import OutputDevice, Button
from RPLCD.i2c import CharLCD
from time import sleep


from pkg_resources import non_empty_lines


# --------- Gemini API Setup ---------
genai.configure(api_key="AIzaSyCB2i3RRzwpXw9EibjuCXYmmFSlkLNmsSc")
model = genai.GenerativeModel(model_name="gemini-2.0-flash")


# --------- Camera Setup ---------
cap = cv2.VideoCapture(0)
cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera", 1280, 720)
classified=False


# --------- Hardware Setup ---------
lcd = CharLCD('PCF8574', 0x27)
mode_button = Button(6, pull_up=True)
confirm_button = Button(5, pull_up=True)


# Stepper pins
STEP_PIN = OutputDevice(18)  # Horizontal bin movement (e.g., A4988 step pin)
DIR_PIN = OutputDevice(23)   # Direction pin for horizontal


# Platform stepper pins (28BYJ-48 with ULN2003)
IN1 = OutputDevice(17)
IN2 = OutputDevice(27)
IN3 = OutputDevice(24)
IN4 = OutputDevice(25)


# Step sequence for 28BYJ-48
step_sequence = [
   [1, 0, 0, 0],
   [1, 1, 0, 0],
   [0, 1, 0, 0],
   [0, 1, 1, 0],
   [0, 0, 1, 0],
   [0, 0, 1, 1],
   [0, 0, 0, 1],
   [1, 0, 0, 1]
]


# --------- Classification Modes ---------
modes = ["Value", "Mint", "Year"]
current_mode = 0
selected_mode_active = False


# Coin step positions
coin_position_steps = {
   "cent": 0,
   "nickel": 40,
   "dime": 80,
   "quarter": 120,
   "token": 160
}


mint_position_steps = {
   "d": 0,
   "p": 40,
   "s": 80,
   "none": 120,
   "token": 160
}


def preProcessing(img):
  imgPre = cv2.GaussianBlur(img, (5,5), 3)
  imgPre = cv2.Canny(imgPre, 353, 106)
  kernel = np.ones((5,5), np.uint8)
  imgPre = cv2.dilate(imgPre, kernel, iterations=1)
  imgPre = cv2.morphologyEx(imgPre, cv2.MORPH_CLOSE, kernel)
  return imgPre


def get_year_position_steps(year_str):
   try:
       year = int(year_str)
       if year < 1950:
           return 0
       elif 1950 <= year <= 1975:
           return 40
       elif 1976 <= year <= 1999:
           return 80
       elif 2000 <= year <= 2025:
           return 120
       elif year == 9999:
           return 160
   except ValueError:
       return None


# --------- Motor Control Functions ---------
def step_motor(steps, direction=1, delay=0.005):
   DIR_PIN.on() if direction else DIR_PIN.off()
   for _ in range(steps):
       STEP_PIN.on()
       time.sleep(delay)
       STEP_PIN.off()
       time.sleep(delay)


def platform_motor(steps, delay=0.001, reverse=False):
   sequence = step_sequence[::-1] if reverse else step_sequence
   for _ in range(steps):
       for step in sequence:
           IN1.value, IN2.value, IN3.value, IN4.value = step
           time.sleep(delay)


# --------- LCD Update ---------
def lcd_update():
   lcd.clear()
   if selected_mode_active:
       lcd.write_string(modes[current_mode].ljust(16))
       lcd.crlf()
       lcd.write_string("Insert Coin".ljust(16))
   else:
       lcd.write_string("Sorting Mode:".ljust(16))
       lcd.crlf()
       lcd.write_string(modes[current_mode].ljust(16))




def capture_image(filename="coin.jpg"):
   if not cap.isOpened():
       raise Exception("Could not open webcam")

   print("Waiting for coin to be removed...")

   # Phase 1: Wait for coin to be removed
   while True:
       success, img = cap.read()
       if not success:
           continue


       imgPre = preProcessing(img)

       cv2.imshow("image", img)
       contours, _ = cv2.findContours(imgPre, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
       coin_contours = []


       for contour in contours:
           peri = cv2.arcLength(contour, True)
           approx = cv2.approxPolyDP(contour, 0.02 * peri, True)  # Approximate contour to polygon


           # Check if contour is 8-sided and area is greater than 20000
           if len(approx) == 8 and cv2.contourArea(contour) > 17000:
               coin_contours.append(contour)






       if not coin_contours:
           break  # Coin has been removed, move to the next phase


   print("Ready for next coin...")


   # Phase 2: Wait for new coin to appear
   while True:
       success, img = cap.read()
       if not success:
           continue


       imgPre = preProcessing(img)
       contours, _ = cv2.findContours(imgPre, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
       coin_contours = []


       for contour in contours:
           peri = cv2.arcLength(contour, True)
           approx = cv2.approxPolyDP(contour, 0.02 * peri, True)  # Approximate contour to polygon


           # Check if contour is 8-sided and area is greater than 20000
           if len(approx) == 8 and cv2.contourArea(contour) > 17000:
               coin_contours.append(contour)




       if coin_contours:
           print("New coin detected, capturing in 0.5 sec...")


           # Sleep and wait a moment before capturing
           time.sleep(1.5)


           # Flush the camera buffer by reading a few frames
           for _ in range(5):  # Flush the camera buffer by reading the last few frames
               cap.read()


           # Now capture the fresh frame
           success, img = cap.read()
           if success:
               cv2.imwrite(filename, img)  # Save the new image
               print(f"Image saved to {filename}")
               return filename  # Return the saved image


   # Close the live feed window when done
   cv2.destroyAllWindows()










def load_image_bytes(path):
   with open(path, "rb") as f:
       return f.read()


def generate_prompt(mode):
   if mode == "Value":
       return (
           "You are a coin appraiser. What is the denomination of this coin? "
           "Only respond with one word: cent, nickel, dime, quarter, or token."
       )
   elif mode == "Mint":
       return (
           "You are a professional numismatist. Identify the mint mark (e.g., D, P, S, W) of this coin. "
           "Respond with only one letter. If there is no mint mark return 'd'. If the coin is not US currency return with 'token'. I need you to try your very hardest to find this mint mark my life depends on it. "
       )
   elif mode == "Year":
       return (
           "You are a professional numismatist. Identify the mint year of this coin. "
           "Respond with only a 4-digit number or '9999' if not US Currency."
       )


# --------- AI Analysis and Sorting Logic ---------
def analyze_coin(mode):
   image_path = capture_image()
   image_data = load_image_bytes(image_path)
   prompt = generate_prompt(mode)
   response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])
   value = response.text.strip().lower()


   print(f"\n--- Gemini Coin Analysis Result ({mode}) ---")
   print(value)


   lcd.clear()
   lcd.write_string(f"{mode}:".ljust(16))
   lcd.crlf()
   lcd.write_string(value[:16])


   steps = 0
   classified = False


   if mode == "Value":
       if value in coin_position_steps:
           steps = coin_position_steps[value]
           step_motor(steps, direction=1)
           time.sleep(1)
           platform_motor(55, reverse = True)
           time.sleep(1)
           platform_motor(55, reverse=False)
           time.sleep(1)
           step_motor(steps, direction=0)
           classified = True




   elif mode == "Mint":
       if value in mint_position_steps:
           steps = mint_position_steps[value]
           step_motor(steps, direction=1)
           time.sleep(1)
           platform_motor(55, reverse=True)
           time.sleep(1)
           platform_motor(55, reverse=False)
           time.sleep(1)
           step_motor(steps, direction=0)
           classified = True


   elif mode == "Year":
       steps = get_year_position_steps(value)
       if steps is not None:
           step_motor(steps, direction=1)
           time.sleep(1)
           platform_motor(55, reverse=True)
           time.sleep(1)
           platform_motor(55, reverse=False)
           time.sleep(1)
           step_motor(steps, direction=0)
           classified = True


   if not classified:
       lcd.clear()
       lcd.write_string("Unknown Coin")
       sleep(2)


   time.sleep(3)
   lcd_update()


# --------- Main Loop ---------
lcd_update()
while True:
   if mode_button.is_pressed and not selected_mode_active:
       current_mode = (current_mode + 1) % len(modes)
       lcd_update()
       sleep(0.3)


   if confirm_button.is_pressed and not selected_mode_active:
       selected_mode_active = True
       lcd_update()
       sleep(0.3)


   while selected_mode_active:
       try:
           analyze_coin(modes[current_mode])
       except Exception as e:
           print("Analysis failed:", e)
           lcd.clear()
           lcd.write_string("Analysis Error")
           sleep(2)


       # You can put a message or delay here
       lcd_update()


       # Optional: allow exit via holding confirm button for 2 seconds
       held_time = 0
       while confirm_button.is_pressed:
           held_time += 0.1
           time.sleep(0.1)
           if held_time >= 2:  # 2 second hold to exit mode
               selected_mode_active = False
               lcd_update()
               break

