"""A module to get the NFT cache from OpenSea API."""

import pathlib
import requests
import math
import tqdm

from collections import defaultdict
from lazy_property import LazyWritableProperty as lazy_property

import numpy as np
import pandas as pd

from bokeh.layouts import Spacer, row, column
from bokeh.models.widgets import Tabs, Panel

import plotly.graph_objs as go
from plotly.subplots import make_subplots

try:
    from nft_research.utils.plotting_utils import plot_table_from_df, bokeh_plot_by_date, bokeh_heading
    from nft_research.utils.timeit import timeit
    from nft_research.utils.logger import get_standard_logger
except ModuleNotFoundError:
    from utils.plotting_utils import plot_table_from_df, bokeh_plot_by_date, bokeh_heading
    from utils.timeit import timeit
    from utils.logger import get_standard_logger


class NftApi(object):
    """
    Base class to handle NFT API requests.
    """
    _opensea_assets_url = "https://api.opensea.io/api/v1/assets"
    _opensea_events_url = "https://api.opensea.io/api/v1/events"

    def __init__(self, contract_address, count_assets=10000, use_cache=True):
        """Initialise a new instance of the NFT API object."""
        self.logger = get_standard_logger(name='NftAPI',
                                          log_dir=self.base_dir.joinpath('logs'))
        self.contract_address = contract_address
        self.count_assets = count_assets
        self.use_cache = use_cache

    @lazy_property
    def base_dir(self):
        """Lazy property to hold the base dir."""
        dir = pathlib.Path(__file__).parent.absolute()
        dir.mkdir(exist_ok=True)
        return dir

    @lazy_property
    def cache_dir(self):
        """Lazy property to hold the cache director."""
        cache_dir = self.base_dir.joinpath('cache')
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    @lazy_property
    def assets_cache_path(self):
        """Lazy property to hold the test raw assets path."""
        dir = self.cache_dir.joinpath('assets')
        dir.mkdir(exist_ok=True)
        return dir.joinpath(f'{self.contract_address}.parquet')

    @lazy_property
    def traits_cache_path(self):
        """Lazy property to hold the test raw assets path."""
        dir = self.cache_dir.joinpath('traits')
        dir.mkdir(exist_ok=True)
        return dir.joinpath(f'{self.contract_address}.parquet')

    @lazy_property
    def raw_events_cache_path(self):
        """Lazy property to hold the test raw assets path."""
        dir = self.cache_dir.joinpath('events')
        dir.mkdir(exist_ok=True)
        return dir.joinpath(f'{self.contract_address}.parquet')

    @lazy_property
    def assets_data(self):
        if self.use_cache and self.assets_cache_path.exists():
            return pd.read_parquet(self.assets_cache_path)
        else:
            return self.raw_assets_data['assets']

    @lazy_property
    def raw_traits_data(self):
        if self.use_cache and self.traits_cache_path.exists():
            return pd.read_parquet(self.traits_cache_path)
        else:
            return self.raw_assets_data['traits']

    @lazy_property
    def traits_data(self):
        """Lazy property to hold the traits data."""
        df = self.raw_traits_data.set_index(['name', 'trait_type'])['value'].unstack().fillna('')
        # XXX Fixme: Want to add some basic traits data.
        return df

    @lazy_property
    def raw_assets_data(self):
        """Lazy property to hold the raw asset cache."""
        data = self.get_raw_assets_data()
        output = defaultdict(dict)
        traits_data = []
        for row in data:
            token_id = row['token_id']
            try:
                output[token_id]['creator_username'] = row['creator']['user']['username']
            except:
                output[token_id]['creator_username'] = None
            try:
                output[token_id]['creator_address'] = row['creator']['address']
            except:
                output[token_id]['creator_address'] = None
            try:
                output[token_id]['owner_username'] = row['owner']['user']['username']
            except:
                output[token_id]['owner_username'] = None

            output[token_id]['name'] = row['name']
            output[token_id]['owner_address'] = row['owner']['address']

            # Handle the traits cache.
            asset_trait_df = pd.DataFrame(row['traits'])
            asset_trait_df['name'] = row['name']
            traits_data.extend(asset_trait_df.itertuples(index=False))

            # Handle the Sales cache.
            output[token_id]['num_sales'] = int(row['num_sales'])
            if isinstance(row['sell_orders'], (tuple, list)):
                for i, order in enumerate(row['sell_orders']):
                    price = float(order['current_price']) / np.power(10, order['payment_token_contract']['decimals'])
                    eth_price = price * float(order['payment_token_contract']['eth_price'])
                    usd_price = price * float(order['payment_token_contract']['usd_price'])
                    key = f'sell_order_{i+1}'
                    output[token_id][f'{key}_sale_kind'] = order['sale_kind']
                    output[token_id][f'{key}_created_date'] = order['created_date']
                    output[token_id][f'{key}_closing_date'] = order['closing_date']
                    output[token_id][f'{key}_eth_price'] = eth_price
                    output[token_id][f'{key}_usd_price'] = usd_price
        assets_df = pd.DataFrame.from_dict(output).T
        assets_df.to_parquet(self.assets_cache_path)
        traits_df = pd.DataFrame(traits_data)
        for col in traits_df.columns:
            traits_df[col] = traits_df[col].astype(str)
        traits_df.to_parquet(self.traits_cache_path)
        return {'assets': assets_df,
                'traits': traits_data}

    @timeit
    def get_raw_assets_data(self):
        """Function to get the raw assets cache from Opensea"""
        iterations = math.ceil(self.count_assets / 30)
        output_data = []
        for i in tqdm.tqdm(range(0, iterations)):
            params = {'token_ids': list(range((i * 30)+1, (i * 30)+30)),
                      'asset_contract_address': self.contract_address,
                      'order_direction': 'desc',
                      'offset': '0',
                      'limit': '30'}
            response = requests.request('GET', type(self)._opensea_assets_url, params=params)
            if response.status_code != 200:
                self.logger.warn(f'Error collecting raw assets cache: {response.status_code}')
                break
            data = response.json()['assets']
            if not len(data):
                break
            output_data.extend(data)
        return output_data

    @lazy_property
    def events_data(self):
        if self.use_cache and self.raw_events_cache_path.exists():
            return pd.read_parquet(self.raw_events_cache_path)
        else:
            return self.raw_events_data

    @lazy_property
    def raw_events_data(self):
        """Lazy property to hold the raw event cache."""
        df = pd.DataFrame.from_dict(self.parse_raw_events_data(data=self.get_raw_events_data())).T
        df['eth_price'] = df['total_price'].divide(np.power(10, df['payment_token_decimals'])).multiply(df['eth_x_token_price'])
        df['usd_price'] = df['total_price'].divide(np.power(10, df['payment_token_decimals'])).multiply(df['usd_x_token_price'])
        df.index.name = 'transaction_hash'
        df.to_parquet(self.raw_events_cache_path)
        return df

    @timeit
    def get_raw_events_data(self):
        """Function to get the raw assets cache from Opensea"""
        # XXX Fixme: Need to think of better way to get number of iterations needed.
        # XXX Fixme: Seems opensea have changed access settings for events data, need to investigate
        output_data = []
        for i in tqdm.tqdm(range(0, 500)):
            params = {'asset_contract_address': self.contract_address,
                      'event_type': 'successful',
                      'only_opensea': 'true',
                      'offset': i*30,
                      'limit': '30'}
            headers = {'Accept': 'application/json'}
            response = requests.request('GET', type(self)._opensea_events_url, headers=headers, params=params)
            if response.status_code != 200:
                self.logger.warn(f'Error collecting raw events cache: {response.status_code}')
                break
            data = response.json()['asset_events']
            if not len(data):
                break
            output_data.extend(data)
        return output_data

    @timeit
    def parse_raw_events_data(self, data):
        """Function to parse the raw events cache."""
        output = defaultdict(dict)
        for row in data:
            transaction_hash = row['transaction']['transaction_hash']
            output[transaction_hash]['is_bundle'] = False
            if row['asset'] != None:
                output[transaction_hash]['asset_id'] = row['asset']['token_id']
            elif row['asset_bundle'] != None:
                output[transaction_hash]['asset_id'] = ';'.join([asset['token_id'] for asset in row['asset_bundle']['assets']])
                output[transaction_hash]['is_bundle'] = True

            output[transaction_hash]['seller_address'] = row['seller']['address']
            output[transaction_hash]['buyer_address'] = row['winner_account']['address']

            try:
                output[transaction_hash]['seller_username'] = row['seller']['user']['username']
            except:
                output[transaction_hash]['seller_username'] = None
            try:
                output[transaction_hash]['buyer_username'] = row['winner_account']['user']['username']
            except:
                output[transaction_hash]['buyer_username'] = None

            output[transaction_hash]['timestamp'] = pd.to_datetime(row['transaction']['timestamp'])
            output[transaction_hash]['total_price'] = float(row['total_price'])
            output[transaction_hash]['payment_token'] = row['payment_token']['symbol']
            output[transaction_hash]['payment_token_decimals'] = row['payment_token']['decimals']
            output[transaction_hash]['usd_x_token_price'] = float(row['payment_token']['usd_price'])
            output[transaction_hash]['eth_x_token_price'] = float(row['payment_token']['eth_price'])
        return output

    @lazy_property
    def transactions_per_day(self):
        """Lazy property to hold the bokeh plot for the number of sales per day."""
        data = self.events_data.copy(deep=True)
        df = data.reset_index().resample('D', on='timestamp')['transaction_hash'].count()
        return df

    @lazy_property
    def rkl_boost_values(self):
        """Lazy property to hold the RKL trait values."""
        sale_df = self.assets_data.set_index('name').copy(deep=True)
        sale_price = sale_df[sale_df['sell_order_1_sale_kind'].eq(0)]['sell_order_1_eth_price'].to_frame(name='eth_sale_price')
        if self.contract_address != '0xef0182dc0574cd5874494a120750fd222fdb909a':
            # This won't exist for all projects, so need to add a placeholder.
            sale_price['sum_boost_scores'] = 0
            df = sale_price['sum_boost_scores'].to_frame(name='sum_boost_scores').copy(deep=True)
        else:
            df = self.traits_data.reindex(['Defense', 'Vision', 'Shooting', 'Finish'], axis=1).copy(deep=True)
            df['sum_boost_scores'] = df.astype(float).sum(axis=1)
        return df.merge(sale_price, left_index=True, right_index=True, how='left')

    @lazy_property
    def plotter(self):
        """Lazy property to hold the plotter object."""
        return NftDataPlotter(api=self)

    @lazy_property
    def plotly_plotter(self):
        """Lazy property to hold the plotter object."""
        return PlotlyNftDataPlotter(api=self)


