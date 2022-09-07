# Copyright 2021-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

{
    'name': "Sale Shipping Terms",
    'summary': """
        This module allows to use shipping terms""",
    'version': "15.0.1.0.0",
    'category': 'Uncategorized',
    'website': "http://sodexis.com/",
    'author': "Sodexis",
    'license': 'OPL-1',
    'installable': True,
    'images': ['images/main_screenshot.png'],
    'depends': [
        'delivery'
        ],
    'data': [
        'data/sale_ship_term_data.xml',
        'views/sale_view.xml',
        'views/stock_picking_view.xml',
        'views/account_invoice_view.xml',
        'views/res_config_settings_views.xml',
        'views/partner_views.xml',
    ],
}
