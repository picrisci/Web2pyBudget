# -*- coding: utf-8 -*-


def index():
    menu = [
        ('Partner', URL('crud_table', args=['res_partner'])),
        ('Prodotti', URL('crud_table', args=['product_product'])),
        ('Budget', URL('crud_table', args=['budget_budget'])),
        ('Righe Budget', URL('crud_table', args=['budget_line'])),
        ('Ordini Vendita', URL('crud_table', args=['sale_order'])),
        ('Righe Ordine', URL('crud_table', args=['sale_order_line'])),
        ('Fatture', URL('crud_table', args=['account_move'])),
        ('Righe Fattura', URL('crud_table', args=['account_move_line'])),
        ('Pagamenti', URL('crud_table', args=['account_payment']))
    ]
    return dict(menu=menu)


def crud_table():
    table = request.args(0)
    if table not in db.tables:
        raise HTTP(404)
    grid = SQLFORM.smartgrid(db[table], linked_tables=['sale_order_line', 'account_move_line'], user_signature=False)
    return dict(grid=grid, table=table)
