import pandas as pd 
from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode, ColumnsAutoSizeMode


# Create the AG Grid from the DataFrame
def df_to_grid(df:pd.DataFrame, theme='streamlit'):
    """ 
    Creates an AG Grid from a DataFrame. 

    df: pd.DataFrame
        DataFrame to convert to AG Grid

    theme: str
        Valid options are:
            streamlit
            alpine
            balham
            material

    Returns:
        AgGrid object
    """
    valid_themes = ['streamlit', 'alpine', 'balham', 'material']
    if theme not in valid_themes:
        raise Exception(f'Theme not in {valid_themes}')

    # allows page arrows to be shown
    custom_css = {"#gridToolBar": {"padding-bottom": "0px !important"}} 
    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_column("Select", checkboxSelection=True, headerCheckboxSelection=True, pinned="left", width=50) # add a check column
    gd.configure_selection(selection_mode='multiple', suppressRowClickSelection=True)
    gd.configure_pagination(enabled=True)
    gridOptions = gd.build()
    
    grid = AgGrid(
        df,
        custom_css=custom_css,
        gridOptions=gridOptions,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        data_return_mode=DataReturnMode.AS_INPUT, 
        update_on='MANUAL',
        theme=theme,
        enable_enterprise_modules=False, # unless we pay aggrid
        allow_unsafe_jscode=True,
        height=300,
        width='100%',
        fit_columns_on_grid_load=True,
    )
    return grid