class NftDataPlotter(object):
    """
    Class to plot the details for the NFT Project.
    """

    def __init__(self, api):
        """Initialise a new instance of the NfTDataPlotter."""
        self.api = api
        self.plot_width = 1200
        self.plot_height = 600

    @lazy_property
    def bokeh_report(self):
        """Lazy property to hold the Bokeh Report."""
        return Tabs(tabs=[self.bokeh_events_panel])

    @lazy_property
    def bokeh_events_panel(self):
        """Lazy property to hold the bokeh events panel."""
        return Panel(child=column(bokeh_heading(heading='NFT Events Overview',
                                                size=200,
                                                width=self.plot_width),
                                  Spacer(width=self.plot_width, height=20),
                                  bokeh_heading(heading=f'Contract Address: {self.api.contract_address}',
                                                size=100,
                                                width=self.plot_width),
                                  Spacer(width=self.plot_width, height=20),
                                  row(self.bokeh_transactions_per_day, self.bokeh_avg_transaction_price_per_day)),
                     title='NFT Events')

    @lazy_property
    def bokeh_transactions_per_day(self):
        """Lazy property to hold the bokeh plot for the number of sales per day."""
        data = self.api.events_data.copy(deep=True)
        df = data.reset_index().resample('D', on='timestamp')['transaction_hash'].count()
        return bokeh_plot_by_date(df=df.to_frame(name='transactions_per_day'),
                                  title='Transactions Per Day',
                                  y_axis_label='Transactions per day',
                                  y_axis_number_format='0',
                                  plot_width=int(self.plot_width / 2),
                                  plot_height=self.plot_height)

    @lazy_property
    def bokeh_avg_transaction_price_per_day(self):
        """Lazy property to hold the bokeh plot for the number of sales per day."""
        data = self.api.events_data.copy(deep=True)
        count_df = data.reset_index().resample('D', on='timestamp')['transaction_hash'].count()
        price_df = data.resample('D', on='timestamp')['eth_price'].sum()
        df = price_df.divide(count_df).to_frame(name='avg_transaction_price_per_day')
        return bokeh_plot_by_date(df=df,
                                  title='Average ETH Transaction Price Per Day',
                                  y_axis_label='Price per day (ETH)',
                                  y_axis_number_format='0.00',
                                  plot_width=int(self.plot_width / 2),
                                  plot_height=self.plot_height)


