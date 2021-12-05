"""A module to get the NFT cache from OpenSea API."""
import dash
from dash import dcc
from dash import html
import plotly.express as px

try:
    from nft_api import NftApi
except ModuleNotFoundError:
    from nft_research.nft_api import NftApi

rumble_kongs_contract_address = '0xef0182dc0574cd5874494a120750fd222fdb909a'
rebel_bots_contract_address = '0xbbe23e96c48030dc5d4906e73c4876c254100d33'

api = NftApi(contract_address=rumble_kongs_contract_address, use_cache=True)
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'NFT Data Analytics'

app.layout = html.Div(
    children=[
        html.Div(children=[
            html.H1(
                children=f'PRT Capital Research',
                className='header-title',
            ),
            html.P(
                children=f'Contract Address of Research: {api.contract_address}',
                className='header-description',
            ),
        ],
            className='header',
        ),
        html.Div(
            children=[
                # html.Div(
                #     dcc.Graph(
                #         figure={
                #             'cache': [
                #                 {
                #                     'x': api.transactions_per_day.index,
                #                     'y': api.transactions_per_day.values,
                #                     'type': 'bar',
                #                 },
                #             ],
                #             'layout': {'title': 'Transactions Per Day'},
                #         },
                #     ),
                #     className='card',
                # ),
                html.Div(
                    dcc.Graph(
                        figure={
                            'cache': [
                                {
                                    'x': api.assets_data[api.assets_data['sell_order_1_eth_price'] < 5.0]['sell_order_1_eth_price'],
                                    'histfunc': 'count',
                                    'type': 'histogram',
                                },
                            ],
                            'layout': {
                                'title': 'Histogram of Live for Sales',
                                'bargap': 0.1
                            },
                        },
                    ),
                    className='card',
                ),
                html.Div(
                    children=[
                        html.Div([
                            html.Div([
                                'Max Eth Price: ',
                                dcc.Input(
                                    id='max_eth_input',
                                    value=9999,
                                    type='text')
                            ], style={'width': '48%', 'display': 'inline-block'}),
                            html.Div([
                                dcc.Dropdown(
                                    id='x_axis_value',
                                    options=[{'label': i, 'value': i} for i in
                                             ['Defense', 'Vision', 'Shooting', 'Finish', 'sum_boost_scores']],
                                    value='Defense'
                                ),
                            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
                        ], style={'display': 'flex', 'flex-direction': 'row', 'padding': 10}),
                        dcc.Graph(id='all_boost_scatter'),
                    ], className='card', style={'padding': 10},
                ),
            ], className='wrapper',
        ),
    ]
)


@app.callback(
    dash.dependencies.Output('all_boost_scatter', 'figure'),
    [dash.dependencies.Input('max_eth_input', 'value'),
     dash.dependencies.Input('x_axis_value', 'value')]
)
def update_all_boost_values_graph(max_eth_input, x_axis_value, title='Shooting'):
    df = api.rkl_boost_values.copy(deep=True)
    print(max_eth_input)
    df = df[df['eth_sale_price'] <= float(max_eth_input)].copy(deep=True)
    fig = px.scatter(x=df[x_axis_value].astype(float),
                     y=df['eth_sale_price'].astype(float),
                     hover_name=df.index)
    # fig.update_layout(margin={'1': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')
    fig.update_xaxes(title=x_axis_value)
    fig.update_yaxes(title='ETH Price')
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
    # Graphs to add:
    # - Quantity for sale vs not for sale
    # - Daily Floor Price
    # - Daily for sale pct
    # - Daily ETH value traded
    # - Daily unique addresses
    # - Daily avg price vs floor price (Are they traded above floor price?)
    # - Scatter plot Rarity vs ETH Price
    # - Overview of project whales, are they buying or selling?
    # - Overview of the rarity items / what is rare or non-rare?
    # - How many for sale up to each price point? Cumulative for sale
