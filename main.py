import streamlit as st
from streamlit import session_state as state
import hydralit as hy

import os
import musicpy as mp
from utils.app_utils.startapp import check_pygame_compatibility


st.set_page_config(
  page_title="MIDI Generator",
  page_icon=None,
  layout="wide",
  initial_sidebar_state="collapsed",
)


#---Start app---#
def run_app():  
  check_pygame_compatibility()
  
  state['user_level'] = state.get('user_level', 1)
  user_level = state.get("user_level", 1)

  #---Start Hydra instance---#
  hydra_theme = None # init hydra theme
  

  with st.sidebar:
    if state['pygame_compatible'] == True:
      if st.button('Stop all sounds'):
        mp.stopall()




  app = hy.HydraApp(
    hide_streamlit_markers=False,
    use_navbar=True, 
    navbar_sticky=False,
    navbar_animation=True,
  )

  #specify a custom loading app for a custom transition between apps, this includes a nice custom spinner
  from apps._loading import MyLoadingApp
  app.add_loader_app(MyLoadingApp(delay=0))

  #---Add apps from folder---#
  @app.addapp(is_home=True, title='Home')
  def homeApp():
    from apps.home import main
    main()

  @app.addapp(title='Create MIDI')
  def midiGenApp():
    from apps.midigen import main
    main()


  #--- Level 1 apps ---#
  if user_level < 2: 
    pass

  #--- Level 2 apps ---#
  if user_level >= 2:
    pass



  def build_navigation(user_level=1):
    complex_nav = {}
    
    # Always add Home first
    complex_nav["Home"] = ['Home']

    # Other apps
    complex_nav["Create MIDI"] = ['Create MIDI']

    return complex_nav
  

  complex_nav = build_navigation(user_level)
  app.run(complex_nav=complex_nav)



    


if __name__ == '__main__':
  run_app()