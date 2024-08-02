import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import calendar
import random
from extra_streamlit_components import CookieManager

BASE_URL = st.secrets["base_url"]

# Initialize cookie manager
cookie_manager = CookieManager()

def login(username, password, device_info):
    uri = BASE_URL + "/login"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": "",
        "User-Agent": "okhttp/4.8.1",
        "Host": st.secrets["hosts"],
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    login_data = {
        "user_password": password,
        "user_name": username,
        **device_info
    }
    response = requests.post(uri, headers=headers, data=json.dumps(login_data))
    return response.json()

def get_headers(token):
    return {
        "Content-Type": "application/json; charset=UTF-8",
        'Authorization': 'Bearer ' + token,
        "User-Agent": "okhttp/4.8.1",
        "Host": st.secrets["hosts"],
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

@st.cache_data
def add_presensi(latitude, longitude, gpsckpoint_id, gpsckpoint_name, gpsckpoint_radius, timezone, timezone_name, time,
                 token):
    uri = BASE_URL + "/addpresence"
    presensi_data = {
        'latitude': latitude,
        'longitude': longitude,
        'gpsckpoint_id': gpsckpoint_id,
        'gpsckpoint_name': gpsckpoint_name,
        'gpsckpoint_radius': gpsckpoint_radius,
        'timezone': timezone,
        'timezone_name': timezone_name,
        'time': time
    }
    response = requests.post(uri, headers=get_headers(token), data=json.dumps(presensi_data))
    return response.json()

@st.cache_data
def get_checkpoints(token):
    uri = BASE_URL + "/checkpoints"
    response = requests.post(uri, headers=get_headers(token))
    return response.json()

def lakukan_presensi(lokasi, token):
    checkpoints = get_checkpoints(token)['data']
    if checkpoints:
        checkpoint_data = checkpoints[lokasi]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = add_presensi(
                str(float(checkpoint_data['gpsckpoint_latitude']) + random.uniform(0.000000001, 0.00001)),
                str(float(checkpoint_data['gpsckpoint_longitude']) + random.uniform(0.000000001, 0.00001)),
                checkpoint_data['gpsckpoint_id'],
                checkpoint_data['gpsckpoint_name'],
                checkpoint_data['gpsckpoint_radius'],
                'WIB', 'Asia/Jakarta',
                now_str,
                token)
            st.success("Presensi Berhasil!")
        except:
            st.error("Presensi Gagal Dilakukan!")
    else:
        st.warning("No checkpoint data available")

@st.cache_data
def datapresencelog(start_date, end_date, token):
    uri = BASE_URL + "/datapresencelog"
    data = {
        'start_date': start_date,
        'end_date': end_date
    }
    response = requests.post(uri, headers=get_headers(token), data=json.dumps(data))
    return response.json()['data']

def main():
    st.title("Sistem Presensi BMKG")

    # Check if token exists in cookies
    token = cookie_manager.get(cookie="token")
    
    if token is not None:
        st.session_state.token = token
        st.session_state.logged_in = True

    # Initialize session state
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'device_info' not in st.session_state:
        st.session_state.device_info = {
            "device_phone_brand": "asus",
            "device_imei": "0f447cfa064895f8",
            "device_phone_series": "ASUS_AI2201_D"
        }

    if not st.session_state.logged_in:
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Optional device info customization
        if st.checkbox("Customize Device Info"):
            st.session_state.device_info["device_phone_brand"] = st.text_input("Device Phone Brand",
                                                                               value=st.session_state.device_info[
                                                                                   "device_phone_brand"])
            st.session_state.device_info["device_imei"] = st.text_input("Device IMEI",
                                                                        value=st.session_state.device_info[
                                                                            "device_imei"])
            st.session_state.device_info["device_phone_series"] = st.text_input("Device Phone Series",
                                                                                value=st.session_state.device_info[
                                                                                    "device_phone_series"])

        if st.button("Login"):
            result = login(username, password, st.session_state.device_info)
            if result['status'] == '200':
                st.session_state.token = result['data'][0]['token']
                st.session_state.logged_in = True
                # Save token to cookie
                cookie_manager.set("token", st.session_state.token, expires_at=datetime.now() + timedelta(days=30))
                st.success("Login berhasil!")
                st.rerun()  # Rerun the script to update the UI
            else:
                st.error("Login gagal. Silakan coba lagi.")
    else:
        menu = st.sidebar.selectbox(
            "Menu",
            ["Histori Presensi", "Lakukan Presensi", "Logout"]
        )

        if menu == "Histori Presensi":
            st.header("Histori Presensi")
            start_date = st.date_input("Tanggal Mulai")
            end_date = st.date_input("Tanggal Akhir")
            if st.button("Lihat Histori"):
                data = datapresencelog(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                                       st.session_state.token)
                st.table(data)

        elif menu == "Lakukan Presensi":
            st.header("Lakukan Presensi")
            checkpoints = get_checkpoints(st.session_state.token)
            lokasi_options = [checkpoint['gpsckpoint_name'] for checkpoint in checkpoints['data']]
            lokasi = st.selectbox("Pilih lokasi presensi", lokasi_options)
            if st.button("Lakukan Presensi"):
                checkpoint_id = lokasi_options.index(lokasi)
                lakukan_presensi(checkpoint_id, st.session_state.token)

        elif menu == "Logout":
            st.session_state.token = None
            st.session_state.logged_in = False
            # Remove token from cookie
            cookie_manager.delete("token")
            st.success("Logout berhasil!")
            st.rerun()  # Rerun the script to update the UI

if __name__ == "__main__":
    main()
