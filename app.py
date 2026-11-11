import streamlit as st
from PIL import Image
from ai_engine import analyze_dispute
from paypal_service import execute_sandbox_resolution

# Page setup & styling
st.set_page_config(page_title="PayPal Dispute Copilot", page_icon="💳", layout="wide")

# Custom PayPal navy header styling
st.markdown(
    """
    <style>
    .main-title { font-size: 32px; font-weight: 700; color: #003087; margin-bottom: 0px; }
    .sub-title { font-size: 16px; color: #0079C1; margin-bottom: 20px; }
    .card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #003087; margin-bottom: 12px; }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">💳 PayPal Dispute Copilot</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-title">AI-Assisted Evidence Gathering & 30-Second Human-in-the-Loop Resolution</div>',
    unsafe_allow_html=True,
)

# Tabs separating the user journey and support agent journey
tab1, tab2 = st.tabs(
    [
        "👤 Buyer Portal (Smart Evidence Intake)",
        "🛡️ Agent Review Dashboard (Support View)",
    ]
)

# Shared state to pass data between tabs
if "analysis" not in st.session_state:
    st.session_state.analysis = None

# ==========================================
# TAB 1: BUYER PORTAL
# ==========================================
with tab1:
    st.subheader("Open a Transaction Dispute")

    col_input1, col_input2 = st.columns([2, 1])

    with col_input1:
        order_id = st.selectbox(
            "Select Transaction",
            [
                "Order #PP-8492 ($180.00 - UltraSharp Monitor)",
                "Order #PP-1049 ($120.00 - Wireless Headphones)",
                "Order #PP-3021 ($45.00 - Mechanical Keyboard)",
            ],
        )
        claim_text = st.text_area(
            "What went wrong?",
            value="I bought the item, but when it arrived, the packaging was completely damaged and the item was broken. The seller is not replying to my messages.",
            height=130,
        )

    with col_input2:
        uploaded_image = st.file_uploader(
            "Upload Evidence (Photo of item, damage, or shipping slip)",
            type=["jpg", "png", "jpeg"],
        )
        if uploaded_image:
            st.image(
                uploaded_image,
                caption="Uploaded Evidence Preview",
                use_container_width=True,
            )

    if st.button("Submit to Dispute Copilot", type="primary", use_container_width=True):
        with st.spinner(
            "AI analyzing evidence against PayPal Buyer Protection standards..."
        ):
            # Real call to your backend AI engine
            result = analyze_dispute(claim_text, uploaded_image)
            st.session_state.analysis = result
            st.success(
                "Claim processed! Switch to the 'Agent Review Dashboard' tab to inspect the reviewer dossier."
            )

# ==========================================
# TAB 2: AGENT REVIEW DASHBOARD
# ==========================================
with tab2:
    st.subheader("Support Specialist One-Page Dossier")
    data = st.session_state.analysis

    if not data:
        st.info(
            "ℹ️ No active dispute submitted yet. Submit a claim on the Buyer Portal first."
        )
    else:
        # Check for missing evidence
        if data.get("missing_evidence") and not data.get("is_complete"):
            st.warning(
                "⚠️ **Action Required from Buyer (Missing Proof):** "
                + ", ".join(data["missing_evidence"])
            )
        else:
            st.success(
                "✅ **Evidence Pack Complete:** All mandatory photographic and transactional proof verified."
            )

        col_left, col_right = st.columns([1, 1])

        # Left Panel: Timeline & Policies
        with col_left:
            st.markdown("### 📅 Automated Incident Timeline")
            timeline = data.get("timeline", [])
            if timeline:
                for item in timeline:
                    st.markdown(
                        f"• **{item.get('date', 'N/A')}**: {item.get('event', '')}"
                    )
            else:
                st.write("No timeline events generated.")

            st.divider()
            st.markdown("### 📜 Verified Policy Alignment")
            st.write(f"**Dispute Type:** {data.get('claim_type', 'N/A')}")
            agent_info = data.get("agent_dossier", {})
            st.write(f"**Applicable Clause:** {agent_info.get('policy_fit', 'N/A')}")

        # Right Panel: Recommendation & Decision
        with col_right:
            st.markdown("### 🎯 Copilot Recommendation")
            agent_info = data.get("agent_dossier", {})

            st.metric(
                label="AI Confidence Score",
                value=f"{agent_info.get('confidence_score', 0)}%",
            )
            st.info(
                f"**Suggested Ruling:** {agent_info.get('recommended_action', 'REQUEST_INFO')}"
            )
            st.write(f"**Case Brief:** {agent_info.get('summary', '')}")
            st.caption(f"**Reasoning:** {agent_info.get('rationale', '')}")

            st.divider()
st.markdown("#### Human Reviewer Decision")
btn1, btn2 = st.columns(2)

if btn1.button("✅ Approve & Release Refund", type="primary", use_container_width=True):
    with st.spinner(
        "Connecting to PayPal Developer Sandbox & authorizing transaction..."
    ):
        paypal_res = execute_sandbox_resolution(amount="180.00")

        if paypal_res.get("success"):
            st.balloons()
            st.success("Case Closed: Refund Authorized on PayPal Developer Platform!")
            st.info(f"**PayPal Sandbox Order ID:** `{paypal_res.get('order_id')}`")
            st.caption(f"Status: **{paypal_res.get('status')}** via PayPal REST API v2")
        else:
            st.error(f"PayPal Sandbox Error: {paypal_res.get('error')}")

if btn2.button("⚠️ Request Tier-2 Escalation", use_container_width=True):
    st.warning("Case flagged for manual supervisor review.")
