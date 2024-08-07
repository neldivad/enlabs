import streamlit as st 
import streamlit.components.v1 as components


def main():
    st.write("""
        Welcome to the MIDI Generator app! This app allows you to create custom MIDI files by selecting various musical parameters.
        Follow the tutorials below to get started, or dive right in using the MIDI Generator. 
    """)

    st.subheader('Features')
    st.write("""
        - **Key and Mode Selection**: Choose the musical key and mode for your composition.
        - **BPM and Length**: Adjust the tempo and length of your song.
        - **Chord Progressions**: Select from predefined chord progressions.
        - **Instrument Selection**: Choose instruments for melody and chords.
        - **Chord and Melody Customization**: Define chord durations and intervals, as well as melody rhythms.
    """)

    st.subheader('Tutorials')
    with st.expander('Basic Usage'):
        st.write("""
            1. **Select Parameters**: Open the MIDI Generator section and fill out the form with your desired musical parameters.
            2. **Generate MIDI**: Submit the form to generate your custom MIDI file.
            3. **Play and Download**: Use the MIDI Player to listen to your creation and download it as a MIDI file.
        """)

    with st.expander('Advanced Customization'):
        st.write("""
            Learn how to fine-tune your compositions with advanced options such as:
            - Custom chord intervals and durations
            - Unique melody rhythms and instruments
        """)

    st.subheader('Get Started')
    st.write("""
        Ready to create your own MIDI files? Head over to the "Create MIDI" section below to start composing!
    """)

    st.divider()
    st.write("""
        *We are looking for partners, contributors, students, developers, and composors. Join our community on Discord from sidebar to get involved!*
    """)