import customtkinter as ctk
import requests
import sys
import ctypes
import datetime
from tkinter import messagebox
from PIL import Image, ImageTk
import io
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

API_KEY = "your API KEY"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
AQI_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
LOCATION_URL = "http://ip-api.com/json/"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("540x600")
app.title("☁️ Weather App")

# Set taskbar icon (Windows only)
if sys.platform.startswith("win"):
    myappid = u'weather.app.customtkinter.001'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    try:
        ico_path = os.path.join(os.path.dirname(__file__), "weather.ico")
        app.iconbitmap(ico_path)
    except:
        print("Icon failed to load.")

tabs = ctk.CTkTabview(app, width=520, height=520)
tabs.pack(pady=10)

current_tab = tabs.add("Current Weather")
forecast_tab = tabs.add("7-Day Forecast")
aqi_tab = tabs.add("Air Quality")

city_entry = ctk.CTkEntry(app, placeholder_text="Enter city or Auto", width=300, font=("Segoe UI", 14))
city_entry.pack(pady=8)

result_label = ctk.CTkLabel(current_tab, text="", font=("Segoe UI", 14), justify="left")
result_label.pack(pady=10)

forecast_frames = []
for i in range(7):
    frame = ctk.CTkFrame(forecast_tab, width=480, height=60, corner_radius=10)
    frame.pack(pady=5)
    forecast_frames.append(frame)

aqi_canvas = None

def get_current_city():
    try:
        res = requests.get(LOCATION_URL, timeout=5)
        data = res.json()
        return data.get("city"), data.get("lat"), data.get("lon")
    except:
        return None, None, None

def update_aqi(lat, lon):
    global aqi_canvas
    for widget in aqi_tab.winfo_children(): widget.destroy()

    try:
        res = requests.get(AQI_URL, params={"lat": lat, "lon": lon, "appid": API_KEY})
        data = res.json()["list"][0]
        aqi = data["main"]["aqi"]

        fig, ax = plt.subplots(figsize=(5, 2))
        categories = ["Good", "Fair", "Moderate", "Poor", "Very Poor"]
        colors = ["green", "lime", "orange", "red", "purple"]
        ax.bar(categories, [1 if i == aqi-1 else 0.2 for i in range(5)], color=colors)
        ax.set_title("Air Quality Index")

        aqi_canvas = FigureCanvasTkAgg(fig, master=aqi_tab)
        aqi_canvas.draw()
        aqi_canvas.get_tk_widget().pack()
    except:
        messagebox.showerror("Error", "Failed to fetch AQI data")

def update_forecast(city):
    try:
        res = requests.get(FORECAST_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
        data = res.json()
        daily = {}

        for item in data["list"]:
            date = item["dt_txt"].split(" ")[0]
            if date not in daily:
                daily[date] = item

        for i, (day, item) in enumerate(list(daily.items())[:7]):
            temp = item["main"]["temp"]
            cond = item["weather"][0]["main"]
            desc = item["weather"][0]["description"]
            dt = datetime.datetime.strptime(day, "%Y-%m-%d")
            weekday = dt.strftime("%A")

            forecast_frames[i].configure(fg_color="#1f1f1f")
            for w in forecast_frames[i].winfo_children():
                w.destroy()

            label = ctk.CTkLabel(forecast_frames[i], text=f"{weekday}: {temp}°C, {cond} ({desc})",
                                 font=("Segoe UI", 13))
            label.pack(pady=10, padx=10)
    except:
        messagebox.showerror("Error", "Failed to fetch forecast")

def get_weather(city):
    if not city:
        messagebox.showerror("Error", "City not found.")
        return

    params = {"q": city, "appid": API_KEY, "units": "metric"}

    try:
        res = requests.get(WEATHER_URL, params=params)
        res.raise_for_status()
        data = res.json()

        temp = data['main']['temp']
        weather = data['weather'][0]['main']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']
        city_name = data['name']

        result = (
            f"📍 City: {city_name}\n"
            f"🌡️ Temp: {temp}°C\n"
            f"☁️ Weather: {weather} ({desc})\n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬️ Wind: {wind} m/s"
        )
        result_label.configure(text=result)

        update_forecast(city)
    except:
        messagebox.showerror("Error", "Could not retrieve weather info.")

def auto_fetch_weather():
    city, lat, lon = get_current_city()
    if city:
        city_entry.delete(0, 'end')
        city_entry.insert(0, city)
        get_weather(city)
        update_aqi(lat, lon)
    else:
        messagebox.showwarning("Warning", "Unable to detect location.")

fetch_btn = ctk.CTkButton(app, text="Get Weather", command=lambda: get_weather(city_entry.get()), font=("Segoe UI", 14))
fetch_btn.pack(pady=6)

auto_btn = ctk.CTkButton(app, text="Auto-Detect Location", command=auto_fetch_weather, font=("Segoe UI", 14))
auto_btn.pack(pady=6)

app.mainloop()
