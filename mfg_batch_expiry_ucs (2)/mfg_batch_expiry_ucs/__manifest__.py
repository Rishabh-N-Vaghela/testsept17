{
    'name': 'UCS Expiry and Manufacturing Date Sync',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Add and synchronize Manufacturing Date and Expiry Date between MO, Lots, and Receipts.',
    'author': 'UCS',
    'license': 'LGPL-3',
    'depends': ['stock', 'product_expiry', 'mrp'],
    'data': [
        'views/stock_move_line_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
