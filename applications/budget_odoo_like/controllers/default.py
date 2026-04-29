# -*- coding: utf-8 -*-

MODULES = [
    dict(key='res_partner', label='Partner', icon='👥', description='Anagrafica clienti e fornitori.'),
    dict(key='product_product', label='Prodotti', icon='📦', description='Catalogo prodotti e servizi.'),
    dict(key='budget_budget', label='Budget', icon='📊', description='Testata budget annuale per cliente.'),
    dict(key='budget_line', label='Righe Budget', icon='🧾', description='Dettaglio voci di budget e importi pianificati.'),
    dict(key='sale_order', label='Ordini Vendita', icon='🛒', description='Gestione ordini e stato di avanzamento.'),
    dict(key='sale_order_line', label='Righe Ordine', icon='📑', description='Dettaglio prodotti, quantità e prezzi degli ordini.'),
    dict(key='account_move', label='Fatture', icon='🧮', description='Documento fattura con totale e stato pagamenti.'),
    dict(key='account_move_line', label='Righe Fattura', icon='🧷', description='Dettaglio righe fattura con quantità e imponibile.'),
    dict(key='account_payment', label='Pagamenti', icon='💶', description='Registrazione incassi e riconciliazione pagamenti.')
]


def _module_index():
    return {m['key']: i for i, m in enumerate(MODULES)}


def index():
    sections = [
        dict(name='Master Data', items=['res_partner', 'product_product']),
        dict(name='Pianificazione', items=['budget_budget', 'budget_line']),
        dict(name='Ciclo Vendite', items=['sale_order', 'sale_order_line']),
        dict(name='Fatturazione e Incassi', items=['account_move', 'account_move_line', 'account_payment'])
    ]
    modules_by_key = dict((m['key'], m) for m in MODULES)
    for section in sections:
        cards = []
        for key in section['items']:
            module = modules_by_key[key]
            cards.append(dict(
                key=module['key'],
                label=module['label'],
                icon=module['icon'],
                description=module['description'],
                link=URL('crud_table', args=[module['key']])
            ))
        section['cards'] = cards
    return dict(sections=sections)


def crud_table():
    table = request.args(0)
    if table not in db.tables:
        raise HTTP(404)

    module_map = dict((m['key'], m) for m in MODULES)
    current = module_map.get(table, dict(label=table, icon='📄', description='Gestione dati.'))
    idx = _module_index().get(table)

    prev_module = MODULES[idx - 1] if idx not in (None, 0) else None
    next_module = MODULES[idx + 1] if idx is not None and idx < len(MODULES) - 1 else None

    grid = SQLFORM.smartgrid(
        db[table],
        linked_tables=['sale_order_line', 'account_move_line'],
        user_signature=False,
        details=True,
        create=True,
        editable=True,
        deletable=True,
    )

    return dict(
        grid=grid,
        table=table,
        title=current['label'],
        icon=current['icon'],
        description=current['description'],
        prev_module=prev_module,
        next_module=next_module,
        modules=MODULES,
    )
