"""Module to hold all the plotting utils functions."""

from bokeh.plotting import show, figure, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models import NumeralTickFormatter, DatetimeTickFormatter
from bokeh.models.widgets import DataTable, TableColumn, Div
from bokeh.models.widgets import HTMLTemplateFormatter, NumberFormatter, StringFormatter
from bokeh.layouts import Spacer, row, column
from bokeh.transform import factor_cmap

from bokeh.palettes import Category20_20 as extended_palette

from math import pi
import numpy as np


def bokeh_plot_by_date(df, colours=None, title='', x_axis_label='Date', y_axis_label='Cumulative P&L (USD)',
                       y_axis_number_format='0.0a', plot_cols=None, plot_width=600, plot_height=600):
    """Function to create a bokeh plot by date."""
    df.index.name = 'date'
    plot_cols = plot_cols if isinstance(plot_cols, (list, tuple)) else df.columns.tolist()
    df['date_format'] = df.index.format()
    data_source = ColumnDataSource(df.reset_index())
    fig = figure(title=title,
                 width=int(plot_width),
                 height=int(plot_height))

    for i, column in enumerate(plot_cols):
        fig.line(source=data_source,
                 x='date',
                 y=column,
                 color=extended_palette[i] if not isinstance(colours, (list, tuple)) else colours[i],
                 legend_label=f'{column} ',
                 alpha=0.7)
    fig.legend.location = 'top_left'
    fig.legend.click_policy = 'hide'
    fig.xaxis.major_label_orientation = pi / 4
    fig.yaxis.formatter = NumeralTickFormatter(format=y_axis_number_format)
    fig.xaxis.formatter = DatetimeTickFormatter(days=['%d-%b-%y'])
    fig.xaxis.axis_label = x_axis_label
    fig.yaxis.axis_label = y_axis_label
    return fig


def plot_table_from_df(df, width=800, height=120, colour=[], commify=[], percentage=[],
                       percentage_2dp=[], percentage_3dp=[], dollarise=[], round=[], ints=[]):
    """Function to plot a bokeh table from the provided DataFrame."""
    data_source = ColumnDataSource(df)

    template = """
    <div style="color:<%=
        (function colorfromint(){
            if(value > 0){return ("green")}
            else if (value < 0){return("red")}
            else {return("black")}
            }()) %>;">
    <%= value %></div>        
    """

    format_dict = {}
    for col in df.columns.tolist():
        if col in commify:
            if col in dollarise:
                format_dict[col] = NumberFormatter(format='%0,0[.]')
            else:
                format_dict[col] = NumberFormatter(format='0,0[.]')
        elif col in percentage:
            format_dict[col] = NumberFormatter(format='0.0%')
        elif col in percentage_2dp:
            format_dict[col] = NumberFormatter(format='0.00%')
        elif col in percentage_3dp:
            format_dict[col] = NumberFormatter(format='0.000%')
        elif col in round:
            format_dict[col] = NumberFormatter(format='0.00')
        elif col in ints:
            format_dict[col] = NumberFormatter(format='0')
        elif col in colour:
            format_dict[col] = HTMLTemplateFormatter(template=template)
        else:
            format_dict[col] = StringFormatter()

    data_columns = [TableColumn(field=x, title=x.replace('_', ' ').title(), formatter=format_dict[x])
                    for x in list(df.columns)]
    return DataTable(source=data_source,
                     columns=data_columns,
                     width=width,
                     height=height,
                     index_position=None)


def bokeh_heading(heading, width, size=100, align='center', colour='navy'):
    return Div(text=f'{heading}<br>',
               style={'font': 'Segoe UI', 'font_size': f'{size}%', 'color': colour, 'text-align': align},
               width=width)

