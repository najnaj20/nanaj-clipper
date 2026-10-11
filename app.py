import streamlit as st
from utils import download_audio, transcribe_audio, analyze_viral_potential, download_video, crop_video_vertical
import os

st.set_page_config(page_title="Nanaj Clipper AI", page_icon="🎬")

st.title("🎬 Nanaj Clipper AI")
st.markdown("### Ubah Video Panjang $\rightarrow$ Viral Vertical Clips ✨")

url = st.text_input("Paste Link YouTube di sini:", placeholder="https://www.youtube.com/watch?v=...")

if url:
    if "transcript" not in st.session_state:
        with st.spinner("🚀 Sedang menganalisis audio & mencari hook viral..."):
            try:
                # 1. Download Audio Only
                audio_path = download_audio(url)
                
                # 2. Transcribe
                transcript = transcribe_audio(audio_path)
                st.session_state.transcript = transcript
                
                # 3. AI Viral Scan
                viral_hooks = analyze_viral_potential(transcript)
                st.session_state.viral_hooks = viral_hooks
                
                st.success("Analisis Selesai!")
            except Exception as e:
                st.error(f"Error: {e}")

    if "transcript" in st.session_state:
        st.subheader("🎯 AI Viral Hook Suggestions")
        for hook in st.session_state.viral_hooks:
            with st.expander(f"⏱️ {hook['start']:.1f}s - {hook['end']:.1f}s: {hook['text'][:50]}..."):
                st.write(f"**Reason:** {hook['reason']}")
                if st.button(f"Potong Klip Ini", key=f"btn_{hook['start']}"):
                    st.session_state.selected_start = hook['start']
                    st.session_state.selected_end = hook['end']

        st.divider()
        st.subheader("📝 Full Transcript")
        for seg in st.session_state.transcript:
            st.write(f"[{seg['start']:.1f}s] {seg['text']}")

    if "selected_start" in st.session_state:
        st.divider()
        st.subheader("✂️ Finalizing your Clip")
        start = st.session_state.selected_start
        end = st.session_state.selected_end
        st.info(f"Klip terpilih: {start:.1f}s sampai {end:.1f}s")
        
        if st.button("Generate Vertical Clip 🚀"):
            with st.spinner("Downloading full video & cropping to 9:16..."):
                try:
                    video_path = download_video(url)
                    output_path = crop_video_vertical(video_path, start, end)
                    
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="Download Your Viral Clip ⬇️",
                            data=file,
                            file_name="viral_clip.mp4",
                            mime="video/mp4"
                        )
                    st.success("Klip berhasil dibuat!")
                except Exception as e:
                    st.error(f"Error saat rendering: {e}")