class PlotlyNftDataPlotter(object):
    """
    Class to plot the details for the NFT Project.
    """

    def __init__(self, api):
        """Initialise a new instance of the NfTDataPlotter."""
        self.api = api
        self.plot_width = 1200
        self.plot_height = 600

    @timeit
    def generate_report(self):
        """Lazy property to hold the Bokeh Report."""
        return self.report_fig.show()

    @lazy_property
    def report_fig(self):
        """Function to generate report."""
        fig = make_subplots(rows=2,
                            cols=2,
                            column_width=[0.4, 0.6],
                            row_heights=[0.5, 0.5],
                            specs=[[{'type': 'histogram', 'rowspan': 2}, {'type': 'bar'}],
                                   [None, {'type': 'scatter'}]])
        fig.add_trace(self.plotly_relative_value,
                      row=1,
                      col=1)
        fig.add_trace(self.plotly_transactions_per_day,
                      row=1,
                      col=2)
        fig.add_trace(self.plotly_avg_transaction_price_per_day,
                      row=2,
                      col=2)
        fig.update_xaxes(tickangle=45)
        fig.update_layout(template='plotly_dark')
        return fig

    @lazy_property
    def plotly_transactions_per_day(self):
        """Lazy property to hold the bokeh plot for the number of sales per day."""
        data = self.api.events_data.copy(deep=True)
        df = data.reset_index().resample('D', on='timestamp')['transaction_hash'].count()
        return go.Bar(x=df.index,
                      y=df.values,
                      marker=dict(color='crimson'),
                      showlegend=False)

    @lazy_property
    def plotly_relative_value(self):
        """Lazy property to hold the bokeh plot for the number of sales per day."""
        # XXX Fixme: Need to remove the test version below.
        data = self.api.assets_data.copy(deep=True)
        prices = data[data['sell_order_1_eth_price'] < 5].copy(deep=True)
        return go.Histogram(histfunc='count',
                            x=prices['sell_order_1_eth_price'].dropna(),
                            name='ETH Sale Price')

    @lazy_property
    def plotly_avg_transaction_price_per_day(self):
        """Lazy property to hold the plotly plot for the average price of the sales per day."""
        data = self.api.events_data.copy(deep=True)
        # count_df = cache.reset_index().resample('D', on='timestamp')['transaction_hash'].count()
        # price_df = cache.resample('D', on='timestamp')['eth_price'].sum()
        # df = price_df.divide(count_df)  # .to_frame(name='avg_transaction_price_per_day')
        return go.Scatter(x=data.timestamp,
                          y=data.eth_price)


if __name__ == '__main__':
    rumble_kongs_contract_address = '0xef0182dc0574cd5874494a120750fd222fdb909a'
    rebel_bots_contract_address = '0xbbe23e96c48030dc5d4906e73c4876c254100d33'
    api = NftApi(contract_address=rumble_kongs_contract_address, use_cache=True)

    # To save traits:
    # api.traits_data.to_csv('...')

    # To get RKL boost values:
    api.rkl_boost_values

    # Events data currently not working in Opensea API. To investigate.
    api.events_data
