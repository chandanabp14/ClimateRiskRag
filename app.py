import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# Streamlit App Title
st.title("🚀 Langflow Astra API - Climate Risk Assessment")

# User input
user_input = st.text_input("💬 Enter your request:", "give me 1 week pune trip plan according to todays date")

# Get URL and token from environment, fall back to runtime input in sidebar
default_url = os.getenv("LANGFLOW_URL", "https://astra.datastax.com/langflow/4346ee0f-2d03-4a37-a3d0-9bc883dd52ac/flow/7bbbae4d-8c24-41a7-8a68-69ed2299de67")
default_token = os.getenv("ASTRA_TOKEN", "")

st.sidebar.header("Configuration")
url = st.sidebar.text_input("Langflow API URL", value=default_url, help="Full Langflow run endpoint URL")
token_input = st.sidebar.text_input("Astra token (keep secret)", value=default_token, type="password")
# If the token field already contains a full Authorization header (e.g. "Bearer ..."), allow user to mark it
use_raw_header = st.sidebar.checkbox("Token is full Authorization header (use value as-is)", value=False)

if not url:
    st.sidebar.error("Please set LANGFLOW_URL in your .env or paste the endpoint URL here.")

if not token_input:
    st.sidebar.warning("No token provided. Set ASTRA_TOKEN in .env or paste it here to authenticate.")

def build_auth_header(token: str, raw: bool = False) -> str:
    if not token:
        return ""
    token = token.strip()
    if raw:
        return token
    # If token already seems like a bearer header, keep as-is
    if token.lower().startswith("bearer "):
        return token
    # Some Astra tokens include a prefix like 'AstraCS:...'. Many services expect 'Bearer <token>'
    # We'll default to prefixing with 'Bearer '
    return f"Bearer {token}"

headers = {
    "Content-Type": "application/json",
}
auth_header = build_auth_header(token_input, raw=use_raw_header)
if auth_header:
    headers["Authorization"] = auth_header

# Button to send input
if st.button("Send to Langflow"):
    if not url:
        st.error("Endpoint URL is missing. Provide LANGFLOW_URL in .env or in the sidebar.")
    elif not auth_header:
        st.error("Authentication token missing. Provide ASTRA_TOKEN in .env or in the sidebar.")
    else:
        payload = {
            "input_value": user_input,
            "output_type": "chat",
            "input_type": "chat"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            # Provide richer debug info on failure
            if not response.ok:
                st.error(f"❌ API responded with status {response.status_code}")
                try:
                    st.text(response.text)
                except Exception:
                    st.write(response.content)
                response.raise_for_status()

            result = response.json()

            # Extract only the "text" field from nested JSON
            try:
                text_output = result["outputs"][0]["outputs"][0]["results"]["message"]["data"]["text"]
                st.success("✅ Result")
                st.write(text_output)
            except (KeyError, IndexError):
                st.error("⚠️ Could not extract text from response; showing full response below")
                st.json(result)

        except requests.exceptions.HTTPError as e:
            # Try to give a helpful message for 401/403
            if response is not None and response.status_code in (401, 403):
                st.error("❌ Authentication failed (401/403). Check your Astra token and permissions.")
            else:
                st.error(f"❌ API request error: {e}")
            try:
                st.text(response.text)
            except Exception:
                pass
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API request error: {e}")
        except ValueError as e:
            st.error(f"❌ Response parsing error: {e}")

st.markdown("---")
st.info("Do not commit secrets to source control. Use a .env file or the sidebar to provide the token.")

