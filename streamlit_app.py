import streamlit as st
from streamlit.components.v1 import html
from datetime import datetime
import random
import json

BASE_URL = "https://spreso.bmkg.go.id/api-mobile-presence/index.php/api/v1"


def main():
    st.title("Sistem Presensi BMKG")

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'device_info' not in st.session_state:
        st.session_state.device_info = {
            "device_phone_brand": "asus",
            "device_imei": "0f447cfa064895f8",
            "device_phone_series": "ASUS_AI2201_D"
        }

    # JavaScript function to make API calls
    js_code = f"""
    <script>
    async function makeApiCall(endpoint, data, token = '') {{
        const response = await fetch("{BASE_URL}/" + endpoint, {{
            method: 'POST',
            headers: {{
                "Content-Type": "application/json; charset=UTF-8",
                "Authorization": token ? 'Bearer ' + token : '',
                "User-Agent": "okhttp/4.8.1",
                "Host": "spreso.bmkg.go.id",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip"
            }},
            body: JSON.stringify(data)
        }});
        return await response.json();
    }}

    window.login = async function(username, password, deviceInfo) {{
        const result = await makeApiCall('login', {{
            user_password: password,
            user_name: username,
            ...deviceInfo
        }});
        window.parent.postMessage({{type: 'login', result}}, '*');
    }};

    window.getCheckpoints = async function(token) {{
        const result = await makeApiCall('checkpoints', {{}}, token);
        window.parent.postMessage({{type: 'checkpoints', result}}, '*');
    }};

    window.addPresensi = async function(presenceData, token) {{
        const result = await makeApiCall('addpresence', presenceData, token);
        window.parent.postMessage({{type: 'addPresensi', result}}, '*');
    }};

    window.getDataPresenceLog = async function(startDate, endDate, token) {{
        const result = await makeApiCall('datapresencelog', {{ start_date: startDate, end_date: endDate }}, token);
        window.parent.postMessage({{type: 'presenceLog', result}}, '*');
    }};
    </script>
    """

    # Inject JavaScript code
    html(js_code)

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
            st.write(f"""
            <script>
            login('{username}', '{password}', {json.dumps(st.session_state.device_info)});
            </script>
            """, unsafe_allow_html=True)

            # Use st.empty() to create a placeholder for the result
            result_placeholder = st.empty()

            # JavaScript to handle the login result
            st.write("""
            <script>
            window.addEventListener('message', function(event) {
                if (event.data.type === 'login') {
                    const result = event.data.result;
                    if (result.status === '200') {
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: JSON.stringify({
                                loggedIn: true,
                                token: result.data[0].token
                            })
                        }, '*');
                    } else {
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: JSON.stringify({
                                loggedIn: false,
                                error: 'Login failed'
                            })
                        }, '*');
                    }
                }
            });
            </script>
            """, unsafe_allow_html=True)

            # Handle the result
            result = json.loads(st.experimental_get_query_params().get('result', ['{}'])[0])
            if result.get('loggedIn'):
                st.session_state.token = result['token']
                st.session_state.logged_in = True
                result_placeholder.success("Login berhasil!")
                st.rerun()
            elif 'error' in result:
                result_placeholder.error(f"Login gagal: {result['error']}")

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
                st.write(f"""
                <script>
                getDataPresenceLog('{start_date}', '{end_date}', '{st.session_state.token}');
                </script>
                """, unsafe_allow_html=True)

                # Use st.empty() to create a placeholder for the result
                result_placeholder = st.empty()

                # JavaScript to handle the presence log result
                st.write("""
                <script>
                window.addEventListener('message', function(event) {
                    if (event.data.type === 'presenceLog') {
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: JSON.stringify(event.data.result)
                        }, '*');
                    }
                });
                </script>
                """, unsafe_allow_html=True)

                # Handle the result
                result = json.loads(st.experimental_get_query_params().get('result', ['{}'])[0])
                if 'data' in result:
                    result_placeholder.table(result['data'])
                else:
                    result_placeholder.error("Failed to fetch presence log")

        elif menu == "Lakukan Presensi":
            st.header("Lakukan Presensi")

            st.write(f"""
            <script>
            getCheckpoints('{st.session_state.token}');
            </script>
            """, unsafe_allow_html=True)

            # Use st.empty() to create a placeholder for the checkpoints
            checkpoints_placeholder = st.empty()

            # JavaScript to handle the checkpoints result
            st.write("""
            <script>
            window.addEventListener('message', function(event) {
                if (event.data.type === 'checkpoints') {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: JSON.stringify(event.data.result)
                    }, '*');
                }
            });
            </script>
            """, unsafe_allow_html=True)

            # Handle the checkpoints result
            checkpoints_result = json.loads(st.experimental_get_query_params().get('result', ['{}'])[0])
            if 'data' in checkpoints_result:
                checkpoints = checkpoints_result['data']
                lokasi_options = [checkpoint['gpsckpoint_name'] for checkpoint in checkpoints]
                lokasi = checkpoints_placeholder.selectbox("Pilih lokasi presensi", lokasi_options)

                if st.button("Lakukan Presensi"):
                    checkpoint_id = lokasi_options.index(lokasi)
                    checkpoint_data = checkpoints[checkpoint_id]
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    presence_data = {
                        'latitude': str(
                            float(checkpoint_data['gpsckpoint_latitude']) + random.uniform(0.000000001, 0.00001)),
                        'longitude': str(
                            float(checkpoint_data['gpsckpoint_longitude']) + random.uniform(0.000000001, 0.00001)),
                        'gpsckpoint_id': checkpoint_data['gpsckpoint_id'],
                        'gpsckpoint_name': checkpoint_data['gpsckpoint_name'],
                        'gpsckpoint_radius': checkpoint_data['gpsckpoint_radius'],
                        'timezone': 'WIB',
                        'timezone_name': 'Asia/Jakarta',
                        'time': now_str
                    }

                    st.write(f"""
                    <script>
                    addPresensi({json.dumps(presence_data)}, '{st.session_state.token}');
                    </script>
                    """, unsafe_allow_html=True)

                    # Use st.empty() to create a placeholder for the result
                    result_placeholder = st.empty()

                    # JavaScript to handle the add presensi result
                    st.write("""
                    <script>
                    window.addEventListener('message', function(event) {
                        if (event.data.type === 'addPresensi') {
                            window.parent.postMessage({
                                type: 'streamlit:setComponentValue',
                                value: JSON.stringify(event.data.result)
                            }, '*');
                        }
                    });
                    </script>
                    """, unsafe_allow_html=True)

                    # Handle the result
                    result = json.loads(st.experimental_get_query_params().get('result', ['{}'])[0])
                    if result.get('status') == '200':
                        result_placeholder.success("Presensi Berhasil!")
                    else:
                        result_placeholder.error("Presensi Gagal Dilakukan!")
            else:
                checkpoints_placeholder.warning("No checkpoint data available")

        elif menu == "Logout":
            st.session_state.token = None
            st.session_state.logged_in = False
            st.success("Logout berhasil!")
            st.rerun()


if __name__ == "__main__":
    main()